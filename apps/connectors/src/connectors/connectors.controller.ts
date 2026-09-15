import {
  Body,
  Controller,
  Get,
  Headers,
  HttpCode,
  Param,
  Patch,
  Post,
  UnauthorizedException,
  UseGuards,
} from "@nestjs/common";
import { HEADER_REQUEST_ID, HEADER_USER_ID } from "@ai-rag/nest-common";
import { IsOptional, IsString } from "class-validator";

import { FeishuConnectorCreateDto } from "./connectors.dto";
import { ConnectorsService } from "./connectors.service";
import { InternalAuthGuard } from "./internal-auth.guard";

class CursorUpdateDto {
  @IsOptional()
  @IsString()
  cursor!: string | null;
}

@Controller()
@UseGuards(InternalAuthGuard)
export class ConnectorsController {
  constructor(private readonly connectorsService: ConnectorsService) {}

  private requireUserId(userId: string | undefined): string {
    if (!userId) {
      throw new UnauthorizedException("Missing X-User-Id");
    }
    return userId;
  }

  @Post("api/v1/knowledge-bases/:kbId/connectors/feishu")
  @HttpCode(201)
  bindFeishu(
    @Param("kbId") kbId: string,
    @Body() body: FeishuConnectorCreateDto,
    @Headers(HEADER_USER_ID) userId: string | undefined,
  ) {
    return this.connectorsService.bindFeishu(kbId, this.requireUserId(userId), body);
  }

  @Post("api/v1/knowledge-bases/:kbId/sync")
  @HttpCode(202)
  triggerSync(
    @Param("kbId") kbId: string,
    @Headers(HEADER_USER_ID) userId: string | undefined,
    @Headers(HEADER_REQUEST_ID) requestId: string | undefined,
  ) {
    return this.connectorsService.triggerSync(
      kbId,
      this.requireUserId(userId),
      requestId,
    );
  }

  @Get("internal/v1/connectors/feishu/:kbId")
  getFeishuByKb(@Param("kbId") kbId: string) {
    return this.connectorsService.getFeishuByKb(kbId);
  }

  @Patch("internal/v1/connectors/:id/cursor")
  updateCursor(@Param("id") id: string, @Body() body: CursorUpdateDto) {
    return this.connectorsService.updateCursor(id, body.cursor ?? null);
  }
}
