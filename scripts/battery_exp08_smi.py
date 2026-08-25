# nvidia-smi + lock peek via own exp08 kernel. No secrets.
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from battery_exp08_hub import Hub, _load_local_env, execute_kernel  # noqa: E402


def main() -> int:
    _load_local_env()
    user = os.environ["JUPYTERHUB_USER"]
    hub = Hub(os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"), user, os.environ["JUPYTERHUB_PASSWORD"])
    hub.login()
    st, sessions = hub.request("GET", f"/user/{user}/api/sessions")
    kid = None
    if isinstance(sessions, list):
        for s in sessions:
            path = str((s or {}).get("path") or "")
            name = str((s or {}).get("name") or "")
            if "exp08" in path or "exp08" in name:
                kid = ((s.get("kernel") or {}).get("id"))
                break
    if not kid:
        print("no_exp08_kernel", flush=True)
        return 3
    time.sleep(1)
    code = r"""
import json, os, time
from pathlib import Path
print("time", time.strftime("%H:%M:%S"))
os.system("nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits")
print("---locks---")
ld = Path.home()/"algoverse_run"/"battery"/"locks"
now = time.time()
for p in sorted(ld.glob("gpu_*.json")):
    rec = json.loads(p.read_text())
    age = now - float(rec.get("ts") or 0)
    print(p.name, rec.get("exp"), rec.get("gpu"), rec.get("pid"), "age", int(age))
print("---peers---")
root = Path.home()/"algoverse_run"/"battery"
for hb in sorted(root.glob("exp*/heartbeat.json")):
    rec = json.loads(hb.read_text())
    print(hb.parent.name, rec.get("stage"), "gpu", rec.get("gpu"))
print("---exp08---")
hb = Path.home()/"algoverse_run"/"battery"/"exp08"/"heartbeat.json"
pid = Path.home()/"algoverse_run"/"battery"/"exp08"/"pid"
print("hb", hb.read_text()[:800] if hb.exists() else None)
print("pidfile", pid.read_text().strip() if pid.exists() else None)
pidn = int(pid.read_text()) if pid.exists() else None
if pidn:
    try:
        os.kill(pidn, 0)
        print("pid_alive", True)
    except OSError:
        print("pid_alive", False)
log = Path.home()/"algoverse_run"/"battery"/"exp08"/"nohup.out"
if log.exists():
    lines = log.read_text(errors="replace").splitlines()
    print("---nohup_tail---")
    for line in lines[-25:]:
        if "hf_" in line or "sk-" in line or "xai-" in line:
            continue
        print(line[:200])
"""
    outs = execute_kernel(hub, kid, code, timeout=90)
    for o in outs:
        c = o.get("content") or {}
        text = str(c.get("text") or c.get("evalue") or "")
        if "hf_" in text or "sk-" in text:
            text = "[redacted]"
        print(o.get("type"), text[:2000].encode("ascii", "replace").decode("ascii"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
