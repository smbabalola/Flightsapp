import hmac
import hashlib
from typing import Optional


def verify_hmac_sha512(secret: str, payload: bytes, signature: str) -> bool:
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha512)
    expected = mac.hexdigest()
    sig = signature.strip()
    return hmac.compare_digest(expected, sig)


def verify_x_hub_signature_256(secret: str, payload: bytes, signature: str) -> bool:
    # signature format: sha256=<hex>
    try:
        method, provided = signature.split("=", 1)
    except Exception:
        return False
    if method.lower() != "sha256":
        return False
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, provided)
