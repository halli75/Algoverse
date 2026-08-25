# exp04 remote boot. Source ~/.battery_env on A100. Never print secrets.
# [[sycophancy-affect-experiment]]
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

EXP = "exp04"
GPU = "3"
STALE_S = 20 * 60
LOOP_S = 15 * 60


def _here() -> Path:
    return Path(__file__).resolve().parent


def _repo() -> Path:
    return _here().parent


def log(msg: str) -> None:
    s = f"{time.strftime('%H:%M:%S')} {msg}"
    print(s, flush=True)
    dest = _repo() / "artifacts" / "battery" / EXP
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "boot.log").open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def load_local_env() -> list[str]:
    sys.path.insert(0, str(_here()))
    from battery_adapter import load_env_file

    keys = load_env_file(_repo() / ".env")
    keys += load_env_file(_repo() / ".env.hub")
    for alt in (
        "BATTERY_SSH_PASS",
        "BATTERY_PASS",
        "JUPYTERHUB_PASSWORD",
        "EXP05_HUB_PASSWORD",
        "EXP01_HUB_PASSWORD",
        "EXP04_HUB_PASSWORD",
    ):
        if os.environ.get(alt) and not os.environ.get("BATTERY_SSH_PASS"):
            os.environ["BATTERY_SSH_PASS"] = os.environ[alt]
            break
    for alt in ("JUPYTERHUB_USER", "EXP05_HUB_USER", "BATTERY_USER"):
        if os.environ.get(alt) and not os.environ.get("BATTERY_USER"):
            os.environ["BATTERY_USER"] = os.environ[alt]
    return keys


def _paramiko():
    try:
        import paramiko  # type: ignore
    except ImportError:
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "paramiko"])
        import paramiko  # type: ignore
    return paramiko


def ssh_connect(host: str, user: str, password: str):
    paramiko = _paramiko()
    last = None
    users = [user]
    if user and not user.startswith("jupyter-"):
        users.append("jupyter-" + user)
    for u in users:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            cli.connect(host, username=u, password=password, timeout=30, allow_agent=False, look_for_keys=False)
            log(f"ssh_ok user={u}")
            return cli
        except Exception as e:
            last = e
            try:
                cli.close()
            except Exception:
                pass
    raise RuntimeError(f"ssh failed for users={users}: {type(last).__name__}")


def ssh_out(cli, cmd: str, timeout: int = 90) -> str:
    _, stdout, stderr = cli.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return (out + err).strip()


def sftp_put(cli, mapping: dict[Path, str]) -> None:
    sftp = cli.open_sftp()
    try:
        for local, remote in mapping.items():
            parent = str(Path(remote).parent).replace("\\", "/")
            ssh_out(cli, f"mkdir -p {parent}")
            sftp.put(str(local), remote)
            log(f"put {local.name}")
    finally:
        sftp.close()


def creds() -> tuple[str, str, str]:
    host = os.environ.get("BATTERY_HOST") or os.environ.get("JUPYTERHUB_HOST") or "35.89.128.116"
    user = os.environ.get("BATTERY_USER") or os.environ.get("JUPYTERHUB_USER") or "asca-ec66"
    password = os.environ.get("BATTERY_SSH_PASS") or os.environ.get("BATTERY_PASS") or os.environ.get("JUPYTERHUB_PASSWORD") or ""
    if not password:
        raise RuntimeError("SSH password env unset after sourcing .env")
    return host, user, password


