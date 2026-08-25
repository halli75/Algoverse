# JupyterHub helper for exp01. Credentials from env only. Never print secrets.
# Own kernel + nohup. Does not touch the overseer UI tab.
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_env_file(path: Path) -> int:
    n = 0
    if not path.is_file():
        return 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n


_load_env_file(ROOT / ".env")

HUB = os.environ.get("EXP01_HUB", os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"))
USER = os.environ.get("EXP01_HUB_USER", os.environ.get("JUPYTERHUB_USER", os.environ.get("BATTERY_USER", "asca-ec66")))
PASS = (
    os.environ.get("EXP01_HUB_PASSWORD")
    or os.environ.get("JUPYTERHUB_PASSWORD")
    or os.environ.get("BATTERY_PASS")
    or os.environ.get("BATTERY_SSH_PASS")
    or ""
)
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("EXP01_HUB_PASSWORD / JUPYTERHUB_PASSWORD unset")
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.uxsrf = ""

    def login(self) -> None:
        self.op.open(f"{HUB}/hub/login", timeout=20).read()
        xsrf = next(c.value for c in self.cj if c.name == "_xsrf" and str(c.path).startswith("/hub"))
        data = urllib.parse.urlencode({"username": USER, "password": PASS, "_xsrf": xsrf}).encode()
        req = urllib.request.Request(f"{HUB}/hub/login", data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Referer", f"{HUB}/hub/login")
        self.op.open(req, timeout=40)
        try:
            self.uxsrf = next(c.value for c in self.cj if c.name == "_xsrf" and "/user/" in str(c.path))
        except StopIteration:
            self.uxsrf = xsrf

    def _cookie_header(self) -> str:
        return "; ".join(f"{c.name}={c.value}" for c in self.cj)

    def req(self, method: str, path: str, body=None, timeout: int = 60):
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

    def put(self, path: str, body: dict):
        return self.req("PUT", path, body, timeout=120)

    def get(self, path: str):
        return self.req("GET", path)

    def post(self, path: str, body=None):
        return self.req("POST", path, body or {})

    def mkdir(self, path: str) -> None:
        try:
            self.put(f"/api/contents/{path}", {"type": "directory"})
        except Exception:
            pass

    def put_text(self, path: str, text: str) -> None:
        self.put(f"/api/contents/{path}", {"type": "file", "format": "text", "content": text})

    def get_text(self, path: str) -> str:
        rec = self.get(f"/api/contents/{path}")
        if rec.get("format") == "base64":
            import base64

            return base64.b64decode(rec.get("content") or "").decode("utf-8", "replace")
        return rec.get("content") or ""

    def new_kernel(self) -> str:
        rec = self.post("/api/kernels", {"name": "python3"})
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
                        "username": "exp01",
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


def upload(h: Hub) -> None:
    files = {
        "Algoverse/scripts/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
        "Algoverse/scripts/battery_exp01_run.py": ROOT / "scripts" / "battery_exp01_run.py",
        "Algoverse/scripts/battery_exp01_boot.py": ROOT / "scripts" / "battery_exp01_boot.py",
        "Algoverse/data/battery/exp01_lotteries.json": ROOT / "data" / "battery" / "exp01_lotteries.json",
        "algoverse_run/battery/exp01/battery_exp01_run.py": ROOT / "scripts" / "battery_exp01_run.py",
        "algoverse_run/battery/exp01/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
        "algoverse_run/battery/exp01/exp01_lotteries.json": ROOT / "data" / "battery" / "exp01_lotteries.json",
        "algoverse_run/battery/exp01/PLAN.md": ROOT / "artifacts" / "battery" / "exp01" / "PLAN.md",
    }
    for d in (
        "Algoverse/scripts",
        "Algoverse/data",
        "Algoverse/data/battery",
        "algoverse_run/battery",
        "algoverse_run/battery/exp01",
    ):
        h.mkdir(d)
    for dest, src in files.items():
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import json, os, subprocess
from pathlib import Path
home = Path.home()
print('HOME', home)
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
for p in [home/'algoverse_run', home/'algoverse_run'/'emotic_data', home/'algoverse_run'/'emotic_split.json',
          home/'Algoverse'/'scripts'/'battery_exp01_run.py', home/'Algoverse'/'scripts'/'battery_adapter.py',
          home/'Algoverse'/'data'/'battery'/'exp01_lotteries.json']:
    print(('OK' if p.exists() else 'MISS'), p)
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', bool(hits))
print('HF_TOKEN', 'yes' if (home/'.hf_token').exists() or os.environ.get('HF_TOKEN') else 'no')
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
locks = home/'algoverse_run'/'battery'/'locks'
print('LOCKS', list(locks.glob('gpu_*.json')) if locks.exists() else 'none')
"""


LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp01'
run.mkdir(parents=True, exist_ok=True)
pidp = run/'nohup.pid'

def _alive(pid: int) -> bool:
    try:
        st = Path(f'/proc/{pid}/stat').read_text().split()
        if len(st) > 2 and st[2] == 'Z':
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False

if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        if _alive(old):
            print('ALREADY_RUNNING', old)
            raise SystemExit(0)
        print('STALE_PID', old)
    except SystemExit:
        raise
    except Exception:
        pass
env = os.environ.copy()
benv = home/'.battery_env'
if benv.is_file():
    for raw in benv.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in env:
            env[k] = v
env['CUDA_VISIBLE_DEVICES'] = '0'
env['EXP01_GPU'] = '0'
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP01'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = 'full'
env['E2E_REPO'] = str(home/'Algoverse')
env['EXP01_LOTTERIES'] = str(home/'Algoverse'/'data'/'battery'/'exp01_lotteries.json')
hf = home/'.hf_token'
if hf.exists() and not env.get('HF_TOKEN'):
    env['HF_TOKEN'] = hf.read_text().strip()
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
print('env_sourced', 'HF_TOKEN' if env.get('HF_TOKEN') else 'no_hf', 'XAI' if env.get('XAI_API_KEY') else 'no_xai')
script = home/'Algoverse'/'scripts'/'battery_exp01_boot.py'
# nohup + background so the launch kernel is not the parent
cmd = f"nohup python3 -u {script} >> {run}/nohup.out 2>&1 & echo $!"
proc = subprocess.run(
    ['bash', '-lc', cmd],
    cwd=str(home/'Algoverse'),
    env=env,
    capture_output=True,
    text=True,
)
pid = (proc.stdout or '').strip().splitlines()[-1] if proc.stdout else ''
pidp.write_text(pid)
print('LAUNCHED', pid, 'stderr', (proc.stderr or '')[:200])
"""


def pull(h: Hub, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("heartbeat.json", "results.json", "results.partial.json", "run.log", "nohup.out", "pools.json", "trials.jsonl"):
        try:
            text = h.get_text(f"algoverse_run/battery/exp01/{name}")
            if text:
                (dest / name).write_text(text, encoding="utf-8")
                print(f"pulled {name} n={len(text)}", flush=True)
        except Exception as e:
            print(f"pull skip {name}: {e}", flush=True)


DIAG = r"""
import os, json, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp01'
print('=== processes ===')
print(subprocess.check_output("ps -u $USER -o pid,ppid,stat,etime,pcpu,pmem,cmd --sort=etime | head -80", shell=True, text=True))
print('=== gpu0 pids ===')
print(subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory,process_name','--format=csv'], text=True))
print('=== trials ===')
tp = run/'trials.jsonl'
print('trials', tp.exists(), tp.stat().st_size if tp.exists() else 0)
if tp.exists():
    n=sum(1 for _ in tp.open())
    print('n_lines', n)
print('=== dmesg oom ===')
try:
    out=subprocess.check_output("dmesg -T 2>/dev/null | tail -40", shell=True, text=True)
    print(out[-2000:])
except Exception as e:
    print('dmesg', e)
print('=== last nohup ===')
p=run/'nohup.out'
if p.exists():
    print('\n'.join(p.read_text(errors='replace').splitlines()[-15:]))
"""


STATUS = r"""
import os, json, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp01'
pidp = run/'nohup.pid'
pid = pidp.read_text().strip() if pidp.exists() else ''
alive = False
if pid:
    try:
        os.kill(int(pid), 0)
        alive = True
    except Exception:
        alive = False
print('PID', pid, 'ALIVE', alive)
for name in ('heartbeat.json','results.json','results.partial.json','pools.json','nohup.pid'):
    p = run/name
    print(('OK' if p.exists() else 'MISS'), name, p.stat().st_size if p.exists() else 0)
log = run/'run.log'
nout = run/'nohup.out'
for p in (log, nout):
    if p.exists():
        t = p.read_text(errors='replace')
        print('---', p.name, 'tail ---')
        print('\n'.join(t.splitlines()[-25:]))
if (run/'heartbeat.json').exists():
    print('HB', (run/'heartbeat.json').read_text()[:400])
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv'], text=True))
print(subprocess.check_output(['ps','-p', pid or '1', '-o','pid,etime,pcpu,pmem,cmd'], text=True, stderr=subprocess.STDOUT) if pid else 'no pid')
"""


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    dest = ROOT / "artifacts" / "battery" / "exp01"
    if cmd == "upload":
        upload(h)
        return 0
    if cmd == "pull":
        pull(h, dest)
        return 0
    if cmd == "probe":
        kid = h.new_kernel()
        print(h.execute(kid, PROBE, timeout=60))
        return 0
    if cmd == "status":
        kid = h.new_kernel()
        print(h.execute(kid, STATUS, timeout=60))
        pull(h, dest)
        return 0
    if cmd == "diag":
        kid = h.new_kernel()
        print(h.execute(kid, DIAG, timeout=60))
        return 0
    upload(h)
    kid = h.new_kernel()
    print(h.execute(kid, PROBE, timeout=90))
    print(h.execute(kid, LAUNCH, timeout=60))
    time.sleep(3)
    pull(h, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
