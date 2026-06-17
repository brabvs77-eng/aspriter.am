#!/usr/bin/env python3
"""Split product and site URLs into N chunks for parallel Wayback download."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHUNKS_DIR = DATA / "chunks"


def split_even(items: list[str], parts: int) -> list[list[str]]:
    k, extra = divmod(len(items), parts)
    chunks: list[list[str]] = []
    start = 0
    for i in range(parts):
        size = k + (1 if i < extra else 0)
        chunks.append(items[start : start + size])
        start += size
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Split URL lists into download chunks")
    parser.add_argument("--parts", type=int, default=18)
    args = parser.parse_args()

    products = [
        l.strip().split()[0]
        for l in (DATA / "product-pages.txt").read_text().splitlines()
        if l.strip()
    ]
    site_pages = [
        l.strip().split()[0]
        for l in (DATA / "site-pages.txt").read_text().splitlines()
        if l.strip()
    ]

    product_chunks = split_even(products, args.parts)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    for i in range(args.parts):
        pad = f"{i + 1:02d}"
        urls = list(site_pages) + product_chunks[i] if i == 0 else product_chunks[i]
        out = CHUNKS_DIR / f"chunk-{pad}.txt"
        out.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
        manifest.append(
            {
                "chunk": pad,
                "file": f"data/chunks/chunk-{pad}.txt",
                "urls": len(urls),
                "site_pages": len(site_pages) if i == 0 else 0,
                "products": len(product_chunks[i]),
            }
        )
        print(f"chunk-{pad}: {len(urls)} URLs ({len(product_chunks[i])} products)")

    (CHUNKS_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {args.parts} chunks → {CHUNKS_DIR}/")


if __name__ == "__main__":
    main()
