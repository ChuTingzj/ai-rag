import { IsString, MinLength } from "class-validator";

export class FeishuConnectorCreateDto {
  @IsString()
  @MinLength(1)
  app_id!: string;

  @IsString()
  @MinLength(1)
  app_secret!: string;

  @IsString()
  @MinLength(1)
  space_id!: string;
}
