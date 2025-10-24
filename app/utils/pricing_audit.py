from typing import Optional, Dict, Any
from app.db.session import SessionLocal
from sqlalchemy import text


def record_pricing_audit(
    base_currency: str,
    display_currency: str,
    raw_rate: Optional[float],
    effective_rate: Optional[float],
    margin_pct: Optional[float],
    source: str = "fx_service",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert a pricing audit row for daily FX/margin tracking.

    Best-effort; failures are swallowed to avoid impacting checkout.
    """
    try:
        with SessionLocal() as db:
            db.execute(
                text(
                    """
                    INSERT INTO pricing_audit(
                        base_currency, display_currency, raw_rate, effective_rate, margin_pct, source, context
                    ) VALUES (:b, :d, :raw, :eff, :m, :s, :ctx)
                    """
                ),
                {
                    "b": (base_currency or "").upper(),
                    "d": (display_currency or "").upper(),
                    "raw": float(raw_rate) if raw_rate is not None else None,
                    "eff": float(effective_rate) if effective_rate is not None else None,
                    "m": float(margin_pct) if margin_pct is not None else None,
                    "s": source,
                    "ctx": context or {},
                },
            )
            db.commit()
    except Exception:
        # Non-fatal
        pass

