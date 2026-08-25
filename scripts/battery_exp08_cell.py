# Jupyter cell / nohup entry for exp08. Starts its own process.
# Do not attach to the overseer kernel.
# [[battery-exp08]]

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    subprocess.run(["nvidia-smi"], check=False)
    root = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    run = root / "battery" / "exp08"
    run.mkdir(parents=True, exist_ok=True)
    os.environ["E2E_ROOT"] = str(root)
    os.environ.setdefault("E2E_TIER", "smoke")
    os.environ.setdefault("E2E_MODEL", "google/gemma-4-E4B-it")
    os.environ.setdefault("E2E_NO_FALLBACK", "1")
    envp = Path.home() / ".battery_env"
    if envp.is_file():
        for raw in envp.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if not os.environ.get("HF_TOKEN"):
        for cand in (Path.home() / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
            if cand.is_file():
                tok = cand.read_text(encoding="utf-8").strip()
                if tok:
                    os.environ["HF_TOKEN"] = tok
                    break
    boot = None
    for cand in (
        Path(__file__).resolve().parent / "battery_exp08_boot.py" if "__file__" in globals() else None,
        Path.cwd() / "scripts" / "battery_exp08_boot.py",
        Path.home() / "Algoverse" / "scripts" / "battery_exp08_boot.py",
        run / "battery_exp08_boot.py",
    ):
        if cand is not None and cand.exists():
            boot = cand
            break
    if boot is None:
        raise FileNotFoundError("battery_exp08_boot.py")
    log = run / "nohup.out"
    cmd = [sys.executable, str(boot)]
    print("spawn", cmd, "log", log, flush=True)
    with log.open("a", encoding="utf-8") as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    (run / "pid").write_text(str(proc.pid), encoding="utf-8")
    print("pid", proc.pid, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
