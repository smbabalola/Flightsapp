from time import time
from typing import Dict

# naive in-memory store: key -> expiry
_IDEMP: Dict[str, float] = {}


def check_and_set_once(key: str, ttl_seconds: int = 3600) -> bool:
    now = time()
    # cleanup expired lazily
    expired = [k for k, v in _IDEMP.items() if v < now]
    for k in expired:
        _IDEMP.pop(k, None)
    if key in _IDEMP:
        return False
    _IDEMP[key] = now + ttl_seconds
    return True
