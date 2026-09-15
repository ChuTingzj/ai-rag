import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from "@nestjs/common";
import { HEADER_INTERNAL_TOKEN } from "@ai-rag/nest-common";
import type { Request } from "express";

@Injectable()
export class InternalAuthGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const expected = process.env.INTERNAL_SERVICE_TOKEN ?? "";
    if (!expected) {
      throw new UnauthorizedException("INTERNAL_SERVICE_TOKEN is not configured");
    }
    const req = context.switchToHttp().getRequest<Request>();
    const token = req.header(HEADER_INTERNAL_TOKEN);
    if (!token || token !== expected) {
      throw new UnauthorizedException("Invalid internal token");
    }
    return true;
  }
}
