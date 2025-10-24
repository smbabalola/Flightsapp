import os
from typing import Optional, Dict
from datetime import datetime, timedelta, date
import httpx
from app.core.settings import get_settings

# In-memory cache for exchange rates
_rate_cache: Dict[str, tuple[float, datetime]] = {}
_CACHE_TTL_MINUTES = 60  # Cache rates for 1 hour


def _fetch_live_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """Fetch live exchange rate from exchangerate-api.io (free, no auth required).

    Args:
        from_currency: Source currency code (e.g., "USD")
        to_currency: Target currency code (e.g., "NGN")

    Returns:
        Exchange rate or None if API fails
    """
    cache_key = f"{from_currency}_{to_currency}"

    # Check cache first
    if cache_key in _rate_cache:
        cached_rate, cached_time = _rate_cache[cache_key]
        if datetime.utcnow() - cached_time < timedelta(minutes=_CACHE_TTL_MINUTES):
            return cached_rate

    # Fetch from API
    try:
        url = f"https://open.exchangerate-api.com/v6/latest/{from_currency.upper()}"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                rates = data.get("rates", {})
                rate = rates.get(to_currency.upper())
                if rate:
                    # Cache the rate
                    _rate_cache[cache_key] = (float(rate), datetime.utcnow())
                    return float(rate)
    except Exception:
        # API call failed, will fall back to static rate
        pass

    return None


def _apply_safety_margin(rate: float, margin_pct: Optional[float] = None) -> float:
    """Apply a percentage safety margin to a raw FX rate."""
    settings = get_settings()
    pct = settings.fx_safety_margin_pct if margin_pct is None else margin_pct
    try:
        pct_f = float(pct)
    except Exception:
        pct_f = 0.0
    if pct_f <= 0:
        return rate
    return rate * (1.0 + (pct_f / 100.0))


def get_rate(from_currency: str, to_currency: str, use_margin: bool = False,
             margin_pct: Optional[float] = None) -> Optional[float]:
    """Get FX rate from -> to, optionally applying safety margin.

    - Uses live rates if enabled, with in-memory cache.
    - Falls back to static NGN rate for USD->NGN, or 1.0 for same currency.
    - Applies safety margin only if `use_margin` is True.
    """
    if not from_currency or not to_currency:
        return None
    f = from_currency.upper()
    t = to_currency.upper()
    if f == t:
        return 1.0

    settings = get_settings()
    raw_rate: Optional[float] = None

    if settings.use_live_fx_rates:
        raw_rate = _fetch_live_rate(f, t)

    if raw_rate is None:
        # Limited static fallback: USD->NGN via FX_NGN_RATE
        try:
            if f == "USD" and t == "NGN":
                raw_rate = float(os.getenv("FX_NGN_RATE", "0")) or None
            elif t == "USD" and f == "NGN":
                base = float(os.getenv("FX_NGN_RATE", "0")) or None
                raw_rate = (1.0 / base) if base and base > 0 else None
        except Exception:
            raw_rate = None

    if raw_rate is None or raw_rate <= 0:
        return None

    return _apply_safety_margin(raw_rate, margin_pct) if use_margin else raw_rate


def convert_amount(amount: Optional[float], from_currency: str, to_currency: str,
                   use_margin: bool = False, margin_pct: Optional[float] = None,
                   fallback_rate: Optional[float] = None) -> Optional[float]:
    """Convert amount between any two currencies with optional safety margin."""
    if amount is None:
        return None
    rate = get_rate(from_currency, to_currency, use_margin=use_margin, margin_pct=margin_pct)
    if rate is None or rate <= 0:
        rate = fallback_rate
    if rate is None or rate <= 0:
        return None
    return float(amount) * rate


def ngn_equivalent(amount: Optional[float], currency: str, fallback_rate: Optional[float] = None) -> Optional[int]:
    """Convert amount to NGN equivalent using live or static exchange rates.

    Flow:
    1. If currency is already NGN, return amount as-is
    2. Try live API rate (if USE_LIVE_FX_RATES=true)
    3. Fall back to FX_NGN_RATE environment variable
    4. Fall back to provided fallback_rate
    5. Return None if no rate available

    Args:
        amount: Amount to convert
        currency: Source currency code (e.g., "USD")
        fallback_rate: Optional fallback rate if env vars not set

    Returns:
        NGN equivalent as integer, or None if conversion not possible
    """
    if amount is None or currency is None:
        return None

    currency = currency.upper()

    if currency == "NGN":
        return int(round(amount))

    # Try live API rate if enabled
    use_live_rates = os.getenv("USE_LIVE_FX_RATES", "false").lower() == "true"
    if use_live_rates:
        live_rate = _fetch_live_rate(currency, "NGN")
        if live_rate and live_rate > 0:
            return int(round(amount * live_rate))

    # Fall back to static rate from environment
    try:
        static_rate = float(os.getenv("FX_NGN_RATE", "0")) or (fallback_rate or 0.0)
    except Exception:
        static_rate = 0.0

    if static_rate <= 0.0:
        return None

    return int(round(amount * static_rate))
