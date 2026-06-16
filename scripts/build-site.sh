#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Clean HTML → site/"
python3 scripts/strip-wayback.py

echo "==> Copy deploy config"
mkdir -p site
cp -f deploy/_headers site/_headers 2>/dev/null || true
cp -f deploy/_redirects site/_redirects 2>/dev/null || true

echo "==> Site stats"
find site -type f | wc -l | xargs echo "Files:"
du -sh site | awk '{print "Size:", $1}'

echo "Done. Deploy directory: site/"
