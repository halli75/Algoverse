# JupyterHub helper for exp06. Credentials from env only. Never print secrets.
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


def _load_local_env() -> None:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import battery_adapter as ba

        ba.source_battery_env()
    except Exception:
        p = ROOT / ".env"
        if p.is_file():
            for raw in p.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'").strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v


_load_local_env()

HUB = os.environ.get("EXP06_HUB", os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"))
USER = os.environ.get("EXP06_HUB_USER", os.environ.get("JUPYTERHUB_USER", "asca-ec66"))
PASS = os.environ.get("EXP06_HUB_PASSWORD", os.environ.get("JUPYTERHUB_PASSWORD", ""))
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("JUPYTERHUB_PASSWORD / EXP06_HUB_PASSWORD unset")
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
        url = (
            f"{BASE.replace('http://', 'ws://').replace('https://', 'wss://')}"
            f"/api/kernels/{kid}/channels?session_id={sid}"
        )
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
                        "username": "exp06",
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
        "Algoverse/scripts/battery_exp06_core.py": ROOT / "scripts" / "battery_exp06_core.py",
        "Algoverse/scripts/battery_exp06_run.py": ROOT / "scripts" / "battery_exp06_run.py",
        "Algoverse/scripts/battery_exp06_boot.py": ROOT / "scripts" / "battery_exp06_boot.py",
        "Algoverse/scripts/battery_exp06_cell.py": ROOT / "scripts" / "battery_exp06_cell.py",
        "Algoverse/data/battery/exp06_waiting.json": ROOT / "data" / "battery" / "exp06_waiting.json",
        "algoverse_run/battery/exp06/battery_exp06_run.py": ROOT / "scripts" / "battery_exp06_run.py",
        "algoverse_run/battery/exp06/battery_exp06_core.py": ROOT / "scripts" / "battery_exp06_core.py",
        "algoverse_run/battery/exp06/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
        "algoverse_run/battery/exp06/exp06_waiting.json": ROOT / "data" / "battery" / "exp06_waiting.json",
    }
    for d in (
        "Algoverse/scripts",
        "Algoverse/data",
        "Algoverse/data/battery",
        "algoverse_run/battery",
        "algoverse_run/battery/exp06",
    ):
        h.mkdir(d)
    for dest, src in files.items():
        if not src.exists():
            print(f"skip missing {src.name}", flush=True)
            continue
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


PROBE = r"""
import json, os, subprocess
from pathlib import Path
home = Path.home()
print('HOME', home)
print('USER', os.environ.get('USER') or os.environ.get('JUPYTERHUB_USER'))
print('CUDA_VIS', os.environ.get('CUDA_VISIBLE_DEVICES'))
print('battery_env', (home/'.battery_env').exists(), 'hf', (home/'.hf_token').exists(), 'xai', (home/'.xai_api_key').exists())
for p in [home/'algoverse_run', home/'algoverse_run'/'emotic_data', home/'algoverse_run'/'emotic_split.json',
          home/'Algoverse'/'scripts'/'battery_exp06_run.py', home/'Algoverse'/'scripts'/'battery_adapter.py',
          home/'Algoverse'/'data'/'battery'/'exp06_waiting.json', home/'algoverse_run'/'battery'/'A100.lock']:
    print(('OK' if p.exists() else 'MISS'), p)
lock = home/'algoverse_run'/'battery'/'A100.lock'
if lock.exists():
    print('LOCK_FILE', lock.is_file(), 'LOCK_DIR', lock.is_dir())
    if lock.is_file():
        print('LOCK', lock.read_text()[:1200])
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', bool(hits))
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
run = home/'algoverse_run'/'battery'/'exp06'
print('exp06_dir', list(p.name for p in run.iterdir()) if run.exists() else None)
for n in ('heartbeat.json','results.json','nohup.out','pid','nohup.pid'):
    p = run/n
    if p.exists():
        print('HAVE', n, p.stat().st_size)
"""


LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp06'
run.mkdir(parents=True, exist_ok=True)
pidp = run/'nohup.pid'
if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        st = Path(f'/proc/{old}/stat')
        state = st.read_text().split()[2] if st.exists() else 'Z'
        if state != 'Z':
            os.kill(old, 0)
            print('ALREADY_RUNNING', old, state)
            raise SystemExit(0)
        print('old_pid_zombie', old)
    except SystemExit:
        raise
    except Exception:
        pass
