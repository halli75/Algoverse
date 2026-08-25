"""A100 host 15-min heartbeat. Survives laptop sleep. Does not overwrite v3."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

ROOT = Path.home() / "algoverse_run" / "battery"
LOG = ROOT / "host_watchdog.log"
HB = ROOT / "host_watchdog_heartbeat.json"


def log(msg: str) -> None:
    line = time.strftime("%H:%M:%S") + " " + msg
    print(line, flush=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def hb(**kw) -> None:
    payload = {"ts": time.time(), "iso": time.strftime("%Y-%m-%d %H:%M:%S"), **kw}
    tmp = HB.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, HB)


def main() -> None:
    log("WATCHDOG_START pid=%s" % os.getpid())
    while True:
        stages = {}
        for path in sorted(ROOT.glob("exp*/heartbeat.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                stages[path.parent.name] = data.get("stage")
            except Exception:
                stages[path.parent.name] = "unreadable"
        hb(stages=stages)
        log("tick " + json.dumps(stages)[:400])
        time.sleep(900)


if __name__ == "__main__":
    main()
