# Create pod, scp payload, boot, poll, pull results, always terminate.
# Never print API keys. Pin: NVIDIA RTX PRO 6000 Blackwell Server Edition only.
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
import battery_v2_runpod as rp

ROOT = Path(__file__).resolve().parents[1]
KEY = Path.home() / ".ssh" / "motion_mirror_runpod_ed25519"
PAYLOAD = ROOT / "artifacts" / "battery_v2" / "payload.tgz"
LOCAL_V2 = ROOT / "artifacts" / "battery_v2"
DEADLINE_S = float(os.environ.get("E2E_MAX_HOURS", "2.75")) * 3600
TICK = "AGENT_LOOP_TICK_battery_v2"


def log(m: str) -> None:
    print(f"[orch {time.strftime('%H:%M:%S')}] {m}", flush=True)


def ssh_base(direct: dict) -> list[str]:
    return [
        "ssh",
        "-i",
        str(KEY),
        "-p",
        str(direct["port"]),
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=20",
        f"{direct['username']}@{direct['host']}",
    ]


def scp_base(direct: dict) -> list[str]:
    return [
        "scp",
        "-i",
        str(KEY),
        "-P",
        str(direct["port"]),
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]


def wait_ssh(pod_id: str, timeout: int = 600) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        pod = rp.get_pod(pod_id)
        st = pod.get("status")
        direct = ((pod.get("ssh") or {}).get("direct")) or {}
        log(f"status={st} ssh_direct={bool(direct)}")
        if st == "RUNNING" and direct.get("host") and direct.get("port"):
            return direct
        if st in ("EXITED", "ERROR", "TERMINATED"):
            raise SystemExit(f"pod {st} before SSH")
        time.sleep(15)
    raise SystemExit("timeout waiting for SSH")


