-- CreateTable
CREATE TABLE "connectors" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "kb_id" UUID,
    "type" TEXT,
    "config_encrypted" BYTEA,
    "cursor" TEXT,
    "enabled" BOOLEAN,

    CONSTRAINT "connectors_pkey" PRIMARY KEY ("id")
);
