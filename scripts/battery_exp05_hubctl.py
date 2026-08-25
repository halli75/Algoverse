# JupyterHub helper for exp05. Credentials from env only. Never print secrets.
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

def _load_dotenv() -> None:
    for cand in (
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[1] / ".env.hub",
        Path.home() / ".battery_env",
    ):
        if not cand.is_file():
            continue
        for raw in cand.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv()
HUB = os.environ.get("EXP05_HUB", "http://35.89.128.116")
USER = os.environ.get("EXP05_HUB_USER", os.environ.get("JUPYTERHUB_USER", "asca-ec66"))
PASS = (
    os.environ.get("EXP05_HUB_PASSWORD")
    or os.environ.get("JUPYTERHUB_PASSWORD")
    or os.environ.get("HUB_PASSWORD")
    or ""
)
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("EXP05_HUB_PASSWORD unset")
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.uxsrf = ""

    def login(self) -> None:
        self.op.open(f"{HUB}/hub/login", timeout=20).read()
        xsrf = next(c.value for c in self.cj if c.name == "_xsrf" and c.path.startswith("/hub"))
        data = urllib.parse.urlencode(
            {"username": USER, "password": PASS, "_xsrf": xsrf}
        ).encode()
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

    def get(self, path: str):
        return self.req("GET", path)

    def post(self, path: str, body: dict | None = None):
        return self.req("POST", path, body or {})

    def put(self, path: str, body: dict):
        return self.req("PUT", path, body)

    def mkdir(self, path: str) -> None:
        try:
            self.put(f"/api/contents/{path}", {"type": "directory"})
        except Exception:
            pass

    def put_text(self, path: str, text: str) -> None:
        self.put(
            f"/api/contents/{path}",
            {"type": "file", "format": "text", "content": text},
        )

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
            header=[
                f"Cookie: {self._cookie_header()}",
                f"X-XSRFToken: {self.uxsrf}",
            ],
            timeout=timeout,
        )
        mid = uuid.uuid4().hex
        ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": mid,
                        "username": "exp05",
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
        "Algoverse/scripts/battery_exp05_run.py": root / "scripts" / "battery_exp05_run.py",
        "Algoverse/scripts/battery_exp05_boot.py": root / "scripts" / "battery_exp05_boot.py",
        "algoverse_run/battery/exp05/battery_exp05_run.py": root / "scripts" / "battery_exp05_run.py",
        "algoverse_run/battery/exp05/items.json": root / "artifacts" / "battery" / "exp05" / "items.json",
        "algoverse_run/battery/exp05/PROTOCOL.md": root / "artifacts" / "battery" / "exp05" / "PROTOCOL.md",
    }
    h.mkdir("algoverse_run/battery")
    h.mkdir("algoverse_run/battery/exp05")
    h.mkdir("Algoverse/scripts")
    for dest, src in files.items():
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import json, os, subprocess, time
from pathlib import Path
home = Path.home()
print('HOME', home)
print('CWD', os.getcwd())
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
print('CUDA_VIS', os.environ.get('CUDA_VISIBLE_DEVICES'))
for p in [home/'algoverse_run', home/'algoverse_run'/'emotic_data', home/'algoverse_run'/'emotic_split.json',
          home/'Algoverse'/'scripts'/'battery_exp05_run.py', home/'algoverse_run'/'battery'/'A100.lock']:
    print(('OK' if p.exists() else 'MISS'), p)
lock = home/'algoverse_run'/'battery'/'A100.lock'
if lock.exists():
    print('LOCK', lock.read_text()[:800])
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', hits)
print('HF_TOKEN', 'yes' if (home/'.hf_token').exists() or os.environ.get('HF_TOKEN') else 'no')
try:
    print(subprocess.check_output(['nvidia-smi','-L'], text=True))
    print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
except Exception as e:
    print('smi', e)
