import html

import streamlit as st

from backend.config import (
    CLASS_COLORS, THALAMUS_COLOR, ANNOTATION_CLASS_NAMES, TRAINING_THRESHOLD,
)
from backend.image_service import list_image_paths, load_image, get_image_stem
from backend.overlay import draw_boxes_on_image
from backend.drawing import canvas_rect_to_yolo
from backend.annotation_service import is_annotated, load_annotation, save_cold_start
from backend.inference_service import load_model_raw, detect_csp
from frontend.drawable_canvas import drawable_canvas
from frontend.components import (
    CSP_TAG as _CSP_TAG, TH_TAG as _TH_TAG,
    render_save_flash, render_nav_bar, get_submission_count,
)


def _do_skip(stem, safe_stem, idx, total):
    """Save empty annotation for stem, advance index, and rerun."""
    st.session_state["_pending_save"] = {
        "stem": stem, "boxes": [], "toast": f"Skipped {safe_stem}",
    }
    if idx < total - 1:
        st.session_state["copilot_index"] = idx + 1
    st.rerun()


@st.cache_resource
def load_model():
    """Load the fine-tuned YOLO model (cached by Streamlit)."""
    return load_model_raw()


def _ai_thinking_html() -> str:
    """AI thinking indicator with Siri-style breathing orb."""
    return (
        '<div class="nyp-ai-thinking">'
        '<div class="nyp-ai-orb-container">'
        '<div class="nyp-ai-orb"></div>'
        '</div>'
        '<span class="nyp-ai-thinking-text">Analyzing ultrasound\u2026</span>'
        '</div>'
    )


def _ai_prompt_html(csp_conf: float) -> str:
    """AI prompt asking user to draw Thalamus."""
    conf_label = f"{csp_conf:.0%}" if csp_conf else ""
    return (
        '<div class="nyp-ai-prompt">'
        '<div class="prompt-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 2a7 7 0 0 1 7 7c0 3-2 5.5-4 7l-1 4H10l-1-4c-2-1.5-4-4-4-7a7 7 0 0 1 7-7z"/>'
        '<line x1="10" y1="22" x2="14" y2="22"/>'
        '</svg>'
        '</div>'
        '<div class="prompt-text">'
        f'<strong>éo suggests a {conf_label} likelihood of CSP</strong> — '
        'confirm the detection, then draw a box around the Thalamus.'
        '</div>'
        '</div>'
    )


def _no_detect_html() -> str:
    """No-detection empty state with SVG icon."""
    return (
        '<div class="nyp-no-detect">'
        '<div class="no-detect-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#C77800" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="8"/>'
        '<line x1="21" y1="21" x2="16.65" y2="16.65"/>'
        '<line x1="8" y1="11" x2="14" y2="11"/>'
        '</svg>'
        '</div>'
        '<div class="no-detect-title">éo did not detect CSP in this image</div>'
        '<div class="no-detect-desc">'
        'Mark the <strong>CSP</strong> and <strong>Thalamus</strong> below '
        'to help éo learn, or skip to confirm no CSP and move to next image.'
        '</div>'
        '</div>'
    )


def _no_model_html(reviewed: int, threshold: int) -> str:
    """No-model state — connects back to Manual mode progress."""
    remaining = max(0, threshold - reviewed)
    if remaining > 0:
        desc = (
            f'{reviewed} of {threshold} manual reviews complete. '
            f'Finish <strong>{remaining} more</strong> in Manual mode, '
            f'then the model can be trained for AI-assisted detection.'
        )
    else:
        desc = (
            f'All {threshold} reviews complete! '
            f'The model needs to be trained before éo can assist. '
            f'Contact your administrator to run training.'
        )
    return (
        '<div class="nyp-error-state">'
        '<div class="error-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#D70015" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86'
        'a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
        '</svg>'
        '</div>'
        f'<div class="error-title">Model not trained yet</div>'
        f'<div class="error-desc">{desc}</div>'
        '</div>'
    )


