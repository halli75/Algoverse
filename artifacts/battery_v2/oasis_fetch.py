"""CPU-side OASIS retrieve while GPU scores. Writes oasis_means.json for v2."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent if Path(__file__).name.startswith("battery") else "/workspace/Algoverse/scripts"))
# When copied to /workspace/oasis_fetch.py
ROOT = Path("/workspace/Algoverse")
sys.path.insert(0, str(ROOT / "scripts"))

import battery_exp08_lib as o8  # noqa: E402

DEST = Path("/workspace/algoverse_run/battery/exp08/oasis")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    rec = o8.retrieve_oasis(DEST)
    items = rec["items"]
    means = DEST / "oasis_means.json"
    means.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")
    n_jpg = sum(1 for _ in DEST.rglob("*.jpg"))
    print(
        json.dumps(
            {
                "n_items": len(items),
                "n_jpg": n_jpg,
                "means": str(means),
                "counts": (rec.get("meta") or {}).get("counts"),
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
