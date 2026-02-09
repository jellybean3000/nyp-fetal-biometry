from backend.config import IMG_WIDTH, IMG_HEIGHT


def canvas_rect_to_yolo(rect: dict, canvas_w: int, canvas_h: int) -> dict:
    """Convert a canvas rect object to YOLO normalized coordinates.

    Canvas rect has keys: left, top, width, height (in pixel coords of canvas).
    Returns dict with cx, cy, w, h normalized to [0, 1].
    """
    left = rect["left"]
    top = rect["top"]
    w = rect["width"]
    h = rect["height"]

    # Handle negative width/height from drawing direction
    if w < 0:
        left = left + w
        w = -w
    if h < 0:
        top = top + h
        h = -h

    cx = (left + w / 2) / canvas_w
    cy = (top + h / 2) / canvas_h
    nw = w / canvas_w
    nh = h / canvas_h

    # Clamp to [0, 1]
    cx = max(0.0, min(1.0, cx))
    cy = max(0.0, min(1.0, cy))
    nw = max(0.0, min(1.0, nw))
    nh = max(0.0, min(1.0, nh))

    return {"cx": cx, "cy": cy, "w": nw, "h": nh}


def yolo_to_pixel(box: dict, img_w: int = IMG_WIDTH, img_h: int = IMG_HEIGHT) -> tuple:
    """Convert YOLO normalized box to pixel (x1, y1, x2, y2)."""
    cx, cy, w, h = box["cx"], box["cy"], box["w"], box["h"]
    x1 = int((cx - w / 2) * img_w)
    y1 = int((cy - h / 2) * img_h)
    x2 = int((cx + w / 2) * img_w)
    y2 = int((cy + h / 2) * img_h)
    return (x1, y1, x2, y2)
