from __future__ import annotations

import html
import json
import time
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_PATH = DATA_DIR / "state.json"
PARAMS_PATH = DATA_DIR / "params.json"
STATE_STALE_SECONDS = 5

DEFAULT_PARAMS = {
    "delay": 1.0,
    "drop_rate": 20,
    "corruption_rate": 10,
}
PARAM_FIELD_SPECS = {
    "delay": {
        "label": "Delay (seconds)",
        "min_value": 0.0,
        "max_value": 3.0,
        "step": 0.1,
    },
    "drop_rate": {
        "label": "Drop Rate (%)",
        "min_value": 0,
        "max_value": 100,
        "step": 1,
    },
    "corruption_rate": {
        "label": "Corruption Rate (%)",
        "min_value": 0,
        "max_value": 100,
        "step": 1,
    },
}

STATUS_COLORS = {
    "WAITING": "#6c757d",
    "STABLE": "#1f8f5f",
    "WARNING": "#d19b00",
    "CRITICAL": "#c53a3a",
}

LOG_COLORS = {
    "INFO": "#28a745",
    "WARNING": "#e6a817",
    "ERROR": "#dc3545",
    "CRITICAL": "#ff4444",
    "RECOVERED": "#17a2b8",
    "DROPPED": "#888888",
}


def load_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback


def build_waiting_state(message: str) -> dict:
    return {
        "status": "WAITING",
        "anomaly_score": 0.0,
        "counts": {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        },
        "stats": {
            "total_received": 0,
            "total_dropped": 0,
            "total_corrupted": 0,
            "total_recovered": 0,
            "drop_rate": 0.0,
        },
        "recent_logs": [],
        "error_rate_history": [],
        "last_updated": "",
        "status_message": message,
    }


def resolve_dashboard_state(state_path: Path) -> dict:
    if not state_path.exists():
        return build_waiting_state("System not started. Run main.py to begin streaming logs.")

    state = load_json(state_path, {})
    if not state:
        return build_waiting_state("Waiting for a valid state.json update from the backend.")

    age_seconds = time.time() - state_path.stat().st_mtime
    if age_seconds > STATE_STALE_SECONDS:
        last_updated = state.get("last_updated", "unknown")
        return build_waiting_state(
            f"Backend appears offline. Last update was {last_updated}. Run main.py to resume."
        )

    return state


