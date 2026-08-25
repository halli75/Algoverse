# Night-shift poller for exp10. Credentials from env only.
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUBCTL = ROOT / "scripts" / "battery_exp10_hubctl.py"
ART = ROOT / "artifacts" / "battery" / "exp10"
SLEEP_S = int(os.environ.get("EXP10_POLL_S", "90"))


def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)
    ART.mkdir(parents=True, exist_ok=True)
    with (ART / "night_loop.log").open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %T')} {msg}\n")


def run_hub(cmd: str) -> tuple[int, str]:
    env = os.environ.copy()
    p = subprocess.run(
        [sys.executable, str(HUBCTL), cmd],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def results_complete() -> bool:
    rp = ART / "results.json"
    if not rp.is_file() or rp.stat().st_size < 40:
        return False
    try:
        rec = json.loads(rp.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(rec.get("complete") is True and rec.get("mechanism_answer") and (rec.get("gates") or {}).get("total"))


def waiter_alive(status_text: str) -> bool:
    hb = ART / "heartbeat.json"
    if hb.is_file():
        try:
            rec = json.loads(hb.read_text(encoding="utf-8"))
            age = time.time() - float(rec.get("ts") or 0)
            stage = str(rec.get("stage") or "")
            if age < 180 and stage in {"model", "units", "dirs", "dirs_rebuild", "scoring", "claimed"}:
                return True
        except Exception:
            pass
    if "UnicodeEncodeError" in status_text or "charmap" in status_text:
        return True
    return "battery_exp10_boot.py --run" in status_text and "defunct" not in status_text.lower()


def write_status(phase: str, extra: str = "") -> None:
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "STATUS.md").write_text(
        f"# exp10 STATUS\n\nphase: {phase}\n{extra}\n"
        "Never writing `artifacts/colab/e2e_mechanism_results_full_v3.json`\n",
        encoding="utf-8",
    )


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    log("night loop start")
    for i in range(400):
        if results_complete():
            log("results complete")
            write_status("complete", "results.json complete=true")
            return 0
        rc, status = run_hub("status")
        log(f"tick {i} status_rc={rc} bytes={len(status)}")
        tail = status[-800:]
        if "RESTARTED" not in status:
            print(tail, flush=True)
        if not waiter_alive(status):
            log("waiter dead; restart")
            rrc, rout = run_hub("restart")
            log(f"restart rc={rrc} {rout[-300:]}")
        run_hub("pull")
        if results_complete():
            log("results complete after pull")
            write_status("complete", "results.json complete=true")
            return 0
        hb = ART / "heartbeat.json"
        stage = "?"
        if hb.is_file():
            try:
                stage = json.loads(hb.read_text(encoding="utf-8")).get("stage")
            except Exception:
                stage = "?"
        write_status(str(stage), f"tick: {i}\nhost_stage: {stage}\n")
        time.sleep(SLEEP_S)
    log("night loop exhausted")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
