# Night-shift poll: exp04/exp06 gates, locks, exp08 heartbeat. No secrets.
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from battery_exp08_hub import Hub, _load_local_env  # noqa: E402


def _content(payload) -> str:
    if not isinstance(payload, dict):
        return str(payload)[:800]
    c = payload.get("content")
    if payload.get("format") == "text" and isinstance(c, str):
        return c
    if isinstance(c, list):
        return "DIR " + str([x.get("name") for x in c if isinstance(x, dict)])
    return json.dumps(c, default=str)[:800]


def main() -> int:
    _load_local_env()
    user = os.environ["JUPYTERHUB_USER"]
    hub = Hub(os.environ.get("JUPYTERHUB_URL", "http://35.89.128.116"), user, os.environ["JUPYTERHUB_PASSWORD"])
    hub.login()
    base = f"/user/{user}/api/contents/algoverse_run/battery"
    paths = [
        f"{base}/locks",
        f"{base}/A100.lock",
        f"{base}/exp04/heartbeat.json",
        f"{base}/exp04/results.json",
        f"{base}/exp06/heartbeat.json",
        f"{base}/exp06/results.json",
        f"{base}/exp08/heartbeat.json",
        f"{base}/exp08/pid",
        f"{base}/exp08/results.json",
        f"{base}/exp08/claim_debug.json",
    ]
    for path in paths:
        st, payload = hub.request("GET", path)
        text = _content(payload)
        if "hf_" in text or "sk-" in text:
            text = "[redacted]"
        # keep results small
        if path.endswith("results.json") and text.startswith("{"):
            try:
                obj = json.loads(payload.get("content") if isinstance(payload, dict) else text)
                slim = {
                    "complete": obj.get("complete"),
                    "job": obj.get("job"),
                    "elapsed_s": obj.get("elapsed_s"),
                    "gates": obj.get("gates"),
                    "headline": (obj.get("headline") or obj.get("mechanism_answer") or "")[:200],
                    "stage_keys": list(obj.keys())[:20],
                }
                text = json.dumps(slim, default=str)
            except Exception:
                text = text[:600]
        print(f"{st} {path.split('/battery/')[-1]}\n{text[:900]}\n", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
