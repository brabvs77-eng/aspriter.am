#!/usr/bin/env bash
# Combined list of non-product site pages for download
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
OUT="$DATA/site-pages.txt"

{
  cat "$DATA/category-pages.txt"
  cat "$DATA/cms-pages.txt"
  printf '%s\n' \
    "https://aspriter.am/" \
    "https://aspriter.am/contact-us" \
    "https://aspriter.am/sitemap" \
    "https://aspriter.am/2-home"
} | sort -u > "$OUT"

echo "Wrote $(wc -l < "$OUT" | tr -d ' ') site pages → $OUT"
