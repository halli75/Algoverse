# exp10 boot: claim a free GPU (max 4 concurrent), launch, 15-min loop.
# Own process. Do not take the overseer JupyterLab tab.
# Source ~/.battery_env. Never print secrets.
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

EXP = "exp10"
MAX_CONCURRENT = 4
STALE_S = 20 * 60
LOOP_S = 15 * 60


def _root() -> Path:
    return Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()


def log(msg: str) -> None:
    s = f"{time.strftime('%H:%M:%S')} {msg}"
    print(s, flush=True)
    p = _root() / "battery" / EXP
    p.mkdir(parents=True, exist_ok=True)
    with (p / "boot.log").open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def load_env_files() -> None:
    for cand in (Path.home() / ".battery_env", Path(__file__).resolve().parents[1] / ".env"):
        if not cand.is_file():
            continue
        for line in cand.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    tok = Path.home() / ".hf_token"
    if tok.is_file() and not os.environ.get("HF_TOKEN"):
        os.environ["HF_TOKEN"] = tok.read_text(encoding="utf-8").strip()
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])


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


def _holder_ts(h: dict) -> float:
    if h.get("unix") is not None:
        try:
            return float(h["unix"])
        except (TypeError, ValueError):
            pass
    ts = h.get("ts")
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return float(ts)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return time.mktime(time.strptime(ts[:19], fmt))
            except ValueError:
                continue
    return 0.0


def live_holders(data: dict) -> dict:
    now = time.time()
    live = {}
    for gid, h in (data.get("holders") or {}).items():
        ts = _holder_ts(h)
        if now - ts <= STALE_S:
            live[str(gid)] = h
        else:
            log(f"STALE_LOCK gpu={gid} exp={h.get('exp')} age={now - ts:.0f}s")
    return live


WAVE_AB = ("exp04", "exp06", "exp02", "exp09")
_WAVE_WAIT = ("wait_gpu", "wait_concurrent", "wait_gpu_occ", "launch", "boot", "download", "queued")
_WAVE_LOADED = ("score", "scoring", "eval", "units", "model", "infer", "trial", "generate", "forward", "probe")


def _wave_one(exp: str) -> str:
    run = _root() / "battery" / exp
    rp = run / "results.json"
    if rp.is_file() and rp.stat().st_size > 20:
        try:
            rec = json.loads(rp.read_text(encoding="utf-8"))
            if rec.get("complete") is True:
                return "done"
        except Exception:
            pass
    hp = run / "heartbeat.json"
    if hp.is_file():
        try:
            rec = json.loads(hp.read_text(encoding="utf-8"))
        except Exception:
            rec = {}
        stage = str(rec.get("stage") or "").lower()
        if any(k in stage for k in _WAVE_WAIT):
            return "waiting"
        if stage and any(k in stage for k in _WAVE_LOADED):
            return "loaded"
        if stage:
            return "loaded"
    return "unknown"


def wave_ab_ready() -> tuple[bool, dict[str, str]]:
    st = {e: _wave_one(e) for e in WAVE_AB}
    ok = all(v in ("loaded", "done") for v in st.values())
    return ok, st


# Night overseer: claim first card with enough free VRAM for Gemma-4 nf4.
# Prefer GPU 2, then GPU 0. Do not require a fully empty card.
MIN_FREE_MIB = 18000
PREFER_GPUS = ("2", "0")


def gpu_free_ids() -> list[str]:
    try:
        raw = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
    except Exception as e:
        log(f"nvidia-smi fail {e}")
        return []
    room: list[tuple[str, float]] = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        idx, used, free_m = parts[0], float(parts[1]), float(parts[2])
        if free_m >= MIN_FREE_MIB or used < 1500:
            room.append((idx, free_m))
            log(f"gpu {idx} claimable used={used:.0f} free={free_m:.0f}")
    order = {g: i for i, g in enumerate(PREFER_GPUS)}
    room.sort(key=lambda t: (order.get(t[0], 99), -t[1]))
    return [idx for idx, _ in room]


def _wait_heartbeat(stage: str, **kw) -> None:
    payload = {
        "job": EXP,
        "stage": stage,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %T"),
        **kw,
    }
    for dest in (
        _root() / "battery" / EXP / "heartbeat.json",
        Path(__file__).resolve().parents[1] / "artifacts" / "battery" / EXP / "heartbeat.json",
    ):
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".tmp")
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            os.replace(tmp, dest)
        except OSError:
            pass


