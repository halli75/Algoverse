from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import battery_exp09_hub as h

CODE = r"""
import subprocess, time
print(subprocess.check_output(['bash','-lc','ls -l /proc/1762804 2>&1 | head; id; fuser -v /dev/nvidia7 2>&1 | head -20'], text=True))
print('fuser_k')
subprocess.call(['bash','-lc','fuser -k /dev/nvidia7 || true'])
time.sleep(2)
print(subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=memory.used','--format=csv'], text=True))
print(subprocess.check_output(['nvidia-smi','-i','7','--query-compute-apps=pid,used_memory','--format=csv'], text=True))
print('reset')
r = subprocess.run(['nvidia-smi','--gpu-reset','-i','7'], capture_output=True, text=True)
print('reset_rc', r.returncode)
print(r.stdout)
print(r.stderr)
time.sleep(2)
print(subprocess.check_output(['nvidia-smi','-i','7','--query-gpu=memory.used,utilization.gpu','--format=csv'], text=True))
"""


def main() -> int:
    hub = h.Hub()
    hub.login()
    kid = hub.new_kernel()
    print(hub.execute(kid, CODE, timeout=90))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
