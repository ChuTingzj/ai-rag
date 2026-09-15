import {
  Body,
  Controller,
  Get,
  Headers,
  HttpCode,
  Post,
  UnauthorizedException,
  UseGuards,
} from "@nestjs/common";
import { HEADER_USER_ID } from "@ai-rag/nest-common";

import { AuthService } from "./auth.service";
import { LoginDto, RegisterDto } from "./auth.dto";
import { InternalAuthGuard } from "./internal-auth.guard";

@Controller()
@UseGuards(InternalAuthGuard)
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post("api/v1/auth/register")
  @HttpCode(201)
  register(@Body() body: RegisterDto) {
    return this.authService.register(body);
  }

  @Post("api/v1/auth/login")
  @HttpCode(200)
  login(@Body() body: LoginDto) {
    return this.authService.login(body);
  }

  @Get("api/v1/me")
  me(@Headers(HEADER_USER_ID) userId: string | undefined) {
    if (!userId) {
      throw new UnauthorizedException("Missing X-User-Id");
    }
    return this.authService.me(userId);
  }
}
