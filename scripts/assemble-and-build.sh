#!/usr/bin/env bash
# Merge mirror-chunks/* into mirror/, fetch missing assets, build site/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHUNKS_DIR="$ROOT/mirror-chunks"
MIRROR="$ROOT/mirror"
SITE="$ROOT/site"

if [[ ! -d "$CHUNKS_DIR" ]] || [[ -z "$(ls -A "$CHUNKS_DIR" 2>/dev/null)" ]]; then
  echo "No mirror-chunks/ found. Run GitHub Actions restore workflow first."
  exit 1
fi

echo "==> Assemble mirror from $(find "$CHUNKS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l) chunks"
rm -rf "$MIRROR"
mkdir -p "$MIRROR"

for chunk in "$CHUNKS_DIR"/*/; do
  [[ -d "$chunk" ]] || continue
  echo "  + $(basename "$chunk")"
  rsync -a "$chunk" "$MIRROR/"
done

export MIRROR_DIR="$MIRROR"
export SNAPSHOT_TIMESTAMP="${SNAPSHOT_TIMESTAMP:-20230321042548}"

echo "==> Download missing theme assets"
python3 scripts/download-assets.py --delay 0.25

echo "==> Build static site"
python3 scripts/strip-wayback.py --input "$MIRROR" --output "$SITE"

mkdir -p "$SITE"
cp -f deploy/_headers deploy/_redirects "$SITE/" 2>/dev/null || true

echo "==> Done"
find "$SITE" -type f | wc -l | xargs echo "Site files:"
du -sh "$SITE" | awk '{print "Site size:", $1}'
