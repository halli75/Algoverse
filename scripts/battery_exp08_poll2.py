# Extra poll: GPU locks, results tail, heartbeat. No secrets.
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from battery_exp08_hub import Hub, _load_local_env  # noqa: E402


def main() -> int:
    _load_local_env()
    user = os.environ["JUPYTERHUB_USER"]
    hub = Hub(os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"), user, os.environ["JUPYTERHUB_PASSWORD"])
    hub.login()
    base = f"/user/{user}/api/contents"
    for path in (
        f"{base}/algoverse_run/battery/locks/gpu_0.json",
        f"{base}/algoverse_run/battery/locks/gpu_2.json",
        f"{base}/algoverse_run/battery/locks/gpu_3.json",
        f"{base}/algoverse_run/battery/locks/gpu_7.json",
        f"{base}/algoverse_run/battery/A100.lock",
        f"{base}/algoverse_run/battery/exp08/heartbeat.json",
        f"{base}/algoverse_run/battery/exp08/results.json",
    ):
        st, payload = hub.request("GET", path)
        if not isinstance(payload, dict):
            print(st, path, type(payload), flush=True)
            continue
        content = payload.get("content")
        if payload.get("format") == "text" and isinstance(content, str):
            if "hf_" in content or "sk-" in content:
                print(st, path, "[redacted]", flush=True)
            else:
                print(st, path, content[:2000], flush=True)
        else:
            print(st, path, str(content)[:200], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
