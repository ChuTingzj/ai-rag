import { Module } from "@nestjs/common";

import { AuthController } from "./auth.controller";
import { AuthService } from "./auth.service";
import { InternalAuthGuard } from "./internal-auth.guard";

@Module({
  controllers: [AuthController],
  providers: [AuthService, InternalAuthGuard],
})
export class AuthModule {}
