from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import LoyaltyAccount


class LoyaltyAccountRepository:
    """Data access layer for loyalty accounts."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: int, include_inactive: bool = False) -> List[LoyaltyAccount]:
        stmt = select(LoyaltyAccount).where(LoyaltyAccount.user_id == user_id)
        if not include_inactive:
            stmt = stmt.where(LoyaltyAccount.is_active.is_(True))
        stmt = stmt.order_by(LoyaltyAccount.airline_iata_code.asc())
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, account_id: int, user_id: Optional[int] = None) -> Optional[LoyaltyAccount]:
        stmt = select(LoyaltyAccount).where(LoyaltyAccount.id == account_id)
        if user_id is not None:
            stmt = stmt.where(LoyaltyAccount.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_and_code(self, user_id: int, airline_iata_code: str) -> Optional[LoyaltyAccount]:
        stmt = select(LoyaltyAccount).where(
            LoyaltyAccount.user_id == user_id,
            LoyaltyAccount.airline_iata_code == airline_iata_code,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        *,
        user_id: int,
        airline_iata_code: str,
        account_number_encrypted: str,
        account_number_last4: str,
        programme_name: Optional[str] = None,
        loyalty_tier: Optional[str] = None,
        loyalty_programme_id: Optional[str] = None,
        perks_snapshot: Optional[dict] = None,
    ) -> LoyaltyAccount:
        account = self.get_by_user_and_code(user_id, airline_iata_code)
        if account:
            account.account_number_encrypted = account_number_encrypted
            account.account_number_last4 = account_number_last4
            account.programme_name = programme_name
            account.loyalty_tier = loyalty_tier
            account.loyalty_programme_id = loyalty_programme_id
            if perks_snapshot is not None:
                account.perks_snapshot = perks_snapshot
            account.is_active = True
        else:
            account = LoyaltyAccount(
                user_id=user_id,
                airline_iata_code=airline_iata_code,
                programme_name=programme_name,
                loyalty_programme_id=loyalty_programme_id,
                account_number_encrypted=account_number_encrypted,
                account_number_last4=account_number_last4,
                loyalty_tier=loyalty_tier,
                perks_snapshot=perks_snapshot or {},
                is_active=True,
            )
            self.db.add(account)
            self.db.flush()
        return account

    def delete(self, account_id: int, user_id: int) -> bool:
        account = self.get_by_id(account_id, user_id)
        if not account:
            return False
        self.db.delete(account)
        return True

    def deactivate_all(self, user_id: int) -> None:
        accounts = self.list_for_user(user_id, include_inactive=True)
        for account in accounts:
            account.is_active = False
