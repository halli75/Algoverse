#!/bin/bash
set -euo pipefail
export E2E_ROOT=/workspace/algoverse_run
export E2E_REPO=/workspace/Algoverse
export E2E_V2=/workspace/Algoverse/artifacts/battery_v2
export E2E_EMOTIC=/workspace/algoverse_run/emotic_data
export E2E_SPLIT=/workspace/algoverse_run/emotic_split.json
export E2E_TIER=budget3h
export E2E_MODELS=e4b,g12
export E2E_CORPORA=emotic,oasis
export E2E_MAX_HOURS=2.75
if [ -f /root/.cache/huggingface/token ]; then
  export HF_TOKEN=$(tr -d '\r\n' < /root/.cache/huggingface/token)
  export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
fi
cd /workspace/Algoverse
mkdir -p artifacts/battery_v2
pkill -f 'scripts/battery_v2_run.py' || true
pkill -f 'scripts/battery_v2_boot.py' || true
sleep 1
python3 - << 'PY'
from pathlib import Path
import json
root = Path("/workspace/Algoverse/artifacts/battery_v2")
for lock in root.rglob("LOCK.json"):
    if "_dry" in lock.parts:
        continue
    res = lock.parent / "results.json"
    ok = False
    if res.is_file():
        try:
            ok = bool(json.loads(res.read_text(encoding="utf-8")).get("complete"))
        except Exception:
            ok = False
    if not ok:
        lock.unlink()
        print("dropped incomplete", lock)
PY
echo "[start_run $(date -u +%H:%M:%S)] launching run.py token_len=${#HF_TOKEN}" >> artifacts/battery_v2/boot.log
nohup python -u scripts/battery_v2_run.py --tier budget3h --models e4b,g12 --corpora emotic,oasis >> artifacts/battery_v2/boot.log 2>&1 </dev/null &
echo PID=$!
sleep 1
pgrep -af battery_v2 || true
