from fastapi import APIRouter, Request, Depends
from typing import Optional
from app.utils.currency import resolve_display_currency, detect_country_code, country_to_currency
from app.auth.dependencies import get_current_user_optional


router = APIRouter()


@router.get("/currency/default")
async def get_default_currency(request: Request, user: Optional[object] = Depends(get_current_user_optional)):
    pref = None
    if user and getattr(user, 'preferred_currency', None):
        pref = user.preferred_currency
    curr = resolve_display_currency(request, user_pref=pref)
    country = detect_country_code(request)
    if not country:
        # Best-effort derive from Accept-Language region (e.g., en-GB)
        al = request.headers.get('Accept-Language') or ''
        parts = [p.strip() for p in al.split(',') if p]
        if parts:
            # look for xx-YY
            for p in parts:
                if '-' in p:
                    country = p.split('-')[-1].upper()
                    break
    return {"currency": curr, "country": country, "country_currency": country_to_currency(country) if country else None}
