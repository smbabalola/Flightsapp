"""Twilio voice webhook routes."""
import structlog
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from typing import Optional
from app.voice.handler import get_voice_handler

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/voice/incoming")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: Optional[str] = Form(None)
):
    """Handle incoming Twilio voice call.

    Args:
        CallSid: Twilio call SID
        From: Caller's phone number
        To: Twilio phone number called
    """
    logger.info("incoming_call", call_sid=CallSid, from_=From)

    handler = get_voice_handler()
    twiml = await handler.handle_incoming_call(CallSid, From)

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/collect-origin")
async def collect_origin(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Collect origin city from caller."""
    logger.info("collect_origin", call_sid=CallSid, speech=SpeechResult)

    handler = get_voice_handler()
    twiml = await handler.handle_origin(CallSid, SpeechResult or "")

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/collect-destination")
async def collect_destination(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Collect destination city from caller."""
    logger.info("collect_destination", call_sid=CallSid, speech=SpeechResult)

    handler = get_voice_handler()
    twiml = await handler.handle_destination(CallSid, SpeechResult or "")

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/collect-date")
async def collect_date(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Collect travel date from caller."""
    logger.info("collect_date", call_sid=CallSid, speech=SpeechResult)

    handler = get_voice_handler()
    twiml = await handler.handle_date(CallSid, SpeechResult or "")

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/select-flight")
async def select_flight(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Handle flight selection from caller."""
    logger.info("select_flight", call_sid=CallSid, speech=SpeechResult)

    handler = get_voice_handler()
    twiml = await handler.handle_flight_selection(CallSid, SpeechResult or "")

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/collect-passenger")
async def collect_passenger(
    CallSid: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Collect passenger name from caller."""
    logger.info("collect_passenger", call_sid=CallSid, speech=SpeechResult)

    handler = get_voice_handler()
    twiml = await handler.handle_passenger_name(CallSid, SpeechResult or "")

    return Response(content=twiml, media_type="application/xml")


@router.post("/voice/status")
async def call_status(request: Request):
    """Handle call status updates from Twilio."""
    data = await request.form()
    logger.info("call_status", status=data.get("CallStatus"), call_sid=data.get("CallSid"))
    return {"status": "ok"}
