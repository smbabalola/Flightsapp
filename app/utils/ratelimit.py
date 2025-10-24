import time
from typing import Dict, Tuple

# key -> (tokens, last_refill)
_BUCKETS: Dict[str, Tuple[float, float]] = {}

class RateLimiter:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity

    def allow(self, key: str) -> bool:
        now = time.time()
        tokens, last = _BUCKETS.get(key, (self.capacity, now))
        # refill
        tokens = min(self.capacity, tokens + (now - last) * self.rate)
        if tokens < 1:
            _BUCKETS[key] = (tokens, now)
            return False
        tokens -= 1
        _BUCKETS[key] = (tokens, now)
        return True

limiter_search = RateLimiter(rate=1.0, capacity=5)      # ~5 req burst, 1 rps
limiter_webhook = RateLimiter(rate=0.5, capacity=3)     # ~3 burst, 1 req / 2s
