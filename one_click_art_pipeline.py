#!/usr/bin/env python3
"""
One-Click Art Pipeline

Drop images into input/ai-art or input/outlaw-art, run one command, and get:
- upgraded Shopify-ready images
- before/after showcase images when originals + processed files exist
- product CSV ready for Shopify import or review
- Shopify API payload draft data for later automation

This intentionally creates draft-ready product data first. Review before publishing.

Examples:
  python one_click_art_pipeline.py --collection ai-art --vendor "Solaryn Grey"
  python one_click_art_pipeline.py --collection outlaw-art --vendor "Outlaw Photography" --before-after
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

COLLECTION_PRESETS = {
    "ai-art": {
        "product_type": "Digital Art Download",
        "vendor": "Solaryn Grey",
        "price": "9.99",
        "tags": ["AI Art", "Solaryn Gallery", "Digital Download", "Wall Art"],
        "title_prefix": "Signal Series",
        "description": "A Solaryn Grey AI art piece prepared for digital display, wall art concepts, and collector-style gallery drops.",
    },
    "outlaw-art": {
        "product_type": "Art Print",
        "vendor": "Outlaw Photography",
        "price": "19.99",
        "tags": ["Outlaw Art", "Photography", "Art Print", "Wall Art"],
        "title_prefix": "Outlaw Frame",
        "description": "Raw Outlaw Photography upgraded for product-ready presentation, wall art, and before/after showcase storytelling.",
    },
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "art-product"


def titleize(path: Path, prefix: str, index: int) -> str:
    raw = re.sub(r"[_-]+", " ", path.stem).strip()
    raw = re.sub(r"\s+", " ", raw)
    if raw and not raw.lower().startswith(("img", "dsc", "image", "photo")):
        return raw.title()
    return f"{prefix} #{index:03d}"


def iter_images(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []
    return [p for p in sorted(folder.rglob("*")) if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]


def run_image_upgrader(input_dir: Path, output_dir: Path, watermark: str) -> None:
    cmd = [sys.executable, "image_upgrader.py", "--input", str(input_dir), "--output", str(output_dir)]
    if watermark:
        cmd += ["--watermark", watermark]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def find_processed_image(output_dir: Path, original: Path) -> Path | None:
    stem = slugify(original.stem)
    candidates = sorted((output_dir / "shopify").glob(f"{stem}*-shopify-2048.jpg"))
    if candidates:
        return candidates[0]
    candidates = sorted((output_dir / "shopify").glob(f"{stem}*.jpg"))
    return candidates[0] if candidates else None


def write_product_csv(rows: list[dict], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "Handle", "Title", "Body (HTML)", "Vendor", "Product Category", "Type", "Tags", "Published",
        "Option1 Name", "Option1 Value", "Variant SKU", "Variant Price", "Variant Inventory Policy",
        "Image Src", "Image Alt Text", "Status"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_api_payload(rows: list[dict], payload_path: Path) -> None:
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payloads = []
    for row in rows:
        tags = [tag.strip() for tag in row["Tags"].split(",") if tag.strip()]
        payloads.append({
            "title": row["Title"],
            "descriptionHtml": row["Body (HTML)"],
            "vendor": row["Vendor"],
            "productType": row["Type"],
            "status": "DRAFT",
            "tags": tags,
            "options": ["Title"],
            "variants": [{
                "title": "Default Title",
                "price": row["Variant Price"],
                "sku": row["Variant SKU"],
                "optionValues": [{"optionName": "Title", "name": "Default Title"}],
            }],
            "imagePathForManualUpload": row["Image Src"],
            "collectionHandle": row.get("Collection Handle", ""),
        })
    payload_path.write_text(json.dumps(payloads, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Process art images and generate Shopify product drafts.")
    parser.add_argument("--collection", choices=COLLECTION_PRESETS.keys(), required=True)
    parser.add_argument("--input", help="Input folder. Defaults to input/<collection>.")
    parser.add_argument("--output", default="output/pipeline", help="Output root folder.")
    parser.add_argument("--vendor", help="Override vendor name.")
    parser.add_argument("--price", help="Override product price.")
    parser.add_argument("--watermark", default="DealzMart.ca")
    parser.add_argument("--before-after", action="store_true", help="Also generate before/after showcases.")
    args = parser.parse_args()

    preset = COLLECTION_PRESETS[args.collection]
    input_dir = Path(args.input or f"input/{args.collection}")
    output_root = Path(args.output) / args.collection
    products_dir = output_root / "products"

    images = list(iter_images(input_dir))
    if not images:
        input_dir.mkdir(parents=True, exist_ok=True)
        print(f"No images found. Add files to {input_dir} and rerun.")
        return 0

    run_image_upgrader(input_dir, products_dir, args.watermark)

    rows = []
    vendor = args.vendor or preset["vendor"]
    price = args.price or preset["price"]

    for idx, original in enumerate(images, start=1):
        title = titleize(original, preset["title_prefix"], idx)
        handle = slugify(title)
        processed = find_processed_image(products_dir, original)
        image_src = str(processed) if processed else str(original)
        sku = f"{args.collection.upper().replace('-', '')}-{idx:03d}"
        body = (
            f"<h2>{title}</h2>"
            f"<p>{preset['description']}</p>"
            f"<p>This draft was generated by the one-click art pipeline. Review title, pricing, images, and fulfillment before publishing.</p>"
        )
        rows.append({
            "Handle": handle,
            "Title": title,
            "Body (HTML)": body,
            "Vendor": vendor,
            "Product Category": "",
            "Type": preset["product_type"],
            "Tags": ", ".join(preset["tags"]),
            "Published": "FALSE",
            "Option1 Name": "Title",
            "Option1 Value": "Default Title",
            "Variant SKU": sku,
            "Variant Price": price,
            "Variant Inventory Policy": "deny",
            "Image Src": image_src,
            "Image Alt Text": title,
            "Status": "draft",
            "Collection Handle": args.collection,
        })

        if args.before_after and processed:
            cmd = [
                sys.executable,
                "dedupe_and_before_after.py",
                "--before", str(original),
                "--after", str(processed),
                "--title", title,
                "--output", str(output_root / "before-after"),
            ]
            print("Running:", " ".join(cmd))
            subprocess.run(cmd, check=True)

    write_product_csv(rows, output_root / f"{args.collection}-shopify-products.csv")
    write_api_payload(rows, output_root / f"{args.collection}-draft-product-payloads.json")

    print(f"Generated {len(rows)} product drafts.")
    print(f"CSV: {output_root / f'{args.collection}-shopify-products.csv'}")
    print(f"API draft payloads: {output_root / f'{args.collection}-draft-product-payloads.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