def claim_gpu() -> str:
    preferred = os.environ.get("CUDA_VISIBLE_DEVICES")
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
            mine = [gid for gid, h in live.items() if h.get("exp") == EXP and int(h.get("pid") or -1) == os.getpid()]
            if mine:
                gid = mine[0]
                live[gid]["ts"] = time.time()
                data["holders"] = live
                write_lock(data)
                return gid
            if len(live) >= MAX_CONCURRENT:
                log(f"max concurrent {list(live)}; wait")
                _wait_heartbeat("wait_concurrent", live=list(live))
                time.sleep(30)
                continue
            if os.environ.get("EXP10_SKIP_WAVE") != "1":
                ready, wave = wave_ab_ready()
                if not ready:
                    log(f"waveAB not ready {wave}; stay last")
                    _wait_heartbeat("wait_wave_ab", live=list(live), wave=wave)
                    time.sleep(45)
                    continue
            held = {g for g, h in live.items() if h.get("exp") not in (None, EXP) and h.get("exp") != "exp10"}
            free = gpu_free_ids()
            cands = []
            if preferred:
                pref = preferred.split(",")[0]
                if pref not in held and pref in free:
                    cands.append(pref)
            cands.extend(g for g in free if g not in held and g not in cands)
            if not cands:
                log(f"no free gpu mem; live_lock={list(live)} wait")
                _wait_heartbeat("wait_gpu", live=list(live), free=free)
                time.sleep(30)
                continue
            gid = cands[0]
            live[gid] = {
                "exp": EXP,
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "ts": time.time(),
                "stage": "claimed",
            }
            data["holders"] = live
            write_lock(data)
            log(f"claimed gpu {gid} concurrent={len(live)}")
            return gid
    finally:
        if lock_f is not None:
            try:
                import fcntl  # type: ignore

                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
                lock_f.close()
            except Exception:
                pass


def find_repo() -> Path:
    for cand in (
        Path(os.environ.get("E2E_REPO", "")),
        Path.home() / "Algoverse",
        Path.home() / "algoverse",
        Path.cwd(),
        Path(__file__).resolve().parent.parent,
    ):
        if cand and (cand / "scripts" / "battery_probe_aperp.py").exists():
            return cand
    raise FileNotFoundError("repo with battery_probe_aperp.py missing")


def run_remote() -> int:
    load_env_files()
    os.environ.setdefault("E2E_ROOT", str(_root()))
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    os.environ.setdefault("E2E_SPLIT", str(_root() / "emotic_split.json"))
    os.environ.setdefault("E2E_EMOTIC", str(_root() / "emotic_data"))
    os.environ.setdefault("E2E_EXP10", str(_root() / "battery" / EXP))
    os.environ.setdefault("E2E_OUT", str(_root() / "battery" / EXP / "results.json"))
    os.environ.setdefault("E2E_HB", str(_root() / "battery" / EXP / "heartbeat.json"))
    gid = claim_gpu()
    os.environ["CUDA_VISIBLE_DEVICES"] = gid
    repo = find_repo()
    os.environ.setdefault("E2E_REPO", str(repo))
    script = repo / "scripts" / "battery_exp10_run.py"
    alt = _root() / "battery" / EXP / "battery_exp10_run.py"
    path = script if script.is_file() else alt
    log(f"exec {path} gpu={gid}")
    ns = {"__name__": "__main__", "__file__": str(path)}
    sys.path.insert(0, str(path.parent))
    exec(path.read_text(encoding="utf-8"), ns)
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


def ssh_out(cli, cmd: str, timeout: int = 90) -> str:
    _, stdout, stderr = cli.exec_command(cmd, timeout=timeout)
    return (stdout.read() + stderr.read()).decode("utf-8", errors="replace").strip()


def sftp_put(cli, mapping: dict[Path, str]) -> None:
    sftp = cli.open_sftp()
    try:
        for local, remote in mapping.items():
            remote_path = Path(remote).as_posix()
            cli.exec_command(f"mkdir -p {Path(remote_path).parent.as_posix()}")
            time.sleep(0.15)
            sftp.put(str(local), remote_path)
            log(f"put {local.name}")
    finally:
        sftp.close()


def ssh_password() -> str:
    load_env_files()
    pw = os.environ.get("BATTERY_SSH_PASS") or os.environ.get("BATTERY_PASS") or os.environ.get("EXP10_HUB_PASSWORD")
    if not pw:
        raise RuntimeError("set BATTERY_SSH_PASS")
    return pw


