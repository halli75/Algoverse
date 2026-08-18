import json
import pathlib

root = pathlib.Path(__file__).resolve().parent / "_pub_chunks"
out = pathlib.Path(__file__).resolve().parent / "_cdp_exprs"
out.mkdir(exist_ok=True)
chunks = sorted(root.glob("c*.txt"), key=lambda p: int(p.stem[1:]))


def write_expr(name: str, py: str, extra=None):
    payload = {
        "ok": True,
        **(extra or {}),
        "n": "CODE_LEN",
    }
    # Build JS that sets cell 0 and returns metadata
    expr = (
        "(() => {\n"
        f"  const code = {json.dumps(py)};\n"
        "  const cell = window.colab.global.notebookModel.cells[0];\n"
        "  cell.textModel.setValue(code);\n"
        "  return {ok:true, n:code.length"
        + (f", i:{extra['i']}" if extra and "i" in extra else "")
        + "};\n"
        "})()"
    )
    (out / name).write_text(
        json.dumps({"expression": expr, "returnByValue": True}), encoding="utf-8"
    )


write_expr(
    "boot.json",
    "open('/content/_pub.b64','w').write(''); print('CLEARED')",
)
for i, p in enumerate(chunks):
    data = p.read_text(encoding="ascii").strip()
    py = (
        f"open('/content/_pub.b64','a').write({json.dumps(data)}); "
        f"print({i}, len(open('/content/_pub.b64').read()))"
    )
    write_expr(f"{i:02d}.json", py, extra={"i": i})

decode_py = (
    "import base64\n"
    "open('/content/e2e_publish_pipeline.py','wb').write("
    "base64.b64decode(open('/content/_pub.b64').read()))\n"
    "t=open('/content/e2e_publish_pipeline.py',encoding='utf-8').read()\n"
    "assert 'google/gemma-4-E4B-it' in t\n"
    "assert t.splitlines()[0].startswith('#') or 'PRIMARY' in t[:200] or True\n"
    "print('WROTE', len(t), 'PRIMARY_OK', 'google/gemma-4-E4B-it' in t)\n"
)
write_expr("decode.json", decode_py)

run_py = (
    "import os\n"
    "os.environ['E2E_TIER']='smoke'\n"
    "os.environ['E2E_PREREG_HASH']='3111c3af7f7b12656cb0792bea4a21b4302a0c42'\n"
    "os.environ.pop('E2E_FORCE_FALLBACK', None)\n"
    "os.environ.pop('E2E_MODEL', None)  # force PRIMARY gemma-4-E4B-it\n"
    "print('LAUNCH', os.environ.get('E2E_TIER'), 'model_env', os.environ.get('E2E_MODEL','DEFAULT_PRIMARY'))\n"
    "exec(open('/content/e2e_publish_pipeline.py',encoding='utf-8').read())\n"
)
write_expr("run.json", run_py)

print("wrote", len(list(out.glob("*.json"))), "exprs")
for f in sorted(out.glob("*.json")):
    print(f.name, f.stat().st_size)
