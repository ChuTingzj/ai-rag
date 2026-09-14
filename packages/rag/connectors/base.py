from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


def fernet_from_secret(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_connector_config(config: dict[str, Any], *, secret: str) -> bytes:
    payload = json.dumps(config).encode("utf-8")
    return fernet_from_secret(secret).encrypt(payload)


def decrypt_connector_config(encrypted: bytes, *, secret: str) -> dict[str, Any]:
    try:
        raw = fernet_from_secret(secret).decrypt(encrypted)
    except InvalidToken as exc:
        raise ValueError("Invalid connector config ciphertext") from exc
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Connector config must be a JSON object")
    return data