print('PY', subprocess.check_output(['which','python3'], text=True).strip())
"""


LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
benv = home / '.battery_env'
if benv.is_file():
    for raw in benv.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:]
        k, _, v = line.partition('=')
        k, v = k.strip(), v.strip().strip(chr(39)+chr(34))
        if k and k not in os.environ:
            os.environ[k] = v
for name, path in (('HF_TOKEN', home/'.hf_token'), ('XAI_API_KEY', home/'.xai_api_key')):
    if not os.environ.get(name) and path.is_file():
        os.environ[name] = path.read_text().strip()
if os.environ.get('HF_TOKEN'):
    os.environ.setdefault('HUGGING_FACE_HUB_TOKEN', os.environ['HF_TOKEN'])
run = home/'algoverse_run'/'battery'/'exp05'
run.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env['CUDA_VISIBLE_DEVICES'] = '1'
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP05'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_N'] = '32'
env['E2E_REPO'] = str(home/'Algoverse')
script = home/'Algoverse'/'scripts'/'battery_exp05_boot.py'
out = open(run/'nohup.out', 'wb', buffering=0)
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
"""


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    if cmd == "probe":
        kid = h.new_kernel()
        print(h.execute(kid, PROBE, timeout=60))
        return 0
    if cmd == "status":
        kid = h.new_kernel()
        code = r"""
import subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp05'
for n in ['heartbeat.json','results.json','nohup.out','pid']:
    p = run/n
    print('====', n, 'exists' if p.exists() else 'MISS', p.stat().st_size if p.exists() else 0)
    if p.exists() and n != 'nohup.out':
        print(p.read_text()[:2000])
    elif p.exists():
        t = p.read_text(errors='replace')
        print(t[-2500:])
pidp = run/'pid'
if pidp.exists():
    pid = pidp.read_text().strip()
    print('==== PS')
    print(subprocess.check_output(['ps','-p',pid,'-o','pid,etime,cmd'], text=True, stderr=subprocess.STDOUT))
print('==== GPU1')
print(subprocess.check_output(['nvidia-smi','-i','1'], text=True))
lk = Path.home()/'algoverse_run'/'battery'/'A100.lock'
print('==== LOCK')
print(lk.read_text() if lk.exists() else 'no lock')
"""
        print(h.execute(kid, code, timeout=60))
        return 0
    if cmd == "pull":
        kid = h.new_kernel()
        code = r"""
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp05'
for n in ['heartbeat.json','results.json']:
    p = run/n
    print('FILE', n)
    print(p.read_text() if p.exists() else '')
    print('ENDFILE', n)
"""
        text = h.execute(kid, code, timeout=45)
        dest = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp05"
        dest.mkdir(parents=True, exist_ok=True)
        cur = None
        buf = []
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
        return 0
    if cmd == "relaunch":
        kid = h.new_kernel()
        print(
            h.execute(
                kid,
                r"""
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp05'
src = run/'results.json'
if src.exists():
    dest = run/'results_run2.json' if (run/'results_run1.json').exists() else run/'results_run1.json'
    dest.write_text(src.read_text())
    print('archived', dest, dest.stat().st_size)
else:
    print('no results to archive')
""",
                timeout=30,
            )
        )
        cmd = "deploy"
    if cmd == "deploy":
        upload_scripts(h)
        kid = h.new_kernel()
        print("===PROBE===")
        print(h.execute(kid, PROBE, timeout=90))
        print("===LAUNCH===")
        print(h.execute(kid, LAUNCH, timeout=60))
        time.sleep(3)
        print("===TAIL===")
        print(
            h.execute(
                kid,
                "from pathlib import Path; p=Path.home()/'algoverse_run'/'battery'/'exp05'/'nohup.out'; print(p.read_text(errors='replace')[-2000:] if p.exists() else 'no out')",
                timeout=30,
            )
        )
        return 0
    raise SystemExit(f"unknown cmd {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
