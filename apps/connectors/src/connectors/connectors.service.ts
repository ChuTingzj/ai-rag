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

  private ragBase(): string {
    return process.env.RAG_API_URL ?? "http://127.0.0.1:8000";
  }

  private internalHeaders(userId?: string, requestId?: string): Record<string, string> {
    const headers: Record<string, string> = {
      [HEADER_INTERNAL_TOKEN]: process.env.INTERNAL_SERVICE_TOKEN ?? "",
    };
    if (userId) headers[HEADER_USER_ID] = userId;
    if (requestId) headers[HEADER_REQUEST_ID] = requestId;
    return headers;
  }

  private async requireOwnedKb(kbId: string, userId: string) {
    const response = await fetch(
      `${this.ragBase()}/internal/v1/knowledge-bases/${kbId}/owner`,
      { headers: this.internalHeaders(userId) },
    );
    if (response.status === 404) {
      throw new NotFoundException("Knowledge base not found");
    }
    if (!response.ok) {
      const text = await response.text();
      throw new ServiceUnavailableException(
        `Failed to verify KB ownership: ${response.status} ${text}`,
      );
    }
    const body = (await response.json()) as { created_by: string | null };
    if (body.created_by !== userId) {
      throw new ForbiddenException("Forbidden");
    }
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

    const response = await fetch(`${this.ragBase()}/internal/v1/enqueue/feishu-sync`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...this.internalHeaders(userId, requestId),
      },
      body: JSON.stringify({ kb_id: kbId }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new ServiceUnavailableException(
        `Failed to enqueue sync job: ${response.status} ${text}`,
      );
    }

    const payload = (await response.json()) as { job_id: string };
    return { job_id: payload.job_id };
  }

  async getFeishuByKb(kbId: string) {
    const connector = await this.prisma.connector.findFirst({
      where: { kbId, type: "feishu", enabled: true },
    });
    if (!connector || !connector.configEncrypted) {
      throw new NotFoundException("Feishu connector not found");
    }
    return {
      id: connector.id,
      kb_id: connector.kbId,
      type: connector.type,
      cursor: connector.cursor,
      config_encrypted_b64: Buffer.from(connector.configEncrypted).toString("base64"),
    };
  }

  async updateCursor(connectorId: string, cursor: string | null) {
    const connector = await this.prisma.connector.findUnique({
      where: { id: connectorId },
    });
    if (!connector) {
      throw new NotFoundException("Connector not found");
    }
    await this.prisma.connector.update({
      where: { id: connectorId },
      data: { cursor },
    });
    return { id: connectorId, cursor };
  }
}
