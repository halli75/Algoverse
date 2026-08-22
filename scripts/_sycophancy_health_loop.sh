#!/usr/bin/env bash
set -u
LOG=/workspace/.agent_sycophancy_loop.log
GIST_URL='https://gist.githubusercontent.com/halli75/d888da53224aac15e38a1f0d30f75805/raw/0a19bbfb0205b6ef2f4e23499a262f7d5dc30e2d/e2e_sycophancy_affect.py'
echo "=== AGENT_LOOP_START sycophancy $(date -Is) pid=$$ ===" | tee -a "$LOG"
while true; do
  ts=$(date -Is)
  code=$(curl -s -o /dev/null -w "%{http_code}" "$GIST_URL" || echo fail)
  echo "AGENT_LOOP_TICK_sycophancy $ts gist_http=$code gpu=none colab_browser=missing" | tee -a "$LOG"
  sleep 900
done
