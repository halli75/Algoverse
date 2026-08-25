# Host boot for exp03 (cross-modal signature). Own process. GPU 6.
# No overseer-tab theft. CUDA_VISIBLE_DEVICES=6.
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def log(m: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)


def source_battery_env() -> None:
    envp = Path.home() / ".battery_env"
    if not envp.is_file():
        return
    for line in envp.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[7:].strip()
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip().strip("'").strip('"')
        if k and v and k not in os.environ:
            os.environ[k] = v


def ensure_secrets() -> None:
    source_battery_env()
    if not os.environ.get("HF_TOKEN"):
        for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
            if cand.is_file():
                tok = cand.read_text(encoding="utf-8").strip()
                if tok:
                    os.environ["HF_TOKEN"] = tok
                    os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                    break
    if not os.environ.get("XAI_API_KEY"):
        xp = Path.home() / ".xai_api_key"
        if xp.is_file():
            key = xp.read_text(encoding="utf-8").strip()
            if key:
                os.environ["XAI_API_KEY"] = key


def main() -> int:
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp03"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ["E2E_EXP03"] = str(run)
    os.environ["E2E_OUT"] = str(run / "results.json")
    os.environ["E2E_HB"] = str(run / "heartbeat.json")
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_DATA", str(run / "data"))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_LOCK", str(root / "battery" / "A100.lock"))
    os.environ.setdefault("E2E_TIER", "smoke")
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("EXP03_GPU", "6")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    ensure_secrets()

    user_site = (
        Path.home()
        / ".local"
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    os.environ["PYTHONPATH"] = str(user_site) + os.pathsep + os.environ.get("PYTHONPATH", "")
    local_bin = str(Path.home() / ".local" / "bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = local_bin + os.pathsep + os.environ.get("PATH", "")

    script = None
    for cand in (
        Path(__file__).resolve().parent / "battery_exp03_run.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "battery_exp03_run.py",
        Path.home() / "Algoverse" / "scripts" / "battery_exp03_run.py",
        run / "battery_exp03_run.py",
    ):
        if cand is not None and cand.exists():
            script = cand
            break
    if script is None:
        raise SystemExit("battery_exp03_run.py not found")

    dest = run / "battery_exp03_run.py"
    if script.resolve() != dest.resolve():
        dest.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
        script = dest

    for spec, mod in (
        ("pandas", "pandas"),
        ("pillow", "PIL"),
        ("accelerate", "accelerate"),
        ("bitsandbytes>=0.46.1", "bitsandbytes"),
        ("huggingface_hub", "huggingface_hub"),
        ("transformers", "transformers"),
        ("numpy", "numpy"),
    ):
        try:
            __import__(mod)
        except ImportError:
            log(f"pip install {spec}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec])

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = os.environ["CUDA_VISIBLE_DEVICES"]
    log(
        "boot exp03 "
        + json_safe(
            {
                "script": str(script),
                "root": str(root),
                "gpu": env["CUDA_VISIBLE_DEVICES"],
                "tier": env.get("E2E_TIER"),
                "hf": bool(env.get("HF_TOKEN")),
                "xai": bool(env.get("XAI_API_KEY")),
            }
        )
    )
    return int(subprocess.call([sys.executable, "-u", str(script)], env=env))


def json_safe(obj) -> str:
    import json

    return json.dumps(obj, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
