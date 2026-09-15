import { Injectable, UnauthorizedException } from "@nestjs/common";
import {
  HEADER_INTERNAL_TOKEN,
  HEADER_REQUEST_ID,
  HEADER_USER_ID,
  HEADER_USER_ROLES,
  decodeAccessToken,
} from "@ai-rag/nest-common";
import type { Request, Response } from "express";
import { randomUUID } from "crypto";

type Upstream = "auth" | "connectors" | "rag";

@Injectable()
export class ProxyService {
  private authUrl = process.env.AUTH_SERVICE_URL ?? "http://127.0.0.1:8081";
  private connectorsUrl =
    process.env.CONNECTORS_SERVICE_URL ?? "http://127.0.0.1:8082";
  private ragUrl = process.env.RAG_API_URL ?? "http://127.0.0.1:8000";
  private jwtSecret = process.env.JWT_SECRET ?? "";
  private internalToken = process.env.INTERNAL_SERVICE_TOKEN ?? "";

  resolveUpstream(method: string, path: string): Upstream {
    const normalized = path.replace(/\/+$/, "") || "/";
    if (
      (method === "POST" && normalized === "/api/v1/auth/register") ||
      (method === "POST" && normalized === "/api/v1/auth/login") ||
      (method === "GET" && normalized === "/api/v1/me")
    ) {
      return "auth";
    }

    const connectorMatch = normalized.match(
      /^\/api\/v1\/knowledge-bases\/[^/]+\/(connectors\/feishu|sync)$/,
    );
    if (
      method === "POST" &&
      connectorMatch &&
      (connectorMatch[1] === "connectors/feishu" || connectorMatch[1] === "sync")
    ) {
      return "connectors";
    }

    return "rag";
  }

  isPublicRoute(method: string, path: string): boolean {
    const normalized = path.replace(/\/+$/, "") || "/";
    return (
      (method === "POST" && normalized === "/api/v1/auth/register") ||
      (method === "POST" && normalized === "/api/v1/auth/login")
    );
  }

  private baseFor(upstream: Upstream): string {
    switch (upstream) {
      case "auth":
        return this.authUrl;
      case "connectors":
        return this.connectorsUrl;
      case "rag":
        return this.ragUrl;
      default: {
        const _exhaustive: never = upstream;
        return _exhaustive;
      }
    }
  }

  async forward(req: Request, res: Response): Promise<void> {
    const method = req.method.toUpperCase();
    const path = req.originalUrl.split("?")[0] ?? req.path;
    const upstream = this.resolveUpstream(method, path);
    const requestId = req.header(HEADER_REQUEST_ID) || randomUUID();

    const headers = new Headers();
    for (const [key, value] of Object.entries(req.headers)) {
      if (value === undefined) continue;
      const lower = key.toLowerCase();
      if (
        lower === "host" ||
        lower === "connection" ||
        lower === "content-length" ||
        lower === "authorization" ||
        lower === HEADER_USER_ID ||
        lower === HEADER_USER_ROLES ||
        lower === HEADER_INTERNAL_TOKEN
      ) {
        continue;
      }
      if (Array.isArray(value)) {
        for (const item of value) headers.append(key, item);
      } else {
        headers.set(key, value);
      }
    }

    headers.set(HEADER_REQUEST_ID, requestId);
    headers.set(HEADER_INTERNAL_TOKEN, this.internalToken);

    if (!this.isPublicRoute(method, path)) {
      const authHeader = req.header("authorization");
      if (!authHeader || !authHeader.toLowerCase().startsWith("bearer ")) {
        throw new UnauthorizedException("Not authenticated");
      }
      const token = authHeader.slice(7).trim();
      try {
        const principal = decodeAccessToken(token, this.jwtSecret);
        headers.set(HEADER_USER_ID, principal.userId);
        headers.set(HEADER_USER_ROLES, principal.roles.join(","));
      } catch {
        throw new UnauthorizedException("Invalid token");
      }
    }

    const target = `${this.baseFor(upstream)}${req.originalUrl}`;
    const init: RequestInit = {
      method,
      headers,
      redirect: "manual",
    };

    if (method !== "GET" && method !== "HEAD") {
      const chunks: Buffer[] = [];
      for await (const chunk of req) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      }
      const body = Buffer.concat(chunks);
      if (body.length > 0) {
        init.body = body;
      }
    }

    const upstreamRes = await fetch(target, init);
    res.status(upstreamRes.status);
    upstreamRes.headers.forEach((value, key) => {
      const lower = key.toLowerCase();
      if (lower === "transfer-encoding" || lower === "connection") return;
      res.setHeader(key, value);
    });
    res.setHeader(HEADER_REQUEST_ID, requestId);

    const buf = Buffer.from(await upstreamRes.arrayBuffer());
    res.send(buf);
  }
}
