import jwt from "jsonwebtoken";

const ALGORITHM = "HS256";
const TOKEN_TTL_SECONDS = 60 * 60 * 24;

export type AccessTokenPayload = {
  sub: string;
  roles?: string[];
  iat: number;
  exp: number;
};

export type DecodedAccessToken = {
  userId: string;
  roles: string[];
};

export function createAccessToken(
  userId: string,
  secret: string,
  roles: string[] = [],
): string {
  if (!secret) {
    throw new Error("JWT_SECRET is not configured");
  }
  return jwt.sign({ sub: userId, roles }, secret, {
    algorithm: ALGORITHM,
    expiresIn: TOKEN_TTL_SECONDS,
  });
}

export function decodeAccessToken(token: string, secret: string): DecodedAccessToken {
  if (!secret) {
    throw new Error("JWT_SECRET is not configured");
  }
  const payload = jwt.verify(token, secret, {
    algorithms: [ALGORITHM],
  }) as AccessTokenPayload;
  if (!payload.sub) {
    throw new Error("missing sub");
  }
  return {
    userId: String(payload.sub),
    roles: Array.isArray(payload.roles) ? payload.roles.map(String) : [],
  };
}
