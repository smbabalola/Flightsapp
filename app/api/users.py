"""
User Management API

Admin and Supervisor endpoints for user CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

from app.auth.dependencies import get_db, get_current_user, require_permission
from app.auth.permissions import User, Role, Permission, can_assign_role
from app.auth.jwt_service import hash_password
from app.models.models import AuditLog

logger = structlog.get_logger(__name__)
router = APIRouter()


class CreateUserRequest(BaseModel):
    """Create user request."""
    email: EmailStr
    name: str
    password: str
    role: str
    status: str = "active"


class UpdateUserRequest(BaseModel):
    """Update user request."""
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """User response."""
    id: int
    email: str
    name: str
    role: str
    status: str


@router.get(
    "/users",
    response_model=List[UserResponse],
    dependencies=[Depends(require_permission(Permission.VIEW_USERS))]
)
async def list_users(
    status: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering.

    **Query Parameters:**
    - `status`: Filter by status (active, inactive)
    - `role`: Filter by role (agent, supervisor, finance, admin)

    **Authorization:** Requires `VIEW_USERS` permission
    """
    # Build query
    where_clauses = []
    params = {}

    if status:
        where_clauses.append("status = :status")
        params["status"] = status

    if role:
        where_clauses.append("role = :role")
        params["role"] = role

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    users = db.execute(
        text(f"""
            SELECT id, email, name, role, status
            FROM users
            WHERE {where_sql}
            ORDER BY created_at DESC
        """),
        params
    ).fetchall()

    logger.info(
        "users_listed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        count=len(users)
    )

    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name or "",
            role=u.role,
            status=u.status
        )
        for u in users
    ]


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.VIEW_USERS))]
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.

    **Path Parameters:**
    - `user_id`: User ID

    **Authorization:** Requires `VIEW_USERS` permission
    """
    user = db.execute(
        text("""
            SELECT id, email, name, role, status
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": user_id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name or "",
        role=user.role,
        status=user.status
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))]
)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user.

    **Request Body:**
    - `email`: User email (must be unique)
    - `name`: User name
    - `password`: Initial password
    - `role`: User role (agent, supervisor, finance, admin)
    - `status`: User status (active, inactive) - defaults to active

    **Authorization:** Requires `MANAGE_USERS` permission

    **Notes:**
    - Supervisor cannot create admin users
    - Only admin can create admin users
    """
    # Validate role
    try:
        target_role = Role(request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}. Must be one of: agent, supervisor, finance, admin"
        )

    # Check if current user can assign this role
    if not can_assign_role(current_user.role, target_role):
        logger.warning(
            "unauthorized_role_assignment",
            actor=current_user.email,
            actor_role=current_user.role.value,
            target_role=target_role.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to assign role: {target_role.value}"
        )

    # Check if email already exists
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": request.email}
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Hash password
    hashed_password = hash_password(request.password)

    # Create user (PostgreSQL)
    result = db.execute(
        text("""
            INSERT INTO users (email, name, role, hash_password, status)
            VALUES (:email, :name, :role, :hash, :status)
            RETURNING id
        """),
        {
            "email": request.email,
            "name": request.name,
            "role": request.role,
            "hash": hashed_password,
            "status": request.status,
        }
    )

    row = result.fetchone()
    user_id = int(row[0]) if row else None

    # Log user creation
    audit_log = AuditLog(
        event="user_created",
        actor=current_user.email,
        details={
            "created_user_id": user_id,
            "created_user_email": request.email,
            "created_user_role": request.role,
            "actor_role": current_user.role.value,
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "user_created",
        actor=current_user.email,
        actor_role=current_user.role.value,
        created_user_id=user_id,
        created_user_email=request.email,
        created_user_role=request.role
    )

    return UserResponse(
        id=user_id,
        email=request.email,
        name=request.name,
        role=request.role,
        status=request.status
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))]
)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information.

    **Path Parameters:**
    - `user_id`: User ID

    **Request Body (all optional):**
    - `name`: New name
    - `role`: New role
    - `status`: New status

    **Authorization:** Requires `MANAGE_USERS` permission

    **Notes:**
    - Supervisor cannot change role to/from admin
    - Only admin can manage admin roles
    """
    # Get existing user
    user = db.execute(
        text("SELECT id, email, role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build update query
    updates = []
    params = {"user_id": user_id}

    if request.name is not None:
        updates.append("name = :name")
        params["name"] = request.name

    if request.role is not None:
        # Validate role
        try:
            target_role = Role(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}"
            )

        # Check if current user can assign this role
        if not can_assign_role(current_user.role, target_role):
            logger.warning(
                "unauthorized_role_change",
                actor=current_user.email,
                actor_role=current_user.role.value,
                target_role=target_role.value,
                target_user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to assign role: {target_role.value}"
            )

        # Check if user being updated is admin (only admin can change admin's role)
        if user.role == "admin" and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can modify admin users"
            )

        updates.append("role = :role")
        params["role"] = request.role

    if request.status is not None:
        updates.append("status = :status")
        params["status"] = request.status

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    # Update user
    db.execute(
        text(f"""
            UPDATE users
            SET {", ".join(updates)}
            WHERE id = :user_id
        """),
        params
    )

    # Log user update
    audit_log = AuditLog(
        event="user_updated",
        actor=current_user.email,
        details={
            "updated_user_id": user_id,
            "updated_user_email": user.email,
            "updates": {k: v for k, v in params.items() if k != "user_id"},
            "actor_role": current_user.role.value,
        }
    )
    db.add(audit_log)
    db.commit()

    # Get updated user
    updated_user = db.execute(
        text("SELECT id, email, name, role, status FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    logger.info(
        "user_updated",
        actor=current_user.email,
        actor_role=current_user.role.value,
        updated_user_id=user_id,
        updates=params
    )

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name or "",
        role=updated_user.role,
        status=updated_user.status
    )


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))]
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user (soft delete).

    **Path Parameters:**
    - `user_id`: User ID

    **Authorization:** Requires `MANAGE_USERS` permission

    **Notes:**
    - Users are not actually deleted, just set to inactive status
    - Supervisor cannot delete admin users
    """
    # Get user
    user = db.execute(
        text("SELECT id, email, role FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is admin (only admin can delete admin)
    if user.role == "admin" and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete admin users"
        )

    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    # Soft delete (set to inactive)
    db.execute(
        text("UPDATE users SET status = 'inactive' WHERE id = :user_id"),
        {"user_id": user_id}
    )

    # Log user deletion
    audit_log = AuditLog(
        event="user_deleted",
        actor=current_user.email,
        details={
            "deleted_user_id": user_id,
            "deleted_user_email": user.email,
            "deleted_user_role": user.role,
            "actor_role": current_user.role.value,
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "user_deleted",
        actor=current_user.email,
        actor_role=current_user.role.value,
        deleted_user_id=user_id,
        deleted_user_email=user.email
    )

    return {"message": "User deactivated successfully"}


class UserPreferencesResponse(BaseModel):
    """User preferences response."""
    country: str
    preferred_currency: str


class UpdatePreferencesRequest(BaseModel):
    """Update preferences request."""
    country: str
    preferred_currency: str


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's regional preferences.

    **Response:**
    - `country`: User's country code (ISO 3166-1 alpha-2)
    - `preferred_currency`: User's preferred currency code (ISO 4217)

    **Authorization:** Requires valid JWT token
    """
    user = db.execute(
        text("""
            SELECT country, preferred_currency
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": current_user.id}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserPreferencesResponse(
        country=user.country or "GB",
        preferred_currency=user.preferred_currency or "GBP"
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's regional preferences.

    **Request Body:**
    - `country`: Country code (ISO 3166-1 alpha-2, e.g., "GB", "US", "NG")
    - `preferred_currency`: Currency code (ISO 4217, e.g., "GBP", "USD", "NGN")

    **Authorization:** Requires valid JWT token
    """
    # Update preferences
    db.execute(
        text("""
            UPDATE users
            SET country = :country, preferred_currency = :currency
            WHERE id = :user_id
        """),
        {
            "country": request.country,
            "currency": request.preferred_currency,
            "user_id": current_user.id
        }
    )

    # Log preference update
    audit_log = AuditLog(
        event="preferences_updated",
        actor=current_user.email,
        details={
            "user_id": current_user.id,
            "country": request.country,
            "currency": request.preferred_currency
        }
    )
    db.add(audit_log)
    db.commit()

    logger.info(
        "preferences_updated",
        user_id=current_user.id,
        email=current_user.email,
        country=request.country,
        currency=request.preferred_currency
    )

    return UserPreferencesResponse(
        country=request.country,
        preferred_currency=request.preferred_currency
    )
