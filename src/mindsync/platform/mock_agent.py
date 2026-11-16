from mindsync.contracts import AgentOutput, ChatRequest, ContextProvider, Mode, ToolEvent

async def run_agent(request: ChatRequest, context_provider: ContextProvider) -> AgentOutput:
    trace = []
    details = []
    used = False
    if request.mode != Mode.TEXT_ONLY:
        reading = context_provider.get_current_vitals(request.profile_id)
        used = reading is not None
        trace.append(ToolEvent(name="get_current_vitals", status="ok", summary="Fresh simulated reading available" if reading else "No fresh valid reading available"))
        details.append("Simulated measurements are available for demonstration only." if reading else "There is no fresh simulated reading to use.")
    if request.mode == Mode.FULL_CONTEXT:
        history = context_provider.get_history_summary(request.profile_id)
        used = used or history.sample_count > 0 or history.recent_sleep_avg_hours is not None or history.earlier_sleep_avg_hours is not None
        trace.append(ToolEvent(name="get_history_summary", status="ok", summary=f"{history.sample_count} samples; missing fraction {history.missing_fraction:.1%}; stale={history.data_stale}"))
        details.append(f"The synthetic seven-day history contains {history.sample_count} readings.")
    return AgentOutput(reply="[Mock agent] Thank you for sharing. What feels most difficult right now? You could choose one small manageable next step or talk with someone you trust. " + " ".join(details), tool_trace=trace, simulated_data_used=used)
