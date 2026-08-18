import json
import pathlib

p = pathlib.Path(r"C:\Users\arnav\Projects\algoverse\scripts\e2e_colab_pipeline.py")
t = p.read_text(encoding="utf-8")
assert "local, no HF dataset" in t
assert "tatsu-lab/alpaca" not in t
if "socket.setdefaulttimeout" not in t:
    t = t.replace(
        'log("PHASE_B_DATA")',
        'import socket\nsocket.setdefaulttimeout(30)\nlog("PHASE_B_DATA")',
    )
    p.write_text(t, encoding="utf-8")
    print("added timeout")
else:
    print("timeout ok")

content = p.read_text(encoding="utf-8")
payload = {
    "files": {"e2e_colab_pipeline.py": {"content": content}},
    "description": "algoverse e2e no-alpaca + timeout",
}
path = pathlib.Path(r"C:\Users\arnav\Projects\algoverse\scripts\_gist_patch.json")
path.write_text(json.dumps(payload), encoding="utf-8")
print("payload", len(content))
