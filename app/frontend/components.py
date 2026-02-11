"""Shared UI helpers used by both mode_a and mode_b."""

import html

import streamlit as st

from backend.config import CLASS_COLORS
from backend.annotation_service import count_cold_start_submissions

# ── Inline class-label HTML (color dot + name) ─────────────────────
_R0, _G0, _B0 = CLASS_COLORS[0]
_R1, _G1, _B1 = CLASS_COLORS[1]
CSP_TAG = (
    f'<span class="cls-label">'
    f'<span class="cls-dot" style="background:rgb({_R0},{_G0},{_B0})"></span>'
    f'CSP</span>'
)
TH_TAG = (
    f'<span class="cls-label">'
    f'<span class="cls-dot" style="background:rgb({_R1},{_G1},{_B1})"></span>'
    f'Thalamus</span>'
)


def render_save_flash():
    """Pop and render the _just_saved flash message if present."""
    _flash = st.session_state.pop("_just_saved", None)
    if _flash:
        st.markdown(
            f'<div class="nyp-save-flash">{html.escape(_flash)}</div>',
            unsafe_allow_html=True,
        )


def render_nav_bar(idx, total, safe_stem, saved, index_key, btn_prefix=""):
    """Render Previous / Image N of M / Next navigation row.

    Args:
        idx: Current zero-based index.
        total: Total number of images.
        safe_stem: HTML-escaped image stem for display.
        saved: Whether the current image has been annotated.
        index_key: session_state key to update on navigation.
        btn_prefix: Optional prefix for button keys to avoid collisions.
    """
    saved_badge = ' <span class="nyp-saved-badge">Saved</span>' if saved else ""
    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("Previous", disabled=idx == 0,
                      key=f"{btn_prefix}prev" if btn_prefix else None,
                      use_container_width=True):
            st.session_state[index_key] = idx - 1
            st.rerun()
    with col_info:
        st.markdown(
            f'<div class="nyp-nav-info">'
            f'<span class="nyp-viewer-badge">{safe_stem}</span> '
            f'{idx + 1} of {total}{saved_badge}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next", disabled=idx >= total - 1,
                      key=f"{btn_prefix}next" if btn_prefix else None,
                      use_container_width=True):
            st.session_state[index_key] = idx + 1
            st.rerun()


def get_submission_count():
    """Return the current submission count, using sidebar cache when available."""
    cached = st.session_state.get("_counts_cache")
    ver = st.session_state.get("_counts_version", 0)
    if cached is not None and cached[0] == ver:
        return cached[1]
    return count_cold_start_submissions()
