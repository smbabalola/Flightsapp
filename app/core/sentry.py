import os
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

def init_sentry():
    """Initialize Sentry error tracking with FastAPI integrations.

    Features enabled:
    - Error tracking and stack traces
    - Performance monitoring (APM)
    - SQLAlchemy query tracking
    - HTTP client request tracking
    - Request context and user data

    Configuration via .env:
    - SENTRY_DSN: Your Sentry project DSN
    - SENTRY_TRACES_SAMPLE_RATE: Performance sampling (0.0-1.0)
    - ENV: Environment name (dev/staging/prod)
    """
    dsn = os.getenv("SENTRY_DSN")
    env = os.getenv("ENV", "dev")

    if not dsn:
        # Sentry disabled - no DSN configured
        return

    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        traces_sample_rate=traces_sample_rate,
        integrations=[
            SqlalchemyIntegration(),  # Track database queries
            HttpxIntegration(),       # Track HTTP client requests (Duffel, Paystack)
        ],
        # Send PII (personally identifiable information) - disable in production if needed
        send_default_pii=True,
        # Attach stack traces to all messages
        attach_stacktrace=True,
        # Release tracking (set via environment if using CI/CD)
        release=os.getenv("SENTRY_RELEASE"),
    )
