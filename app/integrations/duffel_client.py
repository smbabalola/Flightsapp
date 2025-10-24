from app.core.settings import get_settings
from app.utils.app_config import get_bool
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import logging
from app.utils.fx import ngn_equivalent
from app.utils.pricing import calculate_final_price, calculate_display_price_from_usd_base
from app.utils.retry import retry
from app.utils.cache import Cache
import hashlib
import json
from app.core.metrics import record_cache_hit, record_cache_set

class DuffelClient:
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.duffel_api_key
        self.base_url = "https://api.duffel.com/air/"
        self._logger = logging.getLogger(__name__)
        # Conservative connection settings to reduce protocol errors
        self._timeout = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)
        self._limits = httpx.Limits(max_connections=10, max_keepalive_connections=5, keepalive_expiry=30.0)
        self._cache = Cache(self.settings.redis_url)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Duffel-Version": "v2",
            "Content-Type": "application/json",
        }

    def _sanitized_headers(self) -> Dict[str, str]:
        headers = self._headers().copy()
        token = headers.get("Authorization", "")
        if token.startswith("Bearer "):
            tail = token[-6:] if len(token) > 6 else ""
            headers["Authorization"] = f"Bearer ****{tail}"
        return headers

    def _ensure_real(self) -> bool:
        return bool(self.settings.use_real_duffel and self.api_key)

    def _prepare_loyalty_accounts(self, accounts: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Sanitize loyalty accounts for Duffel payloads."""
        prepared: List[Dict[str, Any]] = []
        if not accounts:
            return prepared
        seen = set()
        for raw in accounts:
            if not isinstance(raw, dict):
                continue
            code = (raw.get("airline_iata_code") or raw.get("airline_code") or raw.get("program_code") or "").strip().upper()
            number = (raw.get("account_number") or "").strip()
            if not code or not number:
                continue
            if (code, number) in seen:
                continue
            seen.add((code, number))
            entry: Dict[str, Any] = {
                "airline_iata_code": code,
                "account_number": number,
            }
            tier = raw.get("loyalty_tier") or raw.get("tier")
            if tier:
                entry["loyalty_tier"] = tier
            programme_id = raw.get("loyalty_programme_id") or raw.get("programme_id")
            if programme_id:
                entry["loyalty_programme_id"] = programme_id
            prepared.append(entry)
        return prepared

    def _format_offer(self, offer: Dict[str, Any], display_currency_override: Optional[str] = None) -> Dict[str, Any]:
        total = offer.get("total_amount")
        currency = offer.get("total_currency") or "USD"
        try:
            total_f = float(total) if total is not None else None
        except Exception:
            total_f = None

        # Calculate final customer price with USD base and multi-currency display
        display_currency = (display_currency_override or self.settings.default_display_currency or "NGN").upper()
        final_display_amount = None
        price_breakdown = None
        if total_f and total_f > 0:
            try:
                final_display_amount, price_breakdown = calculate_display_price_from_usd_base(
                    supplier_amount=total_f,
                    supplier_currency=currency,
                    display_currency=display_currency,
                )
            except Exception:
                # Fallback: old NGN path
                final_display_amount = ngn_equivalent(total_f, currency)

        formatted_slices: List[Dict[str, Any]] = []
        for s in offer.get("slices", []) or []:
            segments = []
            for seg in s.get("segments", []) or []:
                segments.append({
                    "departing_at": seg.get("departing_at"),
                    "arriving_at": seg.get("arriving_at"),
                    "origin": seg.get("origin"),
                    "destination": seg.get("destination"),
                    "marketing_carrier": seg.get("marketing_carrier"),
                    "operating_carrier": seg.get("operating_carrier"),
                    "duration": seg.get("duration"),
                })
            formatted_slices.append({"segments": segments})

        loyalty_benefits: List[Dict[str, Any]] = []
        for passenger in offer.get("passengers", []) or []:
            accounts = passenger.get("loyalty_programme_accounts") or []
            earnings = passenger.get("loyalty_programme_earnings") or passenger.get("earnings")
            perks = passenger.get("loyalty_perks") or passenger.get("perks")
            for acct in accounts:
                benefit: Dict[str, Any] = {}
                code = acct.get("airline_iata_code") or acct.get("airline_code")
                if code:
                    benefit["airline_iata_code"] = code
                programme_id = acct.get("loyalty_programme_id") or acct.get("programme_id")
                if programme_id:
                    benefit["loyalty_programme_id"] = programme_id
                tier = acct.get("loyalty_tier") or acct.get("status_tier")
                if tier:
                    benefit["loyalty_tier"] = tier
                last4 = acct.get("account_number_last4")
                acct_number = acct.get("account_number")
                if not last4 and acct_number:
                    last4 = acct_number[-4:]
                if last4:
                    benefit["account_last4"] = last4
                if earnings:
                    benefit["earnings"] = earnings
                if perks:
                    benefit["perks"] = perks
                if benefit:
                    loyalty_benefits.append(benefit)

        return {
            "id": offer.get("id"),
            "total_amount": str(final_display_amount) if final_display_amount else total,
            "total_currency": display_currency,
            "base_amount": total,  # Original supplier price
            "base_currency": currency,  # Original currency
            "ngn_equiv": ngn_equivalent(total_f, currency),
            "price_breakdown": price_breakdown,  # Detailed breakdown for transparency
            "slices": formatted_slices,
            "loyalty_benefits": loyalty_benefits,
        }

    def _airport_country(self, iata_code: Optional[str]) -> Optional[str]:
        """Best-effort mapping from IATA airport code to ISO country code.

        This is a lightweight fallback for when Duffel does not include country codes
        on origin/destination objects. Extend as needed.
        """
        if not iata_code:
            return None
        code = iata_code.upper()
        mapping = {
            # Nigeria
            "LOS": "NG", "ABV": "NG", "PHC": "NG", "KAN": "NG",
            # Ghana
            "ACC": "GH",
            # South Africa
            "JNB": "ZA", "CPT": "ZA",
            # Kenya
            "NBO": "KE",
            # UK
            "LHR": "GB", "LGW": "GB", "LCY": "GB", "MAN": "GB",
            # France
            "CDG": "FR", "ORY": "FR",
            # Netherlands
            "AMS": "NL",
            # USA
            "JFK": "US", "LGA": "US", "EWR": "US", "LAX": "US", "MIA": "US", "ATL": "US", "IAD": "US",
            # UAE
            "DXB": "AE",
            # Qatar
            "DOH": "QA",
            # Turkey
            "IST": "TR",
            # Ethiopia
            "ADD": "ET",
            # Morocco
            "CMN": "MA",
            # Egypt
            "CAI": "EG",
        }
        return mapping.get(code)

    def search(self, slices: List[Dict[str, str]], adults: int, children: int = 0, infants: int = 0,
               cabin: Optional[str] = None, max_stops: Optional[int] = None, bags_included: Optional[bool] = True,
               loyalty_accounts: Optional[List[Dict[str, Any]]] = None,
               display_currency: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._ensure_real():
            slice_info = slices[0] if slices else {"from_": "LOS", "to": "LHR", "date": datetime.utcnow().date().isoformat()}
            mock_depart = f"{slice_info.get('date','2025-10-01')}T09:00:00Z"
            mock_arrive = f"{slice_info.get('date','2025-10-01')}T13:30:00Z"
            # Derive country codes for mock using mapping
            try:
                o_cc = self._airport_country(slice_info.get("from_")) or "NG"
            except Exception:
                o_cc = "NG"
            try:
                d_cc = self._airport_country(slice_info.get("to")) or "GB"
            except Exception:
                d_cc = "GB"

            mock_offer = {
                "id": "mock_offer_1",
                "total_amount": "150.00",
                "total_currency": "USD",
                "slices": [
                    {
                        "segments": [
                            {
                                "departing_at": mock_depart,
                                "arriving_at": mock_arrive,
                                "origin": {"iata_code": slice_info.get("from_", "LOS"), "city_name": slice_info.get("from_"), "name": slice_info.get("from_"), "country_code": o_cc},
                                "destination": {"iata_code": slice_info.get("to", "LHR"), "city_name": slice_info.get("to"), "name": slice_info.get("to"), "country_code": d_cc},
                                "marketing_carrier": {"name": "SureFlights", "iata_code": "SF"},
                                "operating_carrier": {"name": "SureFlights", "iata_code": "SF"},
                                "duration": "PT4H30M",
                            }
                        ]
                    }
                ],
                "loyalty_benefits": [],
            }
            offers = [self._format_offer(mock_offer)]
            # Optional domestic filter
            if get_bool('IGNORE_DOMESTIC_ROUTES', default=bool(self.settings.ignore_domestic_routes)):
                def _is_domestic(o: Dict[str, Any]) -> bool:
                    try:
                        seg = (o.get("slices") or [{}])[0].get("segments")[0]
                        o_country = seg.get("origin", {}).get("country_code") or seg.get("origin", {}).get("iata_country_code")
                        d_country = seg.get("destination", {}).get("country_code") or seg.get("destination", {}).get("iata_country_code")
                        if not o_country:
                            o_country = self._airport_country((seg.get("origin") or {}).get("iata_code"))
                        if not d_country:
                            d_country = self._airport_country((seg.get("destination") or {}).get("iata_code"))
                        return o_country and d_country and o_country == d_country
                    except Exception:
                        return False
                offers = [o for o in offers if not _is_domestic(o)]
            return offers

        prepared_loyalty = self._prepare_loyalty_accounts(loyalty_accounts)
        passengers: List[Dict[str, Any]] = []

        def _add_passengers(count: int, passenger_type: str) -> None:
            for _ in range(max(count, 0)):
                passenger: Dict[str, Any] = {"type": passenger_type}
                if prepared_loyalty:
                    passenger["loyalty_programme_accounts"] = prepared_loyalty
                passengers.append(passenger)

        _add_passengers(adults, "adult")
        _add_passengers(children, "child")
        _add_passengers(infants, "infant_without_seat")

        if not passengers:
            passenger: Dict[str, Any] = {"type": "adult"}
            if prepared_loyalty:
                passenger["loyalty_programme_accounts"] = prepared_loyalty
            passengers.append(passenger)

        payload = {
            "slices": [{"origin": s.get("from_"), "destination": s.get("to"), "departure_date": s.get("date")} for s in slices],
            "passengers": passengers,
            "cabin_class": cabin or "economy"
        }

        # Cache key: normalized payload + display currency; hash to keep key small
        try:
            loyalty_digest = None
            if prepared_loyalty:
                normalized_loyalty = sorted([
                    {k: v for k, v in acct.items() if k in ("airline_iata_code", "account_number", "loyalty_programme_id", "loyalty_tier")}
                    for acct in prepared_loyalty
                ], key=lambda a: (a.get("airline_iata_code"), a.get("account_number", "")))
                loyalty_digest = hashlib.sha256(json.dumps(normalized_loyalty, sort_keys=True).encode()).hexdigest()[:12]
            key_payload = {
                "slices": payload["slices"],
                "adults": adults,
                "children": children,
                "infants": infants,
                "cabin": cabin or "economy",
                "max_stops": max_stops,
                "bags_included": bool(bags_included),
                "loyalty": loyalty_digest,
                "currency": (display_currency or self.settings.default_display_currency or "NGN").upper(),
            }
            cache_key = "duffel:offers:" + hashlib.sha256(json.dumps(key_payload, sort_keys=True).encode()).hexdigest()
        except Exception:
            cache_key = None

        if cache_key:
            cached = self._cache.get(cache_key)
            if isinstance(cached, list) and cached:
                self._logger.debug("duffel.cache_hit", extra={"key": cache_key})
                record_cache_hit("duffel_offers")
                return cached

        url = f"{self.base_url}offer_requests"
        with httpx.Client(timeout=self._timeout, limits=self._limits, http2=True) as client:
            def _call():
                try:
                    self._logger.debug("duffel.request", extra={
                        "url": url,
                        "headers": self._sanitized_headers(),
                        "payload": payload,
                    })
                    resp = client.post(url, json={"data": payload}, headers=self._headers())
                except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                    # Surface to retry wrapper
                    self._logger.warning(f"Duffel call failed (transient): {e}")
                    raise
                # Retry on 5xx and 429
                if resp.status_code >= 500 or resp.status_code == 429:
                    self._logger.warning(
                        f"Duffel transient HTTP {resp.status_code}; will retry",
                    )
                    raise httpx.HTTPError(f"Transient Duffel status: {resp.status_code}")
                return resp

            resp = retry(_call, attempts=4)
            try:
                raw = resp.text
            except Exception:
                raw = "<no-body>"
            body_preview = (raw[:500] + ("…" if len(raw) > 500 else "")) if isinstance(raw, str) else str(raw)
            self._logger.debug("duffel.response", extra={
                "url": url,
                "status": resp.status_code,
                "body": body_preview,
            })
            data = resp.json()
            if resp.status_code >= 400:
                self._logger.error(f"Duffel API error {resp.status_code}: {data}")
                self._logger.error(f"Sent payload: {payload}")
                raise RuntimeError(f"Duffel search failed with {resp.status_code}: {data}")

            offers = data.get("data", {}).get("offers") or []
            formatted = [self._format_offer(o, display_currency_override=display_currency) for o in offers]
            if self.settings.ignore_domestic_routes:
                def _is_domestic(o: Dict[str, Any]) -> bool:
                    try:
                        seg = (o.get("slices") or [{}])[0].get("segments")[0]
                        o_country = seg.get("origin", {}).get("country_code") or seg.get("origin", {}).get("iata_country_code")
                        d_country = seg.get("destination", {}).get("country_code") or seg.get("destination", {}).get("iata_country_code")
                        if not o_country:
                            o_country = self._airport_country((seg.get("origin") or {}).get("iata_code"))
                        if not d_country:
                            d_country = self._airport_country((seg.get("destination") or {}).get("iata_code"))
                        return o_country and d_country and o_country == d_country
                    except Exception:
                        return False
                formatted = [o for o in formatted if not _is_domestic(o)]
            if cache_key:
                try:
                    self._cache.set(cache_key, formatted, ttl_seconds=self.settings.duffel_search_cache_ttl_seconds)
                    self._logger.debug("duffel.cache_set", extra={"key": cache_key, "ttl": self.settings.duffel_search_cache_ttl_seconds, "count": len(formatted)})
                    record_cache_set("duffel_offers")
                except Exception:
                    pass
            return formatted

    def _get_metadata(self, resource: str) -> list[dict]:
        key = f"duffel:meta:{resource}"
        cached = self._cache.get(key)
        if isinstance(cached, list) and cached:
            self._logger.debug("duffel.cache_hit", extra={"key": key})
            record_cache_hit("duffel_meta")
            return cached
        url = f"{self.base_url}{resource}"
        with httpx.Client(timeout=self._timeout, limits=self._limits, http2=True) as client:
            def _call():
                try:
                    self._logger.debug("duffel.request", extra={"url": url, "headers": self._sanitized_headers()})
                    resp = client.get(url, headers=self._headers())
                except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                    self._logger.warning(f"Duffel {resource} failed (transient): {e}")
                    raise
                if resp.status_code >= 500 or resp.status_code == 429:
                    raise httpx.HTTPError(f"Transient Duffel status: {resp.status_code}")
                return resp
            resp = retry(_call, attempts=4)
            body_preview = (resp.text[:500] + ("…" if len(resp.text) > 500 else "")) if isinstance(resp.text, str) else str(resp.text)
            self._logger.debug("duffel.response", extra={"url": url, "status": resp.status_code, "body": body_preview})
            data = resp.json()
            items = data.get("data", []) if isinstance(data, dict) else []
            try:
                self._cache.set(key, items, ttl_seconds=self.settings.duffel_metadata_cache_ttl_seconds)
                record_cache_set("duffel_meta")
            except Exception:
                pass
            return items

    def get_airlines(self) -> list[dict]:
        return self._get_metadata("air/airlines".replace("air/air/","air/"))

    def get_airports(self) -> list[dict]:
        return self._get_metadata("air/airports".replace("air/air/","air/"))

    def get_aircraft(self) -> list[dict]:
        return self._get_metadata("air/aircraft".replace("air/air/","air/"))

    def price_offer(self, offer_id: str, display_currency: Optional[str] = None) -> Dict[str, Any]:
        if not self._ensure_real():
            mock_offer = {
                "id": offer_id,
                "total_amount": "150.00",
                "total_currency": "USD",
                "slices": [],
            }
            return self._format_offer(mock_offer, display_currency_override=display_currency)

        url = f"{self.base_url}offers/{offer_id}"
        with httpx.Client(timeout=self._timeout, limits=self._limits, http2=True) as client:
            def _call():
                try:
                    self._logger.debug("duffel.request", extra={
                        "url": url,
                        "headers": self._sanitized_headers(),
                    })
                    resp = client.get(url, headers=self._headers())
                except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                    self._logger.warning(f"Duffel call failed (transient): {e}")
                    raise
                if resp.status_code >= 500 or resp.status_code == 429:
                    self._logger.warning(
                        f"Duffel transient HTTP {resp.status_code}; will retry",
                    )
                    raise httpx.HTTPError(f"Transient Duffel status: {resp.status_code}")
                return resp

            resp = retry(_call, attempts=4)
            try:
                raw = resp.text
            except Exception:
                raw = "<no-body>"
            body_preview = (raw[:500] + ("…" if len(raw) > 500 else "")) if isinstance(raw, str) else str(raw)
            self._logger.debug("duffel.response", extra={
                "url": url,
                "status": resp.status_code,
                "body": body_preview,
            })
            data = resp.json()
            if resp.status_code >= 400:
                raise RuntimeError(f"Duffel price fetch failed: {data}")
            offer = data.get("data", {})
            return self._format_offer(offer, display_currency_override=display_currency)
