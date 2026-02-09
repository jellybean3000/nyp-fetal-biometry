import sys
from pathlib import Path

# Ensure app directory is on sys.path for reliable subpackage imports
_APP_DIR = str(Path(__file__).resolve().parent)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st

from backend.config import CSS_PATH, TRAINING_THRESHOLD
from backend.annotation_service import save_cold_start, count_cold_start_submissions
from frontend.sidebar import render_sidebar
from frontend.mode_a import render_mode_a
from frontend.mode_b import render_mode_b

# ── Page config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="éo · OB/GYN",
    page_icon="éo",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Process pending save (before sidebar so count is current) ─────────
_pending = st.session_state.pop("_pending_save", None)
if _pending:
    save_cold_start(_pending["stem"], _pending["boxes"])
    st.session_state["_counts_version"] = st.session_state.get("_counts_version", 0) + 1
    count = count_cold_start_submissions()
    st.toast(f"{_pending['toast']} — {count}/{TRAINING_THRESHOLD}")
    st.session_state["_just_saved"] = _pending["toast"]
    if _pending.get("check_threshold") and count >= TRAINING_THRESHOLD:
        st.session_state["_show_threshold"] = True

# ── Load CSS ───────────────────────────────────────────────────────────
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────
mode = render_sidebar()

# ── Main content ───────────────────────────────────────────────────────
if mode == "Manual":
    render_mode_a()
else:
    render_mode_b()
