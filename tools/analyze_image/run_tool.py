#!/usr/bin/env python3
"""
Simple script to run the annotator on image.png and save results.

Usage:
    python run_annotator.py [--mag-limit 12.0] [--radius 1.5]
"""

import json
import argparse
from PIL import Image
from tools.analyze_image.analyze_image_tool import analyze_image


def main():
    parser = argparse.ArgumentParser(description="Run annotator on image.png")
    parser.add_argument("--mag-limit", type=float, default=12.0, help="Magnitude limit (default: 12.0)")
    parser.add_argument("--radius", type=float, default=None, help="Search radius in degrees (default: auto)")
    parser.add_argument("--input", default="files/image.png", help="Input image path (default: image.png)")
    args = parser.parse_args()

    print(f"Loading image: {args.input}")
    img = Image.open(args.input)
    print(f"Image size: {img.size}")
    print()

    result = analyze_image(img, radius=args.radius, mag_limit=args.mag_limit, verbose=True)

    if not result["success"]:
        print(f"\nError: {result['error']}")
        return 1

    # Save annotated image
    output_image = "files/image_annotated.png"
    result["annotated_image"].save(output_image)
    print(f"\nSaved annotated image to: {output_image}")

    # Save JSON results
    output_json = "files/image_results.json"
    json_data = {
        "plate_solving": result["plate_solving"],
        "objects": result["objects"]
    }
    with open(output_json, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"Saved results to: {output_json}")

    return 0


if __name__ == "__main__":
    exit(main())

