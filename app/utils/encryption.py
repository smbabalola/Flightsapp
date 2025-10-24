from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import get_settings


class EncryptionError(RuntimeError):
    """Raised for loyalty encryption/decryption issues."""


@lru_cache()
def _get_fernet() -> Fernet:
    """Return a cached Fernet instance configured from settings."""
    key = get_settings().loyalty_encryption_key
    if not key:
        raise EncryptionError("LOYALTY_ENCRYPTION_KEY is not configured")
    try:
        return Fernet(key)
    except (TypeError, ValueError) as exc:
        raise EncryptionError("Invalid LOYALTY_ENCRYPTION_KEY value") from exc


def encrypt_secret(value: str) -> str:
    """Encrypt a sensitive value for storage."""
    if value is None or value == "":
        raise ValueError("Cannot encrypt empty loyalty value")
    token = _get_fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(token: str) -> str:
    """Decrypt a stored loyalty value."""
    if token is None or token == "":
        raise ValueError("Cannot decrypt empty loyalty token")
    try:
        value = _get_fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise EncryptionError("Failed to decrypt loyalty data") from exc
    return value.decode("utf-8")


def mask_last4(value: str) -> str:
    """Return the last four characters of a loyalty identifier."""
    if not value:
        return ""
    trimmed = value.strip()
    return trimmed[-4:]
