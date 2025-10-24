import os
import time
from typing import Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

class RedisIdempotency:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis is None:
            raise RuntimeError("redis package not installed")
        self.client = redis.from_url(self.url, encoding="utf-8", decode_responses=True)

    def check_and_set_once(self, key: str, ttl_seconds: int = 3600) -> bool:
        # SET key value NX EX ttl
        return bool(self.client.set(name=key, value=str(int(time.time())), nx=True, ex=ttl_seconds))
