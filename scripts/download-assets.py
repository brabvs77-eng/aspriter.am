#!/usr/bin/env python3
"""Discover and download static assets referenced in mirrored HTML."""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
BASE = "https://aspriter.am"
ARCHIVE_LIST = ROOT / "data" / "archive-url-list.txt"

ASSET_RE = re.compile(
    r"""(?:src|href|data-image-large-src|data-src|content)=["']([^"']+)["']""",
    re.I,
)

_spec = importlib.util.spec_from_file_location(
    "download_snapshot", Path(__file__).parent / "download-snapshot.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
local_path = _mod.local_path


def load_cdx_map(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("http"):
            mapping[parts[0]] = parts[1]
    return mapping


def asset_modifier(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".css"):
        return "cs_"
    if lower.endswith(".js"):
        return "js_"
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|ico|woff2?|ttf|eot)(\?|$)", lower):
        return "im_"
    return ""


def normalize_url(raw: str) -> str | None:
    raw = raw.strip()
    if not raw or raw.startswith(("javascript:", "mailto:", "data:", "#")):
        return None
    if raw.startswith("//"):
        raw = "https:" + raw
    if raw.startswith("/"):
        return BASE + raw.split("?")[0]
    parsed = urlparse(raw)
    if "aspriter.am" in parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return None


def is_essential_asset(path: str) -> bool:
    """Skip redundant PrestaShop image sizes to limit download scope."""
    p = path.lower()
    if any(x in p for x in ("/themes/", "/img/", "/upload/stswiper/", "/upload/stthemeeditor/")):
        return True
    if p.endswith((".css", ".js", ".woff", ".woff2", ".ttf", ".svg", ".ico")):
        return True
    if "-home_default/" in p and "_2x" not in p:
        return True
    return False


def collect_asset_urls(mirror: Path, essential_only: bool = True) -> list[str]:
    found: set[str] = set()
    for html in mirror.rglob("*.html"):
        text = html.read_text(encoding="utf-8", errors="ignore")
        for match in ASSET_RE.findall(text):
            url = normalize_url(match)
            if not url:
                continue
            path = urlparse(url).path.lower()
            if not re.search(r"\.(css|js|jpg|jpeg|png|gif|webp|svg|ico|woff2?|ttf|eot)$", path):
                continue
            if essential_only and not is_essential_asset(path):
                continue
            found.add(url)
    return sorted(found)


def download_asset(
    session: requests.Session,
    original: str,
    cdx: dict[str, str],
    snapshot: str,
) -> bool:
    dest = local_path(original)
    if dest.exists() and dest.stat().st_size > 0:
        return True

    ts = cdx.get(original, snapshot)
    modifier = asset_modifier(urlparse(original).path)
    url = f"https://web.archive.org/web/{ts}{modifier}/{original}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=60, allow_redirects=True)
        if resp.status_code != 200:
            return False
        dest.write_bytes(resp.content)
        return True
    except requests.RequestException:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Download assets referenced in mirror HTML")
    parser.add_argument("--mirror", type=Path, default=MIRROR)
    parser.add_argument("--archive", type=Path, default=ARCHIVE_LIST)
    parser.add_argument("--snapshot", default=os.environ.get("SNAPSHOT_TIMESTAMP", "20230321042548"))
    parser.add_argument("--delay", type=float, default=0.4)
    parser.add_argument("--extra", type=Path, nargs="*", help="Additional URL list files")
    parser.add_argument("--all-sizes", action="store_true", help="Include all image size variants")
    args = parser.parse_args()

    if not args.mirror.exists():
        print("Mirror not found.", file=sys.stderr)
        sys.exit(1)

    cdx = load_cdx_map(args.archive) if args.archive.exists() else {}
    targets = set(collect_asset_urls(args.mirror, essential_only=not args.all_sizes))

    # Always include core theme bundles referenced on homepage
    targets.update(
        {
            f"{BASE}/themes/transformer/assets/cache/bottom-66f1e8202.js",
            f"{BASE}/themes/transformer/assets/cache/theme-59bf50203.css",
            f"{BASE}/img/aspritercom-logo-1586547937.jpg",
            f"{BASE}/img/favicon.ico",
        }
    )

    for list_file in args.extra or []:
        for line in list_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("http"):
                targets.add(line.split()[0])

    targets_list = sorted(targets)
    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    print(f"Downloading {len(targets_list)} assets...", flush=True)
    ok = miss = cached = 0
    for i, url in enumerate(targets_list, 1):
        dest = local_path(url)
        if dest.exists() and dest.stat().st_size > 0:
            ok += 1
            cached += 1
        elif download_asset(session, url, cdx, args.snapshot):
            ok += 1
        else:
            miss += 1
        if i % 100 == 0 or i == len(targets_list):
            print(f"  [{i}/{len(targets_list)}] {ok} ok ({cached} cached), {miss} miss", flush=True)
        if not (dest.exists() and dest.stat().st_size > 0):
            time.sleep(args.delay)

    print(f"\nAssets: {ok} ok, {miss} miss.", flush=True)


if __name__ == "__main__":
    main()
