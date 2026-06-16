#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${ROOT_DIR}/data"

source "${SCRIPT_DIR}/config.sh"

mkdir -p "$DATA_DIR"

echo "Fetching CDX index for aspriter.am (this may take a minute)..."

curl -s "${CDX_API}?url=aspriter.am/*&matchType=domain&collapse=urlkey&output=text&fl=original,timestamp,statuscode,mimetype" \
  > "${DATA_DIR}/archive-url-list.txt"

# Product pages (.html under category paths)
grep -E 'https?://(www\.)?aspriter\.am/[^/]+/[0-9]+-[^/]+\.html' "${DATA_DIR}/archive-url-list.txt" \
  | cut -f1 | sort -u > "${DATA_DIR}/product-pages.txt" || true

# Category pages (numeric-id slug, HTML only, exclude image size folders)
grep -E 'https?://(www\.)?aspriter\.am/[0-9]+-[a-z][a-z0-9-]*[[:space:]]' "${DATA_DIR}/archive-url-list.txt" \
  | awk '$3 == "200" && $4 == "text/html" {print $1}' | sort -u > "${DATA_DIR}/category-pages.txt" || true

# CMS / content pages
grep -E 'https?://(www\.)?aspriter\.am/content/' "${DATA_DIR}/archive-url-list.txt" \
  | cut -f1 | sort -u > "${DATA_DIR}/cms-pages.txt" || true

TOTAL=$(wc -l < "${DATA_DIR}/archive-url-list.txt" | tr -d ' ')
PRODUCTS=$(wc -l < "${DATA_DIR}/product-pages.txt" | tr -d ' ')
CATEGORIES=$(wc -l < "${DATA_DIR}/category-pages.txt" | tr -d ' ')

echo "Done."
echo "  Total URLs:    ${TOTAL}"
echo "  Product pages: ${PRODUCTS}"
echo "  Categories:    ${CATEGORIES}"
echo "  Output:        ${DATA_DIR}/"
