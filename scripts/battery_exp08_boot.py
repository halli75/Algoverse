# Remote boot for exp08. Own process / kernel. Does not steal the overseer tab.
# Searches hub for OASIS, downloads from OSF if missing, then runs the GPU job.
# [[battery-exp08]]

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import battery_exp08_lib as L  # noqa: E402


def _plant_hf() -> None:
    if os.environ.get("HF_TOKEN"):
        return
    for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return


def _ensure_pkg(mod: str, spec: str | None = None) -> None:
    try:
        __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec or mod])


def main() -> int:
    root = L.battery_root()
    run = L.exp_run_dir()
    run.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("E2E_ROOT", str(root))
    os.environ.setdefault("E2E_TIER", os.environ.get("E2E_TIER", "smoke"))
    os.environ.setdefault("E2E_MODEL", L.PRIMARY_MODEL)
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))
    os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))
    os.environ.setdefault("E2E_DATA", str(run / "data"))
    os.environ.setdefault("EXP08_OUT", str(run / "results.json"))
    os.environ.setdefault("A100_LOCK", str(root / "battery" / "A100.lock"))
    os.environ.setdefault("EXP08_OASIS", str(run / "oasis"))
    sourced = L.source_battery_env()
    _plant_hf()
    L.heartbeat("boot", root=str(root), run=str(run), env_keys=sourced, hf=bool(os.environ.get("HF_TOKEN")))

    found = L.find_existing_oasis()
    L.heartbeat("oasis_search", found=str(found) if found else None)
    try:
        oasis = L.retrieve_oasis(Path(os.environ["EXP08_OASIS"]))
        L.write_json(run / "oasis_meta.json", oasis["meta"])
        try:
            push = L.push_oasis_checkpoint(Path(os.environ["EXP08_OASIS"]))
            L.write_json(run / "hf_push.json", {k: v for k, v in push.items() if k != "token"})
            L.heartbeat("hf_push", ok=push.get("ok"), repo=push.get("repo"), n_jpg=push.get("n_jpg"))
        except Exception as e:
            L.heartbeat("hf_push_fail", err=type(e).__name__)
    except Exception as e:
        L.write_json(
            L.local_art_dir() / "ADVISOR_REQUEST.md"
            if False
            else run / "ADVISOR_REQUEST.md",
            {"error": str(e)},
        )
        (run / "ADVISOR_REQUEST.md").write_text(
            "# Advisor request (exp08)\n\n"
            "OASIS retrieve failed. Need gpt-5.6-sol-high on official Kurdi OSF 6pnd7 "
            f"download path. Error:\n\n```\n{e}\n```\n\n"
            "Do not invent ratings. Do not substitute IAPS unless OASIS is blocked.\n",
            encoding="utf-8",
        )
        try:
            (L.local_art_dir() / "ADVISOR_REQUEST.md").write_text(
                (run / "ADVISOR_REQUEST.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        except OSError:
            pass
        raise

    for mod, spec in (
        ("PIL", "pillow"),
        ("numpy", "numpy"),
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("bitsandbytes", "bitsandbytes>=0.46.1"),
    ):
        try:
            _ensure_pkg(mod, spec)
        except Exception as e:
            print(f"pkg {mod} skip: {e}", flush=True)

    runner = _HERE / "battery_exp08_run.py"
    if not runner.exists():
        runner = Path.home() / "Algoverse" / "scripts" / "battery_exp08_run.py"
    print("exec", runner, flush=True)
    return subprocess.call([sys.executable, str(runner)])


if __name__ == "__main__":
    raise SystemExit(main())
