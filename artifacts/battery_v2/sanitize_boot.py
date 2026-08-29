from pathlib import Path
p = Path("/workspace/Algoverse/artifacts/battery_v2/boot.log")
t = p.read_bytes().decode("utf-8", "replace")
p.write_text("".join(ch if ord(ch) < 128 else "?" for ch in t), encoding="ascii", errors="replace")
print("sanitized", len(t))
