# Poll exp08 host artifacts. No secrets printed.
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from battery_exp08_hub import Hub, _load_local_env  # noqa: E402


def _text(raw) -> str:
    if isinstance(raw, dict):
        return raw.get("content") if raw.get("format") == "text" else json.dumps(raw.get("content"), indent=2)[:4000]
    if isinstance(raw, (bytes, bytearray)):
        return raw.decode("utf-8", "replace")[:4000]
    return str(raw)[:4000]


def main() -> int:
    _load_local_env()
    user = os.environ.get("JUPYTERHUB_USER", "")
    password = os.environ.get("JUPYTERHUB_PASSWORD", "")
    hub = Hub(os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"), user, password)
    hub.login()
    base = f"/user/{user}/api/contents/algoverse_run/battery"
    paths = [
        f"{base}/exp08",
        f"{base}/A100.lock",
        f"{base}/exp08/heartbeat.json",
        f"{base}/exp08/nohup.out",
        f"{base}/exp08/pid",
        f"{base}/exp08/oasis_meta.json",
        f"{base}/exp08/hf_push.json",
        f"{base}/exp08/results.json",
        f"{base}/exp08/ADVISOR_REQUEST.md",
        f"{base}/exp08/oasis",
        f"{base}/locks",
    ]
    for path in paths:
        st, payload = hub.request("GET", path)
        names = []
        if isinstance(payload, dict) and isinstance(payload.get("content"), list):
            names = [c.get("name") for c in payload["content"] if isinstance(c, dict)]
            print(f"{st} DIR {path} {names}", flush=True)
            continue
        text = _text(payload)
        if "hf_" in text or "sk-" in text or "xai-" in text:
            text = "[redacted-body]"
        print(f"{st} FILE {path}\n{text[:1500]}\n", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
