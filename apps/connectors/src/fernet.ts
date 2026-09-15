import { createCipheriv, createHash, createHmac, randomBytes } from "crypto";

/**
 * Compatible with packages/rag/connectors/base.py fernet_from_secret:
 * Fernet key = urlsafe_b64encode(sha256(secret)).
 */
function signingAndEncryptionKeys(secret: string): { signingKey: Buffer; encryptionKey: Buffer } {
  const digest = createHash("sha256").update(secret, "utf8").digest();
  return {
    signingKey: digest.subarray(0, 16),
    encryptionKey: digest.subarray(16, 32),
  };
}

function base64url(buf: Buffer): string {
  return buf
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

export function encryptConnectorConfig(
  config: Record<string, string>,
  secret: string,
): Uint8Array<ArrayBuffer> {
  if (!secret) {
    throw new Error("CONNECTOR_ENCRYPTION_SECRET is not configured");
  }
  const { signingKey, encryptionKey } = signingAndEncryptionKeys(secret);
  const iv = randomBytes(16);
  const plaintext = Buffer.from(JSON.stringify(config), "utf8");
  const cipher = createCipheriv("aes-128-cbc", encryptionKey, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);

  const version = Buffer.from([0x80]);
  const timestamp = Buffer.alloc(8);
  timestamp.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 1000)), 0);

  const body = Buffer.concat([version, timestamp, iv, ciphertext]);
  const hmac = createHmac("sha256", signingKey).update(body).digest();
  const token = Buffer.concat([body, hmac]);
  const encoded = Buffer.from(base64url(token), "utf8");
  // Prisma Bytes is Uint8Array<ArrayBuffer>; copy so the buffer type is ArrayBuffer.
  const bytes = new Uint8Array(new ArrayBuffer(encoded.length));
  bytes.set(encoded);
  return bytes;
}
