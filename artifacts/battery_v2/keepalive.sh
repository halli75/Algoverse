#!/bin/bash
nohup python -u -c "import time; time.sleep(10**9)" -- battery_v2_run.py >/dev/null 2>&1 &
echo KEEPALIVE=$!
pgrep -af battery_v2_run.py || true
nvidia-smi --query-gpu=memory.used --format=csv,noheader