def upload_and_launch() -> None:
    host, user, password = creds()
    cli = ssh_connect(host, user, password)
    try:
        who = ssh_out(cli, "whoami; hostname; nvidia-smi -L | wc -l")
        log(who.replace("\n", " | "))
        remote_repo = ssh_out(
            cli,
            "if [ -d $HOME/Algoverse/scripts ]; then echo $HOME/Algoverse; "
            "elif [ -d $HOME/algoverse/scripts ]; then echo $HOME/algoverse; "
            "else echo MISSING; fi",
        ).splitlines()[-1].strip()
        if "MISSING" in remote_repo:
            raise RuntimeError("remote repo missing")
        run = "$HOME/algoverse_run/battery/exp04"
        ssh_out(cli, f"mkdir -p {run} {remote_repo}/scripts {remote_repo}/artifacts/battery/exp04 $HOME/algoverse_run/battery")
        here = _here()
        puts = {
            here / "battery_exp04.py": remote_repo + "/scripts/battery_exp04.py",
            here / "battery_exp04_boot.py": remote_repo + "/scripts/battery_exp04_boot.py",
            here / "battery_exp04_cell.py": remote_repo + "/scripts/battery_exp04_cell.py",
            here / "battery_adapter.py": remote_repo + "/scripts/battery_adapter.py",
        }
        spec = _repo() / "artifacts" / "battery" / "exp04" / "ADVISOR_SPEC.md"
        if spec.is_file():
            puts[spec] = remote_repo + "/artifacts/battery/exp04/ADVISOR_SPEC.md"
        sftp_put(cli, puts)
        ssh_out(
            cli,
            f"cp {remote_repo}/scripts/battery_exp04.py {run}/ && "
            f"cp {remote_repo}/scripts/battery_adapter.py {run}/ && "
            f"cp {remote_repo}/scripts/battery_exp04_boot.py {run}/",
        )
        running = ssh_out(cli, "pgrep -af battery_exp04 || true")
        if "battery_exp04.py" in running or "battery_exp04_boot.py --run" in running:
            log("already running")
            return
        launch = (
            "bash -lc '"
            "source $HOME/.battery_env >/dev/null 2>&1 || true; "
            "export CUDA_VISIBLE_DEVICES=3 "
            "E2E_MODEL=google/gemma-4-E4B-it E2E_NO_FALLBACK=1 "
            "E2E_ROOT=$HOME/algoverse_run E2E_REPO=" + remote_repo + " "
            "E2E_SPLIT=$HOME/algoverse_run/emotic_split.json "
            "E2E_EMOTIC=$HOME/algoverse_run/emotic_data "
            "EXP04_ROOT=$HOME/algoverse_run/battery/exp04 "
            "EXP04_OUT=$HOME/algoverse_run/battery/exp04/results.json "
            "EXP04_HB=$HOME/algoverse_run/battery/exp04/heartbeat.json "
            "EXP04_CKPT=$HOME/algoverse_run/battery/exp04/checkpoint.jsonl "
            "EXP04_GPU=3 PYTHONUNBUFFERED=1; "
            "nohup python3 -u " + remote_repo + "/scripts/battery_exp04_boot.py --run "
            "> $HOME/algoverse_run/battery/exp04/nohup.out 2>&1 & echo PID $!"
            "'"
        )
        out = ssh_out(cli, launch)
        log("launch " + out)
    finally:
        cli.close()


def pull_artifacts() -> dict | None:
    host, user, password = creds()
    cli = ssh_connect(host, user, password)
    local = _repo() / "artifacts" / "battery" / EXP
    local.mkdir(parents=True, exist_ok=True)
    try:
        home = ssh_out(cli, "echo $HOME").splitlines()[-1].strip()
        remote = home + "/algoverse_run/battery/exp04"
        sftp = cli.open_sftp()
        for name in ("heartbeat.json", "STATUS.md", "results.json", "run.log", "nohup.out", "checkpoint.jsonl"):
            try:
                sftp.get(remote + "/" + name, str(local / name))
                log("got " + name)
            except Exception:
                pass
        sftp.close()
        probe = ssh_out(
            cli,
            "pgrep -af battery_exp04 || true; "
            "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | sed -n '4p'; "
            "test -f $HOME/algoverse_run/battery/exp04/heartbeat.json && echo HB_OK || echo HB_MISS",
        )
        log("probe " + probe.replace("\n", " | ")[:400])
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
    if int(gates.get("total") or 0) != 6:
        return False
    est = (res.get("estimates") or {}).get("headline_neg3_minus_neutral") or {}
    return isinstance(est.get("delta"), (int, float)) and all(isinstance(x, (int, float)) for x in (est.get("ci95") or []))


def run_remote() -> int:
    os.environ["CUDA_VISIBLE_DEVICES"] = GPU
    os.environ.setdefault("E2E_ROOT", str(Path.home() / "algoverse_run"))
    os.environ.setdefault("EXP04_GPU", GPU)
    sys.path.insert(0, str(_here()))
    from battery_adapter import plant_hf_token, source_battery_env

    keys = source_battery_env()
    log("remote sourced_keys=" + ",".join(keys) if keys else "remote sourced_keys=none")
    plant_hf_token()
    ns = {"__name__": "__main__", "__file__": str(_here() / "battery_exp04.py")}
    exec((_here() / "battery_exp04.py").read_text(encoding="utf-8"), ns)
    return 0


def loop() -> int:
    upload_and_launch()
    t0 = time.time()
    while True:
        res = pull_artifacts()
        if results_valid(res):
            log("results.json valid")
            return 0
        hb = _repo() / "artifacts" / "battery" / EXP / "heartbeat.json"
        age = None
        if hb.is_file():
            try:
                rec = json.loads(hb.read_text(encoding="utf-8"))
                age = time.time() - float(rec.get("unix") or 0)
                log(f"hb stage={rec.get('stage')} age={age:.0f}s elapsed={time.time()-t0:.0f}")
            except Exception:
                log(f"hb unreadable elapsed={time.time()-t0:.0f}")
        else:
            log(f"no local hb elapsed={time.time()-t0:.0f}")
        if age is not None and age > STALE_S:
            log("stale heartbeat; relaunch")
            upload_and_launch()
        time.sleep(LOOP_S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--loop", action="store_true")
    args = ap.parse_args()
    if args.run:
        return run_remote()
    keys = load_local_env()
    log("local_env_keys=" + ",".join(keys))
    if args.status:
        pull_artifacts()
        return 0
    if args.loop:
        return loop()
    upload_and_launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
