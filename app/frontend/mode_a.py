import html

import streamlit as st

from backend.config import (
    ANNOTATION_CLASS_NAMES, CLASS_COLORS, TRAINING_THRESHOLD,
)
from backend.image_service import list_image_paths, load_image, get_image_stem
from backend.drawing import canvas_rect_to_yolo
from backend.annotation_service import is_annotated, load_annotation
from backend.overlay import draw_boxes_on_image
from frontend.modal import show_threshold_dialog
from frontend.drawable_canvas import drawable_canvas
from frontend.components import (
    CSP_TAG as _CSP_TAG, TH_TAG as _TH_TAG,
    render_save_flash, render_nav_bar, get_submission_count,
)


def render_mode_a():
    """Render the Cold Start annotation interface."""
    if st.session_state.pop("_show_threshold", False):
        show_threshold_dialog()

    st.header("Manual Review")

    # ── Rec #1 + #5: Inline progress bar ─────────────────────────────
    count = get_submission_count()
    remaining = max(0, TRAINING_THRESHOLD - count)
    if remaining > 0:
        pct = min(count / TRAINING_THRESHOLD * 100, 100)
        st.markdown(
            f'<div class="nyp-workflow-bar">'
            f'<span class="workflow-text">'
            f'<strong>{count}</strong>/{TRAINING_THRESHOLD} reviewed '
            f'— {remaining} more to unlock éo-Assisted'
            f'</span>'
            f'<div class="workflow-track">'
            f'<div class="workflow-fill" style="width:{pct:.0f}%"></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="nyp-workflow-bar workflow-complete">'
            '<span class="workflow-text">'
            '<strong>Threshold reached</strong> — switch to éo-Assisted mode'
            '</span></div>',
            unsafe_allow_html=True,
        )

    # ── Save flash ────────────────────────────────────────────────────
    render_save_flash()

    # ── Image list ───────────────────────────────────────────────────
    all_images = list_image_paths()
    total = len(all_images)

    if total == 0:
        st.info("No images found. Add PNG files to the images folder to begin reviewing.")
        return

    if "current_index" not in st.session_state:
        first_new = next(
            (i for i, p in enumerate(all_images) if not is_annotated(get_image_stem(p))),
            0,
        )
        st.session_state["current_index"] = first_new

    idx = st.session_state["current_index"]
    idx = max(0, min(idx, total - 1))

    image_path = all_images[idx]
    stem = get_image_stem(image_path)
    saved = is_annotated(stem)
    safe_stem = html.escape(stem)
    render_nav_bar(idx, total, safe_stem, saved, "current_index")

    # ── Load image ───────────────────────────────────────────────────
    try:
        image = load_image(image_path)
    except ValueError as exc:
        st.error(str(exc))
        return
    if saved:
        existing_boxes = load_annotation(stem)
        if existing_boxes:
            image = draw_boxes_on_image(image, existing_boxes)

    img_w, img_h = image.size
    canvas_width = min(img_w, 680)
    scale = canvas_width / img_w
    canvas_height = int(img_h * scale)
    display_image = image.resize((canvas_width, canvas_height))

    # ── Rec #2: Hint placeholder ABOVE canvas ────────────────────────
    hint_slot = st.empty()

    # ── Rec #3: Per-box colors from swap state ───────────────────────
    swapped = st.session_state.get(f"swap_{idx}", False)
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

    # ── Canvas ───────────────────────────────────────────────────────
    rects = drawable_canvas(
        image=display_image,
        height=canvas_height,
        width=canvas_width,
        stroke_color="#32ADE6",
        stroke_width=2,
        fill_color="rgba(50, 173, 230, 0.08)",
        stroke_colors=stroke_colors,
        fill_colors=fill_colors,
        box_labels=box_labels,
        header_label="Image Viewer",
        header_badge=safe_stem,
        key=f"canvas_{idx}",
    )

    # ── Rec #2: Fill hint based on state ─────────────────────────────
    if not rects:
        if saved:
            hint_slot.markdown(
                '<div class="nyp-step-hint">'
                '<span class="step-num">1</span>'
                'Previously reviewed — draw new landmarks to update, '
                'or navigate to the next image.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            hint_slot.markdown(
                '<div class="nyp-step-hint">'
                '<span class="step-num">1</span>'
                f'Draw 2 boxes — {_CSP_TAG} and {_TH_TAG}'
                '</div>',
                unsafe_allow_html=True,
            )
        return

    if len(rects) == 1:
        hint_slot.markdown(
            '<div class="nyp-step-hint">'
            '<span class="step-num">1</span>'
            '1 of 2 landmarks — draw one more.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    if len(rects) > 2:
        hint_slot.warning(
            f"{len(rects)} markers placed — need exactly 2. "
            "Use Undo in the toolbar to remove extras."
        )
        return

    # ── Exactly 2 boxes — verify & submit ────────────────────────────
    hint_slot.markdown(
        '<div class="nyp-step-hint">'
        '<span class="step-num">2</span>'
        'Verify assignment, then confirm.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Rec #4: Assignment display + swap button ─────────────────────
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
        if st.button("Swap", key=f"swap_btn_{idx}", use_container_width=True):
            st.session_state[f"swap_{idx}"] = not swapped
            st.rerun()

    # ── Confirm button ───────────────────────────────────────────────
    if st.button("Confirm & Save", type="primary", use_container_width=True):
        boxes = []
        for rect, cls_name in zip(rects, assignments):
            yolo = canvas_rect_to_yolo(rect, canvas_width, canvas_height)
            cls_id = 0 if cls_name == "CSP" else 1
            boxes.append({"class_id": cls_id, **yolo})

        st.session_state["_pending_save"] = {
            "stem": stem,
            "boxes": boxes,
            "toast": f"Saved {safe_stem}",
            "check_threshold": not st.session_state.get("threshold_dismissed"),
        }
        if idx < total - 1:
            st.session_state["current_index"] = idx + 1
        st.rerun()
