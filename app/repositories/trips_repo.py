from sqlalchemy.orm import Session
from app.models.models import Trip
from typing import Optional, Dict, Any

class TripRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_trip(self, *, quote_id: int, supplier_order_id: Optional[str], pnr: Optional[str], etickets_csv: Optional[str], etickets_json: Optional[list] = None, email: Optional[str], phone: Optional[str], raw_order: Optional[Dict[str, Any]]):
        t = Trip(
            quote_id=quote_id,
            supplier_order_id=supplier_order_id,
            pnr=pnr,
            etickets=etickets_csv,
            etickets_json=etickets_json,
            email=email,
            phone=phone,
            raw_order=raw_order or {},
        )
        self.db.add(t)
        self.db.flush()
        return t

