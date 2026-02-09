from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent

SOURCE_IMAGES_DIR = APP_DIR / "images"
SOURCE_LABELS_DIR = PROJECT_DIR / "Test-Dataset-YOLO" / "obj_train_data"

COLD_START_DIR = APP_DIR / "cold_start_annotations"
COLD_START_DIR.mkdir(exist_ok=True)

DATASET_DIR = APP_DIR / "data"
MODEL_DIR = APP_DIR / "models"
BEST_MODEL_PATH = MODEL_DIR / "best.pt"

ASSETS_DIR = APP_DIR / "assets"
CSS_PATH = ASSETS_DIR / "style.css"

# ── Image dimensions ──────────────────────────────────────────────────
IMG_WIDTH = 959
IMG_HEIGHT = 661

# ── Class mapping ─────────────────────────────────────────────────────
# Source obj.names: 0=Brain, 1=CSP, 2=LV
# Model detects CSP only; Thalamus is user-drawn in Co-Pilot mode
SOURCE_CSP_ID = 1
SOURCE_LV_ID = 2
# Full annotation classes (used in Cold Start for manual labeling)
ANNOTATION_CLASS_MAP = {0: "CSP", 1: "Thalamus"}
ANNOTATION_CLASS_NAMES = list(ANNOTATION_CLASS_MAP.values())

# ── Colors (RGB for PIL) ──────────────────────────────────────────────
CLASS_COLORS = {
    0: (52, 199, 89),    # CSP — Apple green
    1: (255, 149, 0),    # Thalamus — Orange
}
THALAMUS_COLOR = CLASS_COLORS[1]

# ── Overlay font ─────────────────────────────────────────────────────
OVERLAY_FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/SFPro.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux (Debian/Ubuntu — installed via packages.txt)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
OVERLAY_FONT_SIZE = 14

# ── Training threshold ────────────────────────────────────────────────
TRAINING_THRESHOLD = 50

# ── Model inference ───────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.25
