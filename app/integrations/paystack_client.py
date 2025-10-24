from typing import Optional, Dict, Any
import uuid
import httpx
from app.core.settings import get_settings

class PaystackClient:
    def __init__(self, secret_key: Optional[str] = None):
        self.settings = get_settings()
        self.secret_key = secret_key or (self.settings and self.settings.paystack_secret) or None
        self.base_url = (self.settings and self.settings.paystack_base_url) or "https://api.paystack.co"

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"}

    def initialize_payment(
            self,
            amount_minor: int,
            currency: str,
            email: str,
            reference: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            channels: Optional[list[str]] = None,
        ) -> Dict[str, Any]:
        use_real = bool(self.settings and self.settings.use_real_paystack and self.secret_key)
        if not use_real:
            ref = reference or f"REF_{uuid.uuid4().hex[:8].upper()}"
            # Use local mock payment page for development
            return {
                "status": True,
                "data": {
                    "authorization_url": f"/mock-payment.html?reference={ref}",
                    "access_code": ref,
                    "reference": ref,
                },
            }
        ref = reference or f"REF_{uuid.uuid4().hex[:12].upper()}"
        payload = {
            "amount": amount_minor,
            "currency": currency,
            "email": email,
            "reference": ref,
            "metadata": metadata or {},
        }
        if channels:
            payload["channels"] = channels
        url = f"{self.base_url}/transaction/initialize"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=self._headers())
            try:
                data = resp.json()
            except Exception:
                resp.raise_for_status()
                raise
            if resp.status_code >= 400 or not data.get("status"):
                raise RuntimeError(f"Paystack init failed: {data}")
            return data
