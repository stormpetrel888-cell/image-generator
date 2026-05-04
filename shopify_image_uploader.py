#!/usr/bin/env python3
"""
Shopify Image Uploader

Uploads processed images to a Shopify product through the Admin GraphQL API.

Required environment variables:
  SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
  SHOPIFY_ADMIN_ACCESS_TOKEN=shpat_xxx

Example:
  python shopify_image_uploader.py \
    --product-id gid://shopify/Product/9025890287771 \
    --image output/shopify/fire-in-the-sky-shopify-2048.jpg

Note:
  Shopify GraphQL productCreateMedia requires a staged/public image URL.
  Local files cannot be sent directly to Shopify Admin GraphQL.
  This script includes a dry-run mode and a URL mode for hosted files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


GRAPHQL_MUTATION = """
mutation ProductCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
  productCreateMedia(productId: $productId, media: $media) {
    media {
      alt
      mediaContentType
      status
    }
    mediaUserErrors {
      field
      message
    }
    product {
      id
      title
    }
  }
}
"""


def graphql_request(store_domain: str, token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    url = f"https://{store_domain}/admin/api/2025-01/graphql.json"
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        },
        json={"query": query, "variables": variables},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def upload_hosted_image(product_id: str, image_url: str, alt: str, dry_run: bool) -> None:
    store_domain = os.environ.get("SHOPIFY_STORE_DOMAIN")
    token = os.environ.get("SHOPIFY_ADMIN_ACCESS_TOKEN")

    variables = {
        "productId": product_id,
        "media": [
            {
                "mediaContentType": "IMAGE",
                "originalSource": image_url,
                "alt": alt,
            }
        ],
    }

    if dry_run:
        print(json.dumps({"query": GRAPHQL_MUTATION, "variables": variables}, indent=2))
        return

    if not store_domain or not token:
        raise RuntimeError("Missing SHOPIFY_STORE_DOMAIN or SHOPIFY_ADMIN_ACCESS_TOKEN environment variable.")

    result = graphql_request(store_domain, token, GRAPHQL_MUTATION, variables)
    print(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach hosted images to a Shopify product.")
    parser.add_argument("--product-id", required=True, help="Shopify product GID, e.g. gid://shopify/Product/123")
    parser.add_argument("--image-url", help="Public HTTPS image URL to attach to the product.")
    parser.add_argument("--image", help="Local image path. Used for validation only; Shopify needs a hosted URL.")
    parser.add_argument("--alt", default="Product image", help="Alt text for the image.")
    parser.add_argument("--dry-run", action="store_true", help="Print GraphQL payload without sending it.")
    args = parser.parse_args()

    if args.image and not Path(args.image).exists():
        print(f"Local image not found: {args.image}", file=sys.stderr)
        return 2

    if args.image and not args.image_url:
        print(
            "Local image detected. Shopify needs a hosted/public URL. "
            "Upload the image to Shopify Files, GitHub release assets, S3, or another public HTTPS host, "
            "then rerun with --image-url.",
            file=sys.stderr,
        )
        return 2

    if not args.image_url:
        print("Provide --image-url.", file=sys.stderr)
        return 2

    upload_hosted_image(args.product_id, args.image_url, args.alt, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
