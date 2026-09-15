import {
  ConflictException,
  Injectable,
  UnauthorizedException,
} from "@nestjs/common";
import { createAccessToken } from "@ai-rag/nest-common";
import * as bcrypt from "bcryptjs";

import { PrismaService } from "../prisma/prisma.service";
import { LoginDto, RegisterDto } from "./auth.dto";

export type UserOut = {
  id: string;
  email: string;
  roles: string[];
  created_at: Date;
};

@Injectable()
export class AuthService {
  constructor(private readonly prisma: PrismaService) {}

  private toUserOut(user: {
    id: string;
    email: string;
    roles: string[];
    createdAt: Date;
  }): UserOut {
    return {
      id: user.id,
      email: user.email,
      roles: user.roles,
      created_at: user.createdAt,
    };
  }

  async register(dto: RegisterDto): Promise<UserOut> {
    const existing = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (existing) {
      throw new ConflictException("Email already registered");
    }
    const passwordHash = await bcrypt.hash(dto.password, 10);
    const user = await this.prisma.user.create({
      data: {
        email: dto.email,
        passwordHash,
        roles: ["user"],
      },
    });
    return this.toUserOut(user);
  }

  async login(dto: LoginDto): Promise<{ access_token: string; token_type: string }> {
    const user = await this.prisma.user.findUnique({
      where: { email: dto.email },
    });
    if (!user || !(await bcrypt.compare(dto.password, user.passwordHash))) {
      throw new UnauthorizedException("Invalid credentials");
    }
    const secret = process.env.JWT_SECRET ?? "";
    const access_token = createAccessToken(user.id, secret, user.roles);
    return { access_token, token_type: "bearer" };
  }

  async me(userId: string): Promise<UserOut> {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      throw new UnauthorizedException("User not found");
    }
    return this.toUserOut(user);
  }
}
