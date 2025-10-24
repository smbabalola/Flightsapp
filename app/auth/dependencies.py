"""
Authentication Dependencies

FastAPI dependencies for JWT authentication and role-based access control.
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.jwt_service import decode_token, verify_token_type
from app.auth.permissions import (
    Role,
    Permission,
    CompanyRole,
    CompanyPermission,
    get_role_permissions,
    get_company_role_permissions,
    User,
)
from app.db.session import SessionLocal
import structlog

logger = structlog.get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _load_company_membership(
    db: Session,
    user_id: int,
    company_id: Optional[int]
) -> tuple[Optional[int], Optional[int], Optional[CompanyRole], set[CompanyPermission]]:
    """Load and validate company membership for the given user."""
    if not company_id:
        return None, None, set()

    membership = db.execute(
        text(
            """
            SELECT
                cu.company_id,
                cu.id AS company_user_id,
                cu.role AS company_role,
                cu.status AS membership_status,
                c.status AS company_status
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
              AND cu.company_id = :company_id
            """
        ),
        {"user_id": user_id, "company_id": company_id}
    ).fetchone()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant membership not found",
        )

    if membership.membership_status != "active" or membership.company_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant membership inactive",
        )

    try:
        company_role = CompanyRole(membership.company_role)
    except ValueError as exc:
        logger.error(
            "invalid_company_role",
            user_id=user_id,
            company_id=company_id,
            role=membership.company_role,
            error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid company role"
        ) from exc

    permissions = get_company_role_permissions(company_role)
    return membership.company_id, membership.company_user_id, company_role, permissions


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT token, returning the current user."""
    token = credentials.credentials

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    email = payload.get("email")
    role_str = payload.get("role")
    company_id_claim = payload.get("company_id")

    if not user_id or not email or not role_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_record = db.execute(
        text(
            """
            SELECT id, email, name, role, status
            FROM users
            WHERE id = :user_id AND status = 'active'
            """
        ),
        {"user_id": user_id}
    ).fetchone()

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        system_role = Role(role_str)
    except ValueError as exc:
        logger.error("invalid_system_role", user_id=user_id, role=role_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user role",
        ) from exc

    resolved_company_id, company_user_id, company_role, company_permissions = _load_company_membership(
        db=db,
        user_id=user_id,
        company_id=company_id_claim,
    )

    system_permissions = get_role_permissions(system_role)

    return User(
        id=user_record.id,
        email=user_record.email,
        name=user_record.name or "",
        role=system_role,
        status=user_record.status,
        company_id=resolved_company_id,
        company_user_id=company_user_id,
        company_role=company_role,
        permissions=system_permissions,
        company_permissions=company_permissions,
    )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active."""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Best-effort user extraction. Returns None when no/invalid token.

    Does not raise; safe for public endpoints that can benefit from context.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
        if not payload or not verify_token_type(payload, "access"):
            return None
        user_id = payload.get("user_id")
        email = payload.get("email")
        role_str = payload.get("role")
        if not user_id or not email or not role_str:
            return None
        user_record = db.execute(
            text(
                """
                SELECT id, email, name, role, status, country, preferred_currency
                FROM users
                WHERE id = :user_id AND status = 'active'
                """
            ),
            {"user_id": user_id}
        ).fetchone()
        if not user_record:
            return None
        try:
            system_role = Role(role_str)
        except Exception:
            return None
        system_permissions = get_role_permissions(system_role)
        return User(
            id=user_record.id,
            email=user_record.email,
            name=user_record.name or "",
            role=system_role,
            status=user_record.status,
            company_id=None,
            company_user_id=None,
            company_role=None,
            permissions=system_permissions,
            company_permissions=set(),
        )
    except Exception:
        return None


def require_permission(permission: Permission):
    """Dependency factory for requiring a specific system permission."""
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.permissions:
            logger.warning(
                "permission_denied",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_permission=permission.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user

    return permission_checker


def require_any_permission(permissions: List[Permission]):
    """Dependency factory for requiring any of the specified system permissions."""
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not any(p in current_user.permissions for p in permissions):
            logger.warning(
                "permission_denied",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_permissions=[p.value for p in permissions]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {[p.value for p in permissions]}"
            )
        return current_user

    return permission_checker


def require_role(role: Role):
    """Dependency factory for requiring a specific system role."""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != role:
            logger.warning(
                "role_access_denied",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_role=role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {role.value}"
            )
        return current_user

    return role_checker


def require_any_role(roles: List[Role]):
    """Dependency factory for requiring any of the specified system roles."""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in roles:
            logger.warning(
                "role_access_denied",
                user_id=current_user.id,
                user_role=current_user.role.value,
                required_roles=[r.value for r in roles]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of: {[r.value for r in roles]}"
            )
        return current_user

    return role_checker


def require_company_permission(permission: CompanyPermission):
    """Ensure the user has a specific tenant permission."""
    async def checker(current_user: User = Depends(get_current_active_user)):
        if current_user.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context required"
            )
        if permission not in current_user.company_permissions:
            logger.warning(
                "company_permission_denied",
                user_id=current_user.id,
                company_id=current_user.company_id,
                company_role=current_user.company_role.value if current_user.company_role else None,
                required_permission=permission.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient tenant permissions. Required: {permission.value}"
            )
        return current_user

    return checker


def require_any_company_permission(permissions: List[CompanyPermission]):
    """Ensure the user has at least one tenant permission from the list."""
    async def checker(current_user: User = Depends(get_current_active_user)):
        if current_user.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context required"
            )
        if not any(p in current_user.company_permissions for p in permissions):
            logger.warning(
                "company_permission_denied",
                user_id=current_user.id,
                company_id=current_user.company_id,
                company_role=current_user.company_role.value if current_user.company_role else None,
                required_permissions=[p.value for p in permissions],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient tenant permissions. Required one of: {[p.value for p in permissions]}"
            )
        return current_user

    return checker


def require_company_role(role: CompanyRole):
    """Ensure the user holds the specified tenant role."""
    async def checker(current_user: User = Depends(get_current_active_user)):
        if current_user.company_id is None or current_user.company_role != role:
            logger.warning(
                "company_role_denied",
                user_id=current_user.id,
                company_id=current_user.company_id,
                company_role=current_user.company_role.value if current_user.company_role else None,
                required_role=role.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required company role: {role.value}"
            )
        return current_user

    return checker


def require_any_company_role(roles: List[CompanyRole]):
    """Ensure the user holds any of the specified tenant roles."""
    async def checker(current_user: User = Depends(get_current_active_user)):
        if current_user.company_id is None or current_user.company_role not in roles:
            logger.warning(
                "company_role_denied",
                user_id=current_user.id,
                company_id=current_user.company_id,
                company_role=current_user.company_role.value if current_user.company_role else None,
                required_roles=[r.value for r in roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of tenant roles: {[r.value for r in roles]}"
            )
        return current_user

    return checker


# Convenience dependencies for common roles
require_admin = require_role(Role.ADMIN)
require_supervisor_or_admin = require_any_role([Role.SUPERVISOR, Role.ADMIN])
require_finance_or_admin = require_any_role([Role.FINANCE, Role.ADMIN])

require_company_admin = require_company_role(CompanyRole.ADMIN)
require_company_manager = require_company_role(CompanyRole.MANAGER)
require_finance_approver = require_company_role(CompanyRole.FINANCE)
