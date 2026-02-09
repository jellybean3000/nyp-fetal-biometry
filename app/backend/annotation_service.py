from pathlib import Path
from backend.config import COLD_START_DIR


def parse_yolo_labels(label_path: Path) -> list[dict]:
    """Parse a YOLO annotation file into a list of dicts.

    Returns list of {class_id, cx, cy, w, h} (all floats except class_id int).
    """
    boxes = []
    if not label_path.exists():
        return boxes
    text = label_path.read_text().strip()
    if not text:
        return boxes
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        try:
            boxes.append({
                "class_id": int(parts[0]),
                "cx": float(parts[1]),
                "cy": float(parts[2]),
                "w": float(parts[3]),
                "h": float(parts[4]),
            })
        except ValueError:
            continue
    return boxes


def write_yolo_labels(label_path: Path, boxes: list[dict]) -> None:
    """Write a list of box dicts to a YOLO annotation file."""
    lines = []
    for b in boxes:
        lines.append(f"{b['class_id']} {b['cx']:.6f} {b['cy']:.6f} {b['w']:.6f} {b['h']:.6f}")
    label_path.write_text("\n".join(lines) + "\n" if lines else "")


def save_cold_start(image_stem: str, boxes: list[dict]) -> Path:
    """Save cold-start annotations for a given image. Returns the saved path."""
    out_path = COLD_START_DIR / f"{image_stem}.txt"
    write_yolo_labels(out_path, boxes)
    return out_path


def count_cold_start_submissions() -> int:
    """Count how many cold-start annotation files exist."""
    return len(list(COLD_START_DIR.glob("*.txt")))


def count_csp_breakdown() -> tuple[int, int]:
    """Count annotations with CSP found vs no CSP.

    Returns (csp_found, no_csp) based on whether .txt files have content.
    """
    csp_found = 0
    no_csp = 0
    for f in COLD_START_DIR.glob("*.txt"):
        if f.read_text().strip():
            csp_found += 1
        else:
            no_csp += 1
    return csp_found, no_csp


def is_annotated(image_stem: str) -> bool:
    """Check whether a cold-start annotation exists for a given image."""
    return (COLD_START_DIR / f"{image_stem}.txt").exists()


def load_annotation(image_stem: str) -> list[dict]:
    """Load a previously saved cold-start annotation for an image."""
    return parse_yolo_labels(COLD_START_DIR / f"{image_stem}.txt")
