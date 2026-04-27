import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings


NONCE_LENGTH = 12


def _get_key() -> bytes:
    settings = get_settings()
    raw_key = base64.b64decode(settings.aes256_key_b64)
    if len(raw_key) != 32:
        raise ValueError("AES256 key must decode to 32 bytes")
    return raw_key


def encrypt_value(plaintext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LENGTH)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    token = base64.b64encode(nonce + ciphertext).decode("utf-8")
    return token


def decrypt_value(token: str) -> str:
    key = _get_key()
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:NONCE_LENGTH], raw[NONCE_LENGTH:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
