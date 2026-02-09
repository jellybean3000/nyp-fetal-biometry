#!/usr/bin/env python3
"""One-time script: create train/val split with remapped annotations for YOLOv8."""

import os
import sys
import random
from pathlib import Path

# Allow importing from app root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import SOURCE_IMAGES_DIR, SOURCE_LABELS_DIR, DATASET_DIR, SOURCE_CSP_ID, SOURCE_LV_ID

SEED = 42
TRAIN_RATIO = 0.8

# Output directories
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"


def main():
    # Create output dirs
    for d in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
        d.mkdir(parents=True, exist_ok=True)

    # Gather all images
    all_images = sorted(SOURCE_IMAGES_DIR.glob("*.png"))
    print(f"Found {len(all_images)} images")

    # Shuffle and split
    random.seed(SEED)
    indices = list(range(len(all_images)))
    random.shuffle(indices)
    split = int(len(indices) * TRAIN_RATIO)
    train_indices = set(indices[:split])

    train_count = 0
    val_count = 0

    for i, img_path in enumerate(all_images):
        is_train = i in train_indices
        img_dst_dir = IMAGES_TRAIN if is_train else IMAGES_VAL
        lbl_dst_dir = LABELS_TRAIN if is_train else LABELS_VAL

        # Symlink image
        dst_img = img_dst_dir / img_path.name
        if not dst_img.exists():
            os.symlink(img_path.resolve(), dst_img)

        # Remap annotations
        src_lbl = SOURCE_LABELS_DIR / img_path.with_suffix(".txt").name
        dst_lbl = lbl_dst_dir / img_path.with_suffix(".txt").name

        remapped_lines = []
        if src_lbl.exists():
            for line in src_lbl.read_text().strip().splitlines():
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                src_cls = int(parts[0])
                if src_cls == SOURCE_CSP_ID:
                    # Source CSP (id=1) → App CSP (id=0)
                    remapped_lines.append(f"0 {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
                elif src_cls == SOURCE_LV_ID:
                    # Discard LV
                    continue
                # Brain (id=0) is also discarded — not in our app classes

        dst_lbl.write_text("\n".join(remapped_lines) + "\n" if remapped_lines else "")

        if is_train:
            train_count += 1
        else:
            val_count += 1

    print(f"Train: {train_count}, Val: {val_count}")

    # Generate dataset.yaml
    yaml_path = DATASET_DIR / "dataset.yaml"
    yaml_content = f"""path: {DATASET_DIR.resolve()}
train: images/train
val: images/val

names:
  0: CSP
"""
    yaml_path.write_text(yaml_content)
    print(f"Wrote {yaml_path}")
    print("Dataset preparation complete.")


if __name__ == "__main__":
    main()
