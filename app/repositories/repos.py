from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Quote, Payment

class QuoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_quote(self, *, offer_id: str, price_minor: int, currency: str, email: Optional[str], phone: Optional[str], channel: Optional[str], status: str, paystack_reference: Optional[str], raw_offer: Optional[Dict[str, Any]]):
        q = Quote(
            offer_id=offer_id,
            price_minor=price_minor,
            currency=currency,
            email=email,
            phone=phone,
            channel=channel,
            status=status,
            paystack_reference=paystack_reference,
            raw_offer=raw_offer or {},
        )
        self.db.add(q)
        self.db.flush()
        return q

class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_payment_init(
        self,
        *,
        quote_id: int,
        provider: str,
        reference: str,
        amount_minor: int,
        currency: str,
        status: str,
        raw: Optional[Dict[str, Any]],
        method: Optional[str] = None,
    ):
        p = Payment(
            quote_id=quote_id,
            provider=provider,
            reference=reference,
            amount_minor=amount_minor,
            currency=currency,
            status=status,
            method=method,
            raw=raw or {},
        )
        self.db.add(p)
        self.db.flush()
        return p
