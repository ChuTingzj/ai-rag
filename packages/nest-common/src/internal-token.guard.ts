import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from "@nestjs/common";

import { HEADER_INTERNAL_TOKEN } from "./headers";

type HeaderReadable = {
  header(name: string): string | undefined;
};

@Injectable()
export class InternalTokenGuard implements CanActivate {
  constructor(private readonly expectedToken: string) {}

  canActivate(context: ExecutionContext): boolean {
    if (!this.expectedToken) {
      throw new UnauthorizedException("INTERNAL_SERVICE_TOKEN is not configured");
    }
    const req = context.switchToHttp().getRequest<HeaderReadable>();
    const token = req.header(HEADER_INTERNAL_TOKEN);
    if (!token || token !== this.expectedToken) {
      throw new UnauthorizedException("Invalid internal token");
    }
    return true;
  }
}

export function createInternalTokenGuard(expectedToken: string): InternalTokenGuard {
  return new InternalTokenGuard(expectedToken);
}
