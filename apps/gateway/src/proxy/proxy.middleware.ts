import {
  Injectable,
  NestMiddleware,
  UnauthorizedException,
} from "@nestjs/common";
import type { NextFunction, Request, Response } from "express";

import { ProxyService } from "./proxy.service";

@Injectable()
export class ProxyMiddleware implements NestMiddleware {
  constructor(private readonly proxyService: ProxyService) {}

  async use(req: Request, res: Response, next: NextFunction) {
    try {
      await this.proxyService.forward(req, res);
    } catch (err) {
      if (err instanceof UnauthorizedException) {
        res.status(401).json({
          statusCode: 401,
          message: err.message,
          detail: err.message,
        });
        return;
      }
      next(err);
    }
  }
}
