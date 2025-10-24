from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_db,
    get_current_active_user,
    require_company_permission,
    require_company_role,
    require_admin,
)
from app.auth.permissions import (
    User,
    CompanyRole,
    CompanyPermission,
)
from app.services.company_service import CompanyService


router = APIRouter(prefix="/b2b", tags=["B2B Companies"])


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------


class CompanyOnboardingRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    admin_email: EmailStr
    admin_name: str = Field(..., min_length=2)
    admin_password: str = Field(..., min_length=8)


class CompanyOnboardingResponse(BaseModel):
    company_id: int
    company_slug: str
    admin_user_id: int
    message: str = "Company onboarded successfully"


class CompanyProfileResponse(BaseModel):
    id: int
    name: str
    slug: str
    domain: Optional[str]
    country: Optional[str]
    currency: Optional[str]
    status: str
    settings: dict
    payment_preferences: dict
    company_role: Optional[str]
    permissions: List[str]
    company_permissions: List[str]


class UpdateCompanyRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    domain: Optional[str] = None
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    settings: Optional[dict] = None
    payment_preferences: Optional[dict] = None


class CompanyMemberResponse(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    name: Optional[str]
    role: str
    status: str
    department_id: Optional[int]
    title: Optional[str]
    cost_center_code: Optional[str]
    joined_at: Optional[datetime]
    invited_at: Optional[datetime]
    last_seen_at: Optional[datetime]


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str
    department_id: Optional[int] = None
    expires_in_hours: Optional[int] = Field(72, ge=1, le=336)


class InviteMemberResponse(BaseModel):
    token: str
    expires_at: datetime
    role: str


class InvitationPreviewResponse(BaseModel):
    company_id: int
    email: EmailStr
    role: str
    status: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    full_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)


class AcceptInvitationResponse(BaseModel):
    company_id: Optional[int]
    company_user_id: int
    user_id: int
    message: str = "Invitation accepted"


class AdminCompanySummary(BaseModel):
    id: int
    name: str
    slug: str
    status: str
    country: Optional[str]
    currency: Optional[str]
    created_at: datetime


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.post("/companies", response_model=CompanyOnboardingResponse, status_code=status.HTTP_201_CREATED)
async def onboard_company(
    request: CompanyOnboardingRequest,
    db: Session = Depends(get_db)
):
    service = CompanyService(db)
    try:
        result = service.create_company_with_admin(
            name=request.company_name,
            slug=request.slug,
            domain=request.domain,
            country=request.country,
            currency=request.currency,
            admin_email=request.admin_email,
            admin_name=request.admin_name,
            admin_password=request.admin_password,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    company = result["company"]
    return CompanyOnboardingResponse(
        company_id=company.id,
        company_slug=company.slug,
        admin_user_id=result["admin_user_id"],
    )


@router.get(
    "/companies/me",
    response_model=CompanyProfileResponse,
)
async def get_company_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No tenant context in token. Please login with a company selected."
        )

    service = CompanyService(db)
    company = service.repo.get_by_id(current_user.company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        domain=company.domain,
        country=company.country,
        currency=company.currency,
        status=company.status,
        settings=company.settings or {},
        payment_preferences=company.payment_preferences or {},
        company_role=current_user.company_role.value if current_user.company_role else None,
        permissions=sorted(perm.value for perm in current_user.permissions),
        company_permissions=sorted(perm.value for perm in current_user.company_permissions),
    )


@router.put(
    "/companies/me",
    response_model=CompanyProfileResponse,
    dependencies=[Depends(require_company_role(CompanyRole.ADMIN))]
)
async def update_company_profile(
    request: UpdateCompanyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    service = CompanyService(db)
    try:
        company = service.update_company_profile(
            company_id=current_user.company_id,
            name=request.name,
            domain=request.domain,
            country=request.country,
            currency=request.currency,
            settings=request.settings,
            payment_preferences=request.payment_preferences,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return CompanyProfileResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        domain=company.domain,
        country=company.country,
        currency=company.currency,
        status=company.status,
        settings=company.settings or {},
        payment_preferences=company.payment_preferences or {},
        company_role=current_user.company_role.value if current_user.company_role else None,
        permissions=sorted(perm.value for perm in current_user.permissions),
        company_permissions=sorted(perm.value for perm in current_user.company_permissions),
    )


@router.get(
    "/members",
    response_model=List[CompanyMemberResponse],
    dependencies=[Depends(require_company_permission(CompanyPermission.VIEW_EMPLOYEES))]
)
async def list_company_members(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    service = CompanyService(db)
    members = service.list_members(current_user.company_id)
    return [
        CompanyMemberResponse(
            id=row["id"],
            user_id=row["user_id"],
            email=row["email"],
            name=row["name"],
            role=row["role"],
            status=row["status"],
            department_id=row["department_id"],
            title=row["title"],
            cost_center_code=row["cost_center_code"],
            joined_at=row["joined_at"],
            invited_at=row["invited_at"],
            last_seen_at=row["last_seen_at"],
        )
        for row in members
    ]


@router.post(
    "/members/invite",
    response_model=InviteMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_company_permission(CompanyPermission.MANAGE_EMPLOYEES))]
)
async def invite_member(
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        role = CompanyRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Expected one of: company_admin, manager, employee, finance"
        )

    service = CompanyService(db)
    try:
        invitation = service.create_invitation(
            company_id=current_user.company_id,
            inviter_company_user_id=current_user.id,
            email=request.email,
            role=role,
            department_id=request.department_id,
            expires_in_hours=request.expires_in_hours or 72,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return InviteMemberResponse(
        token=invitation.token,
        expires_at=invitation.expires_at,
        role=invitation.role,
    )


@router.get("/invitations/{token}", response_model=InvitationPreviewResponse)
async def preview_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    service = CompanyService(db)
    invitation = service.get_invitation(token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    return InvitationPreviewResponse(
        company_id=invitation.company_id,
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at,
    )


@router.post("/invitations/{token}/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    token: str,
    request: AcceptInvitationRequest,
    db: Session = Depends(get_db)
):
    service = CompanyService(db)
    try:
        user_id, company_user_id, company_id = service.accept_invitation(
            token=token,
            full_name=request.full_name,
            password=request.password,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return AcceptInvitationResponse(
        company_id=company_id,
        company_user_id=company_user_id,
        user_id=user_id,
    )


@router.get(
    "/admin/companies",
    response_model=List[AdminCompanySummary],
    dependencies=[Depends(require_admin)]
)
async def admin_list_companies(db: Session = Depends(get_db)):
    service = CompanyService(db)
    companies = service.list_companies()
    return [
        AdminCompanySummary(
            id=company.id,
            name=company.name,
            slug=company.slug,
            status=company.status,
            country=company.country,
            currency=company.currency,
            created_at=company.created_at,
        )
        for company in companies
    ]
