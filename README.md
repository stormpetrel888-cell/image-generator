# Image Upgrader

Automates image prep for Shopify, Printify, and social.

## Usage

1. Drop raw images into /input
2. Run:
   python image_upgrader.py --watermark "DealzMart.ca"
3. Get outputs in /output folders

## Output
- shopify/ (2048px optimized product images)
- social/ (1080x1350, 1600x900)
- printify/ (3000px high-res)

## Next upgrades
- background removal
- auto upload to Shopify
- mockup generator