smoke = run/'results.json'
if smoke.exists() and '"tier": "smoke"' in smoke.read_text()[:400]:
    (run/'results_smoke.json').write_text(smoke.read_text())
    print('kept results_smoke.json')
env = os.environ.copy()
benv = home/'.battery_env'
if benv.is_file():
    for raw in benv.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        k, _, v = line.partition('=')
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in env:
            env[k] = v
for name, path in (('HF_TOKEN', home/'.hf_token'), ('XAI_API_KEY', home/'.xai_api_key')):
    if not env.get(name) and path.is_file():
        env[name] = path.read_text().strip()
if env.get('HF_TOKEN'):
    env.setdefault('HUGGING_FACE_HUB_TOKEN', env['HF_TOKEN'])
env['CUDA_VISIBLE_DEVICES'] = '2'
env['EXP06_GPU'] = '2'
env['E2E_ROOT'] = str(home/'algoverse_run')
env['EXP06_OUT'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = os.environ.get('E2E_TIER', 'smoke')
env['E2E_REPO'] = str(home/'Algoverse')
env['E2E_LOCK'] = str(home/'algoverse_run'/'battery'/'A100.lock')
print('env_sourced', 'HF_TOKEN' if env.get('HF_TOKEN') else 'no_hf', 'XAI' if env.get('XAI_API_KEY') else 'no_xai')
script = home/'Algoverse'/'scripts'/'battery_exp06_boot.py'
out = open(run/'nohup.out', 'ab', buffering=0)
proc = subprocess.Popen(
    ['python3', '-u', str(script)],
    cwd=str(home/'Algoverse'),
    env=env,
    stdout=out,
    stderr=out,
    start_new_session=True,
)
pidp.write_text(str(proc.pid))
print('LAUNCHED', proc.pid)
print('OUT', run/'nohup.out')
"""


def pull(h: Hub, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("heartbeat.json", "results.json", "checkpoint.json", "STATUS.md", "run.log", "nohup.out", "boot.log"):
        try:
            text = h.get_text(f"algoverse_run/battery/exp06/{name}")
            if text:
                (dest / name).write_text(text, encoding="utf-8")
                print(f"pulled {name} n={len(text)}", flush=True)
        except Exception as e:
            print(f"pull skip {name}: {type(e).__name__}", flush=True)


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    dest = ROOT / "artifacts" / "battery" / "exp06"
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
    if cmd == "status":
        kid = h.new_kernel()
        code = r"""
import subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp06'
for n in ['heartbeat.json','results.json','STATUS.md','nohup.out','nohup.pid','boot.log','run.log']:
    p = run/n
    print('====', n, 'exists' if p.exists() else 'MISS', p.stat().st_size if p.exists() else 0)
    if p.exists() and n != 'nohup.out':
        print(p.read_text(errors='replace')[:2000])
    elif p.exists():
        print(p.read_text(errors='replace')[-2500:])
pidp = run/'nohup.pid'
if pidp.exists():
    pid = pidp.read_text().strip()
    print('==== PS')
    print(subprocess.check_output(['ps','-p',pid,'-o','pid,etime,cmd'], text=True, stderr=subprocess.STDOUT))
print('==== GPU2')
print(subprocess.check_output(['nvidia-smi','-i','2'], text=True))
lk = Path.home()/'algoverse_run'/'battery'/'A100.lock'
print('==== LOCK')
print(lk.read_text()[:1500] if lk.exists() else 'no lock')
"""
        out = h.execute(kid, code, timeout=60)
        Path(os.environ.get("TEMP", ".")).joinpath("exp06_status_out.txt").write_text(out, encoding="utf-8")
        print(out.encode("ascii", "replace").decode("ascii"), flush=True)
        pull(h, dest)
        return 0
    if cmd == "full":
        upload(h)
        kid = h.new_kernel()
        launch_full = LAUNCH.replace(
            "os.environ.get('E2E_TIER', 'smoke')",
            "'full'",
        ).replace(
            "env['E2E_TIER'] = 'full'",
            "env['E2E_TIER'] = 'full'\nenv['EXP06_N_IMG'] = '4'",
        )
        print(h.execute(kid, launch_full, timeout=60))
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
