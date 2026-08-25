# JupyterHub deploy for exp04 using the working exp05 Hub client.
# Credentials from gitignored env files. Never print secrets.
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from battery_exp05_hubctl import Hub  # noqa: E402  loads .env / .env.hub

LAUNCH = r"""
import os, subprocess
from pathlib import Path
home = Path.home()
benv = home / '.battery_env'
if benv.is_file():
    for raw in benv.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        if line.startswith('export '):
            line = line[7:]
        k, _, v = line.partition('=')
        k, v = k.strip(), v.strip().strip(chr(39)+chr(34))
        if k and k not in os.environ:
            os.environ[k] = v
for name, path in (('HF_TOKEN', home/'.hf_token'), ('XAI_API_KEY', home/'.xai_api_key')):
    if not os.environ.get(name) and path.is_file():
        os.environ[name] = path.read_text().strip()
if os.environ.get('HF_TOKEN'):
    os.environ.setdefault('HUGGING_FACE_HUB_TOKEN', os.environ['HF_TOKEN'])
run = home/'algoverse_run'/'battery'/'exp04'
run.mkdir(parents=True, exist_ok=True)
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.free,memory.used','--format=csv'], text=True))
alive = subprocess.check_output(['bash','-lc','pgrep -af battery_exp04 || true'], text=True)
print('ALIVE', alive.strip())
# Stop only our exp04 waiter so it can reclaim a free card. Never touch other battery PIDs.
for line in alive.splitlines():
    if 'battery_exp04_boot.py --run' in line or 'battery_exp04.py' in line:
        pid = line.strip().split()[0]
        if pid.isdigit() and 'pgrep' not in line:
            hb = run/'heartbeat.json'
            stage = ''
            if hb.exists():
                import json as _json
                try:
                    stage = _json.loads(hb.read_text()).get('stage') or ''
                except Exception:
                    stage = ''
            if stage.startswith('wait_gpu') or stage in ('pip', 'boot', 'fatal', ''):
                print('STOP_OWN_WAITER', pid, stage)
                subprocess.call(['kill', pid])
            else:
                print('KEEP_OWN', pid, stage)
alive2 = subprocess.check_output(['bash','-lc','pgrep -af battery_exp04 || true'], text=True)
print('ALIVE2', alive2.strip())
if 'battery_exp04_boot.py --run' in alive2:
    print('ALREADY_RUNNING')
else:
    env = os.environ.copy()
    env.pop('CUDA_VISIBLE_DEVICES', None)
    env.pop('EXP04_GPU', None)
    env['E2E_ROOT'] = str(home/'algoverse_run')
    env['E2E_REPO'] = str(home/'Algoverse')
    env['E2E_SPLIT'] = str(home/'algoverse_run'/'emotic_split.json')
    env['E2E_EMOTIC'] = str(home/'algoverse_run'/'emotic_data')
    env['E2E_MODEL'] = 'google/gemma-4-E4B-it'
    env['E2E_NO_FALLBACK'] = '1'
    env['EXP04_ROOT'] = str(run)
    env['EXP04_OUT'] = str(run/'results.json')
    env['EXP04_HB'] = str(run/'heartbeat.json')
    env['EXP04_CKPT'] = str(run/'checkpoint.jsonl')
    env['EXP04_MIN_FREE_GB'] = '18'
    env['PYTHONUNBUFFERED'] = '1'
    script = home/'Algoverse'/'scripts'/'battery_exp04_boot.py'
    out = open(run/'nohup.out', 'ab', buffering=0)
    proc = subprocess.Popen(
        ['python3', '-u', str(script), '--run'],
        cwd=str(home/'Algoverse'),
        env=env,
        stdout=out,
        stderr=out,
        start_new_session=True,
    )
    (run/'pid').write_text(str(proc.pid))
    print('LAUNCHED', proc.pid)
print('OUT', run/'nohup.out')
"""

STATUS = r"""
import subprocess
from pathlib import Path
run = Path.home()/'algoverse_run'/'battery'/'exp04'
print('HOME', Path.home())
for n in ['heartbeat.json','results.json','STATUS.md','nohup.out','pid','run.log']:
    p = run/n
    print('====', n, 'exists' if p.exists() else 'MISS', p.stat().st_size if p.exists() else 0)
    if p.exists() and n != 'nohup.out':
        print(p.read_text(errors='replace')[:2000])
    elif p.exists():
        print(p.read_text(errors='replace')[-2500:])
print('==== PS')
print(subprocess.check_output(['bash','-lc','pgrep -af battery_exp04 || true'], text=True))
print('==== GPU3')
print(subprocess.check_output(['nvidia-smi','-i','3'], text=True))
print('==== GPUALL')
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,memory.free,utilization.gpu','--format=csv'], text=True))
print('==== PIDS')
print(subprocess.check_output(['bash','-lc','ps -p 1842973,2036982,2050463 -o pid,user,etime,cmd --no-headers || true; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,process_name --format=csv'], text=True, stderr=subprocess.STDOUT))
print('==== LOCKS')
lock = Path.home()/'algoverse_run'/'battery'
for p in sorted(lock.glob('**/*'))[:40]:
    if p.is_file() and ('lock' in p.name.lower() or p.name.startswith('gpu_')):
        print(p, p.read_text(errors='replace')[:200])
"""


def upload(h: Hub) -> None:
    files = {
        "Algoverse/scripts/battery_exp04.py": HERE / "battery_exp04.py",
        "Algoverse/scripts/battery_exp04_boot.py": HERE / "battery_exp04_boot.py",
        "Algoverse/scripts/battery_exp04_cell.py": HERE / "battery_exp04_cell.py",
        "Algoverse/scripts/battery_exp04_hub.py": HERE / "battery_exp04_hub.py",
        "Algoverse/scripts/battery_adapter.py": HERE / "battery_adapter.py",
        "algoverse_run/battery/exp04/battery_exp04.py": HERE / "battery_exp04.py",
        "algoverse_run/battery/exp04/battery_adapter.py": HERE / "battery_adapter.py",
        "algoverse_run/battery/exp04/battery_exp04_boot.py": HERE / "battery_exp04_boot.py",
    }
    spec = REPO / "artifacts" / "battery" / "exp04" / "ADVISOR_SPEC.md"
    if spec.is_file():
        files["Algoverse/artifacts/battery/exp04/ADVISOR_SPEC.md"] = spec
    h.mkdir("algoverse_run/battery")
    h.mkdir("algoverse_run/battery/exp04")
    h.mkdir("Algoverse/scripts")
    h.mkdir("Algoverse/artifacts/battery")
    h.mkdir("Algoverse/artifacts/battery/exp04")
    for dest, src in files.items():
        h.put_text(dest, src.read_text(encoding="utf-8"))
        print(f"uploaded {dest} bytes={src.stat().st_size}", flush=True)


def _sync_slices(text: str, dest: Path) -> None:
    blocks = {}
    cur = None
    buf = []
    for line in text.splitlines(True):
        if line.startswith("==== "):
            if cur:
                blocks[cur] = "".join(buf)
            cur = line.split()[1] if len(line.split()) > 1 else None
            buf = []
        elif cur:
            buf.append(line)
    if cur:
        blocks[cur] = "".join(buf)
    for name in ("heartbeat.json", "results.json", "STATUS.md"):
        body = blocks.get(name)
        if not body or body.startswith("MISS"):
            continue
        (dest / name).write_text(body, encoding="utf-8")
        print("synced", name, "bytes", len(body), flush=True)


def pull_from_text(text: str) -> None:
    dest = REPO / "artifacts" / "battery" / "exp04"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "host_status.txt").write_text(text, encoding="utf-8")
    # also try contents API
    for name in ("heartbeat.json", "results.json", "STATUS.md", "nohup.out"):
        try:
            rec = hget = None
        except Exception:
            pass


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    h = Hub()
    h.login()
    kid = h.new_kernel()
    if cmd == "status":
        text = h.execute(kid, STATUS, timeout=60)
        dest = REPO / "artifacts" / "battery" / "exp04"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "host_status.txt").write_text(text, encoding="utf-8")
        print(text.encode("ascii", "replace").decode("ascii"))
        _sync_slices(text, dest)
        return 0
    if cmd == "deploy":
        upload(h)
        print("===LAUNCH===", flush=True)
        print(h.execute(kid, LAUNCH, timeout=60))
        time.sleep(4)
        print("===STATUS===", flush=True)
        text = h.execute(kid, STATUS, timeout=60)
        print(text)
        dest = REPO / "artifacts" / "battery" / "exp04"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "host_status.txt").write_text(text, encoding="utf-8")
        return 0
    raise SystemExit(f"unknown {cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
