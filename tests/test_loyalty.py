"""Tests for loyalty-aware search integration."""
from typing import Any, Dict, List


from app.services.search_service import SearchService


class DummyDuffel:
    def __init__(self):
        self.last_kwargs: Dict[str, Any] = {}

    def search(self, **kwargs):
        self.last_kwargs = kwargs
        return [
            {
                "loyalty_benefits": [
                    {"airline_iata_code": "BA", "perks": {"bags": 1}}
                ]
            }
        ]


class DummyLoyaltyService:
    def __init__(self):
        self.requested_ids: List[int] = []
        self.updated: Any = None

    def get_accounts_for_injection(self, user_id: int):
        self.requested_ids.append(user_id)
        return [{"airline_iata_code": "BA", "account_number": "123456", "loyalty_tier": "Silver"}]

    def update_perks_snapshot(self, user_id: int, details):
        self.updated = (user_id, details)


class TestSearchServiceLoyalty:
    def test_inline_loyalty_overrides_stored(self):
        duffel = DummyDuffel()
        loyalty = DummyLoyaltyService()
        service = SearchService(duffel=duffel, loyalty_service=loyalty)

        payload = {
            "slices": [{"from_": "LOS", "to": "ABV", "date": "2025-11-15"}],
            "adults": 1,
            "loyalty_user_id": 42,
            "loyalty_accounts": [
                {
                    "airline_iata_code": "ba",
                    "account_number": "999999",
                    "loyalty_tier": "Gold"
                }
            ],
        }

        offers = service.search(payload)

        assert loyalty.requested_ids == [42]
        assert duffel.last_kwargs["loyalty_accounts"][0]["account_number"] == "999999"
        assert duffel.last_kwargs["loyalty_accounts"][0]["loyalty_tier"] == "Gold"
        assert loyalty.updated == (42, [{"airline_iata_code": "BA", "perks": {"bags": 1}}])
        assert offers and offers[0]["loyalty_benefits"][0]["perks"]["bags"] == 1
