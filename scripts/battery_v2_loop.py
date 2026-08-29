# 15-minute overseer for battery v2. Prints AGENT_LOOP_TICK_battery_v2 each cycle.
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
META = ROOT / "artifacts" / "battery_v2" / "pod.json"
TICK = "AGENT_LOOP_TICK_battery_v2"


def py(*args: str) -> str:
    r = subprocess.run([sys.executable, *args], cwd=str(ROOT), capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--interval", type=int, default=900)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    pid = args.id
    if not pid and META.is_file():
        pid = json.loads(META.read_text(encoding="utf-8")).get("id") or ""
    n = 0
    while True:
        n += 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"{TICK} n={n} ts={ts} id={pid}", flush=True)
        if pid:
            out = py(str(SCRIPTS / "battery_v2_runpod.py"), "status", "--id", pid)
            print(out[:2500], flush=True)
            if '"status": "EXITED"' in out or '"status": "TERMINATED"' in out:
                print(f"{TICK} pod_stopped", flush=True)
                return 0
        hb = ROOT / "artifacts" / "battery_v2" / "heartbeat.json"
        if hb.is_file():
            print("heartbeat", hb.read_text(encoding="utf-8")[:800], flush=True)
        status = ROOT / "artifacts" / "battery_v2" / "STATUS.json"
        if status.is_file():
            print("status", status.read_text(encoding="utf-8")[:1200], flush=True)
        if args.once:
            return 0
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
