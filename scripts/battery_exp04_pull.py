from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from battery_exp05_hubctl import Hub  # noqa: E402


def main() -> int:
    h = Hub()
    h.login()
    kid = h.new_kernel()
    code = (
        "from pathlib import Path\n"
        "p = Path.home() / 'algoverse_run' / 'battery' / 'exp04' / 'results.json'\n"
        "print(p.read_text(encoding='utf-8'))\n"
    )
    text = h.execute(kid, code, timeout=60)
    dest = REPO / "artifacts" / "battery" / "exp04" / "results.json"
    dest.write_text(text, encoding="utf-8")
    rec = json.loads(text)
    print("WROTE", dest, "bytes", len(text), flush=True)
    print("complete", rec.get("complete"), flush=True)
    print("headline", rec.get("headline"), flush=True)
    g = rec.get("gates") or {}
    print("gates", g.get("passed"), "/", g.get("total"), flush=True)
    print("mechanism_answer", bool(rec.get("mechanism_answer")), flush=True)
    print("headline_est", (rec.get("estimates") or {}).get("headline_neg3_minus_neutral"), flush=True)
    arms = (g.get("arms") or {})
    for k, v in arms.items():
        print("arm", k, "ok", v.get("ok"), "mass", v.get("fc_mass_mean"), "finite", v.get("finite"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
