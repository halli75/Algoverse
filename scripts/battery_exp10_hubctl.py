# JupyterHub helper for exp10. Credentials from env only. Own kernel.
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

HUB = os.environ.get("EXP10_HUB", os.environ.get("BATTERY_HOST", "http://35.89.128.116"))
if not HUB.startswith("http"):
    HUB = "http://" + HUB
USER = os.environ.get("EXP10_HUB_USER", os.environ.get("BATTERY_USER", "asca-ec66"))
PASS = os.environ.get("EXP10_HUB_PASSWORD") or os.environ.get("BATTERY_SSH_PASS") or os.environ.get("BATTERY_PASS") or ""
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("EXP10_HUB_PASSWORD unset")
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.uxsrf = ""

    def login(self) -> None:
        self.op.open(f"{HUB}/hub/login", timeout=20).read()
        xsrf = next(c.value for c in self.cj if c.name == "_xsrf" and c.path.startswith("/hub"))
        data = urllib.parse.urlencode({"username": USER, "password": PASS, "_xsrf": xsrf}).encode()
        req = urllib.request.Request(f"{HUB}/hub/login", data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Referer", f"{HUB}/hub/login")
        self.op.open(req, timeout=40)
        self.uxsrf = next(c.value for c in self.cj if c.name == "_xsrf" and "/user/" in c.path)

    def _cookie_header(self) -> str:
        return "; ".join(f"{c.name}={c.value}" for c in self.cj)

    def req(self, method: str, path: str, body: dict | None = None, timeout: int = 60):
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request(BASE + path, data=data, method=method)
        r.add_header("X-XSRFToken", self.uxsrf)
        r.add_header("Referer", BASE + "/lab")
        if body is not None:
            r.add_header("Content-Type", "application/json")
        try:
            resp = self.op.open(r, timeout=timeout)
            raw = resp.read()
            return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")[:400]
            raise RuntimeError(f"{method} {path} {e.code}: {err}") from e

    def mkdir(self, path: str) -> None:
        try:
            self.req("PUT", f"/api/contents/{path}", {"type": "directory"})
        except Exception:
            pass

    def put_text(self, path: str, text: str) -> None:
        self.req("PUT", f"/api/contents/{path}", {"type": "file", "format": "text", "content": text})

    def new_kernel(self) -> str:
        rec = self.req("POST", "/api/kernels", {"name": "python3"})
        kid = rec["id"]
        print(f"own_kernel {kid}", flush=True)
        return kid

    def execute(self, kid: str, code: str, timeout: int = 180) -> str:
        from websocket import create_connection

        sid = uuid.uuid4().hex
        url = f"{BASE.replace('http://', 'ws://').replace('https://', 'wss://')}/api/kernels/{kid}/channels?session_id={sid}"
        ws = create_connection(
            url,
            header=[f"Cookie: {self._cookie_header()}", f"X-XSRFToken: {self.uxsrf}"],
            timeout=timeout,
        )
        mid = uuid.uuid4().hex
        ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": mid,
                        "username": "exp10",
                        "session": sid,
                        "msg_type": "execute_request",
                        "version": "5.3",
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": False,
                        "user_expressions": {},
                        "allow_stdin": False,
                        "stop_on_error": False,
                    },
                    "buffers": [],
                    "channel": "shell",
                }
            )
        )
        chunks: list[str] = []
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                raw = ws.recv()
            except Exception:
                break
            if not raw:
                continue
            msg = json.loads(raw)
            if msg.get("parent_header", {}).get("msg_id") != mid:
                continue
            mtype = msg.get("header", {}).get("msg_type")
            content = msg.get("content") or {}
            if mtype == "stream":
                chunks.append(content.get("text") or "")
            elif mtype in ("execute_result", "display_data"):
                chunks.append((content.get("data") or {}).get("text/plain") or "")
            elif mtype == "error":
                chunks.append("\n".join(content.get("traceback") or [content.get("ename", "err")]))
            elif mtype == "status" and content.get("execution_state") == "idle":
                break
        ws.close()
        return "".join(chunks)


