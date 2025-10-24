from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_db,
    get_current_active_user,
    require_company_permission,
)
from app.auth.permissions import (
    User,
    CompanyPermission,
    CompanyRole,
)
from app.services.travel_request_service import TravelRequestService


router = APIRouter(prefix="/b2b", tags=["B2B Travel Requests"])


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class TravelItinerarySegment(BaseModel):
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    departure_airport: Optional[str] = None
    arrival_airport: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    cabin: Optional[str] = None


class CreateTravelRequest(BaseModel):
    policy_id: Optional[int] = None
    trip_type: Optional[str] = Field(None, description="one_way, round_trip, multi_city")
    origin: Optional[str] = Field(None, min_length=3, max_length=3)
    destination: Optional[str] = Field(None, min_length=3, max_length=3)
    departure_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    justification: Optional[str] = None
    traveler_count: int = Field(1, ge=1)
    budget_minor: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    requested_itineraries: Optional[List[dict]] = Field(default_factory=list)
    offer_snapshot: Optional[dict] = None
    auto_submit: bool = False


class TravelRequestSummary(BaseModel):
    id: int
    reference: str
    status: str
    trip_type: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    departure_date: Optional[datetime]
    return_date: Optional[datetime]
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]


class TravelRequestDetail(TravelRequestSummary):
    justification: Optional[str]
    traveler_count: int
    budget_minor: Optional[int]
    currency: Optional[str]
    policy_id: Optional[int]
    approval_state: Optional[dict]
    requested_itineraries: List[dict]
    offer_snapshot: Optional[dict]
    custom_fields: Optional[dict] = None


class SubmitResponse(BaseModel):
    id: int
    status: str
    message: str = "Travel request submitted"


class ApprovalRequest(BaseModel):
    comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    status: str
    message: str


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _to_summary(travel_request) -> TravelRequestSummary:
    return TravelRequestSummary(
        id=travel_request.id,
        reference=travel_request.reference,
        status=travel_request.status,
        trip_type=travel_request.trip_type,
        origin=travel_request.origin,
        destination=travel_request.destination,
        departure_date=travel_request.departure_date,
        return_date=travel_request.return_date,
        submitted_at=travel_request.submitted_at,
        approved_at=travel_request.approved_at,
        rejected_at=travel_request.rejected_at,
    )


def _to_detail(travel_request) -> TravelRequestDetail:
    return TravelRequestDetail(
        **_to_summary(travel_request).model_dump(),
        justification=travel_request.justification,
        traveler_count=travel_request.traveler_count,
        budget_minor=travel_request.budget_minor,
        currency=travel_request.currency,
        policy_id=travel_request.policy_id,
        approval_state=travel_request.approval_state or {},
        requested_itineraries=travel_request.requested_itineraries or [],
        offer_snapshot=travel_request.offer_snapshot or {},
        custom_fields=travel_request.custom_fields or {},
    )


def _ensure_company_context(user: User):
    if user.company_id is None or user.company_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No tenant context in token. Please login with a company selected."
        )


def _can_view_all(user: User) -> bool:
    if user.company_role in {CompanyRole.ADMIN, CompanyRole.MANAGER, CompanyRole.FINANCE}:
        return True
    if CompanyPermission.APPROVE_LEVEL_ONE in user.company_permissions:
        return True
    if CompanyPermission.APPROVE_FINANCE in user.company_permissions:
        return True
    if CompanyPermission.MANAGE_COMPANY in user.company_permissions:
        return True
    return False


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.post(
    "/travel-requests",
    response_model=TravelRequestDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_company_permission(CompanyPermission.SUBMIT_REQUESTS))]
)
async def create_travel_request(
    request: CreateTravelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    if not (
        CompanyPermission.APPROVE_LEVEL_ONE in current_user.company_permissions
        or CompanyPermission.APPROVE_FINANCE in current_user.company_permissions
        or current_user.company_role in {CompanyRole.ADMIN, CompanyRole.MANAGER, CompanyRole.FINANCE}
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to approve this request")
    service = TravelRequestService(db)
    try:
        travel_request = service.create_request(
            company_id=current_user.company_id,
            employee_company_user_id=current_user.company_user_id,
            policy_id=request.policy_id,
            trip_type=request.trip_type,
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            justification=request.justification,
            traveler_count=request.traveler_count,
            budget_minor=request.budget_minor,
            currency=request.currency,
            requested_itineraries=request.requested_itineraries,
            offer_snapshot=request.offer_snapshot,
        )
        if request.auto_submit:
            service.submit_request(
                company_id=current_user.company_id,
                request_id=travel_request.id,
                submitter_company_user_id=current_user.company_user_id,
            )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    db.refresh(travel_request)
    return _to_detail(travel_request)


@router.post(
    "/travel-requests/{request_id}/submit",
    response_model=SubmitResponse,
    dependencies=[Depends(require_company_permission(CompanyPermission.SUBMIT_REQUESTS))]
)
async def submit_travel_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    if not (
        CompanyPermission.APPROVE_LEVEL_ONE in current_user.company_permissions
        or CompanyPermission.APPROVE_FINANCE in current_user.company_permissions
        or current_user.company_role in {CompanyRole.ADMIN, CompanyRole.MANAGER, CompanyRole.FINANCE}
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to reject this request")
    service = TravelRequestService(db)
    try:
        travel_request = service.submit_request(
            company_id=current_user.company_id,
            request_id=request_id,
            submitter_company_user_id=current_user.company_user_id,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return SubmitResponse(id=travel_request.id, status=travel_request.status)


@router.get(
    "/travel-requests",
    response_model=List[TravelRequestSummary],
)
async def list_travel_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    mine: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    service = TravelRequestService(db)

    employee_company_user_id = None
    if mine or not _can_view_all(current_user):
        employee_company_user_id = current_user.company_user_id

    requests = service.list_requests(
        company_id=current_user.company_id,
        employee_company_user_id=employee_company_user_id,
        status=status_filter,
    )
    return [_to_summary(req) for req in requests]


@router.get(
    "/travel-requests/{request_id}",
    response_model=TravelRequestDetail,
)
async def get_travel_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    service = TravelRequestService(db)
    travel_request = service.get_request(company_id=current_user.company_id, request_id=request_id)
    if not travel_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel request not found")

    if (
        travel_request.employee_company_user_id != current_user.company_user_id
        and not _can_view_all(current_user)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this request")

    return _to_detail(travel_request)


@router.post(
    "/travel-requests/{request_id}/approve",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_company_permission(CompanyPermission.APPROVE_LEVEL_ONE))]
)
async def approve_travel_request(
    request_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    service = TravelRequestService(db)
    try:
        travel_request = service.approve_request(
            company_id=current_user.company_id,
            request_id=request_id,
            approver_company_user_id=current_user.company_user_id,
            comment=request.comment,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    message = "Travel request approved"
    return ApprovalResponse(id=travel_request.id, status=travel_request.status, message=message)


@router.post(
    "/travel-requests/{request_id}/reject",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_company_permission(CompanyPermission.APPROVE_LEVEL_ONE))]
)
async def reject_travel_request(
    request_id: int,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    _ensure_company_context(current_user)
    service = TravelRequestService(db)
    try:
        travel_request = service.reject_request(
            company_id=current_user.company_id,
            request_id=request_id,
            approver_company_user_id=current_user.company_user_id,
            comment=request.comment,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    message = "Travel request rejected"
    return ApprovalResponse(id=travel_request.id, status=travel_request.status, message=message)
