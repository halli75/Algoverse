# On-pod boot: data, then battery_v2_run. No v3 write.
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_URL = os.environ.get("E2E_GIT", "https://github.com/halli75/Algoverse.git")


def log(m: str) -> None:
    print(f"[boot {time.strftime('%H:%M:%S')}] {m}", flush=True)


def sh(cmd: list[str]) -> None:
    log(" ".join(cmd))
    subprocess.check_call(cmd)


def plant_token() -> None:
    scripts = Path(__file__).resolve().parent
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import battery_adapter as ba

    tok = ba.plant_hf_token()
    if not tok:
        raise SystemExit("HF_TOKEN missing (env, ~/.hf_token, or ~/.cache/huggingface/token)")
    os.environ["HF_TOKEN"] = tok
    os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)


def main() -> int:
    plant_token()
    root = Path(os.environ.get("E2E_ROOT", "/workspace/algoverse_run")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("E2E_ROOT", str(root))
    repo = Path(os.environ.get("E2E_REPO", "/workspace/Algoverse")).expanduser()
    if not (repo / "scripts" / "battery_v2_run.py").exists():
        if repo.exists():
            sh(["git", "-C", str(repo), "pull", "--ff-only"])
        else:
            sh(["git", "clone", REPO_URL, str(repo)])
    os.chdir(repo)
    try:
        subprocess.call(["bash", "-lc", "command -v unzip >/dev/null || (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq unzip)"])
    except Exception:
        pass
    sh([sys.executable, "-m", "pip", "install", "-q", "-U", "transformers", "accelerate", "pillow", "pandas", "numpy", "huggingface_hub", "gdown"])
    # Data: EMOTIC via existing sycophancy boot helper if missing.
    emotic = root / "emotic_data"
    split = root / "emotic_split.json"
    os.environ["E2E_EMOTIC"] = str(emotic)
    os.environ["E2E_SPLIT"] = str(split)
    if not (emotic / "emotic_pre" / "train.csv").exists():
        log("EMOTIC missing; running a100_sycophancy_boot.ensure_emotic")
        sys.path.insert(0, str(repo / "scripts"))
        import a100_sycophancy_boot as boot

        paths = boot.set_paths()
        boot.ensure_emotic(paths)
        if paths["split"].exists() and not split.exists():
            split.write_bytes(paths["split"].read_bytes())
    oasis_dir = root / "battery" / "exp08" / "oasis"
    oasis_dir.mkdir(parents=True, exist_ok=True)
    if not (oasis_dir / "oasis_means.json").exists():
        log("pull OASIS means from HF if possible")
        try:
            from huggingface_hub import snapshot_download

            snapshot_download(
                "halli75/algoverse-exp08-oasis",
                local_dir=str(oasis_dir),
                token=os.environ.get("HF_TOKEN"),
            )
        except Exception as e:
            log(f"OASIS HF skip: {type(e).__name__}: {e}")
    dirs_dest = root / "e2e_dirs_mechanism.pt"
    if not dirs_dest.exists():
        log("try HF frozen dirs pack (never writes v3 JSON)")
        try:
            from huggingface_hub import hf_hub_download, list_repo_files

            dirs_repo = os.environ.get("EXP10_DIRS_REPO", "halli75/algoverse-battery-exp10")
            files = list_repo_files(dirs_repo, repo_type="dataset", token=os.environ.get("HF_TOKEN"))
            name = next((f for f in files if f.endswith("e2e_dirs_mechanism.pt") or f.endswith("dirs_frozen_v3.pt")), None)
            if name:
                hf_hub_download(
                    dirs_repo,
                    name,
                    repo_type="dataset",
                    token=os.environ.get("HF_TOKEN"),
                    local_dir=str(root),
                )
                os.environ["E2E_DIRS"] = str(root / Path(name).name)
                log(f"dirs {name}")
        except Exception as e:
            log(f"dirs HF skip: {type(e).__name__}: {e}")
    if dirs_dest.exists():
        os.environ.setdefault("E2E_DIRS", str(dirs_dest))
    n_jpg = sum(1 for _ in (emotic / "emotic").rglob("*.jpg")) if (emotic / "emotic").exists() else 0
    if n_jpg < 20000:
        raise SystemExit(f"incomplete EMOTIC n_jpg={n_jpg}")
    os.environ["E2E_V2"] = str(repo / "artifacts" / "battery_v2")
    cmd = [
        sys.executable,
        "-u",
        str(repo / "scripts" / "battery_v2_run.py"),
        "--tier",
        os.environ.get("E2E_TIER", "budget3h"),
        "--models",
        os.environ.get("E2E_MODELS", "e4b,g12"),
        "--corpora",
        os.environ.get("E2E_CORPORA", "emotic,oasis"),
    ]
    log("run " + " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
