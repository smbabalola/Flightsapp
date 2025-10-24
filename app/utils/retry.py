import time
import random
from typing import Callable, TypeVar

T = TypeVar("T")

def retry(fn: Callable[[], T], attempts: int = 3, base: float = 0.3, factor: float = 2.0, jitter: float = 0.2) -> T:
    last_exc = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            delay = base * (factor ** i)
            delay = delay + random.uniform(0, jitter)
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]
