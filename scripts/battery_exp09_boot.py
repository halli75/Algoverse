# ### BATTERY EXP09 boot — GPU 7 lock, remote launch, 15-min loop
# Do not take over the overseer JupyterLab tab. Own process only.

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

EXP = "exp09"
GPU = os.environ.get("CUDA_VISIBLE_DEVICES", "7")
MAX_CONCURRENT = 4
STALE_S = 20 * 60
HEARTBEAT_S = 5 * 60
LOOP_S = 90
MIN_FREE_MIB = 12000


def gpu_free_table() -> list[dict]:
    try:
        raw = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"],
            text=True,
        )
    except Exception as e:
        log(f"nvidia-smi fail {type(e).__name__}")
        return []
    rows = []
    for line in raw.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        idx, used, total = int(parts[0]), int(parts[1]), int(parts[2])
        rows.append({"gpu": str(idx), "used": used, "total": total, "free": total - used})
    return rows


def pick_gpu(min_free: int = MIN_FREE_MIB) -> str | None:
    rows = gpu_free_table()
    if not rows:
        return None
    log("vram " + " ".join(f"{r['gpu']}:{r['free']}MiB" for r in rows))
    pref = os.environ.get("CUDA_VISIBLE_DEVICES")
    if pref and pref.isdigit():
        for r in rows:
            if r["gpu"] == pref and r["free"] >= min_free:
                return r["gpu"]
    for r in sorted(rows, key=lambda x: (-x["free"], int(x["gpu"]))):
        if r["free"] >= min_free:
            return r["gpu"]
    return None


def wait_for_gpu() -> str:
    while True:
        gid = pick_gpu()
        if gid is not None:
            return gid
        log(f"no GPU with >={MIN_FREE_MIB} MiB free; sleep {LOOP_S}s")
        time.sleep(LOOP_S)


def _root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def log(msg: str) -> None:
    s = f"{time.strftime('%H:%M:%S')} {msg}"
    print(s, flush=True)
    p = _root() / "battery" / EXP
    p.mkdir(parents=True, exist_ok=True)
    with (p / "boot.log").open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def lock_path() -> Path:
    return Path(os.environ.get("BATTERY_LOCK", str(_root() / "battery" / "A100.lock")))


def read_lock() -> dict:
    p = lock_path()
    if not p.is_file():
        return {"max_concurrent": MAX_CONCURRENT, "holders": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"max_concurrent": MAX_CONCURRENT, "holders": {}}


def write_lock(data: dict) -> None:
    p = lock_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def _ts(raw) -> float:
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    try:
        return float(s)
    except ValueError:
        pass
    try:
        from datetime import datetime

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s[:19], fmt).timestamp()
            except ValueError:
                continue
    except Exception:
        pass
    return 0.0


def live_holders(data: dict) -> dict:
    now = time.time()
    live = {}
    holders = data.get("holders")
    if not isinstance(holders, dict):
        return live
    for gid, h in holders.items():
        if not isinstance(h, dict):
            continue
        ts = _ts(h.get("ts"))
        if ts and now - ts <= STALE_S:
            live[str(gid)] = h
        else:
            log(f"STALE_LOCK gpu={gid} exp={h.get('exp')} age={now - ts:.0f}s")
    return live


def claim_gpu() -> None:
    lock_f = None
    try:
        import fcntl  # type: ignore

        p = lock_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        lock_f = p.open("a+")
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
    except Exception:
        lock_f = None
    try:
        while True:
            data = read_lock()
            live = live_holders(data)
            mine = live.get(GPU)
            if mine and mine.get("exp") == EXP and int(mine.get("pid") or -1) == os.getpid():
                mine["ts"] = time.time()
                mine["stage"] = mine.get("stage") or "claimed"
                data["holders"] = live
                data["holders"][GPU] = mine
                write_lock(data)
                return
            if mine and int(mine.get("pid") or -1) != os.getpid():
                log(f"gpu {GPU} held by {mine}; wait")
                time.sleep(30)
                continue
            if len(live) >= MAX_CONCURRENT and GPU not in live:
                log(f"max concurrent {len(live)}={list(live)}; wait")
                time.sleep(30)
                continue
            live[GPU] = {
                "exp": EXP,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "ts": time.time(),
                "stage": "claimed",
            }
            data["holders"] = live
            write_lock(data)
            log(f"claimed gpu {GPU} concurrent={len(live)}")
            return
    finally:
        if lock_f is not None:
            try:
                import fcntl  # type: ignore

                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
                lock_f.close()
            except Exception:
                pass


