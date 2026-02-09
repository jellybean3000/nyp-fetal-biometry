#!/usr/bin/env python3
"""Prepare Trans-thalamic dataset for YOLOv8 CSP detection training.

Extracts YOLO labels from Trans-thalamic-YOLO.zip, keeps only CSP (class 1 → 0),
matches to original-size images, splits 80/20 train/val with ~200 negative examples.
"""

import os
import sys
import random
import shutil
import zipfile
from pathlib import Path

# Allow importing from app root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import DATASET_DIR

SEED = 42
TRAIN_RATIO = 0.8
NUM_NEGATIVES = 200

# Source paths
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
TT_IMAGES_DIR = PROJECT_DIR / "Trans-thalamic-orginal-size"
TT_YOLO_ZIP = PROJECT_DIR / "Trans-thalamic" / "Trans-thalamic-YOLO.zip"

# Output directories
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"

# Source class IDs (from obj.names: 0=Brain, 1=CSP, 2=LV)
SOURCE_CSP_ID = 1


def main():
    # Validate source paths
    if not TT_IMAGES_DIR.exists():
        print(f"ERROR: Image directory not found: {TT_IMAGES_DIR}")
        sys.exit(1)
    if not TT_YOLO_ZIP.exists():
        print(f"ERROR: YOLO zip not found: {TT_YOLO_ZIP}")
        sys.exit(1)

    # Clean output directories
    for d in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    # Extract labels from zip into a dict: stem → list of lines
    print("Extracting labels from Trans-thalamic-YOLO.zip...")
    labels_by_stem = {}
    with zipfile.ZipFile(TT_YOLO_ZIP, "r") as zf:
        for name in zf.namelist():
            if not name.startswith("obj_train_data/") or not name.endswith(".txt"):
                continue
            stem = Path(name).stem
            content = zf.read(name).decode("utf-8").strip()
            labels_by_stem[stem] = content

    print(f"Extracted {len(labels_by_stem)} label files from zip")

    # Build available images index
    all_images = {p.stem: p for p in sorted(TT_IMAGES_DIR.glob("*.png"))}
    print(f"Found {len(all_images)} original-size images")

    # Filter labels: keep only CSP (class 1), remap to class 0
    csp_positive_stems = []
    remapped_labels = {}  # stem → list of remapped lines

    for stem, content in labels_by_stem.items():
        if stem not in all_images:
            continue
        csp_lines = []
        for line in content.splitlines():
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            cls_id = int(parts[0])
            if cls_id == SOURCE_CSP_ID:
                # Remap CSP: 1 → 0
                csp_lines.append(f"0 {parts[1]} {parts[2]} {parts[3]} {parts[4]}")

        if csp_lines:
            csp_positive_stems.append(stem)
            remapped_labels[stem] = csp_lines

    print(f"CSP-positive images: {len(csp_positive_stems)}")

    # Collect negative examples (images in source that have NO CSP labels)
    negative_candidates = []
    for stem in all_images:
        if stem not in remapped_labels:
            negative_candidates.append(stem)

    random.seed(SEED)
    num_neg = min(NUM_NEGATIVES, len(negative_candidates))
    negative_stems = random.sample(negative_candidates, num_neg)
    print(f"Negative examples selected: {num_neg}")

    # Combine and split
    all_stems = csp_positive_stems + negative_stems
    random.seed(SEED)
    random.shuffle(all_stems)

    split_idx = int(len(all_stems) * TRAIN_RATIO)
    train_stems = set(all_stems[:split_idx])
    val_stems = set(all_stems[split_idx:])

    print(f"Train: {len(train_stems)}, Val: {len(val_stems)}")

    # Copy images and labels
    train_pos = train_neg = val_pos = val_neg = 0
    for stem in all_stems:
        is_train = stem in train_stems
        img_dst_dir = IMAGES_TRAIN if is_train else IMAGES_VAL
        lbl_dst_dir = LABELS_TRAIN if is_train else LABELS_VAL

        # Copy image (use symlink for speed)
        src_img = all_images[stem]
        dst_img = img_dst_dir / src_img.name
        if not dst_img.exists():
            os.symlink(src_img.resolve(), dst_img)

        # Write label
        dst_lbl = lbl_dst_dir / f"{stem}.txt"
        if stem in remapped_labels:
            dst_lbl.write_text("\n".join(remapped_labels[stem]) + "\n")
            if is_train:
                train_pos += 1
            else:
                val_pos += 1
        else:
            # Negative example: empty label file
            dst_lbl.write_text("")
            if is_train:
                train_neg += 1
            else:
                val_neg += 1

    print(f"Train: {train_pos} positive + {train_neg} negative = {train_pos + train_neg}")
    print(f"Val:   {val_pos} positive + {val_neg} negative = {val_pos + val_neg}")

    # Write dataset.yaml
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
