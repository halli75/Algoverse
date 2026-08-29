"""List RunPod pods; never print the API key."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import battery_v2_runpod as rp

raw = rp.req("GET", "/pods")
if isinstance(raw, dict):
    pods = raw.get("pods") or raw.get("items") or raw.get("data") or [raw]
elif isinstance(raw, list):
    pods = raw
else:
    pods = []
slim = []
for p in pods:
    if not isinstance(p, dict):
        continue
    slim.append(
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "status": p.get("status"),
            "cost": p.get("cost"),
            "gpu": p.get("gpu"),
        }
    )
print(json.dumps({"n": len(slim), "pods": slim}, indent=2, default=str)[:4000])