def upload_and_launch(host: str, user: str, password: str) -> None:
    here = Path(__file__).resolve().parent
    repo = here.parent
    cli = ssh_connect(host, user, password)
    try:
        who = ssh_out(cli, "whoami; hostname; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv")
        log(who.replace("\n", " | ")[:500])
        remote_repo = ssh_out(
            cli,
            "if [ -d $HOME/Algoverse/scripts ]; then echo $HOME/Algoverse; "
            "elif [ -d $HOME/algoverse/scripts ]; then echo $HOME/algoverse; else echo MISSING; fi",
        ).splitlines()[-1].strip()
        if "MISSING" in remote_repo:
            raise RuntimeError("remote repo missing")
        ssh_out(
            cli,
            f"mkdir -p $HOME/algoverse_run/battery/exp10 {remote_repo}/scripts "
            f"{remote_repo}/artifacts/battery/exp10 {remote_repo}/data/battery {remote_repo}/tests",
        )
        puts = {
            here / "battery_probe_aperp.py": remote_repo + "/scripts/battery_probe_aperp.py",
            here / "battery_exp10_run.py": remote_repo + "/scripts/battery_exp10_run.py",
            here / "battery_exp10_boot.py": remote_repo + "/scripts/battery_exp10_boot.py",
            here / "affect_core.py": remote_repo + "/scripts/affect_core.py",
            here / "battery_adapter.py": remote_repo + "/scripts/battery_adapter.py",
        }
        lot = repo / "data" / "battery" / "exp01_lotteries.json"
        if lot.is_file():
            puts[lot] = remote_repo + "/data/battery/exp01_lotteries.json"
        spec = repo / "artifacts" / "battery" / "exp10" / "ADVISOR_SPEC.md"
        if spec.is_file():
            puts[spec] = remote_repo + "/artifacts/battery/exp10/ADVISOR_SPEC.md"
        sftp_put(cli, puts)
        ssh_out(
            cli,
            f"cp {remote_repo}/scripts/battery_probe_aperp.py $HOME/algoverse_run/battery/exp10/ && "
            f"cp {remote_repo}/scripts/battery_exp10_run.py $HOME/algoverse_run/battery/exp10/ && "
            f"cp {remote_repo}/scripts/affect_core.py $HOME/algoverse_run/battery/exp10/ && "
            f"cp {remote_repo}/scripts/battery_adapter.py $HOME/algoverse_run/battery/exp10/",
        )
        running = ssh_out(cli, "pgrep -af battery_exp10 || true")
        if "battery_exp10_run.py" in running or "battery_exp10_boot.py --run" in running:
            log("already running")
            return
        launch = (
            "set -a; [ -f $HOME/.battery_env ] && . $HOME/.battery_env; set +a; "
            "export E2E_MODEL=google/gemma-4-E4B-it E2E_NO_FALLBACK=1 "
            f"E2E_ROOT=$HOME/algoverse_run E2E_REPO={remote_repo} "
            "E2E_SPLIT=$HOME/algoverse_run/emotic_split.json "
            "E2E_EMOTIC=$HOME/algoverse_run/emotic_data "
            "E2E_EXP10=$HOME/algoverse_run/battery/exp10 "
            "E2E_OUT=$HOME/algoverse_run/battery/exp10/results.json "
            "E2E_HB=$HOME/algoverse_run/battery/exp10/heartbeat.json "
            "E2E_TIER=full PYTHONUNBUFFERED=1; "
            f"nohup python3 {remote_repo}/scripts/battery_exp10_boot.py --run "
            "> $HOME/algoverse_run/battery/exp10/nohup.out 2>&1 & echo PID $!"
        )
        out = ssh_out(cli, launch)
        log("launch " + out)
    finally:
        cli.close()


def pull_artifacts(host: str, user: str, password: str) -> dict | None:
    cli = ssh_connect(host, user, password)
    local = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / EXP
    local.mkdir(parents=True, exist_ok=True)
    try:
        home = ssh_out(cli, "echo $HOME").splitlines()[-1].strip()
        remote = home + "/algoverse_run/battery/exp10"
        sftp = cli.open_sftp()
        for name in (
            "heartbeat.json",
            "STATUS.md",
            "results.json",
            "run.log",
            "boot.log",
            "nohup.out",
            "checkpoint.json",
            "pairs_manifest.json",
        ):
            try:
                sftp.get(remote + "/" + name, str(local / name))
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
    if not res or not res.get("complete"):
        return False
    gates = res.get("gates") or {}
    if "passed" not in gates or "total" not in gates:
        return False
    if int(gates.get("total") or 0) < 4:
        return False
    if not res.get("mechanism_answer"):
        return False
    domains = res.get("domains") or {}
    if not domains:
        return False
    for rec in domains.values():
        stats = rec.get("stats") or {}
        if stats.get("n", 0) <= 0:
            return False
        if "pearson" not in stats and rec.get("finite_correlations") is None:
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
        hb = Path(__file__).resolve().parents[1] / "artifacts" / "battery" / EXP / "heartbeat.json"
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
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--host", default=os.environ.get("BATTERY_HOST", "35.89.128.116"))
    ap.add_argument("--user", default=os.environ.get("BATTERY_USER", "asca-ec66"))
    args = ap.parse_args()
    if args.run:
        return run_remote()
    password = ssh_password()
    if args.loop:
        return loop(args.host, args.user, password)
    if args.pull:
        pull_artifacts(args.host, args.user, password)
        return 0
    if args.upload:
        upload_and_launch(args.host, args.user, password)
        return 0
    return run_remote()


if __name__ == "__main__":
    raise SystemExit(main())
