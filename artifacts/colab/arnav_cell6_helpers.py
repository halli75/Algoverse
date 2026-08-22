def get_out_of_bbox_indices(in_bbox_indices, vision_start=5, n_vision_tokens=256):
    all_idx = set(range(vision_start, vision_start + n_vision_tokens))
    return sorted(all_idx - set(in_bbox_indices))

def load_row_image(row):
    path = f"/content/emotic_data/emotic/{row['Folder']}/{row['Filename']}"
    return Image.open(path).convert("RGB")

def cache_layer_activation(model, prompt, image, hook_name):
    inputs = model.prepare_multimodal_inputs(text=prompt, images=image)
    extra = {k: v for k, v in inputs.items() if k not in ("input_ids", "pixel_values")}
    with torch.no_grad():
        _, cache = model.run_with_cache(
            inputs["input_ids"], pixel_values=inputs["pixel_values"],
            names_filter=lambda n: n == hook_name, **extra,
        )
    return cache[hook_name]

def run_patched(model, target_inputs, target_extra, hook_name, source_activation, patch_indices):
    def patch_hook(activation, hook):
        activation[:, patch_indices, :] = source_activation[:, patch_indices, :]
        return activation
    with torch.no_grad():
        return model.run_with_hooks(
            target_inputs["input_ids"], pixel_values=target_inputs["pixel_values"],
            fwd_hooks=[(hook_name, patch_hook)], **target_extra,
        )


EMOTION_WORDS = ["happy", "sad", "afraid", "angry", "confused", "peaceful", "excited", "disconnected"]

def emotion_word_scores(model, logits):
    last = logits[0, -1]
    scores = {}
    for word in EMOTION_WORDS:
        ids = model.tokenizer.encode(" " + word, add_special_tokens=False)
        scores[word] = last[ids[0]].item() if len(ids) == 1 else None
    return scores

PROMPT = (
    "<start_of_turn>user\n"
    "<start_of_image>In one word, this person feels:<end_of_turn>\n"
    "<start_of_turn>model\n"
)

def region_swap_experiment(model, source_row, target_row, layer=10):
    hook_name = f"blocks.{layer}.hook_resid_post"

    source_img = load_row_image(source_row)
    target_img = load_row_image(target_row)

    source_act = cache_layer_activation(model, PROMPT, source_img, hook_name)

    target_inputs = model.prepare_multimodal_inputs(text=PROMPT, images=target_img)
    target_extra = {k: v for k, v in target_inputs.items() if k not in ("input_ids", "pixel_values")}

    with torch.no_grad():
        baseline_logits = model(target_inputs["input_ids"], pixel_values=target_inputs["pixel_values"], **target_extra)

    w, h = target_row["Image Size"][0], target_row["Image Size"][1]
    in_bbox_idx = bbox_to_vision_token_indices(target_row["BBox"], w, h)
    out_bbox_idx = get_out_of_bbox_indices(in_bbox_idx)

    person_logits = run_patched(model, target_inputs, target_extra, hook_name, source_act, in_bbox_idx)
    bg_logits = run_patched(model, target_inputs, target_extra, hook_name, source_act, out_bbox_idx)

    print(f"Source label: {source_row['Categorical_Labels']}")
    print(f"Target label (ground truth): {target_row['Categorical_Labels']}")
    print(f"Patching {len(in_bbox_idx)} person-region tokens vs {len(out_bbox_idx)} background tokens\n")

    baseline_scores = emotion_word_scores(model, baseline_logits)
    person_scores = emotion_word_scores(model, person_logits)
    bg_scores = emotion_word_scores(model, bg_logits)

    print(f"{'word':<14}{'baseline':>10}{'person-patched':>16}{'bg-patched':>12}")
    for w_ in EMOTION_WORDS:
        b, p, g = baseline_scores[w_], person_scores[w_], bg_scores[w_]
        if b is None:
            continue
        print(f"{w_:<14}{b:>10.2f}{p:>16.2f}{g:>12.2f}")

    return baseline_logits, person_logits, bg_logits