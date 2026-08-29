# RunPod v2 create/stop for battery v2. Never print the API key.
# RTX PRO 4500 (~32GB) is not compatible with 12B bf16 + image forwards + hooks.
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.runpod.io/v2"
PREFERRED = [
    "NVIDIA RTX PRO 6000 Blackwell Server Edition",
]
# No 48GB / 32GB fallback. 12B bf16 + hooks need 96GB.
IMAGE = "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04"
SSH_PUB = Path.home() / ".ssh" / "motion_mirror_runpod_ed25519.pub"
POD_META = Path(__file__).resolve().parents[1] / "artifacts" / "battery_v2" / "pod.json"


def key() -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import battery_adapter as ba

    ba.source_battery_env()
    ba.plant_hf_token()
    k = os.environ.get("RUNPOD_API_KEY")
    if not k:
        raise SystemExit("RUNPOD_API_KEY missing")
    return k.strip()


def req(method: str, path: str, body: dict | None = None, query: dict | None = None) -> dict | list | None:
    q = ""
    if query:
        q = "?" + urllib.parse.urlencode(query, doseq=True)
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(
        API + path + q,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        },
    )
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            raw = resp.read().decode()
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:2500]
        raise SystemExit(f"RunPod {e.code} {method} {path}: {err}") from e


def list_gpus() -> list[dict]:
    blob = req("GET", "/catalog/gpus", query={"include": "AVAILABILITY", "product": "POD", "cloud": "SECURE"})
    if isinstance(blob, dict):
        return list(blob.get("gpus") or [])
    return []


def pick_gpu() -> dict:
    want = PREFERRED[0]
    gpus = list_gpus()
    for g in gpus:
        if str(g.get("id") or "") != want:
            continue
        mem = int(g.get("memory") or 0)
        avail = str(g.get("availability") or "NONE")
        if mem < 90 or g.get("secure") is not True or avail not in ("LOW", "MEDIUM", "HIGH"):
            raise SystemExit(f"{want} not usable mem={mem} avail={avail} secure={g.get('secure')}")
        return g
    raise SystemExit(f"{want} missing from catalog; do not substitute another GPU")


def ensure_ssh_key() -> bool:
    if not SSH_PUB.is_file():
        print("WARN: no motion_mirror_runpod_ed25519.pub; SSH may fail", flush=True)
        return False
    pub = SSH_PUB.read_text(encoding="utf-8").strip()
    blob = req("GET", "/account/ssh-keys") or {}
    raw = list(blob.get("keys") or [])
    keys = []
    for k in raw:
        if isinstance(k, str) and k.startswith(("ssh-", "ecdsa-", "sk-")) and len(k.split()) >= 2:
            keys.append(k.strip())
    if any(pub.split()[1] in k for k in keys):
        return True
    keys.append(pub)
    req("PUT", "/account/ssh-keys", {"keys": keys})
    return True


def create_pod(gpu_id: str) -> dict:
    ensure_ssh_key()
    body = {
        "name": "algoverse-battery-v2",
        "cloud": "SECURE",
        "gpu": {"id": gpu_id, "count": 1},
        "image": IMAGE,
        "disk": 200,
        "ports": ["22/tcp"],
        "startSsh": True,
        "startJupyter": False,
        "env": {
            "E2E_TIER": os.environ.get("E2E_TIER", "budget3h"),
            "HF_TOKEN": os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or "",
            "E2E_MODELS": os.environ.get("E2E_MODELS", "e4b,g12"),
            "E2E_CORPORA": os.environ.get("E2E_CORPORA", "emotic,oasis"),
            "E2E_MAX_HOURS": os.environ.get("E2E_MAX_HOURS", "2.75"),
            "E2E_ROOT": "/workspace/algoverse_run",
            "E2E_REPO": "/workspace/Algoverse",
            "E2E_V2": "/workspace/Algoverse/artifacts/battery_v2",
        },
    }
    rec = req("POST", "/pods", body)
    POD_META.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: rec.get(k) if isinstance(rec, dict) else rec for k in ("id", "name", "status", "gpu", "cost", "ssh")}
    if isinstance(rec, dict):
        slim["id"] = rec.get("id")
        slim["status"] = rec.get("status")
        slim["gpu"] = rec.get("gpu")
        slim["cost"] = rec.get("cost")
        slim["ssh"] = rec.get("ssh")
    POD_META.write_text(json.dumps(slim, indent=2, default=str), encoding="utf-8")
    return rec if isinstance(rec, dict) else {"raw": rec}


def get_pod(pod_id: str) -> dict:
    rec = req("GET", f"/pods/{pod_id}")
    return rec if isinstance(rec, dict) else {}


def pod_action(pod_id: str, action: str) -> dict | None:
    return req("POST", f"/pods/{pod_id}/action", {"action": action})


def stop_pod(pod_id: str) -> dict | None:
    return pod_action(pod_id, "stop")


def terminate_pod(pod_id: str) -> dict | None:
    return pod_action(pod_id, "terminate")


def ssh_target(pod: dict) -> dict:
    ssh = pod.get("ssh") or {}
    direct = ssh.get("direct") or {}
    proxy = ssh.get("proxy") or {}
    return {"direct": direct, "proxy": proxy, "status": pod.get("status"), "id": pod.get("id")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("gpus", "create", "status", "ssh", "stop", "terminate"))
    ap.add_argument("--id", default="")
    ap.add_argument("--probe-only", action="store_true")
    args = ap.parse_args()
    if args.cmd == "gpus":
        gpus = list_gpus()
        slim = [
            {
                "id": g.get("id"),
                "memory": g.get("memory"),
                "availability": g.get("availability"),
                "secure": g.get("secure"),
                "price_secure": (g.get("price") or {}).get("secure"),
            }
            for g in gpus
            if int(g.get("memory") or 0) >= 40
        ]
        print(json.dumps(slim, indent=2))
        return 0
    if args.cmd == "create":
        g = pick_gpu()
        print(json.dumps({"gpu": g.get("id"), "memory": g.get("memory"), "availability": g.get("availability"), "price": (g.get("price") or {}).get("secure")}, indent=2))
        if args.probe_only:
            return 0
        rec = create_pod(str(g["id"]))
        print(json.dumps({"id": rec.get("id"), "status": rec.get("status"), "gpu": rec.get("gpu"), "cost": rec.get("cost")}, indent=2, default=str))
        return 0
    pid = args.id
    if not pid and POD_META.is_file():
        pid = json.loads(POD_META.read_text(encoding="utf-8")).get("id") or ""
    if not pid:
        raise SystemExit("--id required")
    if args.cmd == "status":
        pod = get_pod(pid)
        print(json.dumps({"id": pod.get("id"), "status": pod.get("status"), "cost": pod.get("cost"), "ssh": ssh_target(pod)}, indent=2, default=str)[:4000])
        return 0
    if args.cmd == "ssh":
        print(json.dumps(ssh_target(get_pod(pid)), indent=2, default=str))
        return 0
    if args.cmd == "stop":
        print(json.dumps(stop_pod(pid), indent=2, default=str)[:2000])
        return 0
    print(json.dumps(terminate_pod(pid), indent=2, default=str)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
