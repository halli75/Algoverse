# JupyterHub A100 boot for graded sycophancy × affect.
# Not a Colab gist restore. No google.colab userdata.
# [[sycophancy-affect-experiment]]
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_URL = "https://github.com/halli75/Algoverse.git"
EXPECTED_SPLIT = "1e8ea1c22144dd9d"
SPLIT_GIST = (
    "https://gist.githubusercontent.com/halli75/d888da53224aac15e38a1f0d30f75805/"
    "raw/80b9868aa100b5a0dde318082b1678f34d20f4a0/"
)
EMOTIC_DRIVE = "https://drive.google.com/uc?id=1icMKzWIlmFKhTkb4OrH8QAHHaaGOP9Zo"
ORIGINAL_PREREG_HASH = "051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876"


def _root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def log(m: str) -> None:
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    s = f"{time.strftime('%H:%M:%S')} {m}"
    print(s, flush=True)
    with (root / "e2e_sycophancy_boot_log.txt").open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def hb(stage: str, **kw) -> None:
    hb_path = Path(os.environ.get("E2E_HB", str(_root() / "e2e_sycophancy_heartbeat.json")))
    payload = {"stage": stage, "ts": time.time(), "job": "sycophancy_affect", **kw}
    hb_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = hb_path.with_name(hb_path.name + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, hb_path)
    log("HB " + stage + " " + json.dumps(kw)[:200])


def ensure_pkg(mod: str, pip_spec: str | None = None) -> None:
    try:
        __import__(mod)
    except ImportError:
        spec = pip_spec or mod
        log(f"pip install {spec}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec])
    local_bin = str(Path.home() / ".local" / "bin")
    if local_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = local_bin + os.pathsep + os.environ.get("PATH", "")


def set_paths() -> dict[str, Path]:
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    paths = {
        "root": root,
        "out": Path(os.environ.setdefault("E2E_OUT", str(root / "e2e_sycophancy_results.json"))),
        "hb": Path(os.environ.setdefault("E2E_HB", str(root / "e2e_sycophancy_heartbeat.json"))),
        "dirs": Path(os.environ.setdefault("E2E_DIRS", str(root / "e2e_sycophancy_dirs.pt"))),
        "split": Path(os.environ.setdefault("E2E_SPLIT", str(root / "emotic_split.json"))),
        "emotic": Path(os.environ.setdefault("E2E_EMOTIC", str(root / "emotic_data"))),
        "data": Path(os.environ.setdefault("E2E_DATA", str(root / "e2e_data"))),
    }
    paths["data"].mkdir(parents=True, exist_ok=True)
    paths["emotic"].mkdir(parents=True, exist_ok=True)
    return paths


def resolve_repo() -> Path:
    env = os.environ.get("E2E_REPO")
    if env:
        return Path(env).expanduser()
    cwd = Path.cwd()
    if (cwd / "scripts" / "e2e_sycophancy_affect.py").exists():
        return cwd
    here = Path(__file__).resolve().parent.parent if "__file__" in globals() else None
    if here is not None and (here / "scripts" / "e2e_sycophancy_affect.py").exists():
        return here
    return Path.home() / "Algoverse"


def clone_or_pull(repo: Path) -> Path:
    script = repo / "scripts" / "e2e_sycophancy_affect.py"
    if script.exists() and (repo / ".git").exists():
        log(f"git pull {repo}")
        try:
            subprocess.check_call(["git", "-C", str(repo), "pull", "--ff-only"])
        except subprocess.CalledProcessError as e:
            log(f"git pull failed (continue with existing tree): {e}")
        return repo
    if script.exists():
        return repo
    log(f"git clone {REPO_URL} -> {repo}")
    repo.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "clone", REPO_URL, str(repo)])
    return repo


