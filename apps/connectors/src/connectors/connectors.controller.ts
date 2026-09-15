import {
  Body,
  Controller,
  Headers,
  HttpCode,
  Param,
  Post,
  UnauthorizedException,
  UseGuards,
} from "@nestjs/common";
import { HEADER_REQUEST_ID, HEADER_USER_ID } from "@ai-rag/nest-common";

import { FeishuConnectorCreateDto } from "./connectors.dto";
import { ConnectorsService } from "./connectors.service";
import { InternalAuthGuard } from "./internal-auth.guard";

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
}
