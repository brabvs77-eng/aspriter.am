#!/usr/bin/env python3
"""Audit static site for broken local asset references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

REF_RE = re.compile(
    r"""(?:src|href|data-image-large-src|data-src|content)=["']([^"']+)["']""",
    re.I,
)
CSS_URL_RE = re.compile(r"url\(['\"]?([^)'\"]+)['\"]?\)", re.I)


def local_target(ref: str) -> Path | None:
    ref = ref.strip()
    if not ref or ref.startswith(("javascript:", "mailto:", "data:", "#", "https://fonts.")):
        return None
    if ref.startswith("https://aspriter.am") or ref.startswith("http://aspriter.am"):
        ref = urlparse(ref).path
    if ref.startswith("//aspriter.am"):
        ref = urlparse("https:" + ref).path
    if not ref.startswith("/"):
        return None
    return SITE / ref.lstrip("/").split("?")[0]


def audit(site: Path) -> dict:
    missing: list[tuple[str, str]] = []
    external: list[str] = []
    checked = 0

    for html in site.rglob("*.html"):
        text = html.read_text(encoding="utf-8", errors="ignore")
        refs = REF_RE.findall(text) + CSS_URL_RE.findall(text)
        for ref in refs:
            target = local_target(ref)
            if target is None:
                if ref.startswith("http") and "aspriter" not in ref:
                    external.append(ref)
                continue
            checked += 1
            if not target.exists() or target.stat().st_size == 0:
                missing.append((str(html.relative_to(site)), ref))

    # Unique missing
    uniq = sorted(set(missing), key=lambda x: x[1])
    return {
        "checked": checked,
        "missing_count": len(uniq),
        "missing": uniq[:200],
        "external_count": len(set(external)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=SITE)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "audit-report.json")
    args = parser.parse_args()

    if not args.site.exists():
        print(f"Site not found: {args.site}. Run assemble-and-build.sh first.")
        return

    import json

    report = audit(args.site)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Checked {report['checked']} local refs")
    print(f"Missing: {report['missing_count']}")
    print(f"External (CDN etc): {report['external_count']}")
    if report["missing"]:
        print("\nSample missing:")
        for page, ref in report["missing"][:20]:
            print(f"  {ref}  (in {page})")


if __name__ == "__main__":
    main()
