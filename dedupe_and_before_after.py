#!/usr/bin/env python3
"""
Dedupe + Before/After Builder

Scans image folders for likely duplicates and builds before/after showcase images.
Useful for Outlaw Art / photo cleanup products where buyers need to see the upgrade.

Examples:
  python dedupe_and_before_after.py --scan input --report output/duplicate-report.csv
  python dedupe_and_before_after.py --before input/raw.jpg --after output/shopify/raw-shopify-2048.jpg --title "Fire in the Sky"

Outputs:
  output/before-after/*.jpg
  output/duplicate-report.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def iter_images(folder: Path) -> Iterable[Path]:
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def average_hash(path: Path, size: int = 8) -> str:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("L").resize((size, size), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)
    bits = ["1" if p > avg else "0" for p in pixels]
    return "".join(bits)


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def load_font(size: int, bold: bool = True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def scan_duplicates(folder: Path, report_path: Path, threshold: int = 6) -> None:
    images = list(iter_images(folder))
    exact = {}
    perceptual = []

    rows = []
    for path in images:
        exact_hash = file_hash(path)
        phash = average_hash(path)
        if exact_hash in exact:
            rows.append({"type": "exact", "image": str(path), "match": str(exact[exact_hash]), "distance": 0})
        else:
            exact[exact_hash] = path
        perceptual.append((path, phash))

    for i, (path_a, hash_a) in enumerate(perceptual):
        for path_b, hash_b in perceptual[i + 1:]:
            distance = hamming(hash_a, hash_b)
            if distance <= threshold and file_hash(path_a) != file_hash(path_b):
                rows.append({"type": "similar", "image": str(path_a), "match": str(path_b), "distance": distance})

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["type", "image", "match", "distance"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Scanned {len(images)} images. Found {len(rows)} duplicate/similar pairs.")
    print(f"Report: {report_path}")


def make_before_after(before_path: Path, after_path: Path, title: str, output_dir: Path) -> Path:
    width, height = 1800, 1200
    panel_w = 820
    panel_h = 820
    bg = Image.new("RGB", (width, height), (246, 246, 242))
    draw = ImageDraw.Draw(bg)

    title_font = load_font(64, True)
    label_font = load_font(44, True)
    note_font = load_font(28, False)

    before = Image.open(before_path)
    before = ImageOps.exif_transpose(before).convert("RGB")
    after = Image.open(after_path)
    after = ImageOps.exif_transpose(after).convert("RGB")

    before_fit = ImageOps.fit(before, (panel_w, panel_h), Image.Resampling.LANCZOS)
    after_fit = ImageOps.fit(after, (panel_w, panel_h), Image.Resampling.LANCZOS)

    draw.text((90, 70), title, fill=(20, 20, 20), font=title_font)
    draw.text((90, 155), "Before / After image upgrade showcase", fill=(90, 90, 90), font=note_font)

    before_box = (90, 250)
    after_box = (890, 250)
    bg.paste(before_fit, before_box)
    bg.paste(after_fit, after_box)

    draw.rectangle((before_box[0], before_box[1], before_box[0] + panel_w, before_box[1] + panel_h), outline=(30, 30, 30), width=4)
    draw.rectangle((after_box[0], after_box[1], after_box[0] + panel_w, after_box[1] + panel_h), outline=(30, 30, 30), width=4)
    draw.rectangle((90, 250, 90 + panel_w, 320), fill=(20, 20, 20))
    draw.rectangle((890, 250, 890 + panel_w, 320), fill=(20, 20, 20))
    draw.text((120, 262), "BEFORE", fill=(255, 255, 255), font=label_font)
    draw.text((920, 262), "AFTER", fill=(255, 255, 255), font=label_font)

    draw.text((90, 1110), "Use this image on product pages, collection banners, or social posts.", fill=(90, 90, 90), font=note_font)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c.lower() if c.isalnum() else "-" for c in title).strip("-") or "before-after"
    path = output_dir / f"{safe}-before-after.jpg"
    bg.save(path, "JPEG", quality=90, optimize=True, progressive=True)
    print(f"Created {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Find duplicate images and make before/after showcases.")
    parser.add_argument("--scan", help="Folder to scan for duplicate/similar images.")
    parser.add_argument("--report", default="output/duplicate-report.csv", help="CSV duplicate report path.")
    parser.add_argument("--threshold", type=int, default=6, help="Perceptual duplicate threshold. Lower = stricter.")
    parser.add_argument("--before", help="Before image path.")
    parser.add_argument("--after", help="After image path.")
    parser.add_argument("--title", default="Image Upgrade", help="Showcase title.")
    parser.add_argument("--output", default="output/before-after", help="Before/after output folder.")
    args = parser.parse_args()

    if args.scan:
        scan_duplicates(Path(args.scan), Path(args.report), args.threshold)

    if args.before and args.after:
        make_before_after(Path(args.before), Path(args.after), args.title, Path(args.output))

    if not args.scan and not (args.before and args.after):
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