def save_params(params: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PARAMS_PATH.write_text(json.dumps(params, indent=2), encoding="utf-8")


def normalized_params(raw_params: dict) -> dict:
    return {
        "delay": round(float(raw_params.get("delay", DEFAULT_PARAMS["delay"])), 1),
        "drop_rate": int(float(raw_params.get("drop_rate", DEFAULT_PARAMS["drop_rate"]))),
        "corruption_rate": int(float(raw_params.get("corruption_rate", DEFAULT_PARAMS["corruption_rate"]))),
    }


def initialize_sidebar_state(params: dict) -> None:
    normalized = normalized_params(params)
    for key, value in normalized.items():
        session_key = f"param_{key}"
        if session_key not in st.session_state:
            st.session_state[session_key] = value


def persist_sidebar_params() -> None:
    params = {
        "delay": round(float(st.session_state["param_delay"]), 1),
        "drop_rate": int(st.session_state["param_drop_rate"]),
        "corruption_rate": int(st.session_state["param_corruption_rate"]),
    }
    save_params(params)
    st.session_state["saved_params"] = params


def render_status_card(status: str, anomaly_score: float, last_updated: str) -> None:
    color = STATUS_COLORS.get(status, "#6c757d")
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color}22 0%, #f4efe2 100%);
            border: 1px solid {color}55;
            border-radius: 20px;
            padding: 20px 22px;
            margin-bottom: 8px;">
            <div style="font-size: 0.85rem; letter-spacing: 0.12em; color: #725f44;">SYSTEM STATUS</div>
            <div style="font-size: 2.1rem; font-weight: 700; color: {color}; margin-top: 6px;">{status}</div>
            <div style="color: #574b3a; margin-top: 6px;">Last updated: {last_updated or 'waiting for state.json'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(float(anomaly_score))
    st.caption(f"Anomaly Score: {anomaly_score:.2f}")


def render_live_logs(logs: list[dict]) -> None:
    rows = []
    for entry in reversed(logs[-30:]):
        level = "RECOVERED" if entry.get("recovered") else entry.get("level", "INFO")
        color = LOG_COLORS.get(level, "#333333")
        timestamp = html.escape(str(entry.get("timestamp", "")))
        display = html.escape(str(entry.get("display", "")))
        if entry.get("recovered") and entry.get("original"):
            original = html.escape(str(entry.get("original", "")))
            detail = f"<div style='color: #6f6556; margin-top: 4px;'>Recovered from: {original}</div>"
        else:
            detail = ""
        rows.append(
            f"""
            <div style="
                border-bottom: 1px solid #ebe1cf;
                padding: 8px 0;
                font-family: 'IBM Plex Mono', Consolas, monospace;
                font-size: 0.9rem;">
                <span style="color: #7c6a53;">{timestamp}</span>
                <span style="color: {color}; font-weight: 700; margin-left: 10px;">{level}</span>
                <span style="color: #2f2b25; margin-left: 10px;">{display}</span>
                {detail}
            </div>
            """
        )

    if not rows:
        rows.append("<div style='color: #6c757d; padding: 8px 0;'>No live logs yet.</div>")

    st.html(
        """
        <div style="
            background: rgba(255,255,255,0.82);
            border: 1px solid #e6d9c2;
            border-radius: 18px;
            padding: 14px 18px;
            max-height: 520px;
            overflow-y: auto;">
        """
        + "".join(rows)
        + "</div>",
    )


st.set_page_config(page_title="Intelligent Server Log Monitoring System", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 217, 169, 0.35), transparent 35%),
                linear-gradient(180deg, #fff9f1 0%, #f5efe6 100%);
            color: #2f2b25;
            font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid #e9dbc5;
            border-radius: 18px;
            padding: 12px 14px;
        }
        h1, h2, h3 {
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
            color: #2f2b25;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

state = resolve_dashboard_state(STATE_PATH)
params = load_json(PARAMS_PATH, DEFAULT_PARAMS)
initialize_sidebar_state(params)

st.title("Intelligent Server Log Monitoring System")
st.caption("Simulated network constraints, AI-based recovery, and live decision support.")

with st.sidebar:
    st.subheader("Constraint Controls")
    st.slider(
        PARAM_FIELD_SPECS["delay"]["label"],
        PARAM_FIELD_SPECS["delay"]["min_value"],
        PARAM_FIELD_SPECS["delay"]["max_value"],
        step=PARAM_FIELD_SPECS["delay"]["step"],
        key="param_delay",
        on_change=persist_sidebar_params,
    )
    st.slider(
        PARAM_FIELD_SPECS["drop_rate"]["label"],
        PARAM_FIELD_SPECS["drop_rate"]["min_value"],
        PARAM_FIELD_SPECS["drop_rate"]["max_value"],
        step=PARAM_FIELD_SPECS["drop_rate"]["step"],
        key="param_drop_rate",
        on_change=persist_sidebar_params,
    )
    st.slider(
        PARAM_FIELD_SPECS["corruption_rate"]["label"],
        PARAM_FIELD_SPECS["corruption_rate"]["min_value"],
        PARAM_FIELD_SPECS["corruption_rate"]["max_value"],
        step=PARAM_FIELD_SPECS["corruption_rate"]["step"],
        key="param_corruption_rate",
        on_change=persist_sidebar_params,
    )

    if "saved_params" in st.session_state:
        st.success("Parameters saved.")

status = state.get("status", "WAITING")
anomaly_score = float(state.get("anomaly_score", 0.0))
counts = state.get("counts", {})
stats = state.get("stats", {})
status_message = state.get("status_message", "")

left_col, right_col = st.columns([1.15, 1.85])

with left_col:
    render_status_card(status, anomaly_score, state.get("last_updated", ""))
    if status_message:
        st.info(status_message)

    count_cols = st.columns(2)
    count_cols[0].metric("INFO", counts.get("INFO", 0))
    count_cols[1].metric("WARNING", counts.get("WARNING", 0))
    count_cols[0].metric("ERROR", counts.get("ERROR", 0))
    count_cols[1].metric("CRITICAL", counts.get("CRITICAL", 0))

    st.subheader("Recovery Stats")
    stats_cols = st.columns(2)
    stats_cols[0].metric("Received", stats.get("total_received", 0))
    stats_cols[1].metric("Dropped", stats.get("total_dropped", 0))
    stats_cols[0].metric("Corrupted", stats.get("total_corrupted", 0))
    stats_cols[1].metric("Recovered", stats.get("total_recovered", 0))
    st.metric("Drop Rate", f"{stats.get('drop_rate', 0.0)}%")

with right_col:
    st.subheader("Error Rate Graph")
    history = state.get("error_rate_history", [])
    if history:
        chart_df = pd.DataFrame(history)
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"], format="%H:%M:%S", errors="coerce")
        st.line_chart(chart_df.set_index("timestamp")["error_rate"], height=260)
    else:
        st.info("Waiting: state.json has not been updated yet.")

    st.subheader("Live Log Stream")
    render_live_logs(state.get("recent_logs", []))

time.sleep(1)
st.rerun()
