from fastapi import APIRouter, status as http_status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import httpx
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.settings import get_settings


router = APIRouter()


def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        with SessionLocal() as db:
            # Simple query to verify DB connection
            db.execute(text("SELECT 1"))
            return {"status": "healthy", "message": "Database connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {str(e)[:100]}"}


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity (if enabled)."""
    settings = get_settings()

    if not settings.use_redis_idempotency:
        return {"status": "disabled", "message": "Redis idempotency not enabled"}

    try:
        import redis
        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        client.close()
        return {"status": "healthy", "message": "Redis connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Redis error: {str(e)[:100]}"}


def check_duffel() -> Dict[str, Any]:
    """Check Duffel API connectivity (if enabled)."""
    settings = get_settings()

    if not settings.use_real_duffel or not settings.duffel_api_key:
        return {"status": "disabled", "message": "Real Duffel API not enabled"}

    try:
        # Lightweight health check - just verify API key is accepted
        url = "https://api.duffel.com/air/airlines"
        headers = {
            "Authorization": f"Bearer {settings.duffel_api_key}",
            "Duffel-Version": "v2",
            "Accept": "application/json"
        }

        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code in [200, 401, 403]:
                # 200 = success, 401/403 = auth issue but API is reachable
                if resp.status_code == 200:
                    return {"status": "healthy", "message": "Duffel API reachable"}
                else:
                    return {"status": "degraded", "message": f"Duffel API auth issue: {resp.status_code}"}
            else:
                return {"status": "unhealthy", "message": f"Duffel API error: {resp.status_code}"}

    except Exception as e:
        return {"status": "unhealthy", "message": f"Duffel error: {str(e)[:100]}"}


def check_paystack() -> Dict[str, Any]:
    """Check Paystack API connectivity (if enabled)."""
    settings = get_settings()

    if not settings.use_real_paystack or not settings.paystack_secret:
        return {"status": "disabled", "message": "Real Paystack API not enabled"}

    try:
        # Lightweight health check
        url = f"{settings.paystack_base_url}/bank"
        headers = {
            "Authorization": f"Bearer {settings.paystack_secret}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code in [200, 401, 403]:
                if resp.status_code == 200:
                    return {"status": "healthy", "message": "Paystack API reachable"}
                else:
                    return {"status": "degraded", "message": f"Paystack API auth issue: {resp.status_code}"}
            else:
                return {"status": "unhealthy", "message": f"Paystack API error: {resp.status_code}"}

    except Exception as e:
        return {"status": "unhealthy", "message": f"Paystack error: {str(e)[:100]}"}


@router.get("/health")
async def health():
    """
    Comprehensive health check endpoint.

    Returns:
        - 200: All critical services healthy
        - 503: One or more critical services unhealthy

    Response includes:
        - overall: Overall health status
        - checks: Individual service checks
        - timestamp: ISO 8601 timestamp
    """
    from datetime import datetime

    # Run all health checks
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "duffel_api": check_duffel(),
        "paystack_api": check_paystack(),
    }

    # Determine overall health
    # Critical: database must be healthy
    # Optional: redis, duffel, paystack (can be disabled or degraded)
    critical_unhealthy = checks["database"]["status"] == "unhealthy"

    # Optional services - only fail if enabled and unhealthy
    optional_unhealthy = (
        (checks["redis"]["status"] == "unhealthy") or
        (checks["duffel_api"]["status"] == "unhealthy") or
        (checks["paystack_api"]["status"] == "unhealthy")
    )

    if critical_unhealthy:
        overall_status = "unhealthy"
        status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
    elif optional_unhealthy:
        overall_status = "degraded"
        status_code = http_status.HTTP_200_OK
    else:
        overall_status = "healthy"
        status_code = http_status.HTTP_200_OK

    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }

    return JSONResponse(content=response, status_code=status_code)
