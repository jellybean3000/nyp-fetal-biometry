import streamlit as st
from backend.config import TRAINING_THRESHOLD


@st.dialog("Milestone Reached")
def show_threshold_dialog():
    """Show a celebration dialog when the review threshold is reached."""

    # Celebration visual — animated green checkmark
    st.markdown(
        '<div class="nyp-milestone">'
        '<div class="nyp-milestone-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="20 6 9 17 4 12"></polyline>'
        '</svg>'
        '</div>'
        f'<div class="nyp-milestone-title">{TRAINING_THRESHOLD} Cases Reviewed</div>'
        '<div class="nyp-milestone-desc">'
        'Your reviews are ready. The model can now be fine-tuned '
        'on your Thalamus data for AI-assisted detection.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Switch to éo-Assisted", type="primary", use_container_width=True):
            st.session_state["mode_selector"] = "éo-Assisted"
            st.rerun()
    with col2:
        if st.button("Continue Reviewing", use_container_width=True):
            st.session_state["threshold_dismissed"] = True
            st.rerun()
