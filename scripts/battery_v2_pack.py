# Pack v2 code for a RunPod host. Never includes .env or API keys.
from __future__ import annotations

import argparse
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP_DIR = {
    ".git",
    "__pycache__",
    ".ipynb_checkpoints",
    "node_modules",
    "artifacts/battery_v2/_dry",
}
SKIP_FILE = {".env", ".hf_token", ".xai_api_key", ".battery_env", ".runpod_api_key"}
SKIP_SUFFIX = {".pt", ".npy", ".pth", ".log"}
INCLUDE_PREFIX = (
    "scripts/",
    "tests/",
    "data/battery/",
    "docs/battery_v2.md",
    "artifacts/battery/exp09/xstest_prompts.csv",
    "README.md",
    "AGENTS.md",
)


def keep(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    name = Path(rel).name
    if name in SKIP_FILE or name.startswith(".env"):
        return False
    if Path(rel).suffix in SKIP_SUFFIX:
        return False
    parts = set(Path(rel).parts)
    if parts & SKIP_DIR or "__pycache__" in rel:
        return False
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in INCLUDE_PREFIX)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default=str(REPO / "artifacts" / "battery_v2" / "payload.tgz"))
    args = ap.parse_args()
    dest = Path(args.o)
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with tarfile.open(dest, "w:gz") as tar:
        for p in REPO.rglob("*"):
            if not p.is_file():
                continue
            rel = str(p.relative_to(REPO)).replace("\\", "/")
            if not keep(rel):
                continue
            tar.add(p, arcname="Algoverse/" + rel)
            n += 1
    print(f"wrote {dest} files={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
