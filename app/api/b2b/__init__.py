from fastapi import APIRouter

from .companies import router as companies_router
from .travel_requests import router as travel_requests_router

router = APIRouter()
router.include_router(companies_router)
router.include_router(travel_requests_router)

