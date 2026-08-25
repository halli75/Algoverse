# JupyterHub helper for exp09. Credentials from env only. Never print secrets.
# Own kernel + nohup. Does not touch the overseer UI tab.

from __future__ import annotations

import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
try:
    import battery_adapter as ba

    ba.source_battery_env()
except Exception:
    pass

HUB = os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116")
USER = os.environ.get("JUPYTERHUB_USER", os.environ.get("BATTERY_USER", "asca-ec66"))
PASS = (
    os.environ.get("JUPYTERHUB_PASSWORD")
    or os.environ.get("EXP01_HUB_PASSWORD")
    or os.environ.get("EXP02_HUB_PASSWORD")
    or os.environ.get("BATTERY_PASS")
    or os.environ.get("BATTERY_SSH_PASS")
    or ""
)
BASE = f"{HUB}/user/{USER}"


class Hub:
    def __init__(self) -> None:
        if not PASS:
            raise SystemExit("hub password unset")
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
            self.op.open(BASE + "/api/status", timeout=20).read()
        except Exception:
            pass
        try:
            self.uxsrf = next(c.value for c in self.cj if c.name == "_xsrf" and "/user/" in str(c.path))
        except StopIteration:
            self.uxsrf = xsrf
        print("hub_ok", flush=True)

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

    def get_text(self, path: str) -> str | None:
        try:
            rec = self.get(f"/api/contents/{path}")
        except Exception:
            return None
        if rec.get("format") == "base64":
            import base64

            return base64.b64decode(rec.get("content") or "").decode("utf-8", "replace")
        return rec.get("content")

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
                        "username": "exp09",
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
        "Algoverse/scripts/affect_core.py": ROOT / "scripts" / "affect_core.py",
        "Algoverse/scripts/battery_exp09_run.py": ROOT / "scripts" / "battery_exp09_run.py",
        "Algoverse/scripts/battery_exp09_boot.py": ROOT / "scripts" / "battery_exp09_boot.py",
        "Algoverse/scripts/battery_exp09_hub.py": ROOT / "scripts" / "battery_exp09_hub.py",
        "Algoverse/artifacts/battery/exp09/xstest_prompts.csv": ROOT / "artifacts" / "battery" / "exp09" / "xstest_prompts.csv",
        "algoverse_run/battery/exp09/xstest_prompts.csv": ROOT / "artifacts" / "battery" / "exp09" / "xstest_prompts.csv",
        "algoverse_run/battery/exp09/battery_exp09_run.py": ROOT / "scripts" / "battery_exp09_run.py",
        "algoverse_run/battery/exp09/battery_exp09_boot.py": ROOT / "scripts" / "battery_exp09_boot.py",
        "algoverse_run/battery/exp09/affect_core.py": ROOT / "scripts" / "affect_core.py",
        "algoverse_run/battery/exp09/battery_adapter.py": ROOT / "scripts" / "battery_adapter.py",
    }
    for d in (
        "Algoverse/scripts",
        "Algoverse/artifacts",
        "Algoverse/artifacts/battery",
        "Algoverse/artifacts/battery/exp09",
        "algoverse_run/battery",
        "algoverse_run/battery/exp09",
    ):
        h.mkdir(d)
    for dest, local in files.items():
        h.put_text(dest, local.read_text(encoding="utf-8"))
        print("put", dest, flush=True)