def render_mode_b():
    """Render the Partial Co-Pilot interface."""
    st.header("éo-Assisted")

    # ── Save flash ────────────────────────────────────────────────────
    render_save_flash()

    # ── Model check (Rec #1: improved no-model state) ────────────────
    model = load_model()
    if model is None:
        reviewed = get_submission_count()
        st.markdown(_no_model_html(reviewed, TRAINING_THRESHOLD), unsafe_allow_html=True)
        return

    # ── Image navigation ─────────────────────────────────────────────
    all_images = list_image_paths()
    total = len(all_images)

    if total == 0:
        st.info("No images found. Add PNG files to the images folder to begin reviewing.")
        return

    if "copilot_index" not in st.session_state:
        first_new = next(
            (i for i, p in enumerate(all_images) if not is_annotated(get_image_stem(p))),
            0,
        )
        st.session_state["copilot_index"] = first_new

    idx = st.session_state["copilot_index"]
    idx = max(0, min(idx, total - 1))

    image_path = all_images[idx]
    stem = get_image_stem(image_path)
    saved = is_annotated(stem)
    safe_stem = html.escape(stem)
    render_nav_bar(idx, total, safe_stem, saved, "copilot_index", btn_prefix="b_")

    # ── Load image and run inference ─────────────────────────────────
    try:
        image = load_image(image_path)
    except ValueError as exc:
        st.error(str(exc))
        return

    # ── Cache inference per image (avoid re-running on every rerun) ──
    csp_cache_key = f"_csp_cache_{stem}"
    cached_csp = st.session_state.get(csp_cache_key)
    if cached_csp is not None:
        csp_boxes = cached_csp
    else:
        ai_slot = st.empty()
        ai_slot.markdown(_ai_thinking_html(), unsafe_allow_html=True)
        csp_boxes = detect_csp(model, image)
        ai_slot.empty()
        # Evict previous stem's cache entry
        for k in list(st.session_state):
            if k.startswith("_csp_cache_") and k != csp_cache_key:
                del st.session_state[k]
        st.session_state[csp_cache_key] = csp_boxes

    csp_detected = len(csp_boxes) > 0

    # ── Draw CSP overlay + saved Thalamus ────────────────────────────
    overlay = draw_boxes_on_image(image, csp_boxes, show_confidence=True)
    if saved:
        existing = load_annotation(stem)
        thalamus_saved = [b for b in existing if b["class_id"] == 1]
        if thalamus_saved:
            overlay = draw_boxes_on_image(overlay, thalamus_saved)

    canvas_width = min(image.size[0], 680)
    scale = canvas_width / image.size[0]
    canvas_height = int(image.size[1] * scale)

    # ═════════════════════════════════════════════════════════════════
    # FLOW A: CSP detected — user draws Thalamus only
    # ═════════════════════════════════════════════════════════════════
    if csp_detected:
        best_conf = max(b["confidence"] for b in csp_boxes)
        st.markdown(_ai_prompt_html(best_conf), unsafe_allow_html=True)

        # Rec #2: Hint ABOVE canvas
        hint_slot = st.empty()

        display_overlay = overlay.resize((canvas_width, canvas_height))
        tr, tg, tb = THALAMUS_COLOR
        thalamus_rects = drawable_canvas(
            image=display_overlay,
            height=canvas_height,
            width=canvas_width,
            stroke_color=f"rgb({tr}, {tg}, {tb})",
            stroke_width=2,
            fill_color=f"rgba({tr}, {tg}, {tb}, 0.08)",
            box_labels=["Thalamus"],
            key=f"copilot_canvas_{idx}",
        )

        # Fill hint (state 0 covered by AI prompt above)
        if len(thalamus_rects) == 1:
            hint_slot.markdown(
                '<div class="nyp-step-hint">'
                '<span class="step-num">2</span>'
                'Thalamus marked — confirm to save.'
                '</div>',
                unsafe_allow_html=True,
            )
        elif len(thalamus_rects) > 1:
            hint_slot.warning(
                f"{len(thalamus_rects)} markers placed — need exactly 1 for the Thalamus. "
                "Use Undo in the toolbar to remove extras."
            )

        # Action buttons
        col_accept, col_skip = st.columns(2)

        with col_accept:
            valid_thalamus = len(thalamus_rects) == 1
            if st.button("Confirm & Save", type="primary", disabled=not valid_thalamus,
                         use_container_width=True, key="b_confirm_detected"):
                all_boxes = []
                for box in csp_boxes:
                    all_boxes.append({
                        "class_id": 0,
                        "cx": box["cx"], "cy": box["cy"],
                        "w": box["w"], "h": box["h"],
                    })
                yolo = canvas_rect_to_yolo(thalamus_rects[0], canvas_width, canvas_height)
                all_boxes.append({"class_id": 1, **yolo})

                st.session_state["_pending_save"] = {
                    "stem": stem, "boxes": all_boxes, "toast": f"Saved {safe_stem}",
                }
                if idx < total - 1:
                    st.session_state["copilot_index"] = idx + 1
                st.rerun()

        with col_skip:
            if st.button("Skip", use_container_width=True, key="b_skip_detected"):
                csp_only = [{"class_id": 0, "cx": b["cx"], "cy": b["cy"],
                             "w": b["w"], "h": b["h"]} for b in csp_boxes]
                save_cold_start(stem, csp_only)
                st.session_state["_pending_save"] = {
                    "stem": stem, "boxes": csp_only,
                    "toast": f"Skipped {safe_stem}",
                }
                if idx < total - 1:
                    st.session_state["copilot_index"] = idx + 1
                st.rerun()

    # ═════════════════════════════════════════════════════════════════
    # FLOW B: No CSP detected — user draws both landmarks
    # ═════════════════════════════════════════════════════════════════
    else:
        st.markdown(_no_detect_html(), unsafe_allow_html=True)

        preview = image
        if saved:
            existing = load_annotation(stem)
            if existing:
                preview = draw_boxes_on_image(image, existing)

        display_img = preview.resize((canvas_width, canvas_height))

        # Rec #2: Hint ABOVE canvas
        hint_slot = st.empty()

        # Rec #3: Per-box colors from swap state
        swapped = st.session_state.get(f"copilot_swap_{idx}", False)
        class_order = ["Thalamus", "CSP"] if swapped else ["CSP", "Thalamus"]

        box_labels = []
        stroke_colors = []
        fill_colors = []
        for cls in class_order:
            cid = ANNOTATION_CLASS_NAMES.index(cls)
            r, g, b = CLASS_COLORS[cid]
            box_labels.append(cls)
            stroke_colors.append(f"rgb({r},{g},{b})")
            fill_colors.append(f"rgba({r},{g},{b},0.08)")

        manual_rects = drawable_canvas(
            image=display_img,
            height=canvas_height,
            width=canvas_width,
            stroke_color="#32ADE6",
            stroke_width=2,
            fill_color="rgba(50, 173, 230, 0.08)",
            stroke_colors=stroke_colors,
            fill_colors=fill_colors,
            box_labels=box_labels,
            key=f"copilot_manual_{idx}",
        )

        # Fill hint (state 0 covered by no-detect card above)
        if len(manual_rects) == 1:
            hint_slot.markdown(
                '<div class="nyp-step-hint">'
                '<span class="step-num">1</span>'
                '1 of 2 landmarks — draw one more.'
                '</div>',
                unsafe_allow_html=True,
            )
        elif len(manual_rects) > 2:
            hint_slot.warning(
                f"{len(manual_rects)} markers placed — need exactly 2. "
                "Use Undo in the toolbar to remove extras."
            )

        # Exactly 2 boxes — verify and submit
        if len(manual_rects) == 2:
            hint_slot.markdown(
                '<div class="nyp-step-hint">'
                '<span class="step-num">2</span>'
                'Verify assignment, then confirm.'
                '</div>',
                unsafe_allow_html=True,
            )

            # Rec #4: Assignment display + swap
            assignments = list(class_order)
            r0, g0, b0 = CLASS_COLORS[ANNOTATION_CLASS_NAMES.index(assignments[0])]
            r1, g1, b1 = CLASS_COLORS[ANNOTATION_CLASS_NAMES.index(assignments[1])]

            col_assign, col_swap = st.columns([5, 1])
            with col_assign:
                st.markdown(
                    f'<div class="nyp-assignment">'
                    f'<span class="assign-item">'
                    f'<span class="assign-dot" style="background:rgb({r0},{g0},{b0})"></span>'
                    f'Box 1 → <strong>{assignments[0]}</strong>'
                    f'</span>'
                    f'<span class="assign-item">'
                    f'<span class="assign-dot" style="background:rgb({r1},{g1},{b1})"></span>'
                    f'Box 2 → <strong>{assignments[1]}</strong>'
                    f'</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_swap:
                if st.button("Swap", key=f"copilot_swap_btn_{idx}", use_container_width=True):
                    st.session_state[f"copilot_swap_{idx}"] = not swapped
                    st.rerun()

            col_submit, col_skip = st.columns(2)

            with col_submit:
                if st.button("Confirm & Save", type="primary",
                             use_container_width=True, key="b_submit_manual"):
                    boxes = []
                    for rect, cls_name in zip(manual_rects, assignments):
                        yolo = canvas_rect_to_yolo(rect, canvas_width, canvas_height)
                        cls_id = 0 if cls_name == "CSP" else 1
                        boxes.append({"class_id": cls_id, **yolo})

                    st.session_state["_pending_save"] = {
                        "stem": stem, "boxes": boxes, "toast": f"Saved {safe_stem}",
                    }
                    if idx < total - 1:
                        st.session_state["copilot_index"] = idx + 1
                    st.rerun()

            with col_skip:
                if st.button("Skip", use_container_width=True, key="b_skip_no_csp"):
                    _do_skip(stem, safe_stem, idx, total)
        else:
            if st.button("Skip — No CSP", key="b_skip_no_csp_empty", use_container_width=True):
                _do_skip(stem, safe_stem, idx, total)