def remote(direct: dict, cmd: str, check: bool = True) -> str:
    r = subprocess.run(
        ssh_base(direct) + [cmd],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (r.stdout or "") + (r.stderr or "")
    if check and r.returncode != 0:
        raise SystemExit(f"ssh fail {r.returncode}: {out[-2000:]}")
    return out


def pull_results(direct: dict) -> Path:
    dest = LOCAL_V2 / "from_pod"
    if dest.exists():
        import shutil

        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        scp_base(direct)
        + [
            "-r",
            f"{direct['username']}@{direct['host']}:/workspace/Algoverse/artifacts/battery_v2/.",
            str(dest),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise SystemExit(f"scp pull failed: {(r.stderr or r.stdout)[-1500:]}")
    stamp = dest / "pulled_at.json"
    stamp.write_text(json.dumps({"unix": time.time()}, indent=2), encoding="utf-8")
    return dest


EXPECTED_EMOTIC = []
for _mk in ("e4b", "g12"):
    for _exp in ("exp09", "exp05", "exp06", "exp10", "exp03", "mech"):
        EXPECTED_EMOTIC.append(f"{_mk}/emotic/{_exp}/results.json")
        EXPECTED_EMOTIC.append(f"{_mk}/emotic/{_exp}/LOCK.json")


def verify_local(root: Path) -> dict:
    missing = [p for p in EXPECTED_EMOTIC if not (root / p).is_file()]
    dry, complete, bad_lock = [], [], []
    for rel in EXPECTED_EMOTIC:
        p = root / rel
        if not p.is_file():
            continue
        blob = json.loads(p.read_text(encoding="utf-8"))
        if rel.endswith("results.json"):
            if blob.get("dry_run") or blob.get("primary_dv") == "dry":
                dry.append(rel)
            if blob.get("complete"):
                complete.append(rel)
        if rel.endswith("LOCK.json"):
            if blob.get("scorer") == "dry" or blob.get("primary_dv") == "dry":
                bad_lock.append(rel)
    report = {
        "n_expected": len(EXPECTED_EMOTIC),
        "missing": missing,
        "complete_results": complete,
        "dry": dry,
        "bad_lock": bad_lock,
        "ok": (not missing) and (not dry) and (not bad_lock) and len(complete) == len(EXPECTED_EMOTIC) // 2,
    }
    (LOCAL_V2 / "VERIFY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    if not KEY.is_file():
        raise SystemExit(f"missing SSH key {KEY}")
    subprocess.check_call([sys.executable, str(_SCRIPTS / "battery_v2_pack.py")])
    t0 = time.time()
    pod_id = None
    try:
        g = rp.pick_gpu()
        if g.get("id") != "NVIDIA RTX PRO 6000 Blackwell Server Edition":
            raise SystemExit(f"refusing gpu {g.get('id')}")
        log(f"create {g.get('id')} ${g.get('price', {}).get('secure')}/h")
        rec = rp.create_pod(str(g["id"]))
        pod_id = rec.get("id")
        if not pod_id:
            raise SystemExit(f"create returned no id: {rec}")
        log(f"pod {pod_id}")
        direct = wait_ssh(pod_id)
        log("upload payload")
        subprocess.check_call(
            scp_base(direct) + [str(PAYLOAD), f"{direct['username']}@{direct['host']}:/workspace/payload.tgz"]
        )
        remote(direct, "mkdir -p /workspace && tar xzf /workspace/payload.tgz -C /workspace")
        remote(direct, "mkdir -p /workspace/Algoverse/artifacts/battery_v2")
        boot = (
            "cd /workspace/Algoverse && nohup python -u scripts/battery_v2_boot.py "
            "> artifacts/battery_v2/boot.log 2>&1 & echo $!"
        )
        log("start boot")
        print(remote(direct, boot), flush=True)
        n = 0
        while True:
            n += 1
            elapsed = time.time() - t0
            print(f"{TICK} n={n} elapsed_s={elapsed:.0f} id={pod_id}", flush=True)
            hb = remote(
                direct,
                "cat /workspace/Algoverse/artifacts/battery_v2/heartbeat.json 2>/dev/null || echo {}",
                check=False,
            )
            print("heartbeat", hb[:800], flush=True)
            st = remote(
                direct,
                "cat /workspace/Algoverse/artifacts/battery_v2/STATUS.json 2>/dev/null || echo {}",
                check=False,
            )
            print("status", st[:1200], flush=True)
            done = '"campaign complete"' in remote(
                direct, "tail -n 5 /workspace/Algoverse/artifacts/battery_v2/boot.log 2>/dev/null || true", check=False
            )
            alive = remote(direct, "pgrep -af battery_v2_run.py || true", check=False)
            if done or ("battery_v2_run.py" not in alive and n > 2 and elapsed > 600):
                log("boot finished or runner gone")
                break
            remain = DEADLINE_S - (time.time() - t0)
            if remain <= 90:
                log("deadline; stop runner")
                remote(direct, "pkill -f battery_v2_run.py || true", check=False)
                break
            time.sleep(min(900, max(30, remain - 60)))
        dest = pull_results(direct)
        rep = verify_local(dest)
        log(f"verify {rep}")
        return 0 if rep.get("ok") else 1
    finally:
        if pod_id:
            log(f"terminate {pod_id}")
            for action in ("terminate", "stop"):
                try:
                    if action == "terminate":
                        rp.terminate_pod(pod_id)
                    else:
                        rp.stop_pod(pod_id)
                        rp.terminate_pod(pod_id)
                    break
                except BaseException as e:
                    log(f"{action} err {type(e).__name__}: {e}")
            for _ in range(20):
                try:
                    pod = rp.get_pod(pod_id)
                    st = pod.get("status")
                    log(f"final status={st} cost={pod.get('cost')}")
                    if st in ("TERMINATED", "EXITED") or st is None:
                        break
                except BaseException:
                    log("final status unavailable (likely terminated)")
                    break
                time.sleep(6)


if __name__ == "__main__":
    raise SystemExit(main())
