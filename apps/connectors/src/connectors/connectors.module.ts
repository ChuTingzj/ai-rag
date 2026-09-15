import { Module } from "@nestjs/common";

import { ConnectorsController } from "./connectors.controller";
import { ConnectorsService } from "./connectors.service";
import { InternalAuthGuard } from "./internal-auth.guard";

@Module({
  controllers: [ConnectorsController],
  providers: [ConnectorsService, InternalAuthGuard],
})
export class ConnectorsModule {}
