import { NestFactory } from "@nestjs/core";
import { loadEnvFile } from "@ai-rag/nest-common";

import { AppModule } from "./app.module";

loadEnvFile();

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { bodyParser: false });
  app.enableCors({
    origin: true,
    credentials: true,
  });
  const port = Number(process.env.GATEWAY_PORT ?? process.env.PORT ?? 8080);
  await app.listen(port);
}

void bootstrap();
