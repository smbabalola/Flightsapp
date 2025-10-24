from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.loyalty_repo import LoyaltyAccountRepository
from app.utils.encryption import EncryptionError, decrypt_secret, encrypt_secret, mask_last4


class LoyaltyService:
    """Business logic for storing and using loyalty programme accounts."""

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal):
        self._session_factory = session_factory

    @contextmanager
    def _session(self) -> Iterable[Session]:
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def list_accounts(self, user_id: int, include_inactive: bool = False) -> List[Dict[str, Any]]:
        with self._session() as db:
            repo = LoyaltyAccountRepository(db)
            accounts = repo.list_for_user(user_id, include_inactive=include_inactive)
            return [self._serialize(account) for account in accounts]

    def save_account(
        self,
        *,
        user_id: int,
        airline_iata_code: str,
        account_number: str,
        programme_name: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        loyalty_programme_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_code = (airline_iata_code or "").strip().upper()
        if not clean_code:
            raise ValueError("airline_iata_code is required")
        clean_number = (account_number or "").replace(" ", "").replace("-", "").strip()
        if not clean_number:
            raise ValueError("account_number is required")

        encrypted = encrypt_secret(clean_number)
        last4 = mask_last4(clean_number)

        with self._session() as db:
            repo = LoyaltyAccountRepository(db)
            account = repo.upsert(
                user_id=user_id,
                airline_iata_code=clean_code,
                account_number_encrypted=encrypted,
                account_number_last4=last4,
                programme_name=programme_name.strip() if programme_name else None,
                loyalty_tier=loyalty_tier.strip() if loyalty_tier else None,
                loyalty_programme_id=loyalty_programme_id.strip() if loyalty_programme_id else None,
            )
            db.commit()
            db.refresh(account)
            return self._serialize(account)

    def delete_account(self, *, user_id: int, account_id: int) -> bool:
        with self._session() as db:
            repo = LoyaltyAccountRepository(db)
            deleted = repo.delete(account_id, user_id)
            if deleted:
                db.commit()
            return deleted

    def get_accounts_for_injection(self, user_id: int) -> List[Dict[str, Any]]:
        with self._session() as db:
            repo = LoyaltyAccountRepository(db)
            accounts = repo.list_for_user(user_id, include_inactive=False)
            payload: List[Dict[str, Any]] = []
            for account in accounts:
                try:
                    account_number = decrypt_secret(account.account_number_encrypted)
                except EncryptionError:
                    continue
                entry: Dict[str, Any] = {
                    "airline_iata_code": account.airline_iata_code,
                    "account_number": account_number,
                }
                if account.loyalty_tier:
                    entry["loyalty_tier"] = account.loyalty_tier
                if account.loyalty_programme_id:
                    entry["loyalty_programme_id"] = account.loyalty_programme_id
                payload.append(entry)
            return payload

    def update_perks_snapshot(
        self,
        user_id: int,
        loyalty_details: Iterable[Dict[str, Any]],
    ) -> None:
        if not loyalty_details:
            return
        with self._session() as db:
            repo = LoyaltyAccountRepository(db)
            accounts = {acct.airline_iata_code: acct for acct in repo.list_for_user(user_id, include_inactive=True)}
            changed = False
            for detail in loyalty_details:
                code = (detail.get("airline_iata_code") or "").strip().upper()
                if not code or code not in accounts:
                    continue
                account = accounts[code]
                filtered_detail = {
                    k: v for k, v in detail.items() if k not in {"account_number", "account_number_encrypted", "account_number_last4"}
                }
                account.perks_snapshot = filtered_detail
                account.updated_at = datetime.utcnow()
                changed = True
            if changed:
                db.commit()

    def _serialize(self, account) -> Dict[str, Any]:
        return {
            "id": account.id,
            "airline_iata_code": account.airline_iata_code,
            "programme_name": account.programme_name,
            "loyalty_programme_id": account.loyalty_programme_id,
            "account_last4": account.account_number_last4,
            "loyalty_tier": account.loyalty_tier,
            "perks_snapshot": account.perks_snapshot or {},
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        }
