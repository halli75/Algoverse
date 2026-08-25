# JupyterHub helper for exp07. Credentials from env / gitignored .env only.
# Never print secrets. Own kernel + nohup. Does not touch the overseer UI tab.
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

ROOT = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    for envp in (ROOT / ".env", ROOT / ".env.hub"):
        if not envp.is_file():
            continue
        for raw in envp.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v


_load_local_env()
HUB = os.environ.get("EXP07_HUB", os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"))
USER = os.environ.get("EXP07_HUB_USER", os.environ.get("JUPYTERHUB_USER", "asca-ec66"))
PASS = (
    os.environ.get("EXP07_HUB_PASSWORD")
    or os.environ.get("JUPYTERHUB_PASSWORD")
    or os.environ.get("EXP05_HUB_PASSWORD")
    or os.environ.get("BATTERY_SSH_PASS")
    or os.environ.get("BATTERY_PASS")
    or ""
)
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("hub password unset (env / .env)")
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
                        "username": "exp07",
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
    files = {
        "Algoverse/scripts/battery_exp07_run.py": ROOT / "scripts" / "battery_exp07_run.py",
        "Algoverse/scripts/battery_exp07_boot.py": ROOT / "scripts" / "battery_exp07_boot.py",
        "Algoverse/scripts/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
        "algoverse_run/battery/exp07/battery_exp07_run.py": ROOT / "scripts" / "battery_exp07_run.py",
        "algoverse_run/battery/exp07/battery_exp07_boot.py": ROOT / "scripts" / "battery_exp07_boot.py",
        "algoverse_run/battery/exp07/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
    }
    h.mkdir("algoverse_run/battery")
    h.mkdir("algoverse_run/battery/exp07")
    h.mkdir("Algoverse/scripts")
    for dest, src in files.items():
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
print('HOME', home)
print('CWD', os.getcwd())
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
print('battery_env', (home/'.battery_env').exists())
print('hf_token_file', (home/'.hf_token').exists())
print('xai_file', (home/'.xai_api_key').exists())
for p in [home/'algoverse_run', home/'algoverse_run'/'emotic_data', home/'algoverse_run'/'emotic_split.json',
          home/'Algoverse'/'scripts'/'battery_exp07_run.py', home/'algoverse_run'/'battery'/'A100.lock']:
    print(('OK' if p.exists() else 'MISS'), p)
lock = home/'algoverse_run'/'battery'/'A100.lock'
if lock.exists():
    print('LOCK', lock.read_text()[:800])
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', bool(hits))
print('HF_TOKEN_ENV', bool(os.environ.get('HF_TOKEN')))
try:
    print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
except Exception as e:
    print('smi', type(e).__name__)
print('PY', subprocess.check_output(['which','python3'], text=True).strip())
"""


LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp07'
run.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
benv = home/'.battery_env'
if benv.is_file():
    n = 0
    for raw in benv.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:]
        k, _, v = line.partition('=')
        k, v = k.strip(), v.strip().strip("'").strip('"')
        if k and k not in env:
            env[k] = v
            n += 1
    print('sourced_battery_env', n)
env['CUDA_VISIBLE_DEVICES'] = '4'
env['EXP07_GPU'] = '4'
env['E2E_ROOT'] = str(home/'algoverse_run')
env['EXP07_DIR'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_LOCK'] = str(home/'algoverse_run'/'battery'/'A100.lock')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = env.get('E2E_TIER') or 'full'
env['E2E_REPO'] = str(home/'Algoverse')
env['HF_HUB_DISABLE_XET'] = '1'
env['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
if not env.get('HF_TOKEN') and (home/'.hf_token').is_file():
    env['HF_TOKEN'] = (home/'.hf_token').read_text().strip()
if env.get('HF_TOKEN'):
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
script = home/'Algoverse'/'scripts'/'battery_exp07_boot.py'
if not script.exists():
    script = run/'battery_exp07_boot.py'
out = open(run/'nohup.out', 'ab', buffering=0)
proc = subprocess.Popen(
    ['python3', '-u', str(script)],
    cwd=str(home/'Algoverse'),
    env=env,
    stdout=out,
    stderr=out,
    start_new_session=True,
)
(run/'pid').write_text(str(proc.pid))
print('LAUNCHED', proc.pid)
print('OUT', run/'nohup.out')
print('HF_TOKEN_SET', bool(env.get('HF_TOKEN')))
"""


STATUS = r"""
import subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp07'
for n in ['heartbeat.json','results.json','nohup.out','pid','STATUS.md']:
    p = run/n
    print('====', n, 'exists' if p.exists() else 'MISS', p.stat().st_size if p.exists() else 0)
    if p.exists() and n != 'nohup.out':
        print(p.read_text()[:2000])
    elif p.exists():
        print(p.read_text(errors='replace')[-2500:])
pidp = run/'pid'
if pidp.exists():
    pid = pidp.read_text().strip()
    print('==== PS')
    try:
        print(subprocess.check_output(['ps','-p',pid,'-o','pid,etime,cmd'], text=True, stderr=subprocess.STDOUT))
    except Exception as e:
        print('ps', type(e).__name__)
print('==== GPU4')
print(subprocess.check_output(['nvidia-smi','-i','4'], text=True))
lk = Path.home()/'algoverse_run'/'battery'/'A100.lock'
print('==== LOCK')
print(lk.read_text() if lk.exists() else 'no lock')
"""


def _pull_text(h: Hub, kid: str) -> None:
    code = r"""
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp07'
for n in ['heartbeat.json','results.json','STATUS.md']:
    p = run/n
    print('FILE', n)
    print(p.read_text() if p.exists() else '')
    print('ENDFILE', n)
"""
    text = h.execute(kid, code, timeout=45)
    dest = ROOT / "artifacts" / "battery" / "exp07"
    dest.mkdir(parents=True, exist_ok=True)
    cur = None
    buf: list[str] = []
    for line in text.splitlines(True):
        if line.startswith("FILE "):
            cur = line.split(" ", 1)[1].strip()
            buf = []
        elif line.startswith("ENDFILE "):
            if cur:
                (dest / cur).write_text("".join(buf), encoding="utf-8")
                print(f"pulled {cur} bytes={len(''.join(buf))}", flush=True)
            cur = None
        elif cur:
            buf.append(line)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    if cmd == "probe":
        kid = h.new_kernel()
        print(h.execute(kid, PROBE, timeout=60))
        return 0
    if cmd == "tail":
        kid = h.new_kernel()
        code = r"""
import os, subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp07'
p = run/'nohup.out'
print('nohup_exists', p.exists(), 'bytes', p.stat().st_size if p.exists() else 0)
if p.exists():
    t = p.read_text(errors='replace')
    print(t[-3500:])
print('==== CKPT')
ck = run/'checkpoint.json'
print('ckpt', ck.exists(), ck.stat().st_size if ck.exists() else 0)
print('==== PS python')
print(subprocess.check_output(['ps','-u',os.environ.get('USER','jupyter-asca-ec66'),'-o','pid,etime,cmd'], text=True, stderr=subprocess.STDOUT)[-2000:])
print('==== DMESG')
try:
    print(subprocess.check_output(['dmesg','-T'], text=True, stderr=subprocess.STDOUT)[-1500:])
except Exception as e:
    print('dmesg', type(e).__name__)
"""
        text = h.execute(kid, code, timeout=60)
        dest = ROOT / "artifacts" / "battery" / "exp07" / "host_tail.txt"
        dest.write_text(text, encoding="utf-8")
        print(text.encode("ascii", "replace").decode("ascii")[-4000:], flush=True)
        return 0
    if cmd == "status":
        kid = h.new_kernel()
        text = h.execute(kid, STATUS, timeout=60)
        dest = ROOT / "artifacts" / "battery" / "exp07" / "host_status.txt"
        dest.write_text(text, encoding="utf-8")
        print(f"wrote {dest} bytes={len(text)}", flush=True)
        safe = text.encode("ascii", "replace").decode("ascii")
        print(safe[-4000:], flush=True)
        return 0
    if cmd == "pull":
        kid = h.new_kernel()
        _pull_text(h, kid)
        return 0
    if cmd == "deploy":
        upload_scripts(h)
        kid = h.new_kernel()
        print("===PROBE===")
        print(h.execute(kid, PROBE, timeout=90))
        print("===LAUNCH===")
        print(h.execute(kid, LAUNCH, timeout=60))
        time.sleep(4)
        print("===STATUS===")
        print(h.execute(kid, STATUS, timeout=60))
        _pull_text(h, kid)
        return 0
    raise SystemExit(f"unknown cmd {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
