"""Twitter webhook routes for Account Activity API."""
import hashlib
import hmac
import base64
import structlog
from fastapi import APIRouter, Request, Response, HTTPException
from app.core.settings import get_settings
from app.twitter.handler import get_twitter_handler

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/twitter")
async def twitter_webhook_challenge(request: Request):
    """Handle Twitter CRC (Challenge Response Check).

    Twitter sends a GET request with crc_token parameter.
    We must respond with a JSON containing response_token.
    """
    settings = get_settings()
    crc_token = request.query_params.get("crc_token")

    if not crc_token:
        raise HTTPException(status_code=400, detail="Missing crc_token")

    # Create HMAC SHA-256 hash
    consumer_secret = settings.twitter_api_secret
    if not consumer_secret:
        raise HTTPException(status_code=500, detail="Twitter API secret not configured")

    # Calculate response token
    sha256_hash = hmac.new(
        consumer_secret.encode(),
        msg=crc_token.encode(),
        digestmod=hashlib.sha256
    ).digest()

    response_token = "sha256=" + base64.b64encode(sha256_hash).decode()

    logger.info("twitter_crc_validated", crc_token=crc_token[:20])

    return {"response_token": response_token}


@router.post("/twitter")
async def twitter_webhook(request: Request):
    """Handle Twitter webhook events (DMs, etc).

    Twitter sends various events including direct messages.
    """
    try:
        data = await request.json()
        logger.info("twitter_webhook_received", event_keys=list(data.keys()))

        # Verify webhook signature
        signature = request.headers.get("x-twitter-webhooks-signature")
        if signature:
            # Verify signature (optional but recommended)
            settings = get_settings()
            body = await request.body()
            expected_sig = "sha256=" + hmac.new(
                settings.twitter_api_secret.encode(),
                msg=body,
                digestmod=hashlib.sha256
            ).hexdigest()

            if signature != expected_sig:
                logger.warning("twitter_signature_mismatch")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Handle direct message events
        if "direct_message_events" in data:
            for dm_event in data["direct_message_events"]:
                if dm_event.get("type") == "message_create":
                    message_data = dm_event.get("message_create", {})
                    sender_id = message_data.get("sender_id")
                    message_text = message_data.get("message_data", {}).get("text", "")

                    # Get bot's user ID to ignore self-messages
                    settings = get_settings()
                    # Skip if message is from bot itself
                    # You'll need to store bot's user ID or check dynamically

                    if sender_id and message_text:
                        handler = get_twitter_handler()
                        await handler.handle_dm(sender_id, message_text)

        return {"status": "ok"}

    except Exception as e:
        logger.error("twitter_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")
