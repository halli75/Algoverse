# JupyterHub helper for exp02. Credentials from gitignored .env only.
# Own kernel + nohup. Does not touch the overseer UI tab. Never print secrets.
# [[battery-campaign]]
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


def load_dotenv() -> None:
    envp = ROOT / ".env"
    if not envp.is_file():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            os.environ.setdefault(k, v)


load_dotenv()

HUB = os.environ.get("EXP02_HUB", os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"))
USER = os.environ.get("EXP02_HUB_USER", os.environ.get("JUPYTERHUB_USER", "asca-ec66"))
PASS = (
    os.environ.get("EXP02_HUB_PASSWORD")
    or os.environ.get("JUPYTERHUB_PASSWORD")
    or os.environ.get("EXP01_HUB_PASSWORD")
    or os.environ.get("EXP05_HUB_PASSWORD")
    or os.environ.get("BATTERY_SSH_PASS")
    or os.environ.get("BATTERY_PASS")
    or ""
)
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("hub password unset in gitignored .env")
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
                        "username": "exp02",
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
        "Algoverse/scripts/battery_exp02_pairs.py": ROOT / "scripts" / "battery_exp02_pairs.py",
        "Algoverse/scripts/battery_exp02_run.py": ROOT / "scripts" / "battery_exp02_run.py",
        "Algoverse/scripts/battery_exp02_boot.py": ROOT / "scripts" / "battery_exp02_boot.py",
        "algoverse_run/battery/exp02/battery_exp02_pairs.py": ROOT / "scripts" / "battery_exp02_pairs.py",
        "algoverse_run/battery/exp02/battery_exp02_run.py": ROOT / "scripts" / "battery_exp02_run.py",
        "algoverse_run/battery/exp02/battery_exp02_boot.py": ROOT / "scripts" / "battery_exp02_boot.py",
        "algoverse_run/battery/exp01/results.json": ROOT / "artifacts" / "battery" / "exp01" / "results.json",
    }
    for d in (
        "Algoverse/scripts",
        "algoverse_run/battery",
        "algoverse_run/battery/exp01",
        "algoverse_run/battery/exp02",
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
          home/'Algoverse'/'scripts'/'battery_exp02_pairs.py', home/'Algoverse'/'scripts'/'battery_exp02_run.py',
          home/'.battery_env', home/'.hf_token']:
    print(('OK' if p.exists() else 'MISS'), p.name if p.name else p)
print('battery_env', 'yes' if (home/'.battery_env').exists() else 'no')
print('hf_token_file', 'yes' if (home/'.hf_token').exists() else 'no')
cache = home/'.cache'/'huggingface'/'hub'
hits = list(cache.glob('models--google--gemma-4-E4B-it')) if cache.exists() else []
print('GEMMA_CACHE', bool(hits))
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
lock = home/'algoverse_run'/'battery'/'A100.lock'
print('LOCK', lock.exists())
if lock.exists():
    try:
        rec = json.loads(lock.read_text())
        holders = rec.get('holders') or {}
        print('HOLDERS', sorted(holders.keys()), 'n', len(holders))
    except Exception as e:
        print('LOCK_PARSE', type(e).__name__)
print('PGREP', subprocess.getoutput('pgrep -af battery_exp02 || true'))
"""


RESTART = r"""
import os, signal, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp02'
pidp = run/'nohup.pid'
if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        cmd = Path(f'/proc/{old}/cmdline').read_bytes().replace(b'\x00', b' ').decode('utf-8', 'replace')
        print('OLD_PID', old, cmd[:200])
        if 'battery_exp02' in cmd:
            os.kill(old, signal.SIGTERM)
            print('KILLED', old)
        else:
            print('STALE_PID_NOT_OURS')
            pidp.unlink()
    except Exception as e:
        print('PID_CLEAR', type(e).__name__)
        try:
            pidp.unlink()
        except Exception:
            pass
print('PGREP', subprocess.getoutput('pgrep -af battery_exp02 || true'))
"""


LAUNCH = r"""
import json, os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp02'
run.mkdir(parents=True, exist_ok=True)
pidp = run/'nohup.pid'
if pidp.exists():
    try:
        old = int(pidp.read_text().strip())
        cmd = Path(f'/proc/{old}/cmdline').read_bytes().replace(b'\x00', b' ').decode('utf-8', 'replace')
        if 'battery_exp02' in cmd:
            print('ALREADY_RUNNING', old)
            raise SystemExit(0)
        print('STALE_PID', old, cmd[:120])
        pidp.unlink()
    except SystemExit:
        raise
    except Exception:
        try:
            pidp.unlink()
        except Exception:
            pass
env = os.environ.copy()
# source ~/.battery_env without printing
benv = home/'.battery_env'
if benv.exists():
    for line in benv.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        if s.startswith('export '):
            s = s[7:].strip()
        k, _, v = s.partition('=')
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            env.setdefault(k, v)
hf = home/'.hf_token'
if hf.exists() and not env.get('HF_TOKEN'):
    env['HF_TOKEN'] = hf.read_text().strip()
    env['HUGGING_FACE_HUB_TOKEN'] = env['HF_TOKEN']
