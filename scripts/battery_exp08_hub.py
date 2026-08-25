# JupyterHub client for exp08. Own kernel / terminal. No overseer-tab theft.
# Credentials from env: JUPYTERHUB_URL, JUPYTERHUB_USER, JUPYTERHUB_PASSWORD.
# Never print or write the password.
# [[battery-exp08]]

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


class Hub:
    def __init__(self, base: str, user: str, password: str):
        self.base = base.rstrip("/")
        self.user = user
        self.password = password
        self.token = None
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def _xsrf(self, path_pref: str = "") -> str:
        cands = [c for c in self.cj if c.name == "_xsrf"]
        if path_pref:
            for c in cands:
                if path_pref in (c.path or ""):
                    return c.value
        return cands[-1].value if cands else ""

    def request(self, method: str, path: str, data=None, headers=None, timeout=60):
        url = path if path.startswith("http") else self.base + path
        hdrs = {"User-Agent": "algoverse-exp08", "Referer": self.base + f"/user/{self.user}/lab"}
        if self.token:
            hdrs["Authorization"] = f"token {self.token}"
        xsrf = self._xsrf(path_pref=f"/user/{self.user}")
        if xsrf:
            hdrs["X-XSRFToken"] = xsrf
            sep = "&" if "?" in url else "?"
            if "_xsrf=" not in url:
                url = url + sep + "_xsrf=" + urllib.parse.quote(xsrf)
        if headers:
            hdrs.update(headers)
        body = None
        if data is not None:
            if isinstance(data, (dict, list)):
                body = json.dumps(data).encode()
                hdrs.setdefault("Content-Type", "application/json")
            elif isinstance(data, str):
                body = data.encode()
            else:
                body = data
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with self.opener.open(req, timeout=timeout) as r:
                raw = r.read()
                ctype = r.headers.get("content-type", "")
                if "json" in ctype:
                    return r.status, json.loads(raw.decode() or "null")
                return r.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read()
            return e.code, raw

    def login(self) -> None:
        self.request("GET", "/hub/login")
        xsrf = self._xsrf()
        form = urllib.parse.urlencode(
            {"username": self.user, "password": self.password, "_xsrf": xsrf}
        )
        status, _ = self.request(
            "POST",
            "/hub/login",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if status not in {200, 302}:
            # follow: some hubs return 200 on the lab page
            pass
        # start user server if needed, then collect the Jupyter XSRF cookie
        self.request("POST", f"/hub/api/users/{self.user}/server", data={})
        for _ in range(30):
            st, payload = self.request("GET", f"/hub/api/users/{self.user}")
            if st == 200 and isinstance(payload, dict):
                servers = payload.get("servers") or payload.get("server")
                if servers:
                    self.request("GET", f"/user/{self.user}/lab")
                    self.request("GET", f"/user/{self.user}/api")
                    st_t, tok = self.request(
                        "POST",
                        f"/hub/api/users/{self.user}/tokens",
                        data={"note": "exp08-own-kernel"},
                    )
                    if st_t in {200, 201} and isinstance(tok, dict) and tok.get("token"):
                        self.token = tok["token"]
                    return
            time.sleep(2)
        raise RuntimeError("user server did not start")

    def put_file(self, api_path: str, text: str) -> None:
        # api_path like /user/NAME/api/contents/Algoverse/scripts/foo.py
        body = {"type": "file", "format": "text", "content": text}
        st, raw = self.request("PUT", api_path, data=body, timeout=120)
        if st not in {200, 201}:
            raise RuntimeError(f"put {api_path} -> {st} {raw[:200]!r}")

    def get_json(self, path: str):
        st, payload = self.request("GET", path)
        return st, payload


def upload_scripts(hub: Hub) -> list[str]:
    names = [
        "battery_exp08_lib.py",
        "battery_exp08_run.py",
        "battery_exp08_boot.py",
        "battery_exp08_cell.py",
        "battery_exp08_hub.py",
    ]
    uploaded = []
    for name in names:
        text = (_HERE / name).read_text(encoding="utf-8")
        for dest in (
            f"/user/{hub.user}/api/contents/Algoverse/scripts/{name}",
            f"/user/{hub.user}/api/contents/algoverse_run/battery/exp08/{name}",
        ):
            try:
                hub.put_file(dest, text)
                uploaded.append(dest)
            except Exception as e:
                uploaded.append(f"FAIL {dest}: {e}")
    return uploaded


def start_own_kernel_and_boot(hub: Hub) -> dict:
    """Create our own kernel (not overseer) and exec the cell."""
    st, kernels = hub.request("GET", f"/user/{hub.user}/api/kernels")
    payload = {
        "path": "algoverse_run/battery/exp08/exp08.ipynb",
        "type": "notebook",
        "name": "exp08",
        "kernel": {"name": "python3"},
    }
    # write a tiny notebook then start a session
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "source": [
                    "import os, sys\n",
                    "from pathlib import Path\n",
                    "p = Path.home()/'Algoverse'/'scripts'\n",
                    "sys.path.insert(0, str(p))\n",
                    "os.chdir(str(Path.home()/'Algoverse'))\n",
                    "print('cwd', os.getcwd())\n",
                    "print('scripts', list(p.glob('battery_exp08*.py')))\n",
                    "exec((p/'battery_exp08_cell.py').read_text())\n",
                    "print('cell_returned')\n",
                ],
                "outputs": [],
                "execution_count": None,
            }
        ],
    }
    hub.request(
        "PUT",
        f"/user/{hub.user}/api/contents/algoverse_run/battery/exp08/exp08.ipynb",
        data={"type": "notebook", "format": "json", "content": nb},
    )
    st, sess = hub.request(
        "POST",
        f"/user/{hub.user}/api/sessions",
        data={
            "path": "algoverse_run/battery/exp08/exp08.ipynb",
            "type": "notebook",
            "name": "exp08",
            "kernel": {"name": "python3"},
        },
    )
    return {"session_status": st, "session": sess if isinstance(sess, dict) else str(sess)[:300]}


