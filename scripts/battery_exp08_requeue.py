# Kill GPU-0 collision, re-upload, spawn queued boot. No secrets printed.
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from battery_exp08_hub import Hub, _load_local_env, execute_kernel, upload_scripts  # noqa: E402


def main() -> int:
    _load_local_env()
    user = os.environ["JUPYTERHUB_USER"]
    hub = Hub(os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"), user, os.environ["JUPYTERHUB_PASSWORD"])
    hub.login()
    print("uploaded_ok", sum(1 for u in upload_scripts(hub) if not str(u).startswith("FAIL")), flush=True)
    st, sessions = hub.request("GET", f"/user/{user}/api/sessions")
    kernel_id = None
    if isinstance(sessions, list):
        for s in sessions:
            name = (s or {}).get("name") or ""
            path = (s or {}).get("path") or ""
            if "exp08" in name or "exp08" in path:
                kernel_id = ((s.get("kernel") or {}).get("id"))
                break
        if kernel_id is None and sessions:
            kernel_id = ((sessions[-1].get("kernel") or {}).get("id"))
    if not kernel_id:
        print("no_kernel", flush=True)
        return 3
    time.sleep(2)
    code = r"""
import os, signal, time, sys, subprocess
from pathlib import Path
run = Path.home()/"algoverse_run"/"battery"/"exp08"
killed = []
extra = []
if (run/"pid").exists():
    try:
        extra.append(int((run/"pid").read_text().strip()))
    except ValueError:
        pass
lockp = Path.home()/"algoverse_run"/"battery"/"A100.lock"
if lockp.is_file():
    rec = __import__("json").loads(lockp.read_text())
    h = (rec.get("holders") or {}).get("exp08") or {}
    if h.get("pid"):
        extra.append(int(h["pid"]))
try:
    ps = subprocess.check_output(["ps", "-u", os.environ.get("USER", "jupyter-asca-ec66"), "-o", "pid=,cmd="], text=True)
except Exception as e:
    ps = ""
    print("ps_err", type(e).__name__)
for line in ps.splitlines():
    if "battery_exp08" not in line and "exp08" not in line:
        continue
    if "jupyter" in line.lower() and "battery_exp08" not in line:
        continue
    print("PROC", line[:180])
    try:
        extra.append(int(line.split()[0]))
    except ValueError:
        pass
for pid in sorted(set(extra)):
    try:
        os.kill(pid, signal.SIGKILL)
        killed.append(pid)
        print("killed9", pid)
    except ProcessLookupError:
        print("already_dead", pid)
    except Exception as e:
        print("kill_err", pid, type(e).__name__)
print("killed_all", killed)
lib = Path.home()/"Algoverse"/"scripts"/"battery_exp08_lib.py"
txt = lib.read_text()
print(
    "lib_has_smi", "smi_low_free" in txt,
    "lib_has_night_done", "NIGHT_DONE" in txt,
    "lib_has_live_kw", "live=sorted(live)" in txt,
)
scripts = Path.home()/"Algoverse"/"scripts"
for pyc in scripts.rglob("*battery_exp08*.pyc"):
    pyc.unlink()
    print("rm_pyc", str(pyc))
os.environ["EXP08_PREFER_GPU"] = "4"
sys.path.insert(0, str(Path.home()/"Algoverse"/"scripts"))
os.chdir(str(Path.home()/"Algoverse"))
import importlib
import battery_exp08_cell as cell
importlib.reload(cell)
print("respawn", cell.main())
"""
    outs = execute_kernel(hub, kernel_id, code, timeout=120)
    for o in outs:
        c = o.get("content") or {}
        text = str(c.get("text") or c.get("evalue") or "")[:400]
        if "hf_" in text or "sk-" in text:
            text = "[redacted]"
        print(o.get("type"), text, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
