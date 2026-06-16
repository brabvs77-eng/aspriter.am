#!/usr/bin/env python3
"""Download pages and assets from a Wayback Machine snapshot."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

SNAPSHOT = os.environ.get("SNAPSHOT_TIMESTAMP", "20230321042548")
BASE = "https://aspriter.am"
DELAY = float(os.environ.get("REQUEST_DELAY", "1.0"))
ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"


def wayback_url(original: str, raw_html: bool = False) -> str:
    """Build a Wayback URL. Use id_ modifier for raw HTML without toolbar."""
    modifier = "id_" if raw_html else ""
    if original.startswith("http"):
        return f"https://web.archive.org/web/{SNAPSHOT}{modifier}/{original}"
    return f"https://web.archive.org/web/{SNAPSHOT}{modifier}/{BASE}{original}"


def asset_modifier(path: str) -> str:
    """Pick Wayback modifier by file type."""
    lower = path.lower()
    if lower.endswith((".css",)):
        return "cs_"
    if lower.endswith((".js",)):
        return "js_"
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|ico|woff2?|ttf|eot)(\?|$)", lower):
        return "im_"
    return ""


def local_path(url: str) -> Path:
    """Map original aspriter.am URL to local mirror path."""
    parsed = urlparse(url if url.startswith("http") else f"{BASE}{url}")
    path = parsed.path.lstrip("/")
    if not path:
        path = "index.html"
    elif path.endswith("/"):
        path += "index.html"
    elif "." not in Path(path).name and "?" not in path:
        path += "/index.html"
    # Strip query string from filesystem path but keep in download URL
    return MIRROR / path.split("?")[0]


def download(session: requests.Session, original: str, raw_html: bool = False) -> bool:
    if original.startswith("/"):
        original = BASE + original
    if "aspriter.am" not in original:
        return False

    parsed = urlparse(original)
    path = parsed.path
    modifier = "id_" if raw_html else asset_modifier(path)
    url = f"https://web.archive.org/web/{SNAPSHOT}{modifier}/{original}"
    if parsed.query:
        url += f"?{parsed.query}"

    dest = local_path(original)
    if dest.exists() and dest.stat().st_size > 0:
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  SKIP {resp.status_code} {original}", file=sys.stderr)
            return False
        dest.write_bytes(resp.content)
        print(f"  OK {dest.relative_to(ROOT)}")
        return True
    except requests.RequestException as exc:
        print(f"  ERR {original}: {exc}", file=sys.stderr)
        return False


def load_urls(list_file: Path, limit: int | None = None) -> list[str]:
    urls = []
    for line in list_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        # CDX lines are space-separated; URL is always first field
        url = line.split()[0] if " " in line else line
        url = url.split("\t")[0] if "\t" in url else url
        if url.startswith("http"):
            urls.append(url)
    if limit:
        urls = urls[:limit]
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Download aspriter.am from Wayback")
    parser.add_argument(
        "--list",
        type=Path,
        help="File with URLs to download (one per line)",
    )
    parser.add_argument(
        "--poc",
        action="store_true",
        help="Download proof-of-concept set (homepage, theme, sample products)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max URLs from list")
    parser.add_argument("--delay", type=float, default=DELAY, help="Seconds between requests")
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    targets: list[tuple[str, bool]] = []

    if args.poc:
        targets = [
            (f"{BASE}/", True),
            (f"{BASE}/sitemap", True),
            (f"{BASE}/contact-us", True),
            (f"{BASE}/3-beauty-shop-category", True),
            (f"{BASE}/themes/transformer/assets/cache/theme-59bf50203.css", False),
            (f"{BASE}/img/aspritercom-logo-1586547937.jpg", False),
            (f"{BASE}/img/favicon.ico", False),
            (f"{BASE}/upload/stswiper/armenia.jpg", False),
            (f"{BASE}/diverse/912-harisma-olive-oil-castile-soap-100-g.html", True),
            (f"{BASE}/diverse/911-harisma-almond-milk-honey.html", True),
            (f"{BASE}/diverse/910-harisma-activated-charcoal.html", True),
            (f"{BASE}/1303-large_default/harisma-olive-oil-castile-soap-100-g.jpg", False),
            (f"{BASE}/1303-home_default/harisma-olive-oil-castile-soap-100-g.jpg", False),
            (f"{BASE}/content/10-aeu-legal-shipping-and-payment", True),
        ]
    elif args.list:
        urls = load_urls(args.list, args.limit)
        targets = [(u, u.endswith(".html") or "/content/" in u or not Path(urlparse(u).path).suffix) for u in urls]
    else:
        parser.error("Specify --poc or --list")

    print(f"Snapshot: {SNAPSHOT}")
    print(f"Downloading {len(targets)} items to {MIRROR}/", flush=True)

    ok = 0
    skipped = 0
    total = len(targets)
    for i, (original, raw_html) in enumerate(targets, 1):
        dest = local_path(original if original.startswith("http") else BASE + original)
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            ok += 1
            if i % 50 == 0 or i == total:
                print(f"  [{i}/{total}] {ok} ok ({skipped} cached)", flush=True)
            continue
        if download(session, original, raw_html=raw_html):
            ok += 1
        if i % 25 == 0 or i == total:
            print(f"  [{i}/{total}] {ok} ok ({skipped} cached)", flush=True)
        time.sleep(args.delay)

    print(f"\nDownloaded {ok}/{total} items ({skipped} already cached).", flush=True)


if __name__ == "__main__":
    main()
