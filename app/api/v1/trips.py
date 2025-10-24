from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.db.session import SessionLocal
from sqlalchemy import text

router = APIRouter()

class Trip(BaseModel):
    id: int
    pnr: Optional[str]
    etickets: List[str] = []
    email: Optional[str] = None
    phone: Optional[str] = None

@router.get("/trips/{trip_id}", response_model=Trip)
async def get_trip(trip_id: int):
    with SessionLocal() as db:
        row = db.execute(text("SELECT id, pnr, etickets, etickets_json, email, phone FROM trips WHERE id = :id"), {"id": trip_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trip not found")
        et_list = []
        if row.etickets:
            et_list = [e for e in str(row.etickets).split(',') if e]
        return Trip(id=row.id, pnr=row.pnr, etickets=et_list, email=row.email, phone=row.phone)

