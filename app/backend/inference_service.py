from PIL import Image
from backend.config import BEST_MODEL_PATH, CONFIDENCE_THRESHOLD


def load_model_raw():
    """Load the fine-tuned YOLO model (no Streamlit caching).

    Returns the YOLO model instance, or None if not available.
    """
    if not BEST_MODEL_PATH.exists():
        return None
    try:
        from ultralytics import YOLO
        return YOLO(str(BEST_MODEL_PATH))
    except Exception:
        return None


def detect_csp(model, image: Image.Image) -> list[dict]:
    """Run inference and return CSP detections as normalized YOLO boxes.

    Each returned dict has keys: class_id, cx, cy, w, h, confidence.
    """
    results = model(image, conf=CONFIDENCE_THRESHOLD, verbose=False)

    csp_boxes = []
    if results and len(results) > 0:
        result = results[0]
        for det in result.boxes:
            cls_id = int(det.cls.item())
            if cls_id != 0:
                continue
            conf = float(det.conf.item())
            x1, y1, x2, y2 = det.xyxy[0].tolist()
            img_w, img_h = image.size
            cx = ((x1 + x2) / 2) / img_w
            cy = ((y1 + y2) / 2) / img_h
            w = (x2 - x1) / img_w
            h = (y2 - y1) / img_h
            csp_boxes.append({
                "class_id": cls_id,
                "cx": cx, "cy": cy, "w": w, "h": h,
                "confidence": conf,
            })

    return csp_boxes
