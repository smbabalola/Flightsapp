from __future__ import annotations

from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.models import TravelRequest, TravelApproval, TravelRequestComment


class TravelRequestRepository:
    """Persistence layer for travel requests and approvals."""

    def __init__(self, db: Session):
        self.db = db

    # Travel Requests ---------------------------------------------------------

    def create_request(
        self,
        *,
        company_id: int,
        employee_company_user_id: int,
        reference: str,
        policy_id: Optional[int],
        trip_type: Optional[str],
        origin: Optional[str],
        destination: Optional[str],
        departure_date: Optional[datetime],
        return_date: Optional[datetime],
        justification: Optional[str],
        traveler_count: int,
        budget_minor: Optional[int],
        currency: Optional[str],
        requested_itineraries: Optional[list],
        offer_snapshot: Optional[dict],
    ) -> TravelRequest:
        request = TravelRequest(
            company_id=company_id,
            employee_company_user_id=employee_company_user_id,
            policy_id=policy_id,
            reference=reference,
            trip_type=trip_type,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            justification=justification,
            traveler_count=traveler_count,
            budget_minor=budget_minor,
            currency=currency,
            requested_itineraries=requested_itineraries or [],
            offer_snapshot=offer_snapshot or {},
        )
        self.db.add(request)
        self.db.flush()
        return request

    def get_request(self, *, company_id: int, request_id: int) -> Optional[TravelRequest]:
        stmt = select(TravelRequest).where(
            TravelRequest.company_id == company_id,
            TravelRequest.id == request_id,
        )
        return self.db.execute(stmt).scalars().first()

    def list_requests(
        self,
        *,
        company_id: int,
        employee_company_user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[TravelRequest]:
        stmt = select(TravelRequest).where(TravelRequest.company_id == company_id)
        if employee_company_user_id is not None:
            stmt = stmt.where(TravelRequest.employee_company_user_id == employee_company_user_id)
        if status:
            stmt = stmt.where(TravelRequest.status == status)
        stmt = stmt.order_by(TravelRequest.created_at.desc()).limit(limit).offset(offset)
        return self.db.execute(stmt).scalars().all()

    def update_status(
        self,
        request: TravelRequest,
        *,
        status: str,
        approval_state: Optional[dict] = None,
        submitted_at: Optional[datetime] = None,
        approved_at: Optional[datetime] = None,
        rejected_at: Optional[datetime] = None,
        cancelled_at: Optional[datetime] = None,
    ) -> TravelRequest:
        request.status = status
        if approval_state is not None:
            request.approval_state = approval_state
        if submitted_at is not None:
            request.submitted_at = submitted_at
        if approved_at is not None:
            request.approved_at = approved_at
        if rejected_at is not None:
            request.rejected_at = rejected_at
        if cancelled_at is not None:
            request.cancelled_at = cancelled_at
        self.db.flush()
        return request

    # Approvals ---------------------------------------------------------------

    def create_approval(
        self,
        *,
        travel_request_id: int,
        approver_company_user_id: int,
        level: int,
    ) -> TravelApproval:
        approval = TravelApproval(
            travel_request_id=travel_request_id,
            approver_company_user_id=approver_company_user_id,
            level=level,
        )
        self.db.add(approval)
        self.db.flush()
        return approval

    def list_approvals(self, travel_request_id: int) -> Sequence[TravelApproval]:
        stmt = select(TravelApproval).where(TravelApproval.travel_request_id == travel_request_id)
        return self.db.execute(stmt).scalars().all()

    def get_approval_for_user(
        self,
        *,
        travel_request_id: int,
        approver_company_user_id: int,
        only_pending: bool = True,
    ) -> Optional[TravelApproval]:
        stmt = select(TravelApproval).where(
            TravelApproval.travel_request_id == travel_request_id,
            TravelApproval.approver_company_user_id == approver_company_user_id,
        )
        if only_pending:
            stmt = stmt.where(TravelApproval.status == "pending")
        return self.db.execute(stmt).scalars().first()

    def set_approval_decision(
        self,
        approval: TravelApproval,
        *,
        status: str,
        comment: Optional[str] = None,
    ) -> TravelApproval:
        approval.status = status
        approval.decision = status
        approval.comment = comment
        approval.decided_at = datetime.utcnow()
        self.db.flush()
        return approval

    # Comments ----------------------------------------------------------------

    def add_comment(
        self,
        *,
        travel_request_id: int,
        author_company_user_id: int,
        visibility: str,
        body: str,
        extra: Optional[dict] = None,
    ) -> TravelRequestComment:
        comment = TravelRequestComment(
            travel_request_id=travel_request_id,
            author_company_user_id=author_company_user_id,
            visibility=visibility,
            body=body,
            extra=extra or {},
        )
        self.db.add(comment)
        self.db.flush()
        return comment

    def list_comments(self, travel_request_id: int) -> Sequence[TravelRequestComment]:
        stmt = select(TravelRequestComment).where(
            TravelRequestComment.travel_request_id == travel_request_id
        ).order_by(TravelRequestComment.created_at.asc())
        return self.db.execute(stmt).scalars().all()
