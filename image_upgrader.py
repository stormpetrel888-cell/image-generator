#!/usr/bin/env python3
"""
Image Upgrader

Batch-process raw photos into Shopify-ready product images, social crops,
and Printify-friendly source exports.

Usage:
  python image_upgrader.py --input input --output output --watermark "DealzMart.ca"
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "image"


def iter_images(input_dir: Path) -> Iterable[Path]:
    for path in sorted(input_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def enhance_image(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.06)
    img = ImageEnhance.Sharpness(img).enhance(1.12)
    return img


def fit_square(img: Image.Image, size: int = 2048, background=(255, 255, 255)) -> Image.Image:
    canvas = Image.new("RGB", (size, size), background)
    fitted = ImageOps.contain(img, (size, size), Image.Resampling.LANCZOS)
    x = (size - fitted.width) // 2
    y = (size - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def crop_cover(img: Image.Image, width: int, height: int) -> Image.Image:
    return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def add_watermark(img: Image.Image, text: str) -> Image.Image:
    if not text:
        return img
    out = img.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", max(22, out.width // 48))
    except OSError:
        font = ImageFont.load_default()
    margin = max(24, out.width // 40)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = out.width - text_w - margin
    y = out.height - text_h - margin
    pad = max(10, out.width // 200)
    draw.rounded_rectangle((x - pad, y - pad, x + text_w + pad, y + text_h + pad), radius=pad, fill=(255, 255, 255))
    draw.text((x, y), text, fill=(20, 20, 20), font=font)
    return out


def save_jpeg(img: Image.Image, path: Path, quality: int = 88) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


def save_webp(img: Image.Image, path: Path, quality: int = 86) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=quality, method=6)


def process_image(path: Path, output_dir: Path, watermark: str) -> None:
    base = slugify(path.stem)
    original = load_image(path)
    enhanced = enhance_image(original)

    shopify = fit_square(enhanced, 2048)
    shopify = add_watermark(shopify, watermark)
    save_jpeg(shopify, output_dir / "shopify" / f"{base}-shopify-2048.jpg")
    save_webp(shopify, output_dir / "shopify" / f"{base}-shopify-2048.webp")

    social = crop_cover(enhanced, 1080, 1350)
    social = add_watermark(social, watermark)
    save_jpeg(social, output_dir / "social" / f"{base}-social-1080x1350.jpg")

    banner = crop_cover(enhanced, 1600, 900)
    banner = add_watermark(banner, watermark)
    save_jpeg(banner, output_dir / "social" / f"{base}-banner-1600x900.jpg")

    printify = fit_square(enhanced, 3000)
    save_jpeg(printify, output_dir / "printify" / f"{base}-printify-source-3000.jpg", quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch upgrade photos for Shopify and merch workflows.")
    parser.add_argument("--input", default="input", help="Input folder containing raw images.")
    parser.add_argument("--output", default="output", help="Output folder for processed images.")
    parser.add_argument("--watermark", default="", help="Optional watermark text.")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created {input_dir}. Add images there and run again.")
        return 0

    images = list(iter_images(input_dir))
    if not images:
        print(f"No supported images found in {input_dir}.")
        return 0

    for image_path in images:
        print(f"Processing {image_path}")
        process_image(image_path, output_dir, args.watermark)

    print(f"Done. Upgraded images saved in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
