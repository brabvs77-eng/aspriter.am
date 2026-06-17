#!/usr/bin/env bash
# Download one Wayback chunk into mirror-chunks/NN/
set -euo pipefail

CHUNK="${CHUNK:?Set CHUNK=1..18}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAD="$(printf '%02d' "$CHUNK")"
OUT="$ROOT/mirror-chunks/$PAD"
LIST="$ROOT/data/chunks/chunk-${PAD}.txt"
DELAY="${REQUEST_DELAY:-0.75}"
IMG_DELAY="${IMAGE_DELAY:-0.4}"

if [[ ! -f "$LIST" ]]; then
  echo "Missing $LIST — run: python3 scripts/split-chunks.py"
  exit 1
fi

mkdir -p "$OUT"
export MIRROR_DIR="$OUT"
export SNAPSHOT_TIMESTAMP="${SNAPSHOT_TIMESTAMP:-20230321042548}"

URLS=$(wc -l < "$LIST" | tr -d ' ')
echo "==> Chunk $PAD: $URLS URLs → $OUT"

python3 "$ROOT/scripts/download-snapshot.py" \
  --list "$LIST" \
  --mirror-dir "$OUT" \
  --delay "$DELAY"

python3 "$ROOT/scripts/download-chunk-images.py" \
  --mirror-dir "$OUT" \
  --delay "$IMG_DELAY"

echo "$PAD" > "$OUT/.chunk-id"
echo "==> Chunk $PAD complete"
