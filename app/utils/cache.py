from __future__ import annotations

import json
import threading
import time
from typing import Any, Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class Cache:
    """Simple cache facade with Redis (if configured) and in-memory fallback.

    Values are JSON-serialized to keep types consistent across backends.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self._redis = None
        if redis_url and redis is not None:
            try:
                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                # lightweight ping to validate connectivity; ignore errors
                try:
                    self._redis.ping()
                except Exception:
                    self._redis = None
            except Exception:
                self._redis = None

        # in-memory fallback
        self._mem: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        if self._redis is not None:
            try:
                raw = self._redis.get(key)
                return json.loads(raw) if raw is not None else None
            except Exception:
                # fall back to memory
                pass

        now = time.time()
        with self._lock:
            item = self._mem.get(key)
            if not item:
                return None
            expires_at, raw = item
            if expires_at < now:
                self._mem.pop(key, None)
                return None
            try:
                return json.loads(raw)
            except Exception:
                return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        raw = json.dumps(value, separators=(",", ":"))
        if self._redis is not None:
            try:
                self._redis.setex(key, ttl_seconds, raw)
                return
            except Exception:
                # fall through to memory
                pass
        expires_at = time.time() + max(1, int(ttl_seconds))
        with self._lock:
            self._mem[key] = (expires_at, raw)

    def delete_prefix(self, prefix: str) -> int:
        """Delete keys by prefix. Returns number of deleted keys.

        Works for both Redis and in-memory fallback.
        """
        deleted = 0
        if self._redis is not None:
            try:
                # Use scan to avoid blocking Redis
                cursor = 0
                pattern = prefix + "*"
                while True:
                    cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=500)
                    if keys:
                        deleted += self._redis.delete(*keys)
                    if cursor == 0:
                        break
            except Exception:
                pass
        with self._lock:
            to_delete = [k for k in self._mem.keys() if k.startswith(prefix)]
            for k in to_delete:
                self._mem.pop(k, None)
                deleted += 1
        return deleted
