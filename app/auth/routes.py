"""
Authentication Routes

Login, logout, token refresh, and password management.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field, constr
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import timedelta
import structlog

from app.auth.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_password,
    hash_password,
    decode_token,
    verify_token_type,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.auth.dependencies import get_db, get_current_user
from app.auth.permissions import User, Role
from app.models.models import AuditLog
from app.core.rate_limit import rate_limiter
from app.integrations.email_notifier import send_welcome_email

logger = structlog.get_logger(__name__)
router = APIRouter()


class RegisterRequest(BaseModel):
    """Registration request payload."""
    email: EmailStr
    password: constr(min_length=8, max_length=256)
    full_name: str


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str
    company_id: Optional[int] = None
    company_slug: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    company_id: Optional[int] = None
    company_user_id: Optional[int] = None
    company_role: Optional[str] = None
    available_companies: List[dict] = Field(default_factory=list)


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str
    new_password: str


@router.post("/register")
async def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    **Request:**
    - `email`: User email address
    - `password`: User password (minimum 8 characters)
    - `full_name`: User's full name

    **Response:**
    - Success message with user details

    **Rate Limiting:**
    - Maximum 5 registration attempts per 15 minutes per IP
    """
    # Check rate limit
    rate_limiter.check_rate_limit(http_request, max_attempts=5, window_minutes=15)

    client_ip = http_request.client.host if http_request.client else "unknown"

    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check if user already exists
    existing_user = db.execute(
        text("""
            SELECT id FROM users
            WHERE email = :email
        """),
        {"email": request.email}
    ).fetchone()

    if existing_user:
        logger.warning("registration_failed_user_exists", email=request.email, ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = hash_password(request.password)

    # Create user (PostgreSQL only)
    params = {
        "email": request.email,
        "name": request.full_name,
        "hash_password": password_hash
    }
    try:
        result = db.execute(
            text("""
                INSERT INTO users (email, name, role, hash_password, status, created_at)
                VALUES (:email, :name, 'customer', :hash_password, 'active', CURRENT_TIMESTAMP)
                RETURNING id
            """),
            params,
        )
        row = result.fetchone()
        user_id = row[0] if row else None
        if not user_id:
            raise RuntimeError("Failed to create user record")
    except Exception as e:
        db.rollback()
        logger.error("registration_failed_db_error", email=request.email, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {str(e)}")

    # Log registration
    audit_log = AuditLog(
        event="user_registered",
        actor=request.email,
        details={
            "user_id": user_id,
            "name": request.full_name,
            "ip": client_ip
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info("user_registered", user_id=user_id, email=request.email, ip=client_ip)

    # Send welcome email (best-effort, non-blocking)
    try:
        first_name = (request.full_name or '').strip().split(' ')[0] if request.full_name else ''
        send_welcome_email(request.email, first_name)
    except Exception as e:
        logger.warning("welcome_email_failed", email=request.email, error=str(e))

    return {
        "message": "Registration successful",
        "user": {
            "id": user_id,
            "email": request.email,
            "name": request.full_name
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    **Request:**
    - `email`: User email
    - `password`: User password
    - `company_id`: Optional tenant company ID to scope the session
    - `company_slug`: Optional tenant slug (ignored when `company_id` is provided)

    **Response:**
    - `access_token`: JWT access token
    - `refresh_token`: JWT refresh token
    - `token_type`: Always "bearer"
    - `expires_in`: Token expiration time in seconds
    - `company_id`: Active tenant ID when scoped
    - `company_role`: Tenant role when scoped
    - `available_companies`: List of tenant memberships for selection

    **Rate Limiting:**
    - Maximum 5 failed attempts per 15 minutes
    - Account locked for 15 minutes after exceeding limit
    """
    # Check rate limit
    rate_limiter.check_rate_limit(http_request, max_attempts=5, window_minutes=15)

    client_ip = http_request.client.host if http_request.client else "unknown"

    # Find user by email
    user = db.execute(
        text("""
            SELECT id, email, name, role, status, hash_password
            FROM users
            WHERE email = :email
        """),
        {"email": login_request.email}
    ).fetchone()

    if not user:
        logger.warning("login_failed_user_not_found", email=login_request.email, ip=client_ip)
        rate_limiter.record_failed_login(login_request.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(login_request.password, user.hash_password):
        logger.warning("login_failed_wrong_password", email=login_request.email, ip=client_ip)
        rate_limiter.record_failed_login(login_request.email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check user is active
    if user.status != "active":
        logger.warning("login_failed_inactive_user", email=login_request.email, ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    membership_rows = db.execute(
        text("""
            SELECT
                c.id AS company_id,
                c.name AS company_name,
                c.slug AS company_slug,
                c.status AS company_status,
                cu.role AS membership_role,
                cu.status AS membership_status,
                cu.id AS company_user_id
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user.id}
    ).fetchall()

    available_companies = [
        {
            "id": int(row.company_id),
            "name": row.company_name,
            "slug": row.company_slug,
            "status": row.company_status,
            "membership_status": row.membership_status,
            "role": row.membership_role,
            "company_user_id": int(row.company_user_id),
        }
        for row in membership_rows
    ]

    active_memberships = [
        row for row in membership_rows
        if row.company_status == "active" and row.membership_status == "active"
    ]

    selected_membership = None
    if login_request.company_id is not None:
        selected_membership = next(
            (row for row in active_memberships if row.company_id == login_request.company_id),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requested company is not available or inactive",
            )
    elif login_request.company_slug:
        slug = login_request.company_slug.lower()
        selected_membership = next(
            (
                row
                for row in active_memberships
                if (row.company_slug or "").lower() == slug
            ),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requested company is not available or inactive",
            )
    elif len(active_memberships) == 1:
        selected_membership = active_memberships[0]

    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }

    company_id: Optional[int] = None
    company_user_id: Optional[int] = None
    company_role: Optional[str] = None
    if selected_membership:
        company_id = int(selected_membership.company_id)
        company_user_id = int(selected_membership.company_user_id)
        company_role = selected_membership.membership_role
        token_data["company_id"] = company_id
        token_data["company_role"] = company_role

    access_token = create_access_token(token_data)
    refresh_payload = {"user_id": user.id, "email": user.email}
    if company_id is not None:
        refresh_payload["company_id"] = company_id
    refresh_token = create_refresh_token(refresh_payload)

    # Log successful login
    audit_log = AuditLog(
        event="user_login",
        actor=user.email,
        details={
            "user_id": user.id,
            "role": user.role,
            "company_id": company_id,
            "company_role": company_role,
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "user_logged_in",
        user_id=user.id,
        email=user.email,
        role=user.role,
        company_id=company_id,
        company_role=company_role,
    )

    # Clear rate limit attempts on successful login
    rate_limiter.clear_attempts(client_ip)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        company_id=company_id,
        company_user_id=company_user_id,
        company_role=company_role,
        available_companies=available_companies,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    **Request:**
    - `refresh_token`: Valid refresh token

    **Response:**
    - `access_token`: New JWT access token
    - `refresh_token`: New JWT refresh token
    - `company_id`: Tenant ID when scoped
    - `company_role`: Tenant role when scoped
    - `available_companies`: Membership metadata for the user
    """
    payload = decode_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("user_id")
    company_id_claim = payload.get("company_id")

    user = db.execute(
        text("""
            SELECT id, email, name, role, status
            FROM users
            WHERE id = :user_id AND status = 'active'
        """),
        {"user_id": user_id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    membership_rows = db.execute(
        text("""
            SELECT
                c.id AS company_id,
                c.name AS company_name,
                c.slug AS company_slug,
                c.status AS company_status,
                cu.role AS membership_role,
                cu.status AS membership_status
                cu.id AS company_user_id
            FROM company_users cu
            JOIN companies c ON c.id = cu.company_id
            WHERE cu.user_id = :user_id
            ORDER BY c.name
        """),
        {"user_id": user.id}
    ).fetchall()

    available_companies = [
        {
            "id": int(row.company_id),
            "name": row.company_name,
            "slug": row.company_slug,
            "status": row.company_status,
            "membership_status": row.membership_status,
            "role": row.membership_role,
            "company_user_id": int(row.company_user_id),
        }
        for row in membership_rows
    ]

    active_memberships = [
        row for row in membership_rows
        if row.company_status == "active" and row.membership_status == "active"
    ]

    company_id: Optional[int] = None
    company_user_id: Optional[int] = None
    company_role: Optional[str] = None
    if company_id_claim is not None:
        selected_membership = next(
            (row for row in active_memberships if row.company_id == company_id_claim),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant membership is no longer valid",
            )
        company_id = int(selected_membership.company_id)
        company_user_id = int(selected_membership.company_user_id)
        company_role = selected_membership.membership_role

    token_data = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }
    if company_id is not None:
        token_data["company_id"] = company_id
        token_data["company_role"] = company_role

    access_token = create_access_token(token_data)
    refresh_payload = {"user_id": user.id, "email": user.email}
    if company_id is not None:
        refresh_payload["company_id"] = company_id
    refresh_token = create_refresh_token(refresh_payload)

    logger.info("token_refreshed", user_id=user.id, company_id=company_id, company_role=company_role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        company_id=company_id,
        company_user_id=company_user_id,
        company_role=company_role,
        available_companies=available_companies,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.

    **Request:**
    - `current_password`: Current password
    - `new_password`: New password

    **Authorization:** Requires valid JWT token
    """
    # Get user with password hash
    user = db.execute(
        text("""
            SELECT id, email, hash_password
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": current_user.id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(request.current_password, user.hash_password):
        logger.warning("password_change_failed_wrong_current", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_hash = hash_password(request.new_password)

    # Update password
    db.execute(
        text("""
            UPDATE users
            SET hash_password = :hash
            WHERE id = :user_id
        """),
        {"hash": new_hash, "user_id": current_user.id}
    )

    # Log password change
    audit_log = AuditLog(
        event="password_changed",
        actor=current_user.email,
        details={"user_id": current_user.id}
    )
    db.add(audit_log)
    db.commit()

    logger.info("password_changed", user_id=current_user.id)

    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.

    **Authorization:** Requires valid JWT token

    **Response:**
    - `id`: User ID
    - `email`: User email
    - `name`: User name
    - `role`: User role
    - `status`: User status
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "status": current_user.status,
        "company_id": current_user.company_id,
        "company_role": current_user.company_role.value if current_user.company_role else None,
        "permissions": sorted(perm.value for perm in current_user.permissions),
        "company_permissions": sorted(perm.value for perm in current_user.company_permissions),
    }


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    **Request:**
    - `email`: User email address

    **Response:**
    - Success message (always returns success to prevent email enumeration)

    **Rate Limiting:**
    - Maximum 3 requests per 15 minutes per IP
    """
    # Check rate limit for password reset requests
    rate_limiter.check_rate_limit(http_request, max_attempts=3, window_minutes=15)

    # Import service here to avoid circular imports
    from app.services.password_reset_service import PasswordResetService

    # Get base URL from request
    base_url = str(http_request.base_url).rstrip('/')

    # Request password reset
    result = PasswordResetService.request_password_reset(
        db=db,
        email=request.email,
        base_url=base_url
    )

    logger.info("password_reset_requested", email=request.email)

    return {"message": result["message"]}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from email.

    **Request:**
    - `token`: Reset token from email
    - `new_password`: New password (minimum 8 characters recommended)

    **Response:**
    - Success or error message
    """
    # Validate password strength (basic check)
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Import service here to avoid circular imports
    from app.services.password_reset_service import PasswordResetService

    # Reset password
    result = PasswordResetService.reset_password(
        db=db,
        token=request.token,
        new_password=request.new_password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    logger.info("password_reset_completed")

    return {"message": result["message"]}


@router.get("/verify-reset-token")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify if a password reset token is valid.

    **Query Parameters:**
    - `token`: Reset token to verify

    **Response:**
    - `valid`: Boolean indicating if token is valid
    - `message`: Description message
    """
    from app.services.password_reset_service import PasswordResetService

    result = PasswordResetService.verify_reset_token(db=db, token=token)

    return {
        "valid": result["valid"],
        "message": result["message"]
    }
