from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import battery_exp09_hub as h

PROBE = r"""
import subprocess, pathlib, json
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.total,utilization.gpu','--format=csv'], text=True))
print('--- jobs')
print(subprocess.check_output(['bash','-lc','pgrep -af "battery_exp0|battery_exp10" || echo none'], text=True))
print('--- locks')
p = pathlib.Path.home()/'algoverse_run'/'battery'/'locks'
if p.exists():
    for f in sorted(p.glob('*.json')):
        print(f.name, f.read_text().strip())
print('--- ckpt')
ck = pathlib.Path.home()/'algoverse_run'/'battery'/'exp09'/'checkpoint.json'
if ck.exists():
    d=json.loads(ck.read_text())
    print('n_scores', len(d.get('scores',[])), 'n_sanity', len(d.get('sanity',[])))
"""


def main() -> int:
    hub = h.Hub()
    hub.login()
    kid = hub.new_kernel()
    print(hub.execute(kid, PROBE, timeout=60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
