# T4 smoke. Pinned gist revision -- do not use unpinned /raw/file.
import json
import os
import urllib.request
from pathlib import Path
from google.colab import userdata

def _sec(k, default=""):
    try:
        v = userdata.get(k)
        return v if v else default
    except Exception:
        return os.environ.get(k, default)

env = {
    "HF_TOKEN": _sec("HF_TOKEN"),
    "XAI_API_KEY": _sec("XAI_API_KEY"),
    "E2E_TIER": "smoke",
    "E2E_MODEL": "google/gemma-4-E4B-it",
    "E2E_NO_FALLBACK": "1",
    "E2E_PREREG_HASH": "051e1ea79cd116fce56edeb43848ae10526e2830efc49ab0df2cd7d904a20876",
    "E2E_GIST_SHA": "0a19bbfb0205b6ef2f4e23499a262f7d5dc30e2d",
    "XAI_JUDGE_MODEL": "grok-4.6",
    "XAI_REASONING_EFFORT": "high",
}
for k, v in env.items():
    if v:
        os.environ[k] = v
Path("/content/_env.json").write_text(json.dumps({k: v for k, v in env.items() if v}))
print("env ready", {k: bool(v) for k, v in env.items()})
SHA = os.environ["E2E_GIST_SHA"]
url = f"https://gist.githubusercontent.com/halli75/d888da53224aac15e38a1f0d30f75805/raw/{SHA}/_restore_sycophancy_boot.py"
urllib.request.urlretrieve(url, "/content/_restore_sycophancy_boot.py")
print("boot", url)
exec(open("/content/_restore_sycophancy_boot.py", encoding="utf-8").read().split("if __name__")[0] + "\nraise SystemExit(main())")
