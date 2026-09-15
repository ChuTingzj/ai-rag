import { Module } from "@nestjs/common";

import { ConnectorsModule } from "./connectors/connectors.module";
import { HealthController } from "./health.controller";
import { PrismaModule } from "./prisma/prisma.module";

@Module({
  imports: [PrismaModule, ConnectorsModule],
  controllers: [HealthController],
})
export class AppModule {}
