from pydantic import BaseModel
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/sureflights",
    )
    env: str = os.getenv("ENV", "dev")
    paystack_secret: str | None = os.getenv("PAYSTACK_SECRET")
    whatsapp_verify_token: str | None = os.getenv("WHATSAPP_VERIFY_TOKEN")
    whatsapp_app_secret: str | None = os.getenv("WHATSAPP_APP_SECRET")
    whatsapp_phone_number_id: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_access_token: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")
    # Twitter API
    twitter_api_key: str | None = os.getenv("TWITTER_API_KEY")
    twitter_api_secret: str | None = os.getenv("TWITTER_API_SECRET")
    twitter_access_token: str | None = os.getenv("TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: str | None = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    twitter_bearer_token: str | None = os.getenv("TWITTER_BEARER_TOKEN")
    # Twilio Voice
    twilio_account_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number: str | None = os.getenv("TWILIO_PHONE_NUMBER")
    # OpenAI for conversational AI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    admin_user: str | None = os.getenv("ADMIN_USER")
    admin_pass: str | None = os.getenv("ADMIN_PASS")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-12345678901234567890")
    loyalty_encryption_key: str | None = os.getenv("LOYALTY_ENCRYPTION_KEY")
    # Feature flags
    use_real_duffel: bool = os.getenv("USE_REAL_DUFFEL", "false").lower() == "true"
    use_real_paystack: bool = os.getenv("USE_REAL_PAYSTACK", "false").lower() == "true"
    use_redis_idempotency: bool = os.getenv("USE_REDIS_IDEMPOTENCY", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    # API keys / endpoints
    duffel_api_key: str | None = os.getenv("DUFFEL_API_KEY")
    paystack_public_key: str | None = os.getenv("PAYSTACK_PUBLIC_KEY")
    paystack_base_url: str = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")
    # Pricing & FX
    base_pricing_currency: str = os.getenv("BASE_PRICING_CURRENCY", "USD").upper()
    default_display_currency: str = os.getenv("DEFAULT_DISPLAY_CURRENCY", "NGN").upper()
    fx_safety_margin_pct: float = float(os.getenv("FX_SAFETY_MARGIN_PCT", "4.0"))
    use_live_fx_rates: bool = os.getenv("USE_LIVE_FX_RATES", "false").lower() == "true"
    # Search behavior flags
    ignore_domestic_routes: bool = os.getenv("IGNORE_DOMESTIC_ROUTES", "false").lower() == "true"
    # Redis URL (optional for health checks)
    redis_url: str | None = os.getenv("REDIS_URL")
    # Caching controls
    duffel_search_cache_ttl_seconds: int = int(os.getenv("DUFFEL_SEARCH_CACHE_TTL_SECONDS", "900"))
    duffel_metadata_cache_ttl_seconds: int = int(os.getenv("DUFFEL_METADATA_CACHE_TTL_SECONDS", "86400"))

    def validate_startup(self) -> None:
        problems = []
        if self.use_real_duffel and not self.duffel_api_key:
            problems.append("USE_REAL_DUFFEL enabled but DUFFEL_API_KEY missing")
        if self.use_real_paystack and not os.getenv("PAYSTACK_SECRET"):
            problems.append("USE_REAL_PAYSTACK enabled but PAYSTACK_SECRET missing")
        if self.use_real_paystack and not self.paystack_public_key:
            problems.append("USE_REAL_PAYSTACK enabled but PAYSTACK_PUBLIC_KEY missing")
        if not self.loyalty_encryption_key:
            problems.append("LOYALTY_ENCRYPTION_KEY missing - loyalty accounts cannot be encrypted")
        if problems:
            import warnings
            for p in problems:
                warnings.warn(p)

@lru_cache
def get_settings() -> Settings:
    return Settings()