env['CUDA_VISIBLE_DEVICES'] = os.environ.get('EXP02_GPU', '4')
env['EXP02_GPU'] = os.environ.get('EXP02_GPU', '4')
env['E2E_ROOT'] = str(home/'algoverse_run')
env['E2E_EXP02'] = str(run)
env['E2E_OUT'] = str(run/'results.json')
env['E2E_HB'] = str(run/'heartbeat.json')
env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
env['E2E_NO_FALLBACK'] = '1'
env['E2E_TIER'] = 'full'
env['E2E_REPO'] = str(home/'Algoverse')
env['EXP02_REBUILD'] = os.environ.get('EXP02_REBUILD', '0')
env['EXP02_FAMILIES'] = os.environ.get('EXP02_FAMILIES', 'fear_anger,negative_neutral')
env['PYTHONUNBUFFERED'] = '1'
script = home/'Algoverse'/'scripts'/'battery_exp02_run.py'
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
"""


def pull(h: Hub, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in (
        "heartbeat.json",
        "results.json",
        "pairs.json",
        "checkpoint.json",
        "run.log",
        "nohup.out",
        "partial.json",
    ):
        try:
            text = h.get_text(f"algoverse_run/battery/exp02/{name}")
            if text:
                (dest / name).write_text(text, encoding="utf-8")
                print(f"pulled {name} n={len(text)}", flush=True)
        except Exception as e:
            print(f"pull skip {name}: {type(e).__name__}", flush=True)


STATUS = r"""
import json, os, subprocess
from pathlib import Path
home = Path.home()
run = home/'algoverse_run'/'battery'/'exp02'
print('pid_file', (run/'nohup.pid').read_text().strip() if (run/'nohup.pid').exists() else 'none')
print('PGREP', subprocess.getoutput('pgrep -af battery_exp02 || true'))
hb = run/'heartbeat.json'
if hb.exists():
    print('HB', hb.read_text()[:400])
print('pairs', (run/'pairs.json').exists(), 'ckpt', (run/'checkpoint.json').exists())
print('nohup_tail')
print(subprocess.getoutput('tail -n 20 '+str(run/'nohup.out')))
print(subprocess.getoutput("nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv"))
print('COMPUTE')
print(subprocess.getoutput("nvidia-smi --query-compute-apps=gpu_bus_id,pid,process_name,used_gpu_memory --format=csv"))
print('LOCK')
lock = home/'algoverse_run'/'battery'/'A100.lock'
print(lock.read_text()[:800] if lock.exists() else 'none')
print('LIVE_PY', subprocess.getoutput("ps -o pid,etime,cmd -p 2054402,2060717,2061476,2060968 2>/dev/null || true"))
"""


DIAG = r"""
import json, ast, collections
from pathlib import Path
import pandas as pd
home = Path.home()
csv = home/'algoverse_run'/'emotic_data'/'emotic_pre'/'train.csv'
split = json.loads((home/'algoverse_run'/'emotic_split.json').read_text())
eval_ids = set(split['eval_ids'])
df = pd.read_csv(csv)
def labs(x):
    if isinstance(x,str) and x.startswith('['):
        try: return set(map(str, ast.literal_eval(x)))
        except: return set()
    if isinstance(x,(list,tuple)): return set(map(str,x))
    return set()
df['rid'] = df['Folder'].astype(str)+'/'+df['Filename'].astype(str)
sci = df[df.rid.isin(eval_ids)]
print('eval_rows', len(sci), 'eval_ids', len(eval_ids), 'folders', sci['Folder'].nunique())
print(sci['Folder'].value_counts().head(20).to_string())
# image-level union
g = sci.groupby('rid')['Categorical_Labels'].apply(lambda s: set().union(*[labs(x) for x in s]))
fear = [i for i,L in g.items() if 'Fear' in L and 'Anger' not in L]
anger = [i for i,L in g.items() if 'Anger' in L and 'Fear' not in L]
print('fear', len(fear), 'anger', len(anger), 'both', sum(1 for L in g if 'Fear' in L and 'Anger' in L))
# folder overlap
from collections import Counter
ff = Counter(i.split('/')[0] for i in fear)
aa = Counter(i.split('/')[0] for i in anger)
print('fear_folders', dict(ff))
print('anger_folders', dict(aa))
print('shared_folders', sorted(set(ff)&set(aa)))
"""


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    print(f"hub={HUB} user={USER} pass_set={bool(PASS)} cmd={cmd}", flush=True)
    h = Hub()
    h.login()
    dest = ROOT / "artifacts" / "battery" / "exp02"
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
    if cmd == "diag":
        kid = h.new_kernel()
        print(h.execute(kid, DIAG, timeout=120))
        return 0
    if cmd == "status":
        kid = h.new_kernel()
        text = h.execute(kid, STATUS, timeout=60)
        print(text.encode("ascii", "replace").decode("ascii"))
        pull(h, dest)
        return 0
    if cmd == "watch":
        dest = ROOT / "artifacts" / "battery" / "exp02"
        t0 = time.time()
        while time.time() - t0 < 4 * 3600:
            try:
                pull(h, dest)
            except Exception as e:
                print(f"pull_err {type(e).__name__}", flush=True)
            res_path = dest / "results.json"
            hb_path = dest / "heartbeat.json"
            complete = False
            if res_path.exists():
                try:
                    rec = json.loads(res_path.read_text(encoding="utf-8"))
                    complete = bool(rec.get("complete")) and rec.get("mechanism_answer")
                    print(
                        f"watch complete={rec.get('complete')} answer={rec.get('mechanism_answer')} "
                        f"n_rows={rec.get('n_rows')}",
                        flush=True,
                    )
                except Exception as e:
                    print(f"res_err {type(e).__name__}", flush=True)
            if hb_path.exists():
                try:
                    hb = json.loads(hb_path.read_text(encoding="utf-8"))
                    print(f"hb stage={hb.get('stage')} i={hb.get('i')} n={hb.get('n')}", flush=True)
                except Exception:
                    pass
            if complete:
                return 0
            time.sleep(90)
        print("watch timeout", flush=True)
        return 1
    if cmd == "relaunch":
        kid = h.new_kernel()
        print(h.execute(kid, RESTART, timeout=30))
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
