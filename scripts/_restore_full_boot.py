# Colab restore + full mechanism run (A100)
import base64
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

LOG = Path("/content/e2e_restore_log.txt")
HB = Path("/content/e2e_heartbeat.json")
# Pin gist revision so Colab does not hit a stale CDN /raw/ cache.
GIST = "https://gist.githubusercontent.com/halli75/d888da53224aac15e38a1f0d30f75805/raw/80b9868aa100b5a0dde318082b1678f34d20f4a0/"
EMOTIC_ROOT = Path("/content/emotic_data")
EXPECTED_SPLIT = "1e8ea1c22144dd9d"


def log(m: str) -> None:
    s = f"{time.strftime('%H:%M:%S')} {m}"
    print(s, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def hb(stage: str, **kw) -> None:
    HB.write_text(json.dumps({"stage": stage, "ts": time.time(), "tier": "full", **kw}))
    log("HB " + stage + " " + json.dumps(kw)[:200])


def main() -> int:
    env_path = Path("/content/_env.json")
    if env_path.exists():
        for k, v in json.loads(env_path.read_text()).items():
            if v:
                os.environ[k] = v
    for k, default in (
        ("E2E_TIER", "full"),
        ("E2E_MODEL", "google/gemma-4-E4B-it"),
        ("E2E_PREREG_HASH", "3111c3af7f7b12656cb0792bea4a21b4302a0c42"),
        ("E2E_NO_FALLBACK", "1"),
    ):
        os.environ.setdefault(k, default)

    log("BOOT restore+full A100 v3 combined-arrow")
    hb("restore_boot")
    import torch

    log(f"gpu={torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}")

    csv_path = EMOTIC_ROOT / "emotic_pre" / "train.csv"
    if not (csv_path.exists() and (EMOTIC_ROOT / "emotic").exists()):
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "gdown", "pandas", "pillow", "scikit-learn"]
        )
        hb("ann_download")
        if not Path("/content/Annotations.zip").exists():
            b64p = Path("/content/Annotations.zip.b64.txt")
            urllib.request.urlretrieve(GIST + "Annotations.zip.b64.txt", b64p)
            Path("/content/Annotations.zip").write_bytes(base64.b64decode(b64p.read_text().encode()))
        hb("images_download")
        zip_path = Path("/content/emotic_images.zip")
        if not (zip_path.exists() and zip_path.stat().st_size > 1_000_000_000):
            subprocess.check_call(
                [
                    "gdown",
                    "https://drive.google.com/uc?id=1icMKzWIlmFKhTkb4OrH8QAHHaaGOP9Zo",
                    "-O",
                    "/content/emotic_images.zip",
                    "--fuzzy",
                ]
            )
        hb("unpack")
        img_root = Path("/content/emotic_images")
        if not (img_root / "emotic").exists():
            img_root.mkdir(exist_ok=True)
            subprocess.check_call(["bash", "-lc", f"unzip -qo {zip_path} -d {img_root}"])
        emotic = img_root / "emotic"
        EMOTIC_ROOT.mkdir(exist_ok=True)
        if not (EMOTIC_ROOT / "emotic").exists():
            subprocess.check_call(["ln", "-sfn", str(emotic), str(EMOTIC_ROOT / "emotic")])
        subprocess.check_call(
            [
                "bash",
                "-lc",
                "rm -rf /content/annotations && mkdir -p /content/annotations && "
                "unzip -qo /content/Annotations.zip -d /content/annotations",
            ]
        )
        ann = next(Path("/content/annotations").rglob("Annotations"), None)
        if ann is None:
            raise SystemExit("Annotations missing after unzip")
        if not (EMOTIC_ROOT / "Annotations").exists():
            subprocess.check_call(["ln", "-sfn", str(ann), str(EMOTIC_ROOT / "Annotations")])
        hb("mat2py")
        if not csv_path.exists():
            repo = Path("/content/emotic_repo")
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
            subprocess.check_call(
                [sys.executable, "mat2py.py", "--data_dir", str(EMOTIC_ROOT), "--label", "all"],
                cwd=str(repo),
            )
    else:
        log("EMOTIC already present — skip download")

    n_jpg = sum(1 for _ in (EMOTIC_ROOT / "emotic").rglob("*.jpg"))
    log(f"n_jpg={n_jpg}")
    if n_jpg < 20000:
        raise SystemExit(f"incomplete emotic unpack n_jpg={n_jpg} (need ≥20000)")

    hb("split_pin")
    meta = json.loads(urllib.request.urlopen(GIST + "emotic_split_b64_meta.json").read())
    parts = []
    for i in range(meta["n"]):
        parts.append(
            urllib.request.urlopen(GIST + f"emotic_split_b64_{i:02d}.txt").read().decode("ascii")
        )
    b64 = "".join(parts)
    if len(b64) != meta["total"]:
        raise SystemExit(f"b64 len {len(b64)} != {meta['total']}")
    Path("/content/emotic_split.json").write_bytes(base64.b64decode(b64))
    split = json.loads(Path("/content/emotic_split.json").read_text(encoding="utf-8"))
    split_hash = hashlib.sha256(json.dumps(split, sort_keys=True).encode()).hexdigest()[:16]
    log(f"split_hash={split_hash} n_train={len(split['train_ids'])}")
    if split_hash != EXPECTED_SPLIT:
        raise SystemExit(f"pinned split hash mismatch {split_hash}")

    hb("download_script", split_hash=split_hash)
    urllib.request.urlretrieve(GIST + "e2e_mechanism_context_suppress.py", "/content/e2e_mechanism_context_suppress.py")
    urllib.request.urlretrieve(GIST + "mechanism_text_banks.json", "/content/mechanism_text_banks.json")

    hb("full_start")
    env = os.environ.copy()
    env["E2E_TIER"] = "full"
    env["E2E_MODEL"] = "google/gemma-4-E4B-it"
    env["E2E_PREREG_HASH"] = "3111c3af7f7b12656cb0792bea4a21b4302a0c42"
    env["E2E_NO_FALLBACK"] = "1"
    r = subprocess.run([sys.executable, "-u", "/content/e2e_mechanism_context_suppress.py"], env=env)
    log(f"full exit={r.returncode}")
    hb("full_exit", code=r.returncode)
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
