"""LangGraph orchestration with deterministic, retrieval-grounded synthesis.

Only a topic label is remembered, never chat text or vital measurements. Memory
is process-local, expires after 30 minutes, and is bounded to 256 scopes.
"""
from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import TypedDict
import re
from langgraph.graph import StateGraph, START, END
from mindsync.contracts import AgentOutput, ChatRequest, ContextProvider, Mode, ToolEvent
from mindsync.platform.safety import is_urgent, URGENT_REPLY
from .knowledge import Guide, retrieve

_topics: OrderedDict[tuple, tuple[float, str]] = OrderedDict()
_lock = Lock()

def topic_memory(request, topic=None):
    key = (request.session_id, request.profile_id, request.mode.value, request.consent_to_use_vitals)
    now = monotonic()
    with _lock:
        for old in [k for k, (t, _) in _topics.items() if now - t > 1800]:
            del _topics[old]
        if topic:
            _topics[key] = (now, topic)
            _topics.move_to_end(key)
            while len(_topics) > 256:
                _topics.popitem(last=False)
        entry = _topics.get(key)
        return entry[1] if entry else None

class State(TypedDict, total=False):
    guides: list[Guide]
    trace: list[ToolEvent]
    details: list[str]
    used: bool
    result: AgentOutput

async def run_agent(request: ChatRequest, context_provider: ContextProvider) -> AgentOutput:
    # Also protect callers that invoke this entry point outside FastAPI.
    if is_urgent(request.message):
        return AgentOutput(reply=URGENT_REPLY)
    if request.mode != Mode.TEXT_ONLY and not request.consent_to_use_vitals:
        raise PermissionError("Consent is required for vitals-enabled modes")
    if re.search(r"\b(diagnos\w*|medication|prescri\w*|dosage|disorder)\b", request.message, re.I):
        return AgentOutput(reply="I cannot diagnose conditions or advise on medication. A qualified healthcare professional can help with that. I can offer general support with sleep, worries, or a gentle breathing exercise.")

    def collect(state):
        trace, details, used = [], [], False
        if request.mode != Mode.TEXT_ONLY:
            try:
                current = context_provider.get_current_vitals(request.profile_id)
                used = current is not None
                trace.append(ToolEvent(name="get_current_vitals", status="ok", summary="Fresh simulated reading available" if current else "No fresh reading"))
                if current:
                    values = [("pulse", current.heart_rate_bpm, "bpm"), ("SpO2", current.spo2_percent, "%"),
                              ("breathing rate", current.respiratory_rate_per_min, "per minute")]
                    available = [f"{label}: {value:g} {unit}" for label, value, unit in values if value is not None]
                    details.append("Current SIMULATED DATA: " + (", ".join(available) if available else "vital values are missing") + ".")
                else:
                    details.append("No fresh simulated reading is available; missing values are not estimated.")
            except Exception:
                trace.append(ToolEvent(name="get_current_vitals", status="error", summary="Current readings unavailable"))
                details.append("Current readings are unavailable. You can still use the exercise below.")
        if request.mode == Mode.FULL_CONTEXT:
            try:
                history = context_provider.get_history_summary(request.profile_id)
                used |= history.sample_count > 0 or history.recent_sleep_avg_hours is not None or history.earlier_sleep_avg_hours is not None
                trace.append(ToolEvent(name="get_history_summary", status="ok", summary=f"{history.sample_count} samples; stale={history.data_stale}"))
                details.append(f"SIMULATED seven-day history: {history.sample_count} readings; missing fraction {history.missing_fraction:.0%}.")
                for label, value in [("Earlier sleep average", history.earlier_sleep_avg_hours), ("Recent sleep average", history.recent_sleep_avg_hours)]:
                    if value is not None:
                        details.append(f"{label}: {value:.1f} hours.")
                if history.data_stale:
                    details.append("The history is stale and does not describe your current state.")
            except Exception:
                trace.append(ToolEvent(name="get_history_summary", status="error", summary="History unavailable"))
                details.append("The history could not be loaded.")
        if used:
            details.append("These synthetic values cannot establish how you feel or diagnose a condition. The exercise is selected from your words.")
        return {"trace": trace, "details": details, "used": used}

    def search(state):
        guides = retrieve(request.message, topic_memory(request))
        return {"guides": guides, "trace": state["trace"] + [ToolEvent(name="retrieve_guidance", status="ok", summary=f"{len(guides)} curated NHS guidance chunk(s) matched")]}

    def compose(state):
        guides = state["guides"]
        if guides:
            guide = guides[0]
            reply = "Thank you for sharing. Here is an option you can try if it feels useful.\n\n"
            reply += guide.advice + f" [{guide.source.source_id}]\n\n"
            reply += "\n".join(f"{i}. {step}" for i, step in enumerate(guide.steps, 1))
            reply += "\n\nYou can stop or skip this exercise if it feels uncomfortable. What feels manageable for you?"
            topic_memory(request, guide.topic)
        else:
            reply = "I do not have matching guidance in my small local knowledge base. Would you like support with sleep, managing worries, or a gentle breathing exercise? For persistent or worsening difficulties, consider speaking with a qualified professional."
        reply += "\n\n" + " ".join(state["details"]) if state["details"] else ""
        trace = state["trace"] + [ToolEvent(name="compose_grounded_response", status="ok", summary="Deterministic local guidance; no external language model")]
        return {"result": AgentOutput(reply=reply, sources=[g.source for g in guides], tool_trace=trace, simulated_data_used=state["used"])}

    graph = StateGraph(State)
    graph.add_node("context", collect)
    graph.add_node("retrieval", search)
    graph.add_node("response", compose)
    graph.add_edge(START, "context")
    graph.add_edge("context", "retrieval")
    graph.add_edge("retrieval", "response")
    graph.add_edge("response", END)
    return (await graph.compile().ainvoke({}))["result"]
