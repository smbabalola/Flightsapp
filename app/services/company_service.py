from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.jwt_service import hash_password, verify_password
from app.models.models import AuditLog
from app.repositories.company_repo import CompanyRepository
from app.auth.permissions import CompanyRole


class CompanyService:
    """Business logic for corporate tenant onboarding and management."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CompanyRepository(db)

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
        slug = slug.strip("-")
        return slug or uuid.uuid4().hex[:8]

    def _ensure_unique_slug(self, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while self.repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def _get_user_by_email(self, email: str):
        stmt = text(
            """
            SELECT id, email, name, role, status, hash_password
            FROM users
            WHERE email = :email
            """
        )
        return self.db.execute(stmt, {"email": email}).mappings().first()

    def _create_user(self, *, email: str, name: str, password: str) -> int:
        password_hash = hash_password(password)
        stmt = text(
            """
            INSERT INTO users (email, name, role, hash_password, status, created_at)
            VALUES (:email, :name, :role, :hash_password, 'active', :created_at)
            RETURNING id
            """
        )
        result = self.db.execute(
            stmt,
            {
                "email": email,
                "name": name,
                "role": "customer",
                "hash_password": password_hash,
                "created_at": datetime.utcnow(),
            },
        )
        user_id = result.scalar_one()
        return user_id

    # ---------------------------------------------------------------------
    # Company onboarding
    # ---------------------------------------------------------------------

    def create_company_with_admin(
        self,
        *,
        name: str,
        slug: Optional[str],
        domain: Optional[str],
        country: Optional[str],
        currency: Optional[str],
        admin_email: str,
        admin_name: str,
        admin_password: str,
    ) -> dict:
        base_slug = self._slugify(slug or name)
        unique_slug = self._ensure_unique_slug(base_slug)

        existing_user = self._get_user_by_email(admin_email)
        if existing_user:
            raise ValueError("An account with this email already exists. Ask the admin to use invitations instead.")

        company = self.repo.create_company(
            name=name,
            slug=unique_slug,
            domain=domain,
            country=country,
            currency=currency,
        )

        admin_user_id = self._create_user(
            email=admin_email,
            name=admin_name,
            password=admin_password,
        )

        membership = self.repo.create_company_user(
            company_id=company.id,
            user_id=admin_user_id,
            role=CompanyRole.ADMIN.value,
            joined_at=datetime.utcnow(),
        )

        policy = self.repo.create_default_policy(company.id)

        audit = AuditLog(
            event="company_onboarded",
            actor=admin_email,
            details={
                "company_id": company.id,
                "company_slug": company.slug,
                "admin_user_id": admin_user_id,
            },
        )
        self.db.add(audit)

        return {
            "company": company,
            "admin_user_id": admin_user_id,
            "membership": membership,
            "default_policy": policy,
        }

    def update_company_profile(
        self,
        *,
        company_id: int,
        name: Optional[str],
        domain: Optional[str],
        country: Optional[str],
        currency: Optional[str],
        settings: Optional[dict],
        payment_preferences: Optional[dict],
    ):
        company = self.repo.get_by_id(company_id)
        if not company:
            raise ValueError("Company not found")
        return self.repo.update_company(
            company,
            name=name,
            domain=domain,
            country=country,
            currency=currency,
            settings=settings,
            payment_preferences=payment_preferences,
        )

    def list_members(self, company_id: int):
        return self.repo.list_company_members(company_id)

    # ---------------------------------------------------------------------
    # Invitations
    # ---------------------------------------------------------------------

    def create_invitation(
        self,
        *,
        company_id: int,
        inviter_company_user_id: Optional[int],
        email: str,
        role: CompanyRole,
        department_id: Optional[int] = None,
        expires_in_hours: int = 72,
    ):
        existing_invite = self.db.execute(
            text(
                """
                SELECT id FROM company_invitations
                WHERE company_id = :company_id
                  AND email = :email
                  AND status = 'pending'
                """
            ),
            {"company_id": company_id, "email": email},
        ).fetchone()
        if existing_invite:
            raise ValueError("An active invitation already exists for this email")

        membership = None
        user_row = self._get_user_by_email(email)
        if user_row:
            membership = self.repo.get_company_user(company_id=company_id, user_id=user_row["id"])
        if membership and membership.status == "active":
            raise ValueError("User is already a member of this company")

        token = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        invitation = self.repo.create_invitation(
            company_id=company_id,
            inviter_company_user_id=inviter_company_user_id,
            email=email,
            role=role.value,
            department_id=department_id,
            token=token,
            expires_at=expires_at,
        )

        return invitation

    def get_invitation(self, token: str):
        return self.repo.get_invitation_by_token(token)

    def accept_invitation(
        self,
        *,
        token: str,
        full_name: str,
        password: str,
    ) -> Tuple[int, int, int]:
        invitation = self.repo.get_invitation_by_token(token)
        if not invitation:
            raise ValueError("Invitation not found")
        if invitation.status != "pending":
            raise ValueError("Invitation has already been processed")
        if invitation.expires_at < datetime.utcnow():
            self.repo.mark_invitation_status(invitation, "expired")
            raise ValueError("Invitation has expired")

        user_row = self._get_user_by_email(invitation.email)
        if user_row:
            if user_row["status"] != "active":
                raise ValueError("User account is not active")
            if not verify_password(password, user_row["hash_password"]):
                raise ValueError("Incorrect password for existing account")
            user_id = user_row["id"]
        else:
            user_id = self._create_user(email=invitation.email, name=full_name, password=password)

        membership = self.repo.get_company_user(company_id=invitation.company_id, user_id=user_id)
        if membership:
            membership.status = "active"
            membership.joined_at = datetime.utcnow()
            membership.role = invitation.role
            self.db.flush()
        else:
            membership = self.repo.create_company_user(
                company_id=invitation.company_id,
                user_id=user_id,
                role=invitation.role,
                joined_at=datetime.utcnow(),
            )

        self.repo.mark_invitation_status(invitation, "accepted")

        audit = AuditLog(
            event="company_invitation_accepted",
            actor=invitation.email,
            details={
                "company_id": invitation.company_id,
                "company_user_id": membership.id,
            },
        )
        self.db.add(audit)

        return user_id, membership.id, invitation.company_id

    # ---------------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------------

    def list_companies(self):
        return self.repo.list_companies()
