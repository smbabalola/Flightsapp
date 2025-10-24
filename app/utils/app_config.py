from typing import Optional
from sqlalchemy import text
from app.db.session import SessionLocal


def get_bool(key: str, default: bool = False) -> bool:
    """Read a boolean feature flag from app_config table.

    Falls back to default when not present or on error.
    """
    try:
        with SessionLocal() as db:
            row = db.execute(text("SELECT value FROM app_config WHERE key = :k"), {"k": key}).fetchone()
            if not row:
                return default
            v = str(row.value).strip().lower()
            return v in ("1", "true", "yes", "on")
    except Exception:
        return default

