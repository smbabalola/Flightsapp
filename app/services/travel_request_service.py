from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from app.models.models import TravelPolicy, AuditLog, CompanyUser
from app.repositories.travel_request_repo import TravelRequestRepository
from app.repositories.company_repo import CompanyRepository


class TravelRequestService:
    """Core workflow for travel request lifecycle."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = TravelRequestRepository(db)
        self.company_repo = CompanyRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_reference() -> str:
        return f"TR-{uuid.uuid4().hex[:8].upper()}"

    def _resolve_policy(self, company_id: int, policy_id: Optional[int]) -> Optional[TravelPolicy]:
        if policy_id:
            policy = self.db.get(TravelPolicy, policy_id)
            if policy and policy.company_id == company_id and policy.status == "active":
                self.db.refresh(policy)
                return policy
            raise ValueError("Selected travel policy is not available for this company")
        stmt = (
            text(
                """
                SELECT id FROM travel_policies
                WHERE company_id = :company_id AND status = 'active'
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
        )
        row = self.db.execute(stmt, {"company_id": company_id}).fetchone()
        if not row:
            return None
        default_policy = self.db.get(TravelPolicy, row[0])
        if default_policy is not None:
            self.db.refresh(default_policy)
        return default_policy

    def _fetch_approvers(self, *, company_id: int, roles: Sequence[str]) -> list[int]:
        stmt = (
            select(CompanyUser.id)
            .where(CompanyUser.company_id == company_id)
            .where(CompanyUser.role.in_(tuple(roles)))
            .where(CompanyUser.status == "active")
        )
        return list(self.db.execute(stmt).scalars().all())

    # ------------------------------------------------------------------
    # Create / Submit
    # ------------------------------------------------------------------

    def create_request(
        self,
        *,
        company_id: int,
        employee_company_user_id: int,
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
    ):
        reference = self._generate_reference()
        travel_request = self.repo.create_request(
            company_id=company_id,
            employee_company_user_id=employee_company_user_id,
            reference=reference,
            policy_id=policy_id,
            trip_type=trip_type,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            justification=justification,
            traveler_count=traveler_count,
            budget_minor=budget_minor,
            currency=currency,
            requested_itineraries=requested_itineraries,
            offer_snapshot=offer_snapshot,
        )
        return travel_request

    def submit_request(
        self,
        *,
        company_id: int,
        request_id: int,
        submitter_company_user_id: int,
    ):
        travel_request = self.repo.get_request(company_id=company_id, request_id=request_id)
        if not travel_request:
            raise ValueError("Travel request not found")
        if travel_request.employee_company_user_id != submitter_company_user_id:
            raise ValueError("You can only submit your own travel requests")
        if travel_request.status != "draft":
            raise ValueError("Travel request has already been submitted")

        policy = self._resolve_policy(company_id, travel_request.policy_id)
        if travel_request.policy_id is None and policy:
            travel_request.policy_id = policy.id

        approval_state = {"levels": []}
        approvals_created = []

        if policy and policy.require_manager_approval:
            managers = self._fetch_approvers(
                company_id=company_id,
                roles=["manager"],
            )
            if not managers:
                managers = self._fetch_approvers(
                    company_id=company_id,
                    roles=["company_admin"],
                )
            if not managers:
                raise ValueError("No managers configured to approve this request")
            for approver_id in managers:
                approvals_created.append(
                    self.repo.create_approval(
                        travel_request_id=travel_request.id,
                        approver_company_user_id=approver_id,
                        level=1,
                    )
                )
            approval_state["levels"].append(
                {
                    "level": 1,
                    "role": "manager",
                    "status": "pending",
                    "approver_ids": managers,
                }
            )

        if policy and policy.require_finance_approval:
            finance_users = self._fetch_approvers(
                company_id=company_id,
                roles=["finance"],
            )
            if not finance_users:
                raise ValueError("No finance approvers configured")
            for approver_id in finance_users:
                approvals_created.append(
                    self.repo.create_approval(
                        travel_request_id=travel_request.id,
                        approver_company_user_id=approver_id,
                        level=2,
                    )
                )
            approval_state["levels"].append(
                {
                    "level": 2,
                    "role": "finance",
                    "status": "pending",
                    "approver_ids": finance_users,
                }
            )

        status = "approved"
        approved_at = datetime.utcnow()
        if approvals_created:
            status = "pending_approval"
            approved_at = None

        self.repo.update_status(
            travel_request,
            status=status,
            approval_state=approval_state,
            submitted_at=datetime.utcnow(),
            approved_at=approved_at,
        )

        audit = AuditLog(
            event="travel_request_submitted",
            actor=str(submitter_company_user_id),
            details={
                "travel_request_id": travel_request.id,
                "company_id": company_id,
                "status": status,
            },
        )
        self.db.add(audit)

        return travel_request

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def list_requests(
        self,
        *,
        company_id: int,
        employee_company_user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[TravelRequest]:
        return self.repo.list_requests(
            company_id=company_id,
            employee_company_user_id=employee_company_user_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_request(self, *, company_id: int, request_id: int) -> Optional[TravelRequest]:
        return self.repo.get_request(company_id=company_id, request_id=request_id)

    # ------------------------------------------------------------------
    # Approvals
    # ------------------------------------------------------------------

    def approve_request(
        self,
        *,
        company_id: int,
        request_id: int,
        approver_company_user_id: int,
        comment: Optional[str],
    ):
        travel_request = self.repo.get_request(company_id=company_id, request_id=request_id)
        if not travel_request:
            raise ValueError("Travel request not found")
        if travel_request.status not in {"pending_approval"}:
            raise ValueError("Travel request is not awaiting approval")

        approval = self.repo.get_approval_for_user(
            travel_request_id=travel_request.id,
            approver_company_user_id=approver_company_user_id,
        )
        if not approval:
            raise ValueError("No pending approval assigned to this user")

        self.repo.set_approval_decision(approval, status="approved", comment=comment)

        # Update approval state metadata
        state = travel_request.approval_state or {}
        for level in state.get("levels", []):
            if level.get("level") == approval.level:
                remaining = self.db.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM travel_approvals
                        WHERE travel_request_id = :request_id
                          AND level = :level
                          AND status = 'pending'
                        """
                    ),
                    {"request_id": travel_request.id, "level": approval.level},
                ).scalar()
                if remaining == 0:
                    level["status"] = "approved"
                break

        remaining_pending = self.db.execute(
            text(
                """
                SELECT COUNT(*) FROM travel_approvals
                WHERE travel_request_id = :request_id
                  AND status = 'pending'
                """
            ),
            {"request_id": travel_request.id},
        ).scalar()

        approved_at = None
        new_status = travel_request.status
        if remaining_pending == 0:
            new_status = "approved"
            approved_at = datetime.utcnow()

        self.repo.update_status(
            travel_request,
            status=new_status,
            approval_state=state,
            approved_at=approved_at,
        )

        audit = AuditLog(
            event="travel_request_approved",
            actor=str(approver_company_user_id),
            details={
                "travel_request_id": travel_request.id,
                "level": approval.level,
                "final_approval": remaining_pending == 0,
            },
        )
        self.db.add(audit)

        return travel_request

    def reject_request(
        self,
        *,
        company_id: int,
        request_id: int,
        approver_company_user_id: int,
        comment: Optional[str],
    ):
        travel_request = self.repo.get_request(company_id=company_id, request_id=request_id)
        if not travel_request:
            raise ValueError("Travel request not found")
        if travel_request.status not in {"pending_approval"}:
            raise ValueError("Travel request is not awaiting approval")

        approval = self.repo.get_approval_for_user(
            travel_request_id=travel_request.id,
            approver_company_user_id=approver_company_user_id,
        )
        if not approval:
            raise ValueError("No pending approval assigned to this user")

        self.repo.set_approval_decision(approval, status="rejected", comment=comment)

        state = travel_request.approval_state or {}
        for level in state.get("levels", []):
            if level.get("level") == approval.level:
                level["status"] = "rejected"
                break

        self.repo.update_status(
            travel_request,
            status="rejected",
            approval_state=state,
            rejected_at=datetime.utcnow(),
        )

        audit = AuditLog(
            event="travel_request_rejected",
            actor=str(approver_company_user_id),
            details={
                "travel_request_id": travel_request.id,
                "level": approval.level,
            },
        )
        self.db.add(audit)

        return travel_request