LAUNCH = r"""
import os, subprocess, pathlib
home = pathlib.Path.home()
print('home', home)
print('battery_env', (home/'.battery_env').exists())
print('hf_token', (home/'.hf_token').exists())
print('xai_keyfile', (home/'.xai_api_key').exists())
cmd = '''
set -a
[ -f "$HOME/.battery_env" ] && . "$HOME/.battery_env"
set +a
export E2E_MODEL=google/gemma-4-E4B-it
export E2E_NO_FALLBACK=1
export E2E_ROOT="$HOME/algoverse_run"
export E2E_REPO="$HOME/Algoverse"
export E2E_SPLIT="$HOME/algoverse_run/emotic_split.json"
export E2E_EMOTIC="$HOME/algoverse_run/emotic_data"
export BATTERY_EXP09_ROOT="$HOME/algoverse_run/battery/exp09"
export PYTHONUNBUFFERED=1
mkdir -p "$HOME/algoverse_run/battery/exp09"
if pgrep -f "[p]ython3 .*battery_exp09_boot.py --run" >/dev/null; then
  echo ALREADY
  pgrep -af "[p]ython3 .*battery_exp09"
  exit 0
fi
nohup python3 "$HOME/Algoverse/scripts/battery_exp09_boot.py" --run > "$HOME/algoverse_run/battery/exp09/nohup.out" 2>&1 &
echo LAUNCH_PID $!
sleep 2
pgrep -af battery_exp09 || true
tail -n 40 "$HOME/algoverse_run/battery/exp09/nohup.out" || true
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
'''
print(subprocess.check_output(['bash','-lc', cmd], text=True, stderr=subprocess.STDOUT)[-4000:])
"""


def launch() -> int:
    h = Hub()
    h.login()
    upload(h)
    kid = h.new_kernel()
    out = h.execute(kid, LAUNCH, timeout=180)
    print(out[-4000:], flush=True)
    return 0


def pull() -> dict | None:
    h = Hub()
    h.login()
    local = ROOT / "artifacts" / "battery" / "exp09"
    local.mkdir(parents=True, exist_ok=True)
    for name in ("heartbeat.json", "STATUS.md", "results.json", "run.log", "boot.log", "nohup.out", "checkpoint.json"):
        content = h.get_text(f"algoverse_run/battery/exp09/{name}")
        if content is None:
            content = h.get_text(f"Algoverse/artifacts/battery/exp09/{name}")
        if content is not None:
            (local / name).write_text(content, encoding="utf-8")
            print("got", name, "bytes", len(content), flush=True)
    rp = local / "results.json"
    if rp.is_file() and rp.stat().st_size > 20:
        return json.loads(rp.read_text(encoding="utf-8"))
    return None


def results_valid(res: dict | None) -> bool:
    if not res or res.get("complete") is not True:
        return False
    gates = res.get("gates") or {}
    items = gates.get("items") or []
    hard = [g for g in items if g.get("hard", True)]
    if not hard or any(not g.get("passed") for g in hard):
        return False
    if not res.get("mechanism_answer"):
        return False
    primary = (res.get("primary") or {}).get("conditions") or {}
    for cond in ("no_image", "fear", "anger", "sad", "happy", "neutral"):
        rate = (primary.get(cond) or {}).get("refuse_rate")
        if rate is None:
            return False
    return True


def gpu_free_table(h: Hub) -> list[dict]:
    kid = h.new_kernel()
    out = h.execute(
        kid,
        "import subprocess; print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total','--format=csv,noheader,nounits'], text=True)); print('---'); print(subprocess.check_output(['bash','-lc','pgrep -af \"[p]ython3 .*battery_exp09_boot.py --run\" || echo NONE'], text=True))",
        timeout=40,
    )
    print("smi", out, flush=True)
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3 and parts[0].isdigit():
            idx, used, total = int(parts[0]), int(parts[1]), int(parts[2])
            rows.append({"gpu": idx, "used": used, "total": total, "free": total - used})
    return rows


def loop() -> int:
    while True:
        res = pull()
        if results_valid(res):
            print("results.json valid complete=true", flush=True)
            return 0
        h = Hub()
        h.login()
        rows = gpu_free_table(h)
        best = max((r["free"] for r in rows), default=0)
        already = "battery_exp09_boot.py --run" in "".join(
            # last probe print already shown
            []
        )
        print(f"loop best_free={best} rows={rows}", flush=True)
        if best >= 12000:
            print("gpu headroom; launch (resume checkpoint)", flush=True)
            launch()
        else:
            print("no 12GiB card; sleep 90s (do not fuser /dev/nvidia*)", flush=True)
        time.sleep(90)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()
    if args.loop:
        return loop()
    if args.pull:
        pull()
        return 0
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
