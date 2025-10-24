"""
Rate Limiting Middleware

Simple in-memory rate limiter for authentication endpoints.
"""
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Tuple
import structlog

logger = structlog.get_logger(__name__)


class RateLimiter:
    """In-memory rate limiter for authentication endpoints."""

    def __init__(self):
        # Store: {ip_address: [(timestamp, endpoint), ...]}
        self.attempts: Dict[str, list] = {}
        # Store: {ip_address: lockout_until_timestamp}
        self.lockouts: Dict[str, datetime] = {}

    def check_rate_limit(self, request: Request, max_attempts: int = 5, window_minutes: int = 15) -> None:
        """
        Check if request should be rate limited.

        Args:
            request: FastAPI request object
            max_attempts: Maximum attempts allowed in window
            window_minutes: Time window in minutes

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        now = datetime.utcnow()

        # Check if IP is locked out
        if client_ip in self.lockouts:
            lockout_until = self.lockouts[client_ip]
            if now < lockout_until:
                remaining = int((lockout_until - now).total_seconds())
                logger.warning(
                    "rate_limit_lockout",
                    ip=client_ip,
                    endpoint=endpoint,
                    remaining_seconds=remaining
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many failed attempts. Try again in {remaining} seconds."
                )
            else:
                # Lockout expired, remove it
                del self.lockouts[client_ip]

        # Clean old attempts (outside window)
        cutoff_time = now - timedelta(minutes=window_minutes)
        if client_ip in self.attempts:
            self.attempts[client_ip] = [
                (ts, ep) for ts, ep in self.attempts[client_ip]
                if ts > cutoff_time
            ]

        # Count attempts in current window
        if client_ip not in self.attempts:
            self.attempts[client_ip] = []

        current_attempts = len(self.attempts[client_ip])

        if current_attempts >= max_attempts:
            # Lock out for 15 minutes
            lockout_until = now + timedelta(minutes=15)
            self.lockouts[client_ip] = lockout_until

            logger.warning(
                "rate_limit_exceeded",
                ip=client_ip,
                endpoint=endpoint,
                attempts=current_attempts,
                lockout_minutes=15
            )

            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Account locked for 15 minutes."
            )

        # Record this attempt
        self.attempts[client_ip].append((now, endpoint))

        logger.debug(
            "rate_limit_check",
            ip=client_ip,
            endpoint=endpoint,
            attempts=current_attempts + 1,
            max_attempts=max_attempts
        )

    def record_failed_login(self, email: str, ip: str) -> None:
        """Record a failed login attempt."""
        logger.warning(
            "failed_login_attempt",
            email=email,
            ip=ip,
            timestamp=datetime.utcnow().isoformat()
        )

    def clear_attempts(self, ip: str) -> None:
        """Clear rate limit attempts for an IP (after successful login)."""
        if ip in self.attempts:
            del self.attempts[ip]
        if ip in self.lockouts:
            del self.lockouts[ip]


# Global rate limiter instance
rate_limiter = RateLimiter()
