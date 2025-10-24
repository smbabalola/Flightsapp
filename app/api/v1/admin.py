from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

router = APIRouter(dependencies=[Depends(__import__("app.core.auth", fromlist=["require_admin"]).require_admin)])

class Fees(BaseModel):
    rule: dict
    flat_minor: Optional[int] = 0
    percent: Optional[float] = 0.0

@router.post("/admin/fees")
async def set_fees(payload: Fees):
    # TODO: persist fees
    return {"status": "ok"}

