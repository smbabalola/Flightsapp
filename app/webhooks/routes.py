from fastapi import APIRouter, Header, HTTPException, Request
from app.core.settings import get_settings
from app.core.logging import logger
from app.utils.security import verify_hmac_sha512, verify_x_hub_signature_256
from app.utils.idempotency import check_and_set_once
from app.utils.idempotency_redis import RedisIdempotency
from app.utils.ratelimit import limiter_webhook
from app.db.session import SessionLocal
from app.repositories.repos import QuoteRepository, PaymentRepository
from app.workers.ticketing_worker import TicketingWorker
from sqlalchemy import text
import json

router = APIRouter()
settings = get_settings()
_idemp = None
if settings.use_redis_idempotency:
    try:
        _idemp = RedisIdempotency()
    except Exception:
        _idemp = None

@router.post("/paystack")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    if not x_paystack_signature or not settings.paystack_secret:
        raise HTTPException(status_code=401, detail="Missing signature or secret")
    key_rl = f"paystack:{request.client.host}"
    if not limiter_webhook.allow(key_rl):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    key_rl = f"whatsapp:{request.client.host}"
    if not limiter_webhook.allow(key_rl):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    body = await request.body()
    if not verify_hmac_sha512(settings.paystack_secret, body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    key = request.headers.get("X-Paystack-Event-Id") or x_paystack_signature
    if (_idemp and not _idemp.check_and_set_once(f"paystack:{key}")) or (not _idemp and not check_and_set_once(f"paystack:{key}")):
        return {"status": "duplicate_ignored"}

    payload = json.loads(body or b"{}")
    event = payload.get("event")
    data = payload.get("data", {})
    reference = data.get("reference")

    if event == "charge.success" and reference:
        with SessionLocal() as db:
            # Update payment to succeeded and quote to paid
            pr = PaymentRepository(db)
            qr = QuoteRepository(db)
            # naive update via raw SQL to keep simple for MVP
            db.execute(text("""
                UPDATE payments SET status='succeeded', raw=:raw WHERE reference=:ref
            """), {"raw": json.dumps(payload), "ref": reference})
            db.execute(text("""
                UPDATE quotes SET status='paid' WHERE paystack_reference=:ref
            """), {"ref": reference})
            db.commit()
        # Simulate ticket issuance
        worker = TicketingWorker()
        # In real case, map reference->quote_id via DB
        # For MVP, fetch quote_id via simple select
        with SessionLocal() as db:
            row = db.execute(text("SELECT id FROM quotes WHERE paystack_reference=:ref"), {"ref": reference}).fetchone()
            quote_id = row[0] if row else None
        if quote_id:
            result = worker.issue_after_payment(quote_id=quote_id, payment_reference=reference)
            logger.info("ticketed", extra={"request_id": request.headers.get("X-Request-ID")}); return {"status": "ticketed", **result}
        return {"status": "paid_no_quote_found"}

    return {"status": "ignored"}

@router.get("/whatsapp")
async def whatsapp_verify(mode: str = None, challenge: str = None, verify_token: str = None):
    if verify_token and settings.whatsapp_verify_token and verify_token == settings.whatsapp_verify_token:
        return challenge or ""
    raise HTTPException(status_code=401, detail="Invalid verify token")

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    if not x_hub_signature_256 or not settings.whatsapp_app_secret:
        raise HTTPException(status_code=401, detail="Missing signature or secret")
    key_rl = f"paystack:{request.client.host}"
    if not limiter_webhook.allow(key_rl):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    key_rl = f"whatsapp:{request.client.host}"
    if not limiter_webhook.allow(key_rl):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    body = await request.body()
    if not verify_x_hub_signature_256(settings.whatsapp_app_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
    key = request.headers.get("X-Hub-Delivery") or x_hub_signature_256
    if (_idemp and not _idemp.check_and_set_once(f"whatsapp:{key}")) or (not _idemp and not check_and_set_once(f"whatsapp:{key}")):
        return {"status": "duplicate_ignored"}

    # Parse webhook payload
    payload = json.loads(body or b"{}")

    # Process message with conversation handler
    from app.whatsapp.handler import get_conversation_handler
    handler = get_conversation_handler()

    try:
        await handler.handle_message(payload)
    except Exception as e:
        logger.error("whatsapp_handler_error", extra={"error": str(e)})

    return {"status": "ok"}



