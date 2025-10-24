from typing import Dict, Any, Optional
from app.integrations.paystack_client import PaystackClient
from app.repositories.repos import QuoteRepository, PaymentRepository
from app.db.session import SessionLocal
import os
from app.utils.pricing import calculate_display_price_from_usd_base

class BookingService:
    def __init__(self, paystack: PaystackClient | None = None):
        self.paystack = paystack or PaystackClient()

    def create_quote_and_payment_link(
            self,
            offer_id: str,
            contacts: Dict[str, str],
            raw_offer: Dict[str, Any] | None = None,
            channel: str | None = None,
            payment_method: str = "card",
        ) -> Dict[str, Any]:
        # Extract final price from offer (already includes markup and fees)
        if raw_offer:
            # total_amount already has markup applied from DuffelClient
            total_amount = float(raw_offer.get("total_amount", 0))
            total_currency = (raw_offer.get("total_currency") or "NGN").upper()
            supported = set((os.getenv('PAYSTACK_SUPPORTED_CURRENCIES', 'NGN,GHS,ZAR,USD').upper()).split(','))
            fallback_currency = (os.getenv('PAYSTACK_FALLBACK_CURRENCY', 'USD') or 'USD').upper()
            if total_currency not in supported:
                supplier_amount = float(raw_offer.get('base_amount') or raw_offer.get('total_amount') or 0)
                supplier_currency = (raw_offer.get('base_currency') or raw_offer.get('total_currency') or 'USD').upper()
                try:
                    new_total, _ = calculate_display_price_from_usd_base(
                        supplier_amount=supplier_amount,
                        supplier_currency=supplier_currency,
                        display_currency=fallback_currency,
                    )
                    total_amount = float(new_total)
                    total_currency = fallback_currency
                except Exception:
                    total_currency = fallback_currency
        else:
            # Fallback if no offer data
            total_amount = 150.0
            total_currency = "NGN"

        if total_amount <= 0:
            raise ValueError(f"Invalid price: {total_amount}")

        # Convert to kobo (Paystack uses minor units: 1 NGN = 100 kobo)
        price_minor = int(round(total_amount * 100))

        email = contacts.get("email")
        phone = contacts.get("phone")
        booking_channel = channel or "web"

        method_normalized = (payment_method or "card").lower()
        allowed_methods = {"card": "card", "bank": "bank", "ussd": "ussd"}
        if method_normalized not in allowed_methods:
            raise ValueError(f"Unsupported payment method: {payment_method}")
        paystack_channels = [allowed_methods[method_normalized]]

        metadata = {
            "payment_method": method_normalized,
            "booking_channel": booking_channel,
        }
        if email:
            metadata["customer_email"] = email
        if phone:
            metadata["customer_phone"] = phone

        with SessionLocal() as db:
            qr = QuoteRepository(db)
            pr = PaymentRepository(db)
            init = self.paystack.initialize_payment(
                amount_minor=price_minor,
                currency=total_currency,
                email=email or "guest@example.com",
                metadata=metadata,
                channels=paystack_channels,
            )
            data = init["data"]
            quote = qr.create_quote(
                offer_id=offer_id,
                price_minor=price_minor,
                currency=total_currency,
                email=email,
                phone=phone,
                channel=booking_channel,
                status="awaiting_payment",
                paystack_reference=data["reference"],
                raw_offer=raw_offer,
            )
            pr.create_payment_init(
                quote_id=quote.id,
                provider="paystack",
                reference=data["reference"],
                amount_minor=price_minor,
                currency=total_currency,
                status="initialized",
                method=method_normalized,
                raw=init,
            )
            db.commit()
            return {
                "quote_id": quote.id,
                "payment_url": data["authorization_url"],
                "reference": data["reference"],
            }
