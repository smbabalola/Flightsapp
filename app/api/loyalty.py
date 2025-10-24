"""Loyalty programme account management endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog

from app.auth.dependencies import get_current_user, get_db
from app.auth.permissions import Permission, User, has_permission
from app.models.models import AuditLog
from app.services.loyalty_service import LoyaltyService
from app.services.search_service import SearchService
from app.utils.encryption import EncryptionError

router = APIRouter()
logger = structlog.get_logger(__name__)
_service = LoyaltyService()
_search_service = SearchService()


class LoyaltyAccountResponse(BaseModel):
    id: int
    airline_iata_code: str
    programme_name: Optional[str]
    loyalty_programme_id: Optional[str]
    account_last4: str
    loyalty_tier: Optional[str]
    perks_snapshot: dict
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class CreateLoyaltyAccountRequest(BaseModel):
    airline_iata_code: str
    account_number: str
    programme_name: Optional[str] = None
    loyalty_tier: Optional[str] = None
    loyalty_programme_id: Optional[str] = None
    user_id: Optional[int] = None


class LoyaltyAccountListResponse(BaseModel):
    accounts: List[LoyaltyAccountResponse]


class LoyaltySearchSlice(BaseModel):
    from_: str
    to: str
    date: str
    time_window: Optional[str] = None


class LoyaltySearchAccount(BaseModel):
    airline_iata_code: str
    account_number: str
    loyalty_tier: Optional[str] = None
    loyalty_programme_id: Optional[str] = None


class LoyaltySearchRequest(BaseModel):
    slices: List[LoyaltySearchSlice]
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin: Optional[str] = None
    max_stops: Optional[int] = None
    bags_included: Optional[bool] = True
    loyalty_user_id: Optional[int] = None
    loyalty_accounts: Optional[List[LoyaltySearchAccount]] = None


def _resolve_target_user_id(requested_user_id: Optional[int], current_user: User, db: Session) -> int:
    target_user_id = requested_user_id or current_user.id
    if target_user_id != current_user.id:
        if not has_permission(current_user.role, Permission.MANAGE_USERS):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to manage other users' loyalty accounts")
        user_exists = db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": target_user_id},
        ).fetchone()
        if not user_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
    return target_user_id


@router.get("/loyalty/accounts", response_model=LoyaltyAccountListResponse)
async def list_loyalty_accounts(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve loyalty accounts for the current user or a specified user."""
    target_user_id = _resolve_target_user_id(user_id, current_user, db)
    accounts = _service.list_accounts(target_user_id)
    logger.info(
        "loyalty_accounts_listed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        target_user_id=target_user_id,
        count=len(accounts),
    )
    return {"accounts": accounts}


@router.post("/loyalty/search")
async def loyalty_search(
    payload: LoyaltySearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for offers while applying stored loyalty accounts."""
    target_user_id = _resolve_target_user_id(payload.loyalty_user_id, current_user, db)
    payload_dict = payload.model_dump()
    payload_dict["loyalty_user_id"] = target_user_id
    offers = _search_service.search(payload_dict)

    audit = AuditLog(
        event="loyalty_search_performed",
        actor=current_user.email,
        details={
            "actor_role": current_user.role.value,
            "target_user_id": target_user_id,
            "slice_count": len(payload.slices or []),
            "inline_loyalty_codes": sorted({acct.airline_iata_code.upper() for acct in (payload.loyalty_accounts or [])}),
        },
    )
    db.add(audit)
    db.commit()

    logger.info(
        "loyalty_search_performed",
        actor=current_user.email,
        actor_role=current_user.role.value,
        target_user_id=target_user_id,
        offers=len(offers),
    )
    return {"offers": offers}


@router.post("/loyalty/accounts", response_model=LoyaltyAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_loyalty_account(
    payload: CreateLoyaltyAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a loyalty programme account."""
    target_user_id = _resolve_target_user_id(payload.user_id, current_user, db)
    try:
        account = _service.save_account(
            user_id=target_user_id,
            airline_iata_code=payload.airline_iata_code,
            account_number=payload.account_number,
            programme_name=payload.programme_name,
            loyalty_tier=payload.loyalty_tier,
            loyalty_programme_id=payload.loyalty_programme_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EncryptionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Loyalty encryption is misconfigured") from exc

    audit = AuditLog(
        event="loyalty_account_saved",
        actor=current_user.email,
        details={
            "actor_role": current_user.role.value,
            "target_user_id": target_user_id,
            "airline_iata_code": account["airline_iata_code"],
            "loyalty_tier": account.get("loyalty_tier"),
        },
    )
    db.add(audit)
    db.commit()

    logger.info(
        "loyalty_account_saved",
        actor=current_user.email,
        actor_role=current_user.role.value,
        target_user_id=target_user_id,
        airline=account["airline_iata_code"],
    )
    return account


@router.delete("/loyalty/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loyalty_account(
    account_id: int,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a loyalty account."""
    target_user_id = _resolve_target_user_id(user_id, current_user, db)
    deleted = _service.delete_account(user_id=target_user_id, account_id=account_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loyalty account not found")

    audit = AuditLog(
        event="loyalty_account_deleted",
        actor=current_user.email,
        details={
            "actor_role": current_user.role.value,
            "target_user_id": target_user_id,
            "account_id": account_id,
        },
    )
    db.add(audit)
    db.commit()

    logger.info(
        "loyalty_account_deleted",
        actor=current_user.email,
        actor_role=current_user.role.value,
        target_user_id=target_user_id,
        account_id=account_id,
    )
    return None
