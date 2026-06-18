#!/usr/bin/env bash
# Run all 18 Wayback chunks with limited parallelism, then commit to git.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PARALLEL="${PARALLEL:-3}"
LOG="$ROOT/data/restore-all-chunks.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== Restore started $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
pip install -q -r requirements.txt
python3 scripts/split-chunks.py --parts 18

run_chunk() {
  local n="$1"
  echo "--- Chunk $n start $(date -u +%H:%M:%S) ---"
  (cd "$ROOT" && CHUNK="$n" REQUEST_DELAY=0.75 IMAGE_DELAY=0.4 bash scripts/download-chunk.sh)
  echo "--- Chunk $n done ---"
}

for batch in 1 4 7 10 13 16; do
  end=$((batch + PARALLEL - 1))
  [[ $end -gt 18 ]] && end=18
  pids=()
  for i in $(seq "$batch" "$end"); do
    run_chunk "$i" &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do wait "$pid" || true; done
  echo "=== Batch $batch-$end complete ==="
done

echo "=== Assemble ==="
bash scripts/assemble-and-build.sh

echo "=== Git commit ==="
git add mirror-chunks/
git config user.email "restore-bot@aspriter.am"
git config user.name "aspriter-restore"
if git diff --staged --quiet; then
  echo "No changes to commit"
else
  git commit -m "Add mirror-chunks 01-18 from Wayback restore ($(date -u +%Y-%m-%d))"
  git push origin main
fi

echo "=== Restore finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
