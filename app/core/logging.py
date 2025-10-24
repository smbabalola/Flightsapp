import json
import time
import uuid
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os
from app.core.metrics import record

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("sureflights")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        start = time.time()
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            logger.exception("Unhandled error", extra={"request_id": req_id})
            raise
        finally:
            duration_ms = int((time.time() - start) * 1000)
            log = {
                "level": "INFO",
                "ts": int(time.time()),
                "request_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "duration_ms": duration_ms,
            }
            print(json.dumps(log))
            try:
                ep = request.url.path
                record(ep, duration_ms, status)
            except Exception:
                pass
        response.headers["X-Request-ID"] = req_id
        return response

__all__ = ["RequestIDMiddleware", "logger"]
