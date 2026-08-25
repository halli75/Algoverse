# JupyterHub / nohup launcher for battery exp07. Own process, GPU 4.
# Does not touch the overseer notebook tab.
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

JOB = "battery_exp07"
PRIMARY = "google/gemma-4-E4B-it"
GPU = os.environ.get("EXP07_GPU", "4")


def log(m: str) -> None:
    print(m, flush=True)


def source_battery_env() -> None:
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
        log(f"sourced battery_env keys={n}")
    else:
        log("battery_env missing")
    for name, path in (("HF_TOKEN", Path.home() / ".hf_token"), ("XAI_API_KEY", Path.home() / ".xai_api_key")):
        if not os.environ.get(name) and path.is_file():
            os.environ[name] = path.read_text(encoding="utf-8").strip()
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])


def ensure_hf() -> None:
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
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp07"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ["EXP07_DIR"] = str(run)
    os.environ["CUDA_VISIBLE_DEVICES"] = str(GPU)
    os.environ["EXP07_GPU"] = str(GPU)
    os.environ.setdefault("E2E_TIER", os.environ.get("E2E_TIER", "full"))
    os.environ.setdefault("E2E_MODEL", PRIMARY)
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_LOCK", str(root / "battery" / "A100.lock"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    ensure_hf()
    user_site = Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    os.environ["PYTHONPATH"] = str(user_site) + os.pathsep + os.environ.get("PYTHONPATH", "")
    local_bin = str(Path.home() / ".local" / "bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = local_bin + os.pathsep + os.environ.get("PATH", "")

    script = None
    for cand in (
        Path(__file__).resolve().parent / "battery_exp07_run.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "battery_exp07_run.py",
        Path.home() / "Algoverse" / "scripts" / "battery_exp07_run.py",
        run / "battery_exp07_run.py",
    ):
        if cand is not None and cand.exists():
            script = cand
            break
    if script is None:
        raise SystemExit("battery_exp07_run.py not found")

    dest = run / "battery_exp07_run.py"
    if script.resolve() != dest.resolve():
        dest.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
        script = dest

    log(
        "exp07 boot "
        + str(
            {
                "script": str(script),
                "root": str(root),
                "gpu": os.environ["CUDA_VISIBLE_DEVICES"],
                "tier": os.environ["E2E_TIER"],
                "hf": bool(os.environ.get("HF_TOKEN")),
            }
        )
    )
    subprocess.run(["nvidia-smi", "-i", str(GPU)], check=False)
    env = os.environ.copy()
    return subprocess.call([sys.executable, "-u", str(script)], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
