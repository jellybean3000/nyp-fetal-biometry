from PIL import Image, ImageDraw, ImageFont
from backend.config import (
    ANNOTATION_CLASS_MAP, CLASS_COLORS,
    OVERLAY_FONT_CANDIDATES, OVERLAY_FONT_SIZE,
)
from backend.drawing import yolo_to_pixel


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try platform font candidates, falling back to Pillow's built-in default."""
    for path in OVERLAY_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size=size)


def draw_boxes_on_image(
    image: Image.Image,
    boxes: list[dict],
    show_confidence: bool = False,
) -> Image.Image:
    """Draw refined bounding boxes with semi-transparent label backgrounds."""
    img = image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    img_w, img_h = img.size

    font = _load_font(OVERLAY_FONT_SIZE)

    for box in boxes:
        cls_id = box["class_id"]
        r, g, b = CLASS_COLORS.get(cls_id, (255, 255, 255))
        x1, y1, x2, y2 = yolo_to_pixel(box, img_w, img_h)

        # Semi-transparent fill
        draw.rectangle([x1, y1, x2, y2], fill=(r, g, b, 30))
        # Thin outline
        draw.rectangle([x1, y1, x2, y2], outline=(r, g, b, 220), width=2)

        # Label text
        label = ANNOTATION_CLASS_MAP.get(cls_id, f"cls_{cls_id}")
        if show_confidence and "confidence" in box:
            label += f"  {box['confidence']:.0%}"

        # Label background — semi-transparent rounded rectangle
        bbox = draw.textbbox((x1 + 4, y1 - 22), label, font=font)
        pad = 4
        lx0 = bbox[0] - pad
        ly0 = bbox[1] - pad
        lx1 = bbox[2] + pad
        ly1 = bbox[3] + pad
        draw.rounded_rectangle(
            [lx0, ly0, lx1, ly1],
            radius=4,
            fill=(r, g, b, 180),
        )
        draw.text((bbox[0], bbox[1]), label, fill=(255, 255, 255, 255), font=font)

    composited = Image.alpha_composite(img, overlay)
    return composited.convert("RGB")
