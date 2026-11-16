import os
import uuid
from urllib.parse import urlparse
import httpx
import pandas as pd
import streamlit as st

MODES = {"A · Text only": "text_only", "B · Current vitals": "current_vitals", "C · Full context": "full_context"}

def api(method, path, **kwargs):
    url = os.getenv("MINDSYNC_API_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        response = httpx.request(method, url+path, timeout=40, **kwargs)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        detail = exc.response.text if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        st.error(f"API request failed: {detail}")
        return None

def show_response(response):
    st.write(response["reply"])
    st.caption(f"{response['safety_route']} · {response['latency_ms']} ms · simulated data used: {response['simulated_data_used']}")
    for source in response["sources"]:
        st.write(f"{source['publisher']} — {source['title']}")
        if urlparse(source["url"]).scheme in ("http", "https"):
            st.link_button("Open source", source["url"])
    with st.expander("Agent tool execution trace"):
        st.json(response["tool_trace"])

def main():
    st.set_page_config(page_title="MindSync AI", layout="wide")
    st.title("MindSync AI")
    st.warning("SIMULATED DATA · Non-diagnostic wellbeing prototype")
    profiles = api("GET", "/profiles")
    if not profiles:
        st.info("Start the FastAPI server, then refresh this page.")
        return
    names = {p["id"]: p["name"] for p in profiles}
    profile = st.sidebar.selectbox("Synthetic profile", list(names), format_func=names.get)
    st.sidebar.caption(next(p["scenario"] for p in profiles if p["id"] == profile))
    mode_label = st.sidebar.selectbox("Experiment mode", list(MODES))
    consent = st.sidebar.checkbox("Allow simulated vitals in chat", key=f"consent_{profile}")
    st.sidebar.caption("Dashboard readings are separate from agent context permissions.")
    st.sidebar.button("Refresh readings")
    data = api("GET", f"/profiles/{profile}/vitals")
    if data:
        st.subheader("Current simulated readings")
        if data["current"]:
            current = data["current"]
            for col, field, label in zip(st.columns(4), ["heart_rate_bpm", "spo2_percent", "respiratory_rate_per_min", "activity_level"], ["Pulse (bpm)", "SpO₂ (%)", "Breaths/min", "Activity (0–1)"]):
                col.metric(label, current[field] if current[field] is not None else "Missing")
            st.caption(f"Measured at {current['measured_at']}")
        else:
            st.info("No fresh valid reading. Older data may appear in history.")
        st.subheader("Seven-day history")
        if data["history"]:
            frame = pd.DataFrame(data["history"])
            frame["measured_at"] = pd.to_datetime(frame["measured_at"])
            st.line_chart(frame.set_index("measured_at")[["heart_rate_bpm"]])
        if data["sleep"]:
            st.bar_chart(pd.DataFrame(data["sleep"]).set_index("sleep_date")[["hours"]])
        st.json(data["summary"], expanded=False)
    with st.form("check_in"):
        st.subheader("Mood check-in")
        mood = st.slider("Mood (1 = low, 5 = high)", 1, 5, 3)
        note = st.text_input("Optional note", max_chars=2000)
        if st.form_submit_button("Save check-in"):
            if api("POST", f"/profiles/{profile}/check-ins", json={"mood": mood, "note": note}):
                st.success("Check-in saved")
    st.subheader("Support chat")
    history_key = f"chat_{profile}_{MODES[mode_label]}_{consent}"
    messages = st.session_state.setdefault(history_key, [])
    session = st.session_state.setdefault(history_key+"_session", str(uuid.uuid4()))
    for message in messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["text"])
            else:
                show_response(message["response"])
    prompt = st.chat_input("What would you like support with?")
    if prompt:
        if MODES[mode_label] != "text_only" and not consent:
            st.error("Enable consent for the selected mode, or choose text only.")
        else:
            messages.append({"role": "user", "text": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            response = api("POST", "/chat", json={"session_id": session, "profile_id": profile, "message": prompt, "mode": MODES[mode_label], "consent_to_use_vitals": consent})
            if response:
                messages.append({"role": "assistant", "response": response})
                with st.chat_message("assistant"):
                    show_response(response)
    st.subheader("A/B/C comparison")
    compare_prompt = st.text_area("Identical message for all three modes", max_chars=10000)
    if st.button("Compare A/B/C"):
        if not consent or not compare_prompt.strip():
            st.error("Enter a message and enable vitals consent to compare all three modes.")
        else:
            for col, (label, mode) in zip(st.columns(3), MODES.items()):
                with col:
                    st.markdown(f"**{label}**")
                    result = api("POST", "/chat", json={"session_id": str(uuid.uuid4()), "profile_id": profile, "message": compare_prompt, "mode": mode, "consent_to_use_vitals": consent})
                    if result:
                        show_response(result)

if __name__ == "__main__":
    main()
