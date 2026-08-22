import json
from pathlib import Path

nb_path = Path(r"C:\Users\arnav\Projects\algoverse\artifacts\colab\charlotte.ipynb")
out_path = Path(r"C:\Users\arnav\Projects\algoverse\artifacts\colab\charlotte_cells.md")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
parts = [f"cells={len(nb['cells'])}\n"]
for i, c in enumerate(nb["cells"]):
    src = c.get("source", [])
    if isinstance(src, list):
        src = "".join(src)
    parts.append(f"\n\n===== CELL {i} ({c['cell_type']}) =====\n")
    parts.append(src or "")
out_path.write_text("".join(parts), encoding="utf-8")
print("wrote", out_path, "bytes", out_path.stat().st_size)
