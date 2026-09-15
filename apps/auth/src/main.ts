import { NestFactory } from "@nestjs/core";
import { ValidationPipe } from "@nestjs/common";
import { loadEnvFile } from "@ai-rag/nest-common";

import { AppModule } from "./app.module";

loadEnvFile();

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
    }),
  );
  const port = Number(process.env.AUTH_PORT ?? process.env.PORT ?? 8081);
  await app.listen(port);
}

void bootstrap();
