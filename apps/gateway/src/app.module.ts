import { MiddlewareConsumer, Module, NestModule } from "@nestjs/common";

import { HealthController } from "./health.controller";
import { ProxyMiddleware } from "./proxy/proxy.middleware";
import { ProxyService } from "./proxy/proxy.service";

@Module({
  controllers: [HealthController],
  providers: [ProxyService],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(ProxyMiddleware).forRoutes("api/v1", "api/v1/(.*)");
  }
}
