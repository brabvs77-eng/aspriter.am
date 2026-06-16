#!/usr/bin/env python3
"""Extract product catalog data from archived PrestaShop HTML pages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent


def extract_from_html(html: str, source_url: str = "") -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    # Open Graph product meta tags (most reliable on archived pages)
    def og(prop: str) -> str | None:
        tag = soup.find("meta", property=prop)
        return tag["content"].strip() if tag and tag.get("content") else None

    name = og("og:title")
    if not name:
        title = soup.find("title")
        name = title.get_text(strip=True) if title else None
    if not name:
        return None

    product: dict = {
        "name": name,
        "url": og("og:url") or source_url,
        "description": og("og:description") or "",
        "image": og("og:image"),
        "price": og("product:price:amount"),
        "price_currency": og("product:price:currency") or "EUR",
        "pretax_price": og("product:pretax_price:amount"),
        "weight": og("product:weight:value"),
        "weight_unit": og("product:weight:units"),
    }

    # Reference / SKU from page body
    ref_match = re.search(r"Reference:\s*([^\s<]+)", html, re.I)
    if ref_match:
        product["reference"] = ref_match.group(1).strip()

    # Product ID from body class: product-id-912
    id_match = re.search(r"product-id-(\d+)", html)
    if id_match:
        product["product_id"] = int(id_match.group(1))

    # Category from breadcrumb or body class product-id-category-86
    cat_id_match = re.search(r"product-id-category-(\d+)", html)
    if cat_id_match:
        product["category_id"] = int(cat_id_match.group(1))

    breadcrumb = soup.select_one(".breadcrumb a, nav.breadcrumb a")
    categories = [a.get_text(strip=True) for a in soup.select(".breadcrumb a, nav.breadcrumb a")]
    if len(categories) > 1:
        product["category_path"] = categories[1:]

    # Long description
    desc_el = soup.select_one("#product-description-full, .product-description")
    if desc_el:
        product["description_full"] = desc_el.get_text("\n", strip=True)

    # Additional images from gallery
    images = []
    for img in soup.select("[data-image-large-src], .product-cover img, .js-thumb"):
        src = img.get("data-image-large-src") or img.get("src") or img.get("data-src")
        if src and "aspriter.am" in src or (src and src.startswith("/")):
            images.append(src.replace("https://aspriter.am", "").replace("https://www.aspriter.am", ""))
    if images:
        product["images"] = list(dict.fromkeys(images))

    # Canonical URL slug
    if product.get("url"):
        product["slug"] = urlparse(product["url"]).path

    return product


def extract_from_mirror(mirror_dir: Path) -> list[dict]:
    products = []
    patterns = ["**/*.html"]
    seen_ids: set[int] = set()

    for pattern in patterns:
        for path in mirror_dir.glob(pattern):
            if "product-id" not in path.read_text(encoding="utf-8", errors="ignore")[:8000]:
                # Quick filter: skip non-product pages
                text_head = path.read_text(encoding="utf-8", errors="ignore")[:3000]
                if 'og:type" content="product"' not in text_head and "page-product" not in text_head:
                    continue
            html = path.read_text(encoding="utf-8", errors="replace")
            item = extract_from_html(html, source_url="/" + str(path.relative_to(mirror_dir)))
            if not item:
                continue
            pid = item.get("product_id")
            if pid and pid in seen_ids:
                continue
            if pid:
                seen_ids.add(pid)
            products.append(item)

    return sorted(products, key=lambda p: p.get("product_id") or 0)


def extract_from_url_list(list_file: Path, snapshot: str, limit: int | None, delay: float) -> list[dict]:
    import time

    import requests

    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0"
    products = []
    urls = [l.split("\t")[0].strip() for l in list_file.read_text().splitlines() if l.strip()]

    if limit:
        urls = urls[:limit]

    for url in urls:
        wb = f"https://web.archive.org/web/{snapshot}id_/{url}"
        try:
            resp = session.get(wb, timeout=60)
            if resp.status_code != 200:
                print(f"  SKIP {resp.status_code} {url}", file=sys.stderr)
                continue
            item = extract_from_html(resp.text, source_url=url)
            if item:
                products.append(item)
                print(f"  OK {item.get('product_id')} {item.get('name')}")
        except requests.RequestException as exc:
            print(f"  ERR {url}: {exc}", file=sys.stderr)
        time.sleep(delay)

    return products


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PrestaShop products from archived HTML")
    parser.add_argument("--mirror", type=Path, default=ROOT / "mirror", help="Local mirror directory")
    parser.add_argument("--list", type=Path, help="product-pages.txt for live Wayback fetch")
    parser.add_argument("--snapshot", default="20230321042548")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "products.json")
    args = parser.parse_args()

    if args.list:
        if not args.list.exists():
            print(f"List not found: {args.list}", file=sys.stderr)
            sys.exit(1)
        products = extract_from_url_list(args.list, args.snapshot, args.limit, args.delay)
    elif args.mirror.exists():
        products = extract_from_mirror(args.mirror)
    else:
        print("No mirror or URL list found.", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nExtracted {len(products)} products → {args.output}")


if __name__ == "__main__":
    main()
