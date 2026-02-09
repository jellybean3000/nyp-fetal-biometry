import streamlit as st
from backend.config import ANNOTATION_CLASS_MAP, CLASS_COLORS, THALAMUS_COLOR, TRAINING_THRESHOLD, COLD_START_DIR
from backend.annotation_service import count_cold_start_submissions, count_csp_breakdown


def _get_counts():
    """Return (count, csp_found, no_csp) cached per rerun via a version counter."""
    ver = st.session_state.get("_counts_version", 0)
    cached = st.session_state.get("_counts_cache")
    if cached is not None and cached[0] == ver:
        return cached[1], cached[2], cached[3]
    count = count_cold_start_submissions()
    csp_found, no_csp = count_csp_breakdown()
    st.session_state["_counts_cache"] = (ver, count, csp_found, no_csp)
    return count, csp_found, no_csp


def render_sidebar():
    """Render the sidebar with brand lockup, mode selector, class legend, and counter."""
    with st.sidebar:
        # Brand lockup — icon + title
        st.markdown(
            '<div class="nyp-brand">'
            '<div class="nyp-brand-icon">'
            '<svg viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect width="1024" height="1024" rx="188" fill="black"/>'
            '<path d="M647.201 385.75C686.421 385.75 717.859 397.687 741.516 421.561'
            'C765.172 445.434 777 475.785 777 512.609C777 549.434 765.172 579.705 '
            '741.516 603.423C717.859 627.141 686.421 639 647.201 639C607.981 639 '
            '576.388 627.141 552.42 603.423C528.453 579.705 516.469 549.434 516.469 '
            '512.609C516.469 475.785 528.452 445.434 552.42 421.561C576.388 397.687 '
            '607.982 385.75 647.201 385.75ZM374.997 384.814C410.17 384.814 439.43 '
            '395.581 462.775 417.114C491.412 443.641 505.263 482.495 504.329 533.675'
            'H334.377C339.98 563.322 355.544 578.146 381.067 578.146C396.631 578.145 '
            '407.68 572.215 414.217 560.356H499.66C494.369 582.826 479.272 602.019 '
            '454.371 617.935C433.516 631.354 408.147 638.063 378.266 638.063C339.668 '
            '638.063 308.308 626.205 284.185 602.487C260.061 578.77 248 548.498 248 '
            '511.673C248 475.16 259.828 444.889 283.484 420.859C307.141 396.83 '
            '337.645 384.815 374.997 384.814ZM376.865 444.265C353.52 444.265 339.357 '
            '458.464 334.377 486.863H416.552C414.684 473.444 410.249 462.989 403.245 '
            '455.499C396.242 448.009 387.448 444.265 376.865 444.265ZM406.28 366.558'
            'H339.979L367.06 294H468.378L406.28 366.558Z" fill="white"/>'
            '</svg>'
            '</div>'
            '<div>'
            '<div class="nyp-brand-text">OB/GYN</div>'
            '<div class="nyp-brand-sub">Fetal Biometry</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nyp-sidebar-divider"></div>', unsafe_allow_html=True)

        # Mode selector — rendered as segmented control via CSS
        mode = st.radio(
            "Mode",
            ["Manual", "éo-Assisted"],
            key="mode_selector",
        )

        # Mode description — tells user what they're doing (recognition > recall)
        if mode == "Manual":
            st.markdown(
                '<p class="nyp-mode-desc">You identify both landmarks manually.</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p class="nyp-mode-desc">éo assists with CSP detection — you confirm landmarks.</p>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="nyp-sidebar-divider"></div>', unsafe_allow_html=True)

        # Class legend — pill-style items
        legend_colors = {0: CLASS_COLORS[0], 1: THALAMUS_COLOR}
        pills_html = ""
        for cls_id, cls_name in ANNOTATION_CLASS_MAP.items():
            r, g, b = legend_colors[cls_id]
            pills_html += (
                f'<span class="nyp-pill" '
                f'style="background:rgba({r},{g},{b},0.10);color:rgb({r},{g},{b});">'
                f'<span class="dot" style="background:rgb({r},{g},{b});"></span>'
                f'{cls_name}</span>'
            )
        st.markdown(pills_html, unsafe_allow_html=True)

        st.markdown('<div class="nyp-sidebar-divider"></div>', unsafe_allow_html=True)

        # Submission counter — threshold-aware card
        count, csp_found, no_csp = _get_counts()
        pct = min(count / TRAINING_THRESHOLD, 1.0)

        # Card state: near-threshold glow or reached celebration
        if count >= TRAINING_THRESHOLD:
            card_class = "nyp-counter-card threshold-reached"
        elif pct >= 0.7:
            card_class = "nyp-counter-card near-threshold"
        else:
            card_class = "nyp-counter-card"

        breakdown_html = ""
        if count > 0:
            breakdown_html = (
                '<div class="nyp-counter-breakdown">'
                f'<span class="breakdown-item csp-found">'
                f'<span class="breakdown-dot" style="background:rgb(52,199,89);"></span>'
                f'CSP Found <strong>{csp_found}</strong></span>'
                f'<span class="breakdown-item no-csp">'
                f'<span class="breakdown-dot" style="background:var(--color-text-tertiary);"></span>'
                f'No CSP <strong>{no_csp}</strong></span>'
                '</div>'
            )

        st.markdown(
            f'<div class="{card_class}">'
            f'<div class="count">{count} <span class="denominator">/ {TRAINING_THRESHOLD}</span></div>'
            f'<div class="label">Cases Reviewed</div>'
            f'{breakdown_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.progress(pct)

        if count >= TRAINING_THRESHOLD:
            st.success("Threshold reached — model ready to train")

        # Reset button
        if count > 0:
            if st.button("Reset Progress", key="reset_progress", use_container_width=True):
                for f in COLD_START_DIR.glob("*.txt"):
                    f.unlink()
                st.session_state["_counts_version"] = st.session_state.get("_counts_version", 0) + 1
                st.session_state.pop("current_index", None)
                st.session_state.pop("copilot_index", None)
                st.rerun()

    return mode
