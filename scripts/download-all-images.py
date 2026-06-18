#!/usr/bin/env python3
"""Download all archived aspriter.am images from Wayback CDX index."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "archive-url-list.txt"
OUT = ROOT / "mirror-chunks" / "00-images"
BASE = "https://aspriter.am"

_spec = importlib.util.spec_from_file_location(
    "download_images", Path(__file__).parent / "download-images.py"
)
_img = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_img)
download_with_timestamp = _img.download_with_timestamp
fallback_urls = _img.fallback_urls


def existing_paths(chunks_dir: Path) -> set[str]:
    found: set[str] = set()
    for f in chunks_dir.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"}:
            continue
        parts = f.parts
        if "mirror-chunks" not in parts:
            continue
        idx = parts.index("mirror-chunks") + 2
        found.add("/" + "/".join(parts[idx:]))
    return found


def load_image_jobs(archive: Path, have: set[str]) -> list[tuple[str, str]]:
    jobs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in archive.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        url, ts, status, mime = parts[0], parts[1], parts[2], parts[3]
        if status != "200" or not mime.startswith("image/"):
            continue
        if "aspriter.am" not in url:
            continue
        path = urlparse(url).path
        if path in have or path in seen:
            continue
        seen.add(path)
        jobs.append((url, ts))
    return jobs


def local_dest(path: str, out_dir: Path) -> Path:
    return out_dir / path.lstrip("/")


def download_one(session: requests.Session, url: str, ts: str, snapshot: str, out_dir: Path) -> bool:
    dest = local_dest(urlparse(url).path, out_dir)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    if download_with_timestamp(session, url, ts, snapshot):
        return True
    # try size fallbacks for product images
    for alt in fallback_urls(url):
        if alt == url:
            continue
        alt_path = urlparse(alt).path
        alt_dest = local_dest(alt_path, out_dir)
        if alt_dest.exists():
            return True
        if download_with_timestamp(session, alt, ts, snapshot):
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Download all archived images")
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--snapshot", default=os.environ.get("SNAPSHOT_TIMESTAMP", "20230321042548"))
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    os.environ["MIRROR_DIR"] = str(out_dir)

    have = existing_paths(ROOT / "mirror-chunks")
    jobs = load_image_jobs(args.archive, have)
    if args.limit:
        jobs = jobs[: args.limit]

    session = requests.Session()
    session.headers["User-Agent"] = "aspriter-restore/1.0 (Wayback restoration project)"

    print(f"Already have {len(have)} images in mirror-chunks", flush=True)
    print(f"Downloading {len(jobs)} missing images → {out_dir}/", flush=True)

    ok = miss = cached = 0
    for i, (url, ts) in enumerate(jobs, 1):
        dest = local_dest(urlparse(url).path, out_dir)
        if dest.exists() and dest.stat().st_size > 0:
            ok += 1
            cached += 1
        elif download_one(session, url, ts, args.snapshot, out_dir):
            ok += 1
        else:
            miss += 1
            print(f"  MISS {url}", file=sys.stderr)
        if i % 100 == 0 or i == len(jobs):
            print(f"  [{i}/{len(jobs)}] {ok} ok ({cached} cached), {miss} miss", flush=True)
        if not (dest.exists() and dest.stat().st_size > 0):
            time.sleep(args.delay)

    print(f"\nDone: {ok} ok, {miss} miss", flush=True)


if __name__ == "__main__":
    main()
