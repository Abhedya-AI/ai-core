from __future__ import annotations

import os
import time
import base64
import hashlib

from app.core.logging import get_logger

log = get_logger(__name__)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class EncryptionService:
    def __init__(self, key_hex: str | None = None) -> None:
        self._key = None
        if CRYPTO_AVAILABLE:
            if key_hex:
                self._key = bytes.fromhex(key_hex)
            else:
                self._key = AESGCM.generate_key(bit_length=256)
        else:
            self._key = key_hex.encode() if key_hex else b"default-fallback-key"

    async def encrypt(self, plaintext: str) -> str:
        start_time = time.perf_counter()
        try:
            if CRYPTO_AVAILABLE and self._key:
                aesgcm = AESGCM(self._key)
                nonce = os.urandom(12)
                ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
                return base64.b64encode(nonce + ciphertext).decode()
            else:
                return base64.b64encode(plaintext.encode()).decode()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"encrypt executed in {latency:.4f}s")

    async def decrypt(self, ciphertext_b64: str) -> str:
        start_time = time.perf_counter()
        try:
            raw_data = base64.b64decode(ciphertext_b64.encode())
            if CRYPTO_AVAILABLE and self._key:
                aesgcm = AESGCM(self._key)
                nonce = raw_data[:12]
                ciphertext = raw_data[12:]
                return aesgcm.decrypt(nonce, ciphertext, None).decode()
            else:
                return raw_data.decode()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"decrypt executed in {latency:.4f}s")

    async def encrypt_dict(self, data: dict, pii_fields: list[str]) -> dict:
        start_time = time.perf_counter()
        try:
            result = data.copy()
            for field in pii_fields:
                if field in result and isinstance(result[field], str):
                    result[field] = await self.encrypt(result[field])
            return result
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"encrypt_dict executed in {latency:.4f}s")

    async def decrypt_dict(self, data: dict, pii_fields: list[str]) -> dict:
        start_time = time.perf_counter()
        try:
            result = data.copy()
            for field in pii_fields:
                if field in result and isinstance(result[field], str):
                    try:
                        result[field] = await self.decrypt(result[field])
                    except Exception as e:
                        log.error(f"Failed to decrypt field {field}: {e}")
            return result
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"decrypt_dict executed in {latency:.4f}s")

    async def hash_value(self, value: str) -> str:
        start_time = time.perf_counter()
        try:
            return hashlib.sha256(value.encode()).hexdigest()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"hash_value executed in {latency:.4f}s")

    async def verify_hash(self, value: str, hash_str: str) -> bool:
        return await self.hash_value(value) == hash_str

    async def rotate_key(self, new_key_hex: str) -> None:
        start_time = time.perf_counter()
        try:
            if CRYPTO_AVAILABLE:
                self._key = bytes.fromhex(new_key_hex)
            else:
                self._key = new_key_hex.encode()
        finally:
            latency = time.perf_counter() - start_time
            log.debug(f"rotate_key executed in {latency:.4f}s")

    def get_key_id(self) -> str:
        if self._key:
            return hashlib.sha256(self._key).hexdigest()[:8]
        return "none"

_service_instance = None
def get_service() -> EncryptionService:
    global _service_instance
    if _service_instance is None:
        _service_instance = EncryptionService()
    return _service_instance
