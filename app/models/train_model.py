#!/usr/bin/env python3
"""Fine-tune YOLOv8n on the CSP dataset."""

import sys
import shutil
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DATASET_DIR, MODEL_DIR
from ultralytics import YOLO


def _get_device() -> str:
    """Auto-detect best available device: cuda > mps > cpu."""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    dataset_yaml = DATASET_DIR / "dataset.yaml"
    if not dataset_yaml.exists():
        print("ERROR: dataset.yaml not found. Run data/prepare_dataset.py first.")
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Load pretrained YOLOv8n
    model = YOLO("yolov8n.pt")

    # Fine-tune
    results = model.train(
        data=str(dataset_yaml),
        epochs=50,
        imgsz=640,
        device=_get_device(),
        patience=10,
        project=str(MODEL_DIR / "runs"),
        name="csp_finetune",
        exist_ok=True,
    )

    # Copy best weights
    best_src = Path(results.save_dir) / "weights" / "best.pt"
    best_dst = MODEL_DIR / "best.pt"
    if best_src.exists():
        shutil.copy2(best_src, best_dst)
        print(f"Best model copied to {best_dst}")
    else:
        print("WARNING: best.pt not found in training output")


if __name__ == "__main__":
    main()