def search_oasis(hub: Hub) -> dict:
    """Ask the user server to list oasis hits via a one-shot contents walk of known dirs."""
    hits = {}
    for path in (
        f"/user/{hub.user}/api/contents",
        f"/user/{hub.user}/api/contents/Algoverse",
        f"/user/{hub.user}/api/contents/algoverse_run",
        f"/user/{hub.user}/api/contents/oasis",
        f"/user/{hub.user}/api/contents/OASIS",
        f"/user/{hub.user}/api/contents/Algoverse/oasis",
        f"/user/{hub.user}/api/contents/algoverse_run/oasis",
        f"/user/{hub.user}/api/contents/algoverse_run/battery",
    ):
        st, payload = hub.request("GET", path)
        hits[path] = {"status": st, "names": []}
        if isinstance(payload, dict):
            content = payload.get("content") or []
            if isinstance(content, list):
                hits[path]["names"] = [c.get("name") for c in content if isinstance(c, dict)]
    return hits


def execute_kernel(hub: Hub, kernel_id: str, code: str, timeout: int = 120) -> list[dict]:
    try:
        import websocket
    except ImportError:
        subprocess_import = __import__("subprocess")
        subprocess_import.check_call([sys.executable, "-m", "pip", "install", "-q", "websocket-client"])
        import websocket  # type: ignore

    import uuid
    from datetime import datetime, timezone

    token = hub.token or ""
    ws_url = (
        hub.base.replace("http://", "ws://").replace("https://", "wss://")
        + f"/user/{hub.user}/api/kernels/{kernel_id}/channels"
    )
    cookie = "; ".join(f"{c.name}={c.value}" for c in hub.cj)
    hdrs = [f"Cookie: {cookie}"]
    if token:
        hdrs.append(f"Authorization: token {token}")
        ws_url += f"?token={urllib.parse.quote(token)}"
    xsrf = hub._xsrf(path_pref=f"/user/{hub.user}") or hub._xsrf()
    if xsrf:
        hdrs.append(f"X-XSRFToken: {xsrf}")
        sep = "&" if "?" in ws_url else "?"
        ws_url = ws_url + sep + "_xsrf=" + urllib.parse.quote(xsrf)
    print("ws_cookie_names", [c.name for c in hub.cj], flush=True)
    ws = websocket.create_connection(ws_url, header=hdrs, timeout=30)
    session = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())
    msg = {
        "header": {
            "msg_id": msg_id,
            "username": "exp08",
            "session": session,
            "date": datetime.now(timezone.utc).isoformat(),
            "msg_type": "execute_request",
            "version": "5.3",
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": code,
            "silent": False,
            "store_history": True,
            "user_expressions": {},
            "allow_stdin": False,
            "stop_on_error": True,
        },
        "channel": "shell",
        "buffers": [],
    }
    ws.send(json.dumps(msg))
    outs: list[dict] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        ws.settimeout(max(1, deadline - time.time()))
        try:
            raw = ws.recv()
        except Exception:
            break
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        mtype = (data.get("header") or {}).get("msg_type")
        parent = (data.get("parent_header") or {}).get("msg_id")
        if parent != msg_id:
            continue
        if mtype in {"stream", "execute_result", "error", "display_data"}:
            outs.append({"type": mtype, "content": data.get("content")})
        if mtype == "status" and (data.get("content") or {}).get("execution_state") == "idle":
            if outs:
                break
    ws.close()
    return outs


