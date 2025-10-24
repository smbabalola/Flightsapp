"""
Pricing utilities for calculating final customer prices with markup and fees.
"""
import os
from typing import Tuple
from app.utils.fx import ngn_equivalent, convert_amount, get_rate
from app.core.settings import get_settings
from app.utils.pricing_audit import record_pricing_audit
from app.db.session import SessionLocal
from app.models.models import PricingConfig


def get_pricing_config() -> dict:
    """Get pricing configuration from DB (fallback to environment)."""
    try:
        with SessionLocal() as db:
            cfg = db.query(PricingConfig).order_by(PricingConfig.id.asc()).first()
            if cfg:
                return {
                    "markup_percentage": float(cfg.markup_percentage),
                    "booking_fee_fixed": float(cfg.booking_fee_fixed),
                    "payment_fee_percentage": float(cfg.payment_fee_percentage),
                }
    except Exception:
        pass
    return {
        "markup_percentage": float(os.getenv("MARKUP_PERCENTAGE", "10.0")),
        "booking_fee_fixed": float(os.getenv("BOOKING_FEE_FIXED", "5000")),
        "payment_fee_percentage": float(os.getenv("PAYMENT_FEE_PERCENTAGE", "1.5")),
    }


def calculate_final_price(base_amount: float, currency: str) -> Tuple[float, dict]:
    """
    Calculate final customer price with markup and fees.

    Formula:
    1. Convert base price to NGN
    2. Add markup percentage
    3. Add fixed booking fee
    4. Add payment processing fee percentage

    Args:
        base_amount: Original flight price from supplier
        currency: Currency code (e.g., "GBP", "USD")

    Returns:
        Tuple of (final_ngn_amount, breakdown_dict)
    """
    config = get_pricing_config()

    # 1. Convert to NGN
    base_ngn = ngn_equivalent(base_amount, currency, fallback_rate=1650.0)
    if base_ngn is None or base_ngn <= 0:
        raise ValueError(f"Failed to convert {base_amount} {currency} to NGN")

    # 2. Add markup
    markup_amount = base_ngn * (config["markup_percentage"] / 100.0)
    subtotal_after_markup = base_ngn + markup_amount

    # 3. Add booking fee
    subtotal_with_booking_fee = subtotal_after_markup + config["booking_fee_fixed"]

    # 4. Add payment processing fee
    payment_fee = subtotal_with_booking_fee * (config["payment_fee_percentage"] / 100.0)
    final_amount = subtotal_with_booking_fee + payment_fee

    # Round to nearest Naira
    final_amount = round(final_amount)

    breakdown = {
        "base_price_ngn": int(base_ngn),
        "markup": int(markup_amount),
        "booking_fee": int(config["booking_fee_fixed"]),
        "payment_fee": int(payment_fee),
        "total_ngn": int(final_amount),
        "original_amount": base_amount,
        "original_currency": currency,
    }

    return final_amount, breakdown


def calculate_display_price_from_usd_base(supplier_amount: float, supplier_currency: str,
                                          display_currency: str) -> Tuple[int, dict]:
    """Calculate customer-facing price using USD as base, with FX safety margin.

    Steps:
    1) Convert supplier -> USD (no margin)
    2) Convert USD -> display currency (with safety margin)
    3) Apply markup, booking fee, payment fee
    """
    settings = get_settings()
    config = get_pricing_config()

    # 1) Supplier -> USD (raw rate, no margin)
    usd_amount = supplier_amount
    if supplier_currency.upper() != "USD":
        usd_amount = convert_amount(supplier_amount, supplier_currency, "USD", use_margin=False)
    if usd_amount is None:
        raise ValueError("Failed to convert supplier to USD")

    # 2) USD -> display (apply safety margin). Also log audit (raw vs effective)
    display_amount = usd_amount
    raw_rate = None
    eff_rate = None
    if display_currency.upper() != "USD":
        raw_rate = get_rate("USD", display_currency, use_margin=False)
        eff_rate = get_rate("USD", display_currency, use_margin=True)
        display_amount = usd_amount * (eff_rate or 1.0) if eff_rate else None
    if display_amount is None:
        raise ValueError("Failed to convert USD to display currency")

    # 3) Pricing components
    markup_amount = display_amount * (config["markup_percentage"] / 100.0)
    subtotal = display_amount + markup_amount + config["booking_fee_fixed"]
    payment_fee = subtotal * (config["payment_fee_percentage"] / 100.0)
    final_amount = round(subtotal + payment_fee)

    breakdown = {
        "base_currency": "USD",
        "display_currency": display_currency.upper(),
        "supplier_amount": float(supplier_amount),
        "supplier_currency": supplier_currency.upper(),
        "converted_base_usd": float(usd_amount),
        "converted_display_before_fees": float(display_amount),
        "markup": int(markup_amount),
        "booking_fee": int(config["booking_fee_fixed"]),
        "payment_fee": int(payment_fee),
        "total_display_minor": int(final_amount),
    }
    # audit (best-effort)
    try:
        record_pricing_audit(
            base_currency="USD",
            display_currency=display_currency,
            raw_rate=raw_rate,
            effective_rate=eff_rate,
            margin_pct=get_settings().fx_safety_margin_pct,
            source="pricing",
            context={
                "supplier_currency": supplier_currency.upper(),
            },
        )
    except Exception:
        pass
    return final_amount, breakdown


def format_price_breakdown(breakdown: dict) -> str:
    """Format price breakdown for display."""
    lines = [
        f"Base Price: ₦{breakdown['base_price_ngn']:,}",
        f"Markup ({get_pricing_config()['markup_percentage']}%): ₦{breakdown['markup']:,}",
        f"Booking Fee: ₦{breakdown['booking_fee']:,}",
        f"Payment Fee ({get_pricing_config()['payment_fee_percentage']}%): ₦{breakdown['payment_fee']:,}",
        f"Total: ₦{breakdown['total_ngn']:,}",
    ]
    return "\n".join(lines)
