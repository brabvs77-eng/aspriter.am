#!/usr/bin/env python3
"""Export products.json to PrestaShop-compatible CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def clean_price(value: str | None) -> str:
    if not value:
        return "0.00"
    try:
        price = float(value)
        # Filter obvious extraction errors (e.g. mis-parsed list prices)
        if price > 100_000:
            return "0.00"
        return f"{price:.2f}"
    except ValueError:
        return "0.00"


def clean_text(text: str | None, max_len: int = 8000) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def image_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path.replace("large_default", "home_default")
    return f"https://aspriter.am{path}".replace("large_default", "home_default")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export catalog to PrestaShop CSV")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "products.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "products-prestashop.csv")
    args = parser.parse_args()

    products = json.loads(args.input.read_text(encoding="utf-8"))

    # PrestaShop 8.x import columns (common subset)
    fieldnames = [
        "ID",
        "Active",
        "Name",
        "Categories",
        "Price tax included",
        "Tax rules ID",
        "Reference",
        "Description",
        "Short description",
        "Weight",
        "Image URLs",
        "URL rewritten",
    ]

    rows = []
    for p in products:
        cat = str(p.get("category_id") or "")
        slug = (p.get("slug") or "").strip("/").replace(".html", "")
        rows.append(
            {
                "ID": p.get("product_id", ""),
                "Active": "1",
                "Name": p.get("name", ""),
                "Categories": cat,
                "Price tax included": clean_price(p.get("price")),
                "Tax rules ID": "1",
                "Reference": p.get("reference", ""),
                "Description": clean_text(p.get("description_full") or p.get("description")),
                "Short description": clean_text(p.get("description"), 400),
                "Weight": p.get("weight") or "",
                "Image URLs": image_url(p.get("image")),
                "URL rewritten": slug,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} products → {args.output}")


if __name__ == "__main__":
    main()
