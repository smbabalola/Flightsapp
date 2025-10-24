from typing import Optional
from fastapi import Request
from app.core.settings import get_settings


SUPPORTED = {
    # Africa
    "NGN", "GHS", "ZAR", "KES", "XOF", "XAF", "MAD", "EGP", "TZS", "UGX", "ETB",
    # Americas
    "USD", "CAD", "MXN", "BRL", "ARS", "CLP", "COP",
    # Europe
    "EUR", "GBP", "CHF", "SEK", "NOK", "DKK", "PLN", "TRY",
    # Middle East
    "AED", "SAR", "QAR", "KWD",
    # Asia/Pacific
    "JPY", "CNY", "INR", "AUD", "NZD",
}


def country_to_currency(country_code: Optional[str]) -> Optional[str]:
    if not country_code:
        return None
    cc = country_code.upper()
    mapping = {
        # Africa
        "NG": "NGN", "GH": "GHS", "ZA": "ZAR", "KE": "KES", "SN": "XOF", "CI": "XOF",
        "BJ": "XOF", "TG": "XOF", "BF": "XOF", "ML": "XOF", "NE": "XOF", "GW": "XOF",
        "CM": "XAF", "GA": "XAF", "GQ": "XAF", "CG": "XAF", "TD": "XAF", "CF": "XAF",
        "MA": "MAD", "EG": "EGP", "TZ": "TZS", "UG": "UGX", "ET": "ETB",
        # Americas
        "US": "USD", "CA": "CAD", "MX": "MXN", "BR": "BRL", "AR": "ARS", "CL": "CLP", "CO": "COP",
        # Europe
        "FR": "EUR", "DE": "EUR", "ES": "EUR", "IT": "EUR", "NL": "EUR", "PT": "EUR", "IE": "EUR",
        "BE": "EUR", "AT": "EUR", "GR": "EUR", "FI": "EUR", "SK": "EUR", "SI": "EUR", "LV": "EUR",
        "LT": "EUR", "EE": "EUR", "LU": "EUR", "MT": "EUR", "CY": "EUR",
        "GB": "GBP", "CH": "CHF", "SE": "SEK", "NO": "NOK", "DK": "DKK", "PL": "PLN", "TR": "TRY",
        # Middle East
        "AE": "AED", "SA": "SAR", "QA": "QAR", "KW": "KWD",
        # Asia/Pacific
        "JP": "JPY", "CN": "CNY", "IN": "INR", "AU": "AUD", "NZ": "NZD",
    }
    return mapping.get(cc)


def _parse_accept_language(header: Optional[str]) -> Optional[str]:
    if not header:
        return None
    # crude mapping based on regional variants
    header = header.lower()
    if "-ng" in header:
        return "NGN"
    if "-gh" in header:
        return "GHS"
    if "-za" in header:
        return "ZAR"
    return None


def resolve_display_currency(request: Request, user_pref: Optional[str] = None) -> str:
    settings = get_settings()
    # 1) logged-in user preference
    if user_pref and user_pref.upper() in SUPPORTED:
        return user_pref.upper()

    # 2) try country from CDN / proxy headers
    country = (
        request.headers.get("CF-IPCountry")
        or request.headers.get("X-Country-Code")
        or request.headers.get("X-Appengine-Country")
    )
    curr = country_to_currency(country)
    if curr in SUPPORTED:
        return curr

    # 3) Accept-Language hint
    curr = _parse_accept_language(request.headers.get("Accept-Language"))
    if curr in SUPPORTED:
        return curr

    # 4) default
    default_curr = (settings.default_display_currency or "NGN").upper()
    return default_curr if default_curr in SUPPORTED else "USD"


def detect_country_code(request: Request) -> Optional[str]:
    return (
        request.headers.get("CF-IPCountry")
        or request.headers.get("X-Country-Code")
        or request.headers.get("X-Appengine-Country")
    )