def ensure_emotic(paths: dict[str, Path]) -> None:
    emotic_root = paths["emotic"]
    split_path = paths["split"]
    root = paths["root"]
    csv_path = emotic_root / "emotic_pre" / "train.csv"
    if csv_path.exists() and (emotic_root / "emotic").exists():
        log("EMOTIC already present — skip download")
    else:
        ensure_pkg("gdown")
        ensure_pkg("pandas")
        ensure_pkg("PIL", "pillow")
        ensure_pkg("sklearn", "scikit-learn")
        hb("ann_download")
        ann_zip = root / "Annotations.zip"
        if not ann_zip.exists():
            b64p = root / "Annotations.zip.b64.txt"
            urllib.request.urlretrieve(SPLIT_GIST + "Annotations.zip.b64.txt", b64p)
            ann_zip.write_bytes(base64.b64decode(b64p.read_text().encode()))
        hb("images_download")
        zip_path = root / "emotic_images.zip"
        if not (zip_path.exists() and zip_path.stat().st_size > 1_000_000_000):
            subprocess.check_call(
                [sys.executable, "-m", "gdown", EMOTIC_DRIVE, "-O", str(zip_path)]
            )
        hb("unpack")
        img_root = root / "emotic_images"
        if not (img_root / "emotic").exists():
            img_root.mkdir(exist_ok=True)
            try:
                subprocess.check_call(["bash", "-lc", f"unzip -qo {zip_path} -d {img_root}"])
            except subprocess.CalledProcessError:
                import zipfile

                log("unzip binary missing; extracting with zipfile")
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(img_root)
        emotic = img_root / "emotic"
        emotic_root.mkdir(parents=True, exist_ok=True)
        if not (emotic_root / "emotic").exists():
            subprocess.check_call(["ln", "-sfn", str(emotic), str(emotic_root / "emotic")])
        ann_dir = root / "annotations"
        subprocess.check_call(
            [
                "bash",
                "-lc",
                f"rm -rf {ann_dir} && mkdir -p {ann_dir} && unzip -qo {ann_zip} -d {ann_dir}",
            ]
        )
        ann = next(ann_dir.rglob("Annotations"), None)
        if ann is None:
            raise SystemExit("Annotations missing after unzip")
        if not (emotic_root / "Annotations").exists():
            subprocess.check_call(["ln", "-sfn", str(ann), str(emotic_root / "Annotations")])
        hb("mat2py")
        if not csv_path.exists():
            ensure_pkg("cv2", "opencv-python-headless")
            repo = root / "emotic_repo"
            if not repo.exists():
                subprocess.check_call(
                    ["git", "clone", "-q", "https://github.com/Tandon-A/emotic.git", str(repo)]
                )
            mat2py = repo / "mat2py.py"
            text = mat2py.read_text(encoding="utf-8", errors="ignore")
            old = (
                "      cv2.imwrite(os.path.join(save_dir, 'context1.png'), context_arr[-1])\n"
                "      cv2.imwrite(os.path.join(save_dir, 'body1.png'), body_arr[-1])"
            )
            new = (
                "      if generate_npy:\n"
                "        cv2.imwrite(os.path.join(save_dir, 'context1.png'), context_arr[-1])\n"
                "        cv2.imwrite(os.path.join(save_dir, 'body1.png'), body_arr[-1])"
            )
            if old in text:
                mat2py.write_text(text.replace(old, new), encoding="utf-8")
            env = os.environ.copy()
            user_site = str(Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
            env["PYTHONPATH"] = user_site + os.pathsep + env.get("PYTHONPATH", "")
            subprocess.check_call(
                [sys.executable, "mat2py.py", "--data_dir", str(emotic_root), "--label", "all"],
                cwd=str(repo),
                env=env,
            )

    n_jpg = sum(1 for _ in (emotic_root / "emotic").rglob("*.jpg"))
    log(f"n_jpg={n_jpg}")
    if n_jpg < 20000:
        raise SystemExit(f"incomplete emotic unpack n_jpg={n_jpg} (need ≥20000)")

    if not split_path.exists():
        hb("split_pin")
        meta = json.loads(urllib.request.urlopen(SPLIT_GIST + "emotic_split_b64_meta.json").read())
        parts = []
        for i in range(meta["n"]):
            parts.append(
                urllib.request.urlopen(SPLIT_GIST + f"emotic_split_b64_{i:02d}.txt").read().decode("ascii")
            )
        b64 = "".join(parts)
        if len(b64) != meta["total"]:
            raise SystemExit(f"b64 len {len(b64)} != {meta['total']}")
        split_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = split_path.with_name(split_path.name + ".tmp")
        tmp.write_bytes(base64.b64decode(b64))
        os.replace(tmp, split_path)
    split = json.loads(split_path.read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    log(f"split_hash={split_hash} n_train={len(split['train_ids'])}")
    if split_hash != EXPECTED_SPLIT:
        raise SystemExit(f"pinned split hash mismatch {split_hash}")


def main() -> int:
    if "google.colab" in sys.modules:
        log("NOTE: running on JupyterHub boot path; ignoring google.colab userdata")

    paths = set_paths()
    os.environ.setdefault("E2E_TIER", "smoke")
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_PREREG_HASH", ORIGINAL_PREREG_HASH)
    os.environ.setdefault("XAI_JUDGE_MODEL", "grok-4.6")
    os.environ.setdefault("XAI_REASONING_EFFORT", "high")

    for k in ("HF_TOKEN", "XAI_API_KEY"):
        if not os.environ.get(k):
            log(f"{k} not in env — gated load / Grok may fail")

    log(f"BOOT a100 tier={os.environ['E2E_TIER']} root={paths['root']}")
    hb("a100_boot", tier=os.environ["E2E_TIER"], root=str(paths["root"]))

    repo = clone_or_pull(resolve_repo())
    script = repo / "scripts" / "e2e_sycophancy_affect.py"
    if not script.exists():
        raise SystemExit(f"missing {script}")

    for spec in (
        "pandas",
        "pillow",
        "scikit-learn",
        "huggingface_hub",
        "accelerate",
        "bitsandbytes>=0.46.1",
    ):
        mod = spec.split(">=")[0].replace("-", "_")
        if spec.startswith("pillow"):
            mod = "PIL"
        elif spec.startswith("scikit"):
            mod = "sklearn"
        elif spec.startswith("bitsandbytes"):
            mod = "bitsandbytes"
        elif spec.startswith("huggingface"):
            mod = "huggingface_hub"
        try:
            __import__(mod)
        except ImportError:
            log(f"pip install {spec}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", spec])
    try:
        import transformer_lens  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "git+https://github.com/TransformerLensOrg/TransformerLens.git",
            ]
        )

    ensure_emotic(paths)
    hb("run_start", tier=os.environ["E2E_TIER"], script=str(script))
    env = os.environ.copy()
    env["E2E_MODEL"] = "google/gemma-4-E4B-it"
    env["E2E_NO_FALLBACK"] = "1"
    r = subprocess.run([sys.executable, "-u", str(script)], env=env)
    log(f"run exit={r.returncode}")
    hb("run_exit", code=r.returncode)
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
