"""JupyterHub / nohup boot for exp06. Own process. GPU 2.

Does not touch the overseer UI. Claims ~/algoverse_run/battery/locks/gpu_2.json.
Serializes first Gemma-4 download if another job is fetching.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

EXP = "exp06"
GPU = os.environ.get("EXP06_GPU", "2")
REPO_URL = "https://github.com/halli75/Algoverse.git"
STALE_S = 20 * 60
MAX_CONCURRENT = 4


def _root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def log(msg: str) -> None:
    root = _root() / "battery" / EXP
    root.mkdir(parents=True, exist_ok=True)
    s = f"{time.strftime('%H:%M:%S')} {msg}"
    print(s, flush=True)
    with (root / "boot.log").open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def lock_dir() -> Path:
    d = _root() / "battery" / "locks"
    d.mkdir(parents=True, exist_ok=True)
    # also accept A100.lock as a directory
    alt = _root() / "battery" / "A100.lock"
    if alt.exists() and alt.is_dir():
        return alt
    return d


def lock_path(gpu: str) -> Path:
    return lock_dir() / f"gpu_{gpu}.json"


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def running_gpu_jobs() -> list[dict]:
    now = time.time()
    jobs = []
    for p in lock_dir().glob("gpu_*.json"):
        rec = read_json(p)
        if not rec:
            continue
        ts = float(rec.get("ts") or 0)
        if now - ts > STALE_S:
            rec["stale"] = True
        jobs.append(rec)
    return jobs


def claim_shared_file(gpu: str) -> None:
    path = Path(os.environ.get("E2E_LOCK", str(_root() / "battery" / "A100.lock")))
    now = time.time()
    data = {"holders": {}}
    if path.exists() and path.is_file():
        rec = read_json(path)
        if rec:
            data = rec
    holders = data.setdefault("holders", {})
    live = []
    for gid, rec in list(holders.items()):
        ts = float(rec.get("unix") or rec.get("ts") or 0)
        if now - ts <= STALE_S:
            live.append(str(gid))
    if len(live) >= MAX_CONCURRENT and gpu not in live:
        raise SystemExit(f"max concurrent {MAX_CONCURRENT}: {live}")
    other = holders.get(gpu) or holders.get(str(gpu)) or {}
    if other.get("exp") not in (None, EXP):
        age = now - float(other.get("unix") or 0)
        if age <= STALE_S and not other.get("stale"):
            raise SystemExit(f"gpu {gpu} held by {other.get('exp')}")
    holders[str(gpu)] = {"exp": EXP, "pid": os.getpid(), "unix": now, "ts": time.strftime("%Y-%m-%d %T")}
    data["holders"] = holders
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    log(f"claimed shared A100.lock gpu={gpu} live={live}")


def claim_gpu(gpu: str) -> None:
    path = lock_path(gpu)
    rec = read_json(path)
    now = time.time()
    if rec and rec.get("exp") not in (None, EXP):
        age = now - float(rec.get("ts") or 0)
        if age <= STALE_S:
            raise SystemExit(f"gpu {gpu} held by {rec.get('exp')} age={age:.0f}s")
        log(f"STALE_LOCK gpu={gpu} prev={rec}")
    live = [j for j in running_gpu_jobs() if not j.get("stale") and j.get("exp") != EXP]
    if len(live) >= MAX_CONCURRENT:
        raise SystemExit(f"max concurrent {MAX_CONCURRENT} already running: {[j.get('exp') for j in live]}")
    payload = {
        "gpu": gpu,
        "exp": EXP,
        "pid": os.getpid(),
        "ts": now,
        "host": os.uname().nodename if hasattr(os, "uname") else "win",
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)
    log(f"claimed gpu={gpu} lock={path}")
    try:
        claim_shared_file(gpu)
    except SystemExit:
        raise
    except Exception as e:
        log(f"shared lock skip: {type(e).__name__}")


def refresh_lock(gpu: str) -> None:
    path = lock_path(gpu)
    rec = read_json(path) or {}
    rec.update({"gpu": gpu, "exp": EXP, "pid": os.getpid(), "ts": time.time()})
    path.write_text(json.dumps(rec), encoding="utf-8")


def wait_for_first_download() -> None:
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    marker = _root() / "battery" / "hf_gemma4.ready"
    if marker.exists():
        return
    # if snapshots already present, mark ready
    hits = list(cache.glob("models--google--gemma-4-E4B-it/**/config.json")) if cache.exists() else []
    if hits:
        marker.write_text("cached\n", encoding="utf-8")
        return
    downloading = _root() / "battery" / "hf_gemma4.downloading"
    if downloading.exists():
        rec = read_json(downloading) or {}
        if rec.get("exp") != EXP:
            log("waiting for first HF download")
            for _ in range(180):
                if marker.exists():
                    return
                time.sleep(10)
            log("download wait timed out — proceeding")
            return
    downloading.write_text(json.dumps({"exp": EXP, "ts": time.time()}), encoding="utf-8")


def mark_download_ready() -> None:
    marker = _root() / "battery" / "hf_gemma4.ready"
    marker.write_text("ok\n", encoding="utf-8")
    dl = _root() / "battery" / "hf_gemma4.downloading"
    if dl.exists():
        try:
            rec = json.loads(dl.read_text(encoding="utf-8"))
            if rec.get("exp") == EXP:
                dl.unlink()
        except Exception:
            pass


def resolve_repo() -> Path:
    env = os.environ.get("E2E_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve().parent.parent
    if (here / "scripts" / "battery_exp06_run.py").exists():
        return here
    for cand in (Path.cwd(), Path.home() / "Algoverse", Path.home() / "algoverse"):
        if (cand / "scripts" / "battery_exp06_run.py").exists():
            return cand
    dest = Path.home() / "Algoverse"
    if not dest.exists():
        log(f"git clone {REPO_URL}")
        subprocess.check_call(["git", "clone", REPO_URL, str(dest)])
    return dest


def source_battery_env() -> None:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import battery_adapter as ba  # noqa: E402

        keys = ba.source_battery_env()
        ba.plant_hf_token()
        log(f"sourced battery_env keys={len(keys)}")
        return
    except Exception as e:
        log(f"adapter source skip: {type(e).__name__}")
    p = Path.home() / ".battery_env"
    n = 0
    if p.is_file():
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:]
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v
                n += 1
    for name, path in (("HF_TOKEN", Path.home() / ".hf_token"), ("XAI_API_KEY", Path.home() / ".xai_api_key")):
        if not os.environ.get(name) and path.is_file():
            os.environ[name] = path.read_text(encoding="utf-8").strip()
            n += 1
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
    log(f"sourced battery_env keys={n}")


def plant_hf() -> None:
    source_battery_env()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
        return
    for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return


def main() -> int:
    source_battery_env()
    subprocess.run(["nvidia-smi"], check=False)
    os.environ["CUDA_VISIBLE_DEVICES"] = GPU
    os.environ.setdefault("E2E_ROOT", str(Path.home() / "algoverse_run"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_TIER", os.environ.get("EXP06_TIER", "smoke"))
    os.environ.setdefault("E2E_EMOTIC", str(_root() / "emotic_data"))
    os.environ.setdefault("E2E_SPLIT", str(_root() / "emotic_split.json"))
    os.environ["EXP06_GPU"] = GPU
    plant_hf()
    claim_gpu(GPU)
    wait_for_first_download()
    repo = resolve_repo()
    os.environ.setdefault("E2E_REPO", str(repo))
    run = repo / "scripts" / "battery_exp06_run.py"
    if not run.exists():
        raise SystemExit(f"missing {run} — upload exp06 scripts first")
    log(f"exec {run}")
    refresh_lock(GPU)
    ns = {"__name__": "battery_exp06_run", "__file__": str(run)}
    code = run.read_text(encoding="utf-8")
    try:
        exec(compile(code, str(run), "exec"), ns)
        rc = int(ns.get("main", lambda: 0)())
    finally:
        mark_download_ready()
        refresh_lock(GPU)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
