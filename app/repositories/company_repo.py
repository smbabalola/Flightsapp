from __future__ import annotations

from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.models import (
    Company,
    CompanyUser,
    CompanyInvitation,
    TravelPolicy,
)


class CompanyRepository:
    """Data access layer for multi-tenant company entities."""

    def __init__(self, db: Session):
        self.db = db

    # Company -----------------------------------------------------------------

    def get_by_id(self, company_id: int) -> Optional[Company]:
        return self.db.get(Company, company_id)

    def get_by_slug(self, slug: str) -> Optional[Company]:
        stmt = select(Company).where(Company.slug == slug)
        return self.db.execute(stmt).scalars().first()

    def create_company(
        self,
        *,
        name: str,
        slug: str,
        domain: Optional[str],
        country: Optional[str],
        currency: Optional[str],
        settings: Optional[dict] = None,
        payment_preferences: Optional[dict] = None,
    ) -> Company:
        company = Company(
            name=name,
            slug=slug,
            domain=domain,
            country=country,
            currency=currency,
            settings=settings or {},
            payment_preferences=payment_preferences or {},
        )
        self.db.add(company)
        self.db.flush()
        return company

    def update_company(
        self,
        company: Company,
        *,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        country: Optional[str] = None,
        currency: Optional[str] = None,
        settings: Optional[dict] = None,
        payment_preferences: Optional[dict] = None,
        status: Optional[str] = None,
    ) -> Company:
        if name is not None:
            company.name = name
        if domain is not None:
            company.domain = domain
        if country is not None:
            company.country = country
        if currency is not None:
            company.currency = currency
        if settings is not None:
            company.settings = settings
        if payment_preferences is not None:
            company.payment_preferences = payment_preferences
        if status is not None:
            company.status = status
        self.db.flush()
        return company

    def list_companies(self) -> Sequence[Company]:
        stmt = select(Company).order_by(Company.created_at.desc())
        return self.db.execute(stmt).scalars().all()

    # Company Users ------------------------------------------------------------

    def get_company_user(self, *, company_id: int, user_id: int) -> Optional[CompanyUser]:
        stmt = select(CompanyUser).where(
            CompanyUser.company_id == company_id,
            CompanyUser.user_id == user_id,
        )
        return self.db.execute(stmt).scalars().first()

    def create_company_user(
        self,
        *,
        company_id: int,
        user_id: int,
        role: str,
        status: str = "active",
        department_id: Optional[int] = None,
        title: Optional[str] = None,
        cost_center_code: Optional[str] = None,
        extra: Optional[dict] = None,
        joined_at: Optional[datetime] = None,
        invited_at: Optional[datetime] = None,
    ) -> CompanyUser:
        membership = CompanyUser(
            company_id=company_id,
            user_id=user_id,
            role=role,
            status=status,
            department_id=department_id,
            title=title,
            cost_center_code=cost_center_code,
            extra=extra or {},
            joined_at=joined_at or datetime.utcnow(),
            invited_at=invited_at,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def list_company_members(self, company_id: int):
        stmt = text(
            """
            SELECT
                cu.id,
                cu.company_id,
                cu.user_id,
                cu.role,
                cu.status,
                cu.department_id,
                cu.title,
                cu.cost_center_code,
                cu.joined_at,
                cu.invited_at,
                cu.last_seen_at,
                u.email,
                u.name
            FROM company_users cu
            JOIN users u ON u.id = cu.user_id
            WHERE cu.company_id = :company_id
            ORDER BY COALESCE(u.name, u.email), u.email
            """
        )
        return self.db.execute(stmt, {"company_id": company_id}).mappings().all()

    # Invitations --------------------------------------------------------------

    def create_invitation(
        self,
        *,
        company_id: int,
        inviter_company_user_id: Optional[int],
        email: str,
        role: str,
        token: str,
        expires_at: datetime,
        department_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> CompanyInvitation:
        invitation = CompanyInvitation(
            company_id=company_id,
            inviter_company_user_id=inviter_company_user_id,
            email=email,
            role=role,
            department_id=department_id,
            token=token,
            expires_at=expires_at,
            payload=payload or {},
        )
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get_invitation_by_token(self, token: str) -> Optional[CompanyInvitation]:
        stmt = select(CompanyInvitation).where(CompanyInvitation.token == token)
        return self.db.execute(stmt).scalars().first()

    def mark_invitation_status(self, invitation: CompanyInvitation, status: str) -> CompanyInvitation:
        invitation.status = status
        invitation.updated_at = datetime.utcnow()
        self.db.flush()
        return invitation

    # Travel Policies ----------------------------------------------------------

    def create_default_policy(self, company_id: int) -> TravelPolicy:
        policy = TravelPolicy(
            company_id=company_id,
            name="Default Policy",
            description="Automatically generated policy",
            require_manager_approval=True,
            require_finance_approval=False,
            auto_ticketing_enabled=False,
            rules={},
            approval_flow=[{"level": 1, "role": "manager"}],
        )
        self.db.add(policy)
        self.db.flush()
        return policy
