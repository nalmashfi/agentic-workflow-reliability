#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: $0 /path/to/bench_manifest.full.jsonl [output_dir]"
  exit 2
fi
MANIFEST="$1"
OUT="${2:-outputs}"
python scripts/run_all.py --manifest "$MANIFEST" --out "$OUT"
