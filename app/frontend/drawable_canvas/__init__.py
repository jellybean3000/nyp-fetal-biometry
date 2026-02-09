import os
import base64
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

_component_func = components.declare_component(
    "drawable_canvas",
    path=_FRONTEND_DIR,
)


def drawable_canvas(
    image,
    height: int,
    width: int,
    stroke_color: str = "#32ADE6",
    stroke_width: int = 2,
    fill_color: str = "rgba(50,173,230,0.08)",
    stroke_colors: list[str] | None = None,
    fill_colors: list[str] | None = None,
    box_labels: list[str] | None = None,
    header_label: str = "",
    header_badge: str = "",
    key=None,
):
    """Render an image with a drawable rectangle overlay.

    Args:
        image: PIL Image to display as background.
        height: Canvas height in pixels.
        width: Canvas width in pixels.
        stroke_color: Default CSS color for rectangle borders.
        stroke_width: Border width in pixels.
        fill_color: Default CSS color for rectangle fill.
        stroke_colors: Per-box stroke colors (by drawing order). Falls back to stroke_color.
        fill_colors: Per-box fill colors (by drawing order). Falls back to fill_color.
        box_labels: Per-box label text (by drawing order). Falls back to box number.
        header_label: Optional label for header bar (e.g. "Image Viewer").
        header_badge: Optional badge text for header bar (e.g. image filename).
        key: Streamlit component key.

    Returns:
        List of drawn rectangles, each dict with: left, top, width, height, type.
    """
    cache_key = f"_b64_{key}"
    cached = st.session_state.get(cache_key) if key else None
    if cached is not None:
        image_b64 = cached
    else:
        buf = BytesIO()
        image.save(buf, format="PNG")
        image_b64 = base64.b64encode(buf.getvalue()).decode()
        if key:
            # Evict all other _b64_ entries to prevent memory leak
            for k in list(st.session_state):
                if k.startswith("_b64_") and k != cache_key:
                    del st.session_state[k]
            st.session_state[cache_key] = image_b64

    result = _component_func(
        image_b64=image_b64,
        height=height,
        width=width,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        fill_color=fill_color,
        stroke_colors=stroke_colors,
        fill_colors=fill_colors,
        box_labels=box_labels,
        header_label=header_label,
        header_badge=header_badge,
        key=key,
        default=[],
    )

    return result if result is not None else []
