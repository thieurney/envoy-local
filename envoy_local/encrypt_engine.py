"""Encryption engine for securing .env file values at rest."""

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.env_file import EnvFile


@dataclass
class EncryptResult:
    encrypted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        parts = [f"Encrypted: {len(self.encrypted)}"]
        if self.skipped:
            parts.append(f"Skipped: {len(self.skipped)}")
        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
        return " | ".join(parts)


class EncryptEngine:
    """Encrypts and decrypts .env values using a passphrase-derived key."""

    MARKER = "enc:"

    def __init__(self, passphrase: str) -> None:
        self._key = hashlib.sha256(passphrase.encode()).digest()

    def _xor_bytes(self, data: bytes, key: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def encrypt_value(self, plaintext: str) -> str:
        salt = os.urandom(8)
        key = hashlib.sha256(self._key + salt).digest()
        encrypted = self._xor_bytes(plaintext.encode(), key)
        payload = salt + encrypted
        return self.MARKER + base64.urlsafe_b64encode(payload).decode()

    def decrypt_value(self, ciphertext: str) -> Optional[str]:
        if not ciphertext.startswith(self.MARKER):
            return None
        try:
            payload = base64.urlsafe_b64decode(ciphertext[len(self.MARKER):])
            salt, encrypted = payload[:8], payload[8:]
            key = hashlib.sha256(self._key + salt).digest()
            return self._xor_bytes(encrypted, key).decode()
        except Exception:
            return None

    def encrypt_file(self, env_file: EnvFile, keys: Optional[List[str]] = None) -> EncryptResult:
        result = EncryptResult()
        target_keys = keys if keys is not None else list(env_file.all().keys())
        for key in target_keys:
            value = env_file.get(key)
            if value is None:
                result.errors.append(f"Key not found: {key}")
                continue
            if value.startswith(self.MARKER):
                result.skipped.append(key)
                continue
            result.encrypted[key] = self.encrypt_value(value)
        return result

    def decrypt_file(self, env_file: EnvFile) -> Dict[str, str]:
        decrypted = {}
        for key, value in env_file.all().items():
            if value.startswith(self.MARKER):
                plain = self.decrypt_value(value)
                decrypted[key] = plain if plain is not None else value
            else:
                decrypted[key] = value
        return decrypted
