from fastapi import APIRouter
from app.core.settings import get_settings

router = APIRouter()

@router.get("/api")
async def root():
    s = get_settings()
    return {"app": "SureFlights API", "version": "0.1.0", "flags": {"use_real_duffel": s.use_real_duffel, "use_real_paystack": s.use_real_paystack}}
