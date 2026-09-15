import { Controller, Get } from "@nestjs/common";

@Controller()
export class HealthController {
  @Get("health")
  async health() {
    const authUrl = process.env.AUTH_SERVICE_URL ?? "http://127.0.0.1:8081";
    const connectorsUrl =
      process.env.CONNECTORS_SERVICE_URL ?? "http://127.0.0.1:8082";
    const ragUrl = process.env.RAG_API_URL ?? "http://127.0.0.1:8000";

    const checks = await Promise.allSettled([
      fetch(`${authUrl}/health`).then((r) => r.ok),
      fetch(`${connectorsUrl}/health`).then((r) => r.ok),
      fetch(`${ragUrl}/health`).then((r) => r.ok),
    ]);

    const [auth, connectors, rag] = checks.map(
      (c) => c.status === "fulfilled" && c.value === true,
    );

    const ok = auth && connectors && rag;
    return {
      status: ok ? "ok" : "degraded",
      upstreams: { auth, connectors, rag },
    };
  }
}
