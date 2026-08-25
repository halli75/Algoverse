# JupyterHub helper for exp03. Credentials from env only. Never print secrets.
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

HUB = os.environ.get("EXP03_HUB", os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"))
USER = os.environ.get("EXP03_HUB_USER", os.environ.get("JUPYTERHUB_USER", "asca-ec66"))
PASS = os.environ.get("EXP03_HUB_PASSWORD", os.environ.get("JUPYTERHUB_PASSWORD", ""))
BASE = f"{HUB}/user/{USER}"
ROOT = Path(__file__).resolve().parents[1]


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("EXP03_HUB_PASSWORD / JUPYTERHUB_PASSWORD unset")
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
                        "username": "exp03",
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
        "Algoverse/scripts/battery_exp03_run.py": ROOT / "scripts" / "battery_exp03_run.py",
        "Algoverse/scripts/battery_exp03_boot.py": ROOT / "scripts" / "battery_exp03_boot.py",
        "algoverse_run/battery/exp03/battery_exp03_run.py": ROOT / "scripts" / "battery_exp03_run.py",
        "algoverse_run/battery/exp03/battery_exp03_boot.py": ROOT / "scripts" / "battery_exp03_boot.py",
        "algoverse_run/battery/exp03/ADVISOR_LOCK.md": ROOT / "artifacts" / "battery" / "exp03" / "ADVISOR_LOCK.md",
    }
    for d in (
        "Algoverse/scripts",
        "algoverse_run/battery",
        "algoverse_run/battery/exp03",
    ):
        h.mkdir(d)
    for dest, src in files.items():
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
print('HOME', home)
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
for p in [
    home/'algoverse_run',
    home/'algoverse_run'/'emotic_data',
    home/'algoverse_run'/'emotic_split.json',
    home/'Algoverse'/'scripts'/'battery_exp03_run.py',
    home/'Algoverse'/'scripts'/'battery_exp03_boot.py',
    home/'.hf_token',
    home/'.xai_api_key',
    home/'.battery_env',
]:
    print(('OK' if p.exists() else 'MISS'), p)
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', bool(hits))
print('HF_FILE', (home/'.hf_token').exists())
print('XAI_FILE', (home/'.xai_api_key').exists())
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
lock = home/'algoverse_run'/'battery'/'A100.lock'
print('LOCK', lock.exists(), lock.read_text()[:400] if lock.exists() else '')
"""


KILL = r"""
import os, signal
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp03'
pidp = run/'nohup.pid'
if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        os.kill(old, signal.SIGTERM)
        print('KILLED', old)
        pidp.unlink(missing_ok=True)
    except ProcessLookupError:
        print('DEAD', old if 'old' in dir() else None)
        pidp.unlink(missing_ok=True)
    except Exception as e:
        print('KILL_FAIL', type(e).__name__)
else:
    print('NO_PIDFILE')
"""


LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp03'
run.mkdir(parents=True, exist_ok=True)
pidp = run/'nohup.pid'
if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        os.kill(old, 0)
        print('ALREADY_RUNNING', old)
        raise SystemExit(0)
    except Exception:
        pass
# source host env files without printing
env = os.environ.copy()
benv = home/'.battery_env'
if benv.exists():
    for line in benv.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        if s.startswith('export '):
            s = s[7:].strip()
        k, _, v = s.partition('=')
        k, v = k.strip(), v.strip().strip("'").strip('"')
        if k and v:
            env[k] = v
hf = home/'.hf_token'
if hf.exists() and not env.get('HF_TOKEN'):
    env['HF_TOKEN'] = hf.read_text().strip()
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
xk = home/'.xai_api_key'
if xk.exists() and not env.get('XAI_API_KEY'):
    env['XAI_API_KEY'] = xk.read_text().strip()
env['CUDA_VISIBLE_DEVICES'] = '6'
env['EXP03_GPU'] = '6'
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP03'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_DATA'] = str(run/'data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = 'smoke'
env['E2E_REPO'] = str(home/'Algoverse')
env['E2E_LOCK'] = str(home/'algoverse_run'/'battery'/'A100.lock')
env['HF_HUB_DISABLE_XET'] = '1'
env['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
script = home/'Algoverse'/'scripts'/'battery_exp03_boot.py'
if not script.exists():
    script = run/'battery_exp03_boot.py'
out = open(run/'nohup.out', 'ab', buffering=0)
proc = subprocess.Popen(
    ['python3', '-u', str(script)],
    cwd=str(home/'Algoverse') if (home/'Algoverse').exists() else str(run),
    env=env,
    stdout=out,
    stderr=out,
    start_new_session=True,
)
pidp.write_text(str(proc.pid))
print('LAUNCHED', proc.pid)
print('XAI_SET', bool(env.get('XAI_API_KEY')))
print('HF_SET', bool(env.get('HF_TOKEN')))
"""


def pull(h: Hub, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("heartbeat.json", "results.json", "nohup.out", "manifest.json", "caption_cache.json"):
        try:
            text = h.get_text(f"algoverse_run/battery/exp03/{name}")
            if text:
                # never stash completions; caption_cache is literal scene text only
                (dest / name).write_text(text, encoding="utf-8")
                print(f"pulled {name} n={len(text)}", flush=True)
        except Exception as e:
            print(f"pull skip {name}: {e}", flush=True)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    dest = ROOT / "artifacts" / "battery" / "exp03"
    if cmd == "upload":
        upload(h)
        return 0
    if cmd == "pull":
        pull(h, dest)
        return 0
    if cmd == "probe":
        kid = h.new_kernel()
        print(h.execute(kid, PROBE, timeout=90))
        return 0
    if cmd == "restart":
        upload(h)
        kid = h.new_kernel()
        print(h.execute(kid, KILL, timeout=30))
        print(h.execute(kid, LAUNCH, timeout=60))
        time.sleep(4)
        pull(h, dest)
        return 0
    upload(h)
    kid = h.new_kernel()
    print(h.execute(kid, PROBE, timeout=90))
    print(h.execute(kid, LAUNCH, timeout=60))
    time.sleep(4)
    pull(h, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