def upload_scripts(h: Hub) -> None:
    root = Path(__file__).resolve().parents[1]
    files = {
        "Algoverse/scripts/battery_probe_aperp.py": root / "scripts" / "battery_probe_aperp.py",
        "Algoverse/scripts/battery_exp10_run.py": root / "scripts" / "battery_exp10_run.py",
        "Algoverse/scripts/battery_exp10_boot.py": root / "scripts" / "battery_exp10_boot.py",
        "Algoverse/scripts/affect_core.py": root / "scripts" / "affect_core.py",
        "Algoverse/scripts/battery_adapter.py": root / "scripts" / "battery_adapter.py",
        "Algoverse/artifacts/battery/exp10/ADVISOR_SPEC.md": root / "artifacts" / "battery" / "exp10" / "ADVISOR_SPEC.md",
        "Algoverse/data/battery/exp01_lotteries.json": root / "data" / "battery" / "exp01_lotteries.json",
    }
    h.mkdir("Algoverse")
    h.mkdir("Algoverse/scripts")
    h.mkdir("Algoverse/data")
    h.mkdir("Algoverse/data/battery")
    h.mkdir("Algoverse/artifacts")
    h.mkdir("Algoverse/artifacts/battery")
    h.mkdir("Algoverse/artifacts/battery/exp10")
    h.mkdir("algoverse_run")
    h.mkdir("algoverse_run/battery")
    h.mkdir("algoverse_run/battery/exp10")
    for dest, src in files.items():
        if not src.is_file():
            print(f"skip missing {src}", flush=True)
            continue
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import json, os, subprocess
from pathlib import Path
home = Path.home()
print('HOME', home)
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
for p in [
    home/'algoverse_run',
    home/'algoverse_run'/'emotic_data',
    home/'algoverse_run'/'emotic_split.json',
    home/'algoverse_run'/'e2e_dirs_mechanism.pt',
    home/'algoverse_run'/'battery'/'e2e_dirs_mechanism.pt',
    home/'algoverse_run'/'battery'/'exp10'/'e2e_dirs_mechanism.pt',
    home/'Algoverse'/'scripts'/'battery_probe_aperp.py',
    home/'.battery_env', home/'.hf_token',
]:
    print(('OK' if p.exists() else 'MISS'), p)
print('==== FIND DIRS ====')
for p in home.rglob('e2e_dirs_mechanism.pt'):
    print('HIT', p, p.stat().st_size)
    if str(p).count(os.sep) > 8:
        break
print('==== LOCK ====')
lk = home/'algoverse_run'/'battery'/'A100.lock'
print(lk.read_text()[:1200] if lk.exists() else 'no lock')
print('==== SMI ====')
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
print('==== EXP10 PROC ====')
print(subprocess.check_output(['bash','-lc','pgrep -af battery_exp10 || true'], text=True))
"""

LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp10'
run.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP10'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = 'full'
env['E2E_REPO'] = str(home/'Algoverse')
env['PYTHONUNBUFFERED'] = '1'
env['CUDA_VISIBLE_DEVICES'] = '2'
env['EXP10_SKIP_WAVE'] = '1'
# source battery_env without printing
benv = home/'.battery_env'
if benv.exists():
    for line in benv.read_text().splitlines():
        s=line.strip()
        if s and not s.startswith('#') and '=' in s:
            k,_,v=s.partition('=')
            k,v=k.strip(),v.strip().strip('"').strip("'")
            if k and k not in env:
                env[k]=v
hf = home/'.hf_token'
if hf.exists() and not env.get('HF_TOKEN'):
    env['HF_TOKEN'] = hf.read_text().strip()
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
script = home/'Algoverse'/'scripts'/'battery_exp10_boot.py'
out = open(run/'nohup.out', 'ab', buffering=0)
proc = subprocess.Popen(
    ['python3', '-u', str(script), '--run'],
    cwd=str(home/'Algoverse'),
    env=env,
    stdout=out,
    stderr=out,
    start_new_session=True,
)
(run/'pid').write_text(str(proc.pid))
print('LAUNCHED', proc.pid)
"""

STATUS = r"""
import subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp10'
for n in ['heartbeat.json','results.json','STATUS.md','pid','checkpoint.json']:
    p = run/n
    print('====', n, 'exists' if p.exists() else 'MISS', p.stat().st_size if p.exists() else 0)
    if p.exists() and n != 'results.json':
        print(p.read_text(errors='replace')[:2000])
    elif p.exists():
        t=p.read_text(errors='replace')
        print(t[:1500])
        print('...tail...')
        print(t[-1500:])
p = run/'nohup.out'
print('==== nohup', p.exists(), p.stat().st_size if p.exists() else 0)
if p.exists():
    print(p.read_text(errors='replace')[-2500:])
pidp = run/'pid'
if pidp.exists():
    pid = pidp.read_text().strip()
    print('==== PS')
    print(subprocess.check_output(['ps','-p',pid,'-o','pid,etime,cmd'], text=True, stderr=subprocess.STDOUT))
print('==== SMI')
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv'], text=True))
"""

