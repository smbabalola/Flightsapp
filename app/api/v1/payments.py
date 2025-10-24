from fastapi import APIRouter, HTTPException
from app.db.session import SessionLocal

router = APIRouter()

@router.get("/payments/{reference}")
async def get_payment_status(reference: str):
    with SessionLocal() as db:
        row = db.execute("SELECT status FROM payments WHERE reference = :ref", {"ref": reference}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {"reference": reference, "status": row.status}
