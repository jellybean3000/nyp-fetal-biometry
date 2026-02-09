from pathlib import Path
from PIL import Image
from backend.config import SOURCE_IMAGES_DIR, SOURCE_LABELS_DIR


def list_image_paths() -> list[Path]:
    """Return all PNG image paths sorted by filename."""
    return sorted(SOURCE_IMAGES_DIR.glob("*.png"))


def load_image(path: Path) -> Image.Image:
    """Load an image as RGB PIL Image.

    Raises ValueError with filename if the image is corrupt or unreadable.
    """
    try:
        return Image.open(path).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot open image {path.name}: {exc}") from exc


def get_annotation_path(image_path: Path) -> Path:
    """Return the YOLO .txt annotation path for a given image."""
    return SOURCE_LABELS_DIR / image_path.with_suffix(".txt").name


def get_image_stem(image_path: Path) -> str:
    """Return the filename stem (e.g. '480_HC')."""
    return image_path.stem
