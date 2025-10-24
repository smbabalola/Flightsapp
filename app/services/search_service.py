from typing import List, Dict, Any, Optional
from app.integrations.duffel_client import DuffelClient
from app.services.loyalty_service import LoyaltyService

class SearchService:
    def __init__(self, duffel: Optional[DuffelClient] = None, loyalty_service: Optional[LoyaltyService] = None):
        self.duffel = duffel or DuffelClient()
        self.loyalty_service = loyalty_service or LoyaltyService()

    def _merge_loyalty_accounts(self, stored: List[Dict[str, Any]], inline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        for account in stored:
            code = account.get("airline_iata_code")
            if code:
                merged[code] = account
        for raw in inline:
            if not isinstance(raw, dict):
                continue
            code = (raw.get("airline_iata_code") or raw.get("airline_code") or "").strip().upper()
            number = (raw.get("account_number") or "").strip()
            if not code or not number:
                continue
            entry: Dict[str, Any] = {"airline_iata_code": code, "account_number": number}
            tier = raw.get("loyalty_tier") or raw.get("tier")
            if tier:
                entry["loyalty_tier"] = tier
            programme_id = raw.get("loyalty_programme_id") or raw.get("programme_id")
            if programme_id:
                entry["loyalty_programme_id"] = programme_id
            merged[code] = entry
        return list(merged.values())

    def search(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        loyalty_user_id = payload.get("loyalty_user_id")
        inline_accounts = payload.get("loyalty_accounts") or []
        stored_accounts: List[Dict[str, Any]] = []
        if loyalty_user_id:
            stored_accounts = self.loyalty_service.get_accounts_for_injection(loyalty_user_id)
        merged_accounts = self._merge_loyalty_accounts(stored_accounts, inline_accounts)

        offers = self.duffel.search(
            slices=payload.get("slices", []),
            adults=payload.get("adults", 1),
            children=payload.get("children", 0),
            infants=payload.get("infants", 0),
            cabin=payload.get("cabin"),
            max_stops=payload.get("max_stops"),
            bags_included=payload.get("bags_included", True),
            loyalty_accounts=merged_accounts if merged_accounts else None,
            display_currency=payload.get("display_currency"),
        )

        if loyalty_user_id and offers:
            loyalty_details: List[Dict[str, Any]] = []
            for offer in offers:
                for benefit in offer.get("loyalty_benefits") or []:
                    if isinstance(benefit, dict):
                        loyalty_details.append(benefit)
            if loyalty_details:
                self.loyalty_service.update_perks_snapshot(loyalty_user_id, loyalty_details)

        return offers

    def price_offer(self, offer_id: str, display_currency: Optional[str] = None) -> Dict[str, Any]:
        return self.duffel.price_offer(offer_id, display_currency=display_currency)
