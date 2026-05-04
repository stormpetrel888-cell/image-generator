#!/usr/bin/env python3
"""
Mockup Generator

Creates simple merch mockups for Shopify product photos and social posts.
Works with either text slogans or a transparent artwork/logo image.

Examples:
  python mockup_generator.py --text "BOOM!\nUNBELIEVABLE!" --product tee --brand "Miss Major Slots"
  python mockup_generator.py --text "BACK TO BACK" --product hoodie --brand "Miss Major Slots"
  python mockup_generator.py --artwork input/logo.png --product mug --brand "Miss Major Slots"

Outputs:
  output/mockups/*.jpg
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

CANVAS_SIZE = (1800, 1800)
BACKGROUND = (245, 245, 242)
TEXT_DARK = (18, 18, 18)
TEXT_LIGHT = (255, 255, 255)
SHADOW = (0, 0, 0, 70)

PRODUCT_COLORS = {
    "black": (18, 18, 18),
    "charcoal": (54, 54, 54),
    "white": (245, 245, 240),
    "red": (130, 20, 28),
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "mockup"


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, fill, max_size: int = 140) -> None:
    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    lines = text.split("\\n")

    font_size = max_size
    while font_size > 20:
        font = load_font(font_size, bold=True)
        line_boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
        text_w = max(b[2] - b[0] for b in line_boxes)
        line_h = max(b[3] - b[1] for b in line_boxes)
        total_h = len(lines) * line_h + (len(lines) - 1) * int(font_size * 0.25)
        if text_w <= max_w and total_h <= max_h:
            break
        font_size -= 4

    font = load_font(font_size, bold=True)
    line_gap = int(font_size * 0.25)
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    total_h = sum(line_heights) + line_gap * (len(lines) - 1)
    y = y1 + (max_h - total_h) // 2

    for line, line_h in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = x1 + (max_w - line_w) // 2
        draw.text((x + 4, y + 4), line, fill=(0, 0, 0, 90), font=font)
        draw.text((x, y), line, fill=fill, font=font)
        y += line_h + line_gap


def paste_artwork(canvas: Image.Image, artwork_path: str, box: Tuple[int, int, int, int]) -> None:
    artwork = Image.open(artwork_path).convert("RGBA")
    x1, y1, x2, y2 = box
    fitted = ImageOps.contain(artwork, (x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    x = x1 + ((x2 - x1) - fitted.width) // 2
    y = y1 + ((y2 - y1) - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))


def add_header_footer(canvas: Image.Image, brand: str, product_label: str) -> None:
    draw = ImageDraw.Draw(canvas)
    font = load_font(46, bold=True)
    small = load_font(28, bold=False)
    draw.text((90, 78), brand, fill=TEXT_DARK, font=font)
    draw.text((90, 134), product_label, fill=(95, 95, 95), font=small)
    draw.text((90, 1680), "Preview mockup — verify final placement in Printify", fill=(120, 120, 120), font=small)


def draw_tee(canvas: Image.Image, text: str, artwork: str | None, color: str, brand: str) -> None:
    garment = PRODUCT_COLORS.get(color, PRODUCT_COLORS["black"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    # torso
    draw.rounded_rectangle((470, 360, 1330, 1500), radius=120, fill=garment)
    # sleeves
    draw.polygon([(470, 410), (245, 650), (390, 850), (555, 610)], fill=garment)
    draw.polygon([(1330, 410), (1555, 650), (1410, 850), (1245, 610)], fill=garment)
    # neck
    draw.ellipse((735, 300, 1065, 520), fill=BACKGROUND)
    draw.ellipse((785, 335, 1015, 490), fill=garment)
    # soft shadow
    draw.ellipse((400, 1460, 1400, 1585), fill=(0, 0, 0, 35))

    area = (650, 620, 1150, 1040)
    if artwork:
        paste_artwork(canvas, artwork, area)
    else:
        draw_centered_text(draw, area, text, TEXT_LIGHT if color != "white" else TEXT_DARK, 116)
    add_header_footer(canvas, brand, f"{color.title()} tee mockup")


def draw_hoodie(canvas: Image.Image, text: str, artwork: str | None, color: str, brand: str) -> None:
    garment = PRODUCT_COLORS.get(color, PRODUCT_COLORS["charcoal"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((455, 420, 1345, 1520), radius=160, fill=garment)
    draw.ellipse((610, 245, 1190, 680), fill=garment)
    draw.ellipse((720, 340, 1080, 660), fill=BACKGROUND)
    draw.rectangle((650, 500, 1150, 760), fill=garment)
    draw.polygon([(455, 510), (250, 850), (410, 1030), (570, 690)], fill=garment)
    draw.polygon([(1345, 510), (1550, 850), (1390, 1030), (1230, 690)], fill=garment)
    draw.rounded_rectangle((680, 1180, 1120, 1360), radius=55, fill=tuple(max(0, c - 25) for c in garment))
    draw.line((800, 560, 830, 780), fill=(230, 230, 230, 170), width=8)
    draw.line((1000, 560, 970, 780), fill=(230, 230, 230, 170), width=8)
    draw.ellipse((390, 1480, 1410, 1605), fill=(0, 0, 0, 35))

    area = (635, 720, 1165, 1100)
    if artwork:
        paste_artwork(canvas, artwork, area)
    else:
        draw_centered_text(draw, area, text, TEXT_LIGHT if color != "white" else TEXT_DARK, 108)
    add_header_footer(canvas, brand, f"{color.title()} hoodie mockup")


def draw_mug(canvas: Image.Image, text: str, artwork: str | None, color: str, brand: str) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    mug = (248, 248, 244) if color == "white" else PRODUCT_COLORS.get(color, PRODUCT_COLORS["white"])
    draw.rounded_rectangle((540, 520, 1180, 1320), radius=80, fill=mug)
    draw.ellipse((500, 470, 1220, 620), fill=mug)
    draw.ellipse((540, 505, 1180, 600), fill=(220, 220, 215))
    draw.arc((1110, 710, 1480, 1120), start=-80, end=85, fill=mug, width=90)
    draw.arc((1180, 790, 1390, 1040), start=-80, end=85, fill=BACKGROUND, width=90)
    draw.ellipse((450, 1290, 1280, 1430), fill=(0, 0, 0, 35))

    area = (650, 735, 1070, 1075)
    fill = TEXT_DARK if color == "white" else TEXT_LIGHT
    if artwork:
        paste_artwork(canvas, artwork, area)
    else:
        draw_centered_text(draw, area, text, fill, 92)
    add_header_footer(canvas, brand, f"{color.title()} mug mockup")


def draw_sticker(canvas: Image.Image, text: str, artwork: str | None, color: str, brand: str) -> None:
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((430, 520, 1370, 1180), radius=90, fill=(255, 255, 255), outline=(20, 20, 20), width=10)
    draw.rounded_rectangle((465, 555, 1335, 1145), radius=70, fill=PRODUCT_COLORS.get(color, PRODUCT_COLORS["red"]))
    area = (560, 670, 1240, 1030)
    if artwork:
        paste_artwork(canvas, artwork, area)
    else:
        draw_centered_text(draw, area, text, TEXT_LIGHT, 126)
    draw.ellipse((470, 1160, 1330, 1295), fill=(0, 0, 0, 30))
    add_header_footer(canvas, brand, f"{color.title()} sticker mockup")


def create_mockup(product: str, text: str, artwork: str | None, color: str, brand: str, output_dir: Path) -> Path:
    canvas = Image.new("RGBA", CANVAS_SIZE, BACKGROUND + (255,))
    if product == "tee":
        draw_tee(canvas, text, artwork, color, brand)
    elif product == "hoodie":
        draw_hoodie(canvas, text, artwork, color, brand)
    elif product == "mug":
        draw_mug(canvas, text, artwork, color, brand)
    elif product == "sticker":
        draw_sticker(canvas, text, artwork, color, brand)
    else:
        raise ValueError(f"Unsupported product: {product}")

    rgb = canvas.convert("RGB")
    output_dir.mkdir(parents=True, exist_ok=True)
    name_seed = Path(artwork).stem if artwork else slugify(text.replace("\\n", " "))
    path = output_dir / f"{name_seed}-{product}-{color}-mockup.jpg"
    rgb.save(path, "JPEG", quality=90, optimize=True, progressive=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate simple merch mockups.")
    parser.add_argument("--text", default="MISS MAJOR\nSLOTS", help="Mockup slogan text. Use quoted text; \\n creates lines.")
    parser.add_argument("--artwork", help="Optional transparent PNG/logo/artwork file.")
    parser.add_argument("--product", choices=["tee", "hoodie", "mug", "sticker", "all"], default="all")
    parser.add_argument("--color", choices=list(PRODUCT_COLORS.keys()) + ["all"], default="black")
    parser.add_argument("--brand", default="Miss Major Slots")
    parser.add_argument("--output", default="output/mockups")
    args = parser.parse_args()

    text = args.text.replace("\\n", "\n")
    products = ["tee", "hoodie", "mug", "sticker"] if args.product == "all" else [args.product]
    colors = ["black", "charcoal", "white", "red"] if args.color == "all" else [args.color]

    if args.artwork and not Path(args.artwork).exists():
        raise FileNotFoundError(args.artwork)

    output_dir = Path(args.output)
    made = []
    for product in products:
        for color in colors:
            # mugs/stickers usually need fewer color passes, but keep all available for testing.
            made.append(create_mockup(product, text, args.artwork, color, args.brand, output_dir))

    print("Generated mockups:")
    for path in made:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
