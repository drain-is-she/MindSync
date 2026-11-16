import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone
from time import perf_counter
from fastapi import APIRouter, HTTPException, Request
from pydantic import Field
from mindsync.contracts import Contract, ChatRequest, ChatResponse, AgentOutput, Mode, VitalReading
from .context_service import RestrictedContextProvider
from .safety import is_urgent, URGENT_REPLY

router = APIRouter()
logger = logging.getLogger(__name__)

def require_profile(request, profile_id):
    if not request.app.state.repository.exists(profile_id):
        raise HTTPException(404, "Unknown synthetic profile")

@router.get("/health")
def health(request: Request):
    return {"status": "ok", "agent": request.app.state.settings.agent, "simulated": True}

@router.get("/profiles")
def profiles(request: Request):
    return request.app.state.repository.profiles()

@router.get("/profiles/{profile_id}/vitals")
def vitals(profile_id: str, request: Request):
    require_profile(request, profile_id)
    now = datetime.now(timezone.utc)
    return {"current": request.app.state.context.get_current_vitals(profile_id),
            "history": request.app.state.repository.samples(profile_id, now-timedelta(days=7), now),
            "summary": request.app.state.context.get_history_summary(profile_id),
            "sleep": request.app.state.repository.sleep(profile_id, (now-timedelta(days=7)).date(), now.date())}

@router.post("/telemetry", response_model=VitalReading)
def telemetry(reading: VitalReading, request: Request):
    require_profile(request, reading.profile_id)
    if not reading.simulated:
        raise HTTPException(422, "Only simulated measurements are accepted")
    if reading.measured_at > datetime.now(timezone.utc):
        raise HTTPException(422, "Future measurements are not accepted")
    return request.app.state.repository.save_vital(reading)

class CheckIn(Contract):
    mood: int = Field(ge=1, le=5, strict=True)
    note: str = Field(default="", max_length=2000)

@router.post("/profiles/{profile_id}/check-ins", status_code=201)
def check_in(profile_id: str, body: CheckIn, request: Request):
    require_profile(request, profile_id)
    request.app.state.repository.check_in(profile_id, body.mood, body.note)
    return {"saved": True}

@router.get("/profiles/{profile_id}/check-ins")
def check_ins(profile_id: str, request: Request):
    require_profile(request, profile_id)
    return request.app.state.repository.check_ins(profile_id)

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    started = perf_counter()
    require_profile(request, body.profile_id)
    if body.mode != Mode.TEXT_ONLY and not body.consent_to_use_vitals:
        raise HTTPException(403, "Consent is required for vitals-enabled modes")
    urgent = is_urgent(body.message)
    if urgent:
        result = AgentOutput(reply=URGENT_REPLY)
    else:
        context = RestrictedContextProvider(request.app.state.context, body)
        # Keep memory keys isolated even when direct API clients reuse session IDs.
        scope = json.dumps([body.session_id, body.profile_id, body.mode.value,
                            body.consent_to_use_vitals], separators=(",", ":"))
        agent_request = body.model_copy(update={
            "session_id": hashlib.sha256(scope.encode("utf-8")).hexdigest()})
        try:
            result = AgentOutput.model_validate(await asyncio.wait_for(request.app.state.agent(agent_request, context), timeout=request.app.state.settings.agent_timeout_seconds))
        except TimeoutError:
            raise HTTPException(504, "Agent timed out; please try again") from None
        except Exception:
            logger.error("Agent failed; request content omitted")
            raise HTTPException(502, "Agent unavailable; please try again") from None
    return ChatResponse(**result.model_dump(), mode=body.mode,
        safety_route="urgent_support" if urgent else "ordinary_support",
        latency_ms=max(0, int((perf_counter()-started)*1000)))
