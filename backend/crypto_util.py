"""Password-based encryption shared by the build script (Python) and the site (WebCrypto).

Format of an encrypted file:  b"AIDENC1" + nonce(12) + AES-256-GCM(ciphertext || tag)
Key: PBKDF2-HMAC-SHA256(password, salt, 310000 iterations, 32 bytes). The salt is a
public per-repository value stored in data/salt.txt. The JavaScript side
(web/static_data.js) uses exactly the same parameters.
"""
from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path

MAGIC = b"AIDENC1"
ITERATIONS = 310_000


def derive_key(password: str, salt: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS, dklen=32)


def _aesgcm(key: bytes):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

    return AESGCM(key)


def encrypt_bytes(key: bytes, data: bytes) -> bytes:
    nonce = secrets.token_bytes(12)
    return MAGIC + nonce + _aesgcm(key).encrypt(nonce, data, None)


def decrypt_bytes(key: bytes, blob: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("not an AIDENC1 file")
    nonce = blob[len(MAGIC) : len(MAGIC) + 12]
    return _aesgcm(key).decrypt(nonce, blob[len(MAGIC) + 12 :], None)


def load_or_create_salt(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    salt = secrets.token_hex(16)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(salt + "\n", encoding="utf-8")
    return salt


def password_from_env() -> str:
    return os.environ.get("PANEL_PASSWORD", "").strip()
