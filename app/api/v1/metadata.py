from fastapi import APIRouter
from app.integrations.duffel_client import DuffelClient

router = APIRouter()
_client = DuffelClient()

@router.get("/metadata/airlines")
async def airlines():
    return {"data": _client.get_airlines()}

@router.get("/metadata/airports")
async def airports():
    return {"data": _client.get_airports()}

@router.get("/metadata/aircraft")
async def aircraft():
    return {"data": _client.get_aircraft()}