PULL = r"""
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp10'
for n in ['heartbeat.json','results.json','STATUS.md']:
    p = run/n
    print('FILE', n)
    print(p.read_text() if p.exists() else '')
    print('ENDFILE', n)
"""


def pull_local(text: str) -> None:
    dest = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp10"
    dest.mkdir(parents=True, exist_ok=True)
    cur = None
    buf = []
    for line in text.splitlines(True):
        if line.startswith("FILE "):
            cur = line.split(" ", 1)[1].strip()
            buf = []
        elif line.startswith("ENDFILE "):
            body = "".join(buf)
            if cur and body.strip():
                (dest / cur).write_text(body, encoding="utf-8")
                print(f"pulled {cur} bytes={len(body)}", flush=True)
            elif cur:
                print(f"skip empty {cur}", flush=True)
            cur = None
        elif cur:
            buf.append(line)


RESTART = r"""
import os, subprocess, time
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp10'
# stop previous waiter only
subprocess.call(['bash','-lc','pkill -f "battery_exp10_boot.py --run" || true'])
time.sleep(1)
env = os.environ.copy()
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP10'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = 'full'
env['E2E_REPO'] = str(home/'Algoverse')
env['PYTHONUNBUFFERED'] = '1'
env['CUDA_VISIBLE_DEVICES'] = '2'
env['EXP10_SKIP_WAVE'] = '1'
benv = home/'.battery_env'
if benv.exists():
    for line in benv.read_text().splitlines():
        s=line.strip()
        if s and not s.startswith('#') and '=' in s:
            k,_,v=s.partition('=')
            k,v=k.strip(),v.strip().strip('"').strip("'")
            if k and k not in env:
                env[k]=v
hf = home/'.hf_token'
if hf.exists() and not env.get('HF_TOKEN'):
    env['HF_TOKEN'] = hf.read_text().strip()
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
out = open(run/'nohup.out', 'ab', buffering=0)
proc = subprocess.Popen(
    ['python3', '-u', str(home/'Algoverse'/'scripts'/'battery_exp10_boot.py'), '--run'],
    cwd=str(home/'Algoverse'),
    env=env,
    stdout=out,
    stderr=out,
    start_new_session=True,
)
(run/'pid').write_text(str(proc.pid))
print('RESTARTED', proc.pid)
"""


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    kid = h.new_kernel()
    try:
        return _dispatch(h, kid, cmd)
    finally:
        try:
            h.req("DELETE", f"/api/kernels/{kid}")
        except Exception:
            pass


def _dispatch(h: Hub, kid: str, cmd: str) -> int:
    if cmd == "probe":
        print(h.execute(kid, PROBE, timeout=90))
        return 0
    if cmd == "status":
        print(h.execute(kid, STATUS, timeout=60))
        return 0
    if cmd == "pull":
        pull_local(h.execute(kid, PULL, timeout=45))
        return 0
    if cmd == "watch":
        print(h.execute(kid, STATUS, timeout=60))
        pull_local(h.execute(kid, PULL, timeout=45))
        dest = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp10" / "results.json"
        if dest.is_file() and dest.stat().st_size > 20:
            try:
                res = json.loads(dest.read_text(encoding="utf-8"))
                if res.get("complete") and res.get("mechanism_answer") and (res.get("gates") or {}).get("total"):
                    print("RESULTS_VALID")
                    return 0
            except Exception:
                pass
        print("RESULTS_PENDING")
        return 2
    if cmd == "restart":
        upload_scripts(h)
        print(h.execute(kid, RESTART, timeout=60))
        time.sleep(3)
        print(h.execute(kid, STATUS, timeout=60))
        return 0
    if cmd == "deploy":
        upload_scripts(h)
        print("===PROBE===")
        print(h.execute(kid, PROBE, timeout=90))
        print("===LAUNCH===")
        print(h.execute(kid, LAUNCH, timeout=60))
        time.sleep(4)
        print("===STATUS===")
        print(h.execute(kid, STATUS, timeout=60))
        return 0
    raise SystemExit(f"unknown {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
