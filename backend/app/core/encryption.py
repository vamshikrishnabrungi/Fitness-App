from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

import anyio
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import get_settings


@dataclass(frozen=True)
class Envelope:
    ciphertext: str
    wrapped_dek: str
    key_version: str


async def encrypt_json(payload: dict[str, Any], *, aad: bytes) -> Envelope:
    settings = get_settings()
    dek = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = nonce + AESGCM(dek).encrypt(nonce, json.dumps(payload, separators=(",", ":")).encode(), aad)
    if settings.kms_key_name:
        def wrap() -> tuple[bytes, str]:
            from google.cloud import kms
            client = kms.KeyManagementServiceClient()
            response = client.encrypt(request={"name": settings.kms_key_name, "plaintext": dek, "additional_authenticated_data": aad})
            return response.ciphertext, settings.kms_key_name
        wrapped, key_version = await anyio.to_thread.run_sync(wrap)
    elif settings.environment == "test":
        local_key = hashlib.sha256(b"runlete-test-envelope-key").digest()
        local_nonce = os.urandom(12)
        wrapped = local_nonce + AESGCM(local_key).encrypt(local_nonce, dek, aad)
        key_version = "test-only-v1"
    else:
        raise RuntimeError("KMS_KEY_NAME is required outside tests")
    return Envelope(base64.b64encode(ciphertext).decode(), base64.b64encode(wrapped).decode(), key_version)


async def decrypt_json(envelope: Envelope, *, aad: bytes) -> dict[str, Any]:
    settings = get_settings()
    wrapped = base64.b64decode(envelope.wrapped_dek)
    if envelope.key_version == "test-only-v1":
        if settings.environment != "test":
            raise RuntimeError("Test ciphertext cannot be decrypted outside tests")
        local_key = hashlib.sha256(b"runlete-test-envelope-key").digest()
        dek = AESGCM(local_key).decrypt(wrapped[:12], wrapped[12:], aad)
    else:
        if not settings.kms_key_name:
            raise RuntimeError("KMS_KEY_NAME is required to decrypt sensitive data")

        def unwrap() -> bytes:
            from google.cloud import kms

            client = kms.KeyManagementServiceClient()
            response = client.decrypt(
                request={
                    "name": settings.kms_key_name,
                    "ciphertext": wrapped,
                    "additional_authenticated_data": aad,
                }
            )
            return response.plaintext

        dek = await anyio.to_thread.run_sync(unwrap)
    ciphertext = base64.b64decode(envelope.ciphertext)
    value = json.loads(AESGCM(dek).decrypt(ciphertext[:12], ciphertext[12:], aad))
    if not isinstance(value, dict):
        raise ValueError("Encrypted payload is not an object")
    return value
