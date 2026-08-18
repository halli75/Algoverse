import base64
import json
from pathlib import Path

raw = Path(__file__).resolve().parents[1] / "data" / "emotic_split.json"
b64 = base64.b64encode(raw.read_bytes()).decode("ascii")
outdir = Path(__file__).resolve().parent / "_split_chunks"
outdir.mkdir(exist_ok=True)
for p in outdir.glob("c*.txt"):
    p.unlink()
chunk = 120000
n = 0
for i in range(0, len(b64), chunk):
    (outdir / f"c{n:02d}.txt").write_text(b64[i : i + chunk], encoding="ascii")
    n += 1
meta = {"n": n, "total": len(b64)}
(Path(__file__).resolve().parent / "_split_chunks_meta.json").write_text(json.dumps(meta))
print(meta)