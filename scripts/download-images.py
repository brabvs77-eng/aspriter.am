#!/usr/bin/env python3
"""Download product images using per-URL timestamps from the CDX index."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
BASE = "https://aspriter.am"
ARCHIVE_LIST = ROOT / "data" / "archive-url-list.txt"

_spec = importlib.util.spec_from_file_location(
    "download_snapshot", Path(__file__).parent / "download-snapshot.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
local_path = _mod.local_path

SIZE_CHAIN = ("large_default", "home_default", "medium_default", "small_default")


def load_cdx_map(path: Path) -> dict[str, str]:
    """Map original URL -> best archived timestamp."""
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("http"):
            mapping[parts[0]] = parts[1]
    return mapping


def fallback_urls(url: str) -> list[str]:
    """Try alternate PrestaShop image sizes if primary is missing from archive."""
    urls = [url]
    for size in SIZE_CHAIN:
        if size in url:
            for alt in SIZE_CHAIN:
                if alt != size:
                    urls.append(url.replace(size, alt))
            break
    # Deduplicate preserving order
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def download_with_timestamp(
    session: requests.Session,
    original: str,
    timestamp: str,
    snapshot_default: str,
) -> bool:
    if original.startswith("/"):
        original = BASE + original
    if "aspriter.am" not in original:
        return False

    dest = local_path(original)
    if dest.exists() and dest.stat().st_size > 0:
        return True

    ts = timestamp or snapshot_default
    url = f"https://web.archive.org/web/{ts}im_/{original}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return False
        dest.write_bytes(resp.content)
        return True
    except requests.RequestException:
        return False


def image_urls_from_products(products_file: Path) -> list[str]:
    products = json.loads(products_file.read_text(encoding="utf-8"))
    seen: set[str] = set()
    urls: list[str] = []
    for p in products:
        for src in [p.get("image")] + (p.get("images") or []):
            if not src:
                continue
            full = src if src.startswith("http") else f"{BASE}{src}"
            if full not in seen:
                seen.add(full)
                urls.append(full)
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Download product images from Wayback")
    parser.add_argument("--products", type=Path, default=ROOT / "data" / "products.json")
    parser.add_argument("--archive", type=Path, default=ARCHIVE_LIST)
    parser.add_argument("--snapshot", default=os.environ.get("SNAPSHOT_TIMESTAMP", "20230321042548"))
    parser.add_argument("--delay", type=float, default=float(os.environ.get("REQUEST_DELAY", "0.5")))
    args = parser.parse_args()

    if not args.products.exists():
        print("products.json not found.", file=sys.stderr)
        sys.exit(1)
    if not args.archive.exists():
        print("archive-url-list.txt not found.", file=sys.stderr)
        sys.exit(1)

    cdx = load_cdx_map(args.archive)
    targets = image_urls_from_products(args.products)
    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    print(f"Downloading images for {len(targets)} products...", flush=True)
    ok = 0
    miss = 0
    for i, primary in enumerate(targets, 1):
        saved = False
        for candidate in fallback_urls(primary):
            ts = cdx.get(candidate, "")
            if download_with_timestamp(session, candidate, ts, args.snapshot):
                ok += 1
                saved = True
                break
        if not saved:
            miss += 1
            print(f"  MISS {primary}", file=sys.stderr)
        if i % 50 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] {ok} ok, {miss} miss", flush=True)
        time.sleep(args.delay)

    print(f"\nDownloaded {ok}/{len(targets)} images ({miss} not in archive).", flush=True)


if __name__ == "__main__":
    main()
