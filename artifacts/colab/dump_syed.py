import json
import re
from pathlib import Path

nb = json.loads(Path(r"C:\Users\arnav\Projects\algoverse\artifacts\colab\syed.ipynb").read_text(encoding="utf-8"))
out = Path(r"C:\Users\arnav\Projects\algoverse\artifacts\colab\syed_caption_hits.md")
hits = []
keys = re.compile(r"caption|parquet|to_parquet|plain|rich|DESCRIBE|results/stage_c", re.I)
for i, c in enumerate(nb["cells"]):
    src = c.get("source", [])
    if isinstance(src, list):
        src = "".join(src)
    if keys.search(src or ""):
        hits.append(f"\n\n===== CELL {i} ({c['cell_type']}) =====\n{src}")
out.write_text(f"hit_cells={len(hits)}\n" + "".join(hits), encoding="utf-8")
print("wrote", out, "hits", len(hits), "total_cells", len(nb["cells"]))

# also search outputs for parquet paths
out_paths = []
for i, c in enumerate(nb["cells"]):
    for o in c.get("outputs", []) or []:
        text = ""
        if o.get("text"):
            text = "".join(o["text"]) if isinstance(o["text"], list) else o["text"]
        elif o.get("data", {}).get("text/plain"):
            tp = o["data"]["text/plain"]
            text = "".join(tp) if isinstance(tp, list) else tp
        if "caption" in text.lower() or "parquet" in text.lower():
            out_paths.append(f"cell{i}: {text[:500]}")
print("output hits", len(out_paths))
Path(r"C:\Users\arnav\Projects\algoverse\artifacts\colab\syed_output_hits.txt").write_text("\n---\n".join(out_paths), encoding="utf-8")