def refresh_lock(stage: str) -> None:
    data = read_lock()
    live = live_holders(data)
    h = live.get(GPU) or {"exp": EXP, "pid": os.getpid(), "host": socket.gethostname()}
    h["ts"] = time.time()
    h["stage"] = stage
    h["pid"] = os.getpid()
    live[GPU] = h
    data["holders"] = live
    write_lock(data)


def source_battery_env() -> None:
    try:
        import battery_adapter as ba

        keys = ba.source_battery_env()
        ba.plant_hf_token()
        log(f"sourced battery_env keys={len(keys)}")
        return
    except Exception:
        pass
    p = Path.home() / ".battery_env"
    n = 0
    if p.is_file():
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
                n += 1
    xai = Path.home() / ".xai_api_key"
    if xai.is_file() and not os.environ.get("XAI_API_KEY"):
        os.environ["XAI_API_KEY"] = xai.read_text(encoding="utf-8").strip()
        n += 1
    log(f"sourced battery_env keys={n}")
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
        return
    for cand in (
        Path.home() / ".hf_token",
        Path.home() / ".cache" / "huggingface" / "token",
    ):
        if cand.is_file():
            tok = cand.read_text(encoding="utf-8").strip()
            if tok:
                os.environ["HF_TOKEN"] = tok
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", tok)
                return


def wait_for_model_cache() -> None:
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    marker = hub / "models--google--gemma-4-E4B-it"
    if marker.exists():
        log("hf cache present; skip download serialize")
        return
    data = read_lock()
    holder = (data.get("lock_holder") or data.get("download_holder") or "")
    if holder and holder != EXP:
        log(f"waiting first HF download holder={holder}")
        for _ in range(120):
            if marker.exists():
                log("hf cache appeared")
                return
            time.sleep(15)
    data = read_lock()
    data["download_holder"] = EXP
    write_lock(data)
    log("this job may perform first HF download")


def find_repo() -> Path:
    for cand in (
        Path(os.environ.get("E2E_REPO", "")),
        Path.home() / "Algoverse",
        Path.home() / "algoverse",
        Path.cwd(),
    ):
        if cand and (cand / "scripts" / "affect_core.py").exists():
            return cand
    raise FileNotFoundError("Algoverse repo with affect_core.py not found")


def run_remote() -> int:
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    os.environ.setdefault("E2E_ROOT", str(_root()))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_SPLIT", str(_root() / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(_root() / "emotic_data"))
    os.environ.setdefault("BATTERY_EXP09_ROOT", str(_root() / "battery" / EXP))
    source_battery_env()
    gid = wait_for_gpu()
    os.environ["CUDA_VISIBLE_DEVICES"] = gid
    global GPU
    GPU = gid
    log(f"using gpu {gid}")
    try:
        import battery_adapter as ba

        while True:
            live = [j for j in ba.running_gpu_jobs() if not j.get("stale") and j.get("exp") != EXP]
            if len(live) >= MAX_CONCURRENT:
                log(f"max concurrent wait {[j.get('exp') for j in live]}")
                time.sleep(LOOP_S)
                continue
            try:
                ba.claim_gpu(EXP, gid)
                break
            except SystemExit as e:
                log(f"adapter claim wait {e}")
                time.sleep(LOOP_S)
        ba.wait_for_first_download(EXP)
        used_adapter = True
    except Exception as e:
        log(f"adapter claim fallback {type(e).__name__}")
        claim_gpu()
        wait_for_model_cache()
        used_adapter = False
    if used_adapter:
        try:
            import battery_adapter as ba

            ba.refresh_lock(EXP, gid)
        except Exception:
            pass
    else:
        refresh_lock("launch_run")
    repo = find_repo()
    run = repo / "scripts" / "battery_exp09_run.py"
    alt = _root() / "battery" / EXP / "battery_exp09_run.py"
    script = run if run.is_file() else alt
    if not script.is_file():
        raise FileNotFoundError(script)
    sys.path.insert(0, str(script.parent))
    log(f"exec {script}")
    ns = {"__name__": "__main__", "__file__": str(script)}
    exec(script.read_text(encoding="utf-8"), ns)
    refresh_lock("done")
    return 0


def _paramiko():
    try:
        import paramiko  # type: ignore
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"])
        import paramiko  # type: ignore
    return paramiko


def ssh_connect(host: str, user: str, password: str):
    paramiko = _paramiko()
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(host, username=user, password=password, timeout=30, allow_agent=False, look_for_keys=False)
    return cli


def sftp_put(cli, mapping: dict[Path, str]) -> None:
    sftp = cli.open_sftp()
    try:
        for local, remote in mapping.items():
            remote_path = Path(remote).as_posix()
            parent = str(Path(remote_path).parent)
            cli.exec_command(f"mkdir -p {parent}")
            time.sleep(0.2)
            sftp.put(str(local), remote_path)
            log(f"put {local.name} -> {remote_path}")
    finally:
        sftp.close()


def ssh_out(cli, cmd: str, timeout: int = 60) -> str:
    _, stdout, stderr = cli.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return (out + err).strip()


def upload_and_launch(host: str, user: str, password: str) -> None:
    here = Path(__file__).resolve().parent
    repo = here.parent
    cli = ssh_connect(host, user, password)
    try:
        who = ssh_out(cli, "whoami; hostname; echo CUDA_CHECK; nvidia-smi -L | head")
        log(who)
        remote_repo = ssh_out(
            cli,
            "if [ -d $HOME/Algoverse/scripts ]; then echo $HOME/Algoverse; "
            "elif [ -d $HOME/algoverse/scripts ]; then echo $HOME/algoverse; "
            "else echo MISSING; fi",
        )
        if "MISSING" in remote_repo:
            raise RuntimeError("remote repo missing")
        remote_repo = remote_repo.splitlines()[-1].strip()
        ssh_out(cli, f"mkdir -p $HOME/algoverse_run/battery/exp09 {remote_repo}/scripts {remote_repo}/artifacts/battery/exp09 $HOME/algoverse_run/battery")
        puts = {
            here / "battery_exp09_run.py": remote_repo + "/scripts/battery_exp09_run.py",
            here / "battery_exp09_boot.py": remote_repo + "/scripts/battery_exp09_boot.py",
            here / "affect_core.py": remote_repo + "/scripts/affect_core.py",
            repo / "artifacts" / "battery" / "exp09" / "xstest_prompts.csv": remote_repo
            + "/artifacts/battery/exp09/xstest_prompts.csv",
        }
        split_local = repo / "artifacts" / "colab" / "emotic_split_1e8ea1c22144dd9d.json"
        if split_local.is_file():
            puts[split_local] = remote_repo + "/artifacts/battery/exp09/emotic_split_1e8ea1c22144dd9d.json"
        sftp_put(cli, puts)
        ssh_out(
            cli,
            f"mkdir -p $HOME/algoverse_run/battery/exp09 && "
            f"cp {remote_repo}/artifacts/battery/exp09/xstest_prompts.csv $HOME/algoverse_run/battery/exp09/ && "
            f"cp {remote_repo}/scripts/battery_exp09_run.py $HOME/algoverse_run/battery/exp09/ && "
            f"cp {remote_repo}/scripts/affect_core.py $HOME/algoverse_run/battery/exp09/ && "
            f"if [ ! -f $HOME/algoverse_run/emotic_split.json ] && [ -f {remote_repo}/artifacts/battery/exp09/emotic_split_1e8ea1c22144dd9d.json ]; then "
            f"cp {remote_repo}/artifacts/battery/exp09/emotic_split_1e8ea1c22144dd9d.json $HOME/algoverse_run/emotic_split.json; fi",
        )
        running = ssh_out(cli, "pgrep -af battery_exp09 || true")
        if "battery_exp09_run.py" in running or "battery_exp09_boot.py --run" in running:
            log("remote exp09 already running:\n" + running)
            return
        launch = (
            "export CUDA_VISIBLE_DEVICES=7 E2E_MODEL=google/gemma-4-E4B-it E2E_NO_FALLBACK=1 "
            "E2E_ROOT=$HOME/algoverse_run E2E_REPO=" + remote_repo + " "
            "E2E_SPLIT=$HOME/algoverse_run/emotic_split.json "
            "E2E_EMOTIC=$HOME/algoverse_run/emotic_data "
            "BATTERY_EXP09_ROOT=$HOME/algoverse_run/battery/exp09 "
            "PYTHONUNBUFFERED=1; "
            "nohup python3 $HOME/Algoverse/scripts/battery_exp09_boot.py --run "
            "> $HOME/algoverse_run/battery/exp09/nohup.out 2>&1 & echo PID $!"
        )
        # use discovered repo path
        launch = launch.replace("$HOME/Algoverse/scripts/battery_exp09_boot.py", remote_repo + "/scripts/battery_exp09_boot.py")
        out = ssh_out(cli, launch)
        log("launch " + out)
    finally:
        cli.close()


