#auth
from google.colab import userdata
import os
os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")

#install
!pip install -q "git+https://github.com/TransformerLensOrg/TransformerLens.git"
!pip install -q circuitsvis gdown

import torch
from transformer_lens.model_bridge import TransformerBridge
from io import BytesIO
import requests
from PIL import Image

print(torch.__version__, torch.cuda.is_available())

#gemma 3
mm_model = TransformerBridge.boot_transformers(
    "google/gemma-3-4b-it",
    device="cuda",
    dtype=torch.bfloat16,
)
for p in mm_model.parameters():
    p.requires_grad = False

print(f"Multimodal: {getattr(mm_model.cfg, 'is_multimodal', False)}")
print(f"Vision tokens per image: {getattr(mm_model.cfg, 'mm_tokens_per_image', None)}")

def get_vision_token_range(input_ids, image_placeholder_id=262144):
    positions = (input_ids[0] == image_placeholder_id).nonzero().flatten()
    start, end = positions[0].item(), positions[-1].item() + 1
    assert end - start == 256, f"expected 256 vision tokens, got {end - start}"
    return start, end

#emotic
!gdown "https://drive.google.com/uc?id=1icMKzWIlmFKhTkb4OrH8QAHHaaGOP9Zo" -O emotic_images.zip --fuzzy
!ls -lh emotic_images.zip
!unzip -qo emotic_images.zip -d emotic_images

#annotations (drag Annotations.zip into the Colab Files panel -> /content/Annotations.zip)
assert os.path.exists("/content/Annotations.zip"), "Upload Annotations.zip to /content first (drag into the Files panel)"
!unzip -qo /content/Annotations.zip -d annotations
!find annotations -name "*.mat"

#mat2py preprocessing
!git clone -q https://github.com/Tandon-A/emotic.git emotic_repo

path = "emotic_repo/mat2py.py"
with open(path) as f:
    content = f.read()
old = """      cv2.imwrite(os.path.join(save_dir, 'context1.png'), context_arr[-1])
      cv2.imwrite(os.path.join(save_dir, 'body1.png'), body_arr[-1])"""
new = """      if generate_npy:
        cv2.imwrite(os.path.join(save_dir, 'context1.png'), context_arr[-1])
        cv2.imwrite(os.path.join(save_dir, 'body1.png'), body_arr[-1])"""
if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("patched mat2py.py")
else:
    print("pattern not found - already patched or script differs, check before proceeding")

!mkdir -p emotic_data
!ln -sf /content/emotic_images/emotic /content/emotic_data/emotic
!ln -sf /content/annotations/Annotations /content/emotic_data/Annotations
!ls -la emotic_data

!cd emotic_repo && python mat2py.py --data_dir /content/emotic_data --label all

#load and parse csv
import pandas as pd
import ast

train_df = pd.read_csv("/content/emotic_data/emotic_pre/train.csv")
train_df["BBox"] = train_df["BBox"].apply(ast.literal_eval)
train_df["Categorical_Labels"] = train_df["Categorical_Labels"].apply(ast.literal_eval)
train_df["Image Size"] = train_df["Image Size"].apply(ast.literal_eval)
print(train_df.shape)
print(train_df.iloc[0])

# axis-order
import matplotlib.pyplot as plt
import matplotlib.patches as patches

non_square = train_df[train_df["Image Size"].apply(lambda s: s[0] != s[1])]
row = non_square.iloc[0]
print(row["Folder"], row["Filename"], "size:", row["Image Size"], "bbox:", row["BBox"])

img_path = f"/content/emotic_data/emotic/{row['Folder']}/{row['Filename']}"
img = Image.open(img_path).convert("RGB")
print("actual PIL size (width, height):", img.size)

x1, y1, x2, y2 = row["BBox"]
fig, ax = plt.subplots()
ax.imshow(img)
ax.add_patch(patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor="red", facecolor="none"))
plt.title(f"{row['Categorical_Labels']}")
plt.show()