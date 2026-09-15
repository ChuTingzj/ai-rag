import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  NotFoundException,
  ServiceUnavailableException,
} from "@nestjs/common";
import {
  HEADER_INTERNAL_TOKEN,
  HEADER_REQUEST_ID,
  HEADER_USER_ID,
} from "@ai-rag/nest-common";

import { encryptConnectorConfig } from "../fernet";
import { PrismaService } from "../prisma/prisma.service";
import { FeishuConnectorCreateDto } from "./connectors.dto";

@Injectable()
export class ConnectorsService {
  constructor(private readonly prisma: PrismaService) {}

  private encryptionSecret(): string {
    const secret =
      process.env.CONNECTOR_ENCRYPTION_SECRET || process.env.JWT_SECRET || "";
    if (!secret) {
      throw new ServiceUnavailableException(
        "JWT_SECRET is required to store connector credentials",
      );
    }
    return secret;
  }

  private async requireOwnedKb(kbId: string, userId: string) {
    const kb = await this.prisma.knowledgeBase.findUnique({ where: { id: kbId } });
    if (!kb) {
      throw new NotFoundException("Knowledge base not found");
    }
    if (kb.createdBy !== userId) {
      throw new ForbiddenException("Forbidden");
    }
    return kb;
  }

  async bindFeishu(kbId: string, userId: string, body: FeishuConnectorCreateDto) {
    await this.requireOwnedKb(kbId, userId);
    const encrypted = encryptConnectorConfig(
      {
        app_id: body.app_id,
        app_secret: body.app_secret,
        space_id: body.space_id,
      },
      this.encryptionSecret(),
    );

    const existing = await this.prisma.connector.findFirst({
      where: { kbId, type: "feishu" },
    });

    const connector = existing
      ? await this.prisma.connector.update({
          where: { id: existing.id },
          data: { configEncrypted: encrypted, enabled: true },
        })
      : await this.prisma.connector.create({
          data: {
            kbId,
            type: "feishu",
            configEncrypted: encrypted,
            enabled: true,
          },
        });

    return {
      id: connector.id,
      kb_id: connector.kbId,
      type: connector.type,
      enabled: connector.enabled,
      cursor: connector.cursor,
    };
  }

  async triggerSync(kbId: string, userId: string, requestId?: string) {
    await this.requireOwnedKb(kbId, userId);

    const connector = await this.prisma.connector.findFirst({
      where: { kbId, type: "feishu", enabled: true },
    });
    if (!connector) {
      throw new BadRequestException("Bind a Feishu connector before syncing");
    }

    const job = await this.prisma.indexJob.create({
      data: {
        kbId,
        jobType: "feishu_sync",
        state: "pending",
      },
    });

    const ragBase = process.env.RAG_API_URL ?? "http://127.0.0.1:8000";
    const internalToken = process.env.INTERNAL_SERVICE_TOKEN ?? "";
    const response = await fetch(`${ragBase}/internal/v1/enqueue/feishu-sync`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        [HEADER_INTERNAL_TOKEN]: internalToken,
        [HEADER_USER_ID]: userId,
        ...(requestId ? { [HEADER_REQUEST_ID]: requestId } : {}),
      },
      body: JSON.stringify({ kb_id: kbId, job_id: job.id }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new ServiceUnavailableException(
        `Failed to enqueue sync job: ${response.status} ${text}`,
      );
    }

    return { job_id: job.id };
  }
}