def print_listings(hub: Hub) -> None:
    for path in (
        f"/user/{hub.user}/api/contents",
        f"/user/{hub.user}/api/contents/Algoverse",
        f"/user/{hub.user}/api/contents/algoverse_run",
        f"/user/{hub.user}/api/contents/algoverse_run/battery",
    ):
        st, payload = hub.request("GET", path)
        names = []
        if isinstance(payload, dict):
            content = payload.get("content") or []
            if isinstance(content, list):
                names = [c.get("name") for c in content if isinstance(c, dict)]
        print("LIST", path, st, names, flush=True)


def _load_local_env() -> None:
    repo_env = Path(__file__).resolve().parent.parent / ".env"
    if repo_env.is_file():
        for raw in repo_env.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> int:
    _load_local_env()
    base = os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116")
    user = os.environ.get("JUPYTERHUB_USER", "")
    password = os.environ.get("JUPYTERHUB_PASSWORD", "")
    if not user or not password:
        print("set JUPYTERHUB_USER and JUPYTERHUB_PASSWORD", flush=True)
        return 2
    hub = Hub(base, user, password)
    print("login", base, user, flush=True)
    hub.login()
    print("logged_in", flush=True)
    hits = search_oasis(hub)
    print("oasis_search", json.dumps({k: v["status"] for k, v in hits.items()}), flush=True)
    for k, v in hits.items():
        names = [n for n in v.get("names") or [] if n and "oasis" in n.lower()]
        if names:
            print("HIT", k, names, flush=True)
    print_listings(hub)
    st_s, sessions = hub.request("GET", f"/user/{hub.user}/api/sessions")
    if isinstance(sessions, list):
        print("n_sessions", len(sessions), flush=True)
    uploaded = upload_scripts(hub)
    print("uploaded_ok", sum(1 for u in uploaded if not str(u).startswith("FAIL")), flush=True)
    sess = start_own_kernel_and_boot(hub)
    kernel_id = None
    if isinstance(sess.get("session"), dict):
        kernel_id = ((sess["session"].get("kernel") or {}).get("id"))
    print("session_status", sess.get("session_status"), "kernel", bool(kernel_id), flush=True)
    if not kernel_id:
        return 3
    time.sleep(3)
    code = r"""
import os, sys
from pathlib import Path
envp = Path.home() / ".battery_env"
if envp.is_file():
    for raw in envp.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
print("hf_set", bool(os.environ.get("HF_TOKEN")))
print("home", Path.home())
for rel in ["Algoverse", "algoverse_run", "algoverse_run/battery", "algoverse_run/emotic_data"]:
    p = Path.home() / rel
    print("exists", rel, p.exists())
hits = []
for root in (Path.home(), Path.home()/"Algoverse", Path.home()/"algoverse_run"):
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if "oasis" in p.name.lower():
            hits.append(str(p))
        if len(hits) >= 40:
            break
print("oasis_hits", hits[:40])
sys.path.insert(0, str(Path.home()/"Algoverse"/"scripts"))
os.chdir(str(Path.home()/"Algoverse"))
import battery_exp08_cell as cell
print("spawn_rc", cell.main())
"""
    outs = execute_kernel(hub, kernel_id, code, timeout=180)
    for o in outs:
        text = ""
        c = o.get("content") or {}
        if o.get("type") == "stream":
            text = str(c.get("text") or "")
        elif o.get("type") == "error":
            text = str(c.get("ename")) + " " + str(c.get("evalue"))
        elif o.get("type") == "execute_result":
            text = str((c.get("data") or {}).get("text/plain") or "")
        redacted = text
        for needle in ("hf_", "sk-", "xai-", "Bearer "):
            if needle in redacted:
                redacted = "[redacted]"
        print("OUT", o.get("type"), redacted[:800], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