def pull_artifacts(host: str, user: str, password: str) -> dict | None:
    cli = ssh_connect(host, user, password)
    local = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp09"
    local.mkdir(parents=True, exist_ok=True)
    try:
        sftp = cli.open_sftp()
        remote = "/home/asca-ec66/algoverse_run/battery/exp09"
        home = ssh_out(cli, "echo $HOME").splitlines()[-1].strip()
        remote = home + "/algoverse_run/battery/exp09"
        for name in ("heartbeat.json", "STATUS.md", "results.json", "run.log", "boot.log", "nohup.out", "checkpoint.json"):
            r = remote + "/" + name
            dest = local / name
            try:
                sftp.get(r, str(dest))
                log(f"got {name}")
            except Exception:
                pass
        sftp.close()
        rp = local / "results.json"
        if rp.is_file():
            return json.loads(rp.read_text(encoding="utf-8"))
        return None
    finally:
        cli.close()


def results_valid(res: dict | None) -> bool:
    if not res:
        return False
    gates = res.get("gates") or {}
    items = gates.get("items") or []
    if not items:
        return False
    hard = [g for g in items if g.get("hard", True)]
    if not hard:
        return False
    if any(not g.get("passed") for g in hard):
        return False
    primary = (res.get("primary") or {}).get("conditions") or {}
    for cond in ("no_image", "fear", "anger", "sad", "happy", "neutral"):
        row = primary.get(cond) or {}
        rate = row.get("refuse_rate")
        if rate is None or not isinstance(rate, (int, float)):
            return False
    return True


def loop(host: str, user: str, password: str) -> int:
    upload_and_launch(host, user, password)
    t0 = time.time()
    while True:
        res = pull_artifacts(host, user, password)
        if results_valid(res):
            log("results.json valid")
            return 0
        hb = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / "exp09" / "heartbeat.json"
        age = None
        if hb.is_file():
            try:
                age = time.time() - float(json.loads(hb.read_text(encoding="utf-8")).get("ts") or 0)
            except Exception:
                age = None
        log(f"loop age_hb={age} elapsed={time.time() - t0:.0f}")
        if age is not None and age > STALE_S:
            log("stale heartbeat; relaunch")
            upload_and_launch(host, user, password)
        time.sleep(LOOP_S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="run experiment on this host (GPU 7)")
    ap.add_argument("--loop", action="store_true", help="upload, launch, 15-min poll")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--host", default=os.environ.get("BATTERY_HOST", "35.89.128.116"))
    ap.add_argument("--user", default=os.environ.get("BATTERY_USER", "asca-ec66"))
    args = ap.parse_args()
    if args.run:
        return run_remote()
    password = os.environ.get("BATTERY_SSH_PASS") or os.environ.get("BATTERY_PASS")
    if not password:
        raise RuntimeError("set BATTERY_SSH_PASS")
    if args.loop:
        return loop(args.host, args.user, password)
    if args.upload:
        upload_and_launch(args.host, args.user, password)
        return 0
    return run_remote()


if __name__ == "__main__":
    raise SystemExit(main())
