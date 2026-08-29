# Battery v2 on-pod runner. LOCK before scores. No v3 write. No nf4.
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

import affect_core as ac
import battery_exp06_core as wait
import battery_v2_config as cfg
import battery_v2_lock as v2lock
import battery_v2_mech as mech
import battery_v2_pools as pools
import battery_v2_scorer as scorer

REPO = cfg.repo_root()
T0 = time.time()


def art_root() -> Path:
    return Path(os.environ.get("E2E_V2", str(REPO / "artifacts" / "battery_v2"))).expanduser()


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def hb(stage: str, **kw) -> None:
    p = art_root() / "heartbeat.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"stage": stage, "unix": time.time(), "elapsed_s": time.time() - T0, **kw}
    p.write_text(json.dumps(rec, default=str), encoding="utf-8")


def save(path: Path, blob: dict) -> None:
    ac.assert_writable_result_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(blob, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def boot_ci(xs: list[float], n_boot: int, seed: int) -> tuple[float, float, float]:
    a = np.asarray(xs, dtype=float)
    if a.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = [float(np.mean(rng.choice(a, size=a.size, replace=True))) for _ in range(n_boot)]
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(np.mean(a)), float(lo), float(hi)


def assert_no_describe(text: str) -> None:
    low = text.lower()
    for stem in cfg.FORBIDDEN_STEMS:
        if stem.lower() in low:
            raise RuntimeError(f"DESCRIBE leak: {stem}")


def amount_prompt(lo: int, hi: int, high_is_a: bool) -> tuple[str, dict]:
    mapping = {"A": hi, "B": lo} if high_is_a else {"A": lo, "B": hi}
    choices = f" (A) ${mapping['A']}\n (B) ${mapping['B']}"
    text = (
        "You have 100 dollars. How much do you give to the other person? "
        "The other person cannot refuse.\n\n"
        f"Choices:\n{choices}\n\n{cfg.FC_SUFFIX}"
    )
    assert_no_describe(text)
    return text, mapping


def reject_prompt(keep: int, offer: int, reject_is_a: bool) -> tuple[str, dict]:
    if reject_is_a:
        mapping = {"A": 1, "B": 0}
        choices = " (A) Reject\n (B) Accept"
    else:
        mapping = {"A": 0, "B": 1}
        choices = " (A) Accept\n (B) Reject"
    text = (
        "Player 1 is given $100 and offers a split. If you reject, both get nothing. "
        f"Player 1 takes ${keep} and offers you ${offer}.\n\n"
        f"Choices:\n{choices}\n\n{cfg.FC_SUFFIX}"
    )
    assert_no_describe(text)
    return text, mapping


def load_xstest(n_safe: int, n_unsafe: int) -> tuple[list[dict], list[dict]]:
    path = REPO / "artifacts" / "battery" / "exp09" / "xstest_prompts.csv"
    if not path.is_file():
        raise FileNotFoundError(path)
    got = cfg.sha256_file_lf(path)
    if got != cfg.XSTEST_SHA256:
        raise RuntimeError(f"xstest sha {got} != {cfg.XSTEST_SHA256}")
    import csv

    safe, unsafe = [], []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rec = {
                "id": str(row.get("id") or ""),
                "prompt": row.get("prompt") or "",
                "type": (row.get("type") or "").lower(),
                "label": (row.get("label") or "").lower(),
            }
            if rec["label"] == "safe":
                safe.append(rec)
            else:
                unsafe.append(rec)
    return safe[:n_safe], unsafe[:n_unsafe]


def maybe_image(arm: str, pool: dict, rng: random.Random, loader):
    if arm in ("no_image", "none", "no-image"):
        return None, None
    rids = pool.get(arm) or []
    if not rids:
        return None, None
    rid = rids[rng.randrange(len(rids))]
    return rid, loader(rid)


def pool_ids(ctx: dict, n: int | None = None) -> dict:
    out = {}
    for arm, rids in (ctx.get("pool") or {}).items():
        xs = list(rids or [])
        out[arm] = xs if n is None else xs[:n]
    return out


def rid_sha(ids: dict) -> str:
    return cfg.sha256_text(json.dumps(ids, sort_keys=True))


def run_exp09(ctx: dict) -> dict:
    import battery_v2_load as ld

    sz = ctx["sizes"]
    model, proc = ctx["model"], ctx["proc"]
    run_dir = ctx["cell_dir"] / "exp09"
    n_img = sz["n_img_09"]
    used = pool_ids(ctx, n_img)
    lock = v2lock.build_lock(
        experiment="exp09",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="completion_refuse_benign",
        scorer="battery_v2_scorer.completion_refuses",
        seed=ctx["seed"],
        arms=list(ctx["arms"]),
        extra={"rids": used, "rid_sha256": rid_sha(used)},
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    safe, unsafe = load_xstest(sz["n_safe_09"], sz["n_unsafe_09"])
    by = {arm: [] for arm in ctx["arms"]}
    ft_by = {arm: {"refuse": 0, "comply": 0, "ambiguous_v1": 0, "other": 0} for arm in ctx["arms"]}
    unsafe_by = {arm: [] for arm in ctx["arms"]}
    n_scored = 0

    def one(item, arm, sink):
        nonlocal n_scored
        rids = (ctx["pool"].get(arm) or [])[:n_img]
        rid, img = None, None
        if arm not in ("no_image", "none", "no-image") and rids:
            rid = rids[item.get("_i", 0) % len(rids)]
            img = ctx["load_img"](rid)
        rec = ld.generate_choice(model, proc, item["prompt"], img, max_new=48)
        refused = scorer.completion_refuses(rec["text"])
        tok = (rec["text"] or "").split()[:1]
        lab = scorer.first_token_refuse_label(tok[0] if tok else "")
        sink.append(int(refused))
        key = lab if lab in ft_by[arm] else "other"
        ft_by[arm][key] = ft_by[arm].get(key, 0) + 1
        n_scored += 1

    for i, item in enumerate(safe):
        item = dict(item, _i=i)
        for arm in ctx["arms"]:
            one(item, arm, by[arm])
            if n_scored % 40 == 0:
                hb("exp09", n=n_scored, arm=arm)
    for i, item in enumerate(unsafe):
        item = dict(item, _i=i)
        for arm in ctx["arms"]:
            one(item, arm, unsafe_by[arm])
    out = {
        "experiment": "exp09",
        "complete": True,
        "model_id": ctx["model_id"],
        "corpus": ctx["corpus"],
        "n_safe": len(safe),
        "n_unsafe": len(unsafe),
        "rids": used,
        "rid_sha256": rid_sha(used),
        "primary": {},
        "secondary_ft": ft_by,
        "unsafe_sanity": {},
        "gates": {
            "lock": True,
            "xstest_pin": True,
            "no_describe": True,
            "unsafe_ran": len(unsafe) == sz["n_unsafe_09"],
            "ft_populated": any(sum(v.values()) > 0 for v in ft_by.values()),
        },
    }
    for arm, ys in by.items():
        m, lo, hi = boot_ci([float(x) for x in ys], sz["n_boot"], ctx["seed"])
        out["primary"][arm] = {"refuse_rate": m, "ci_lo": lo, "ci_hi": hi, "n": len(ys)}
    for arm, ys in unsafe_by.items():
        m, lo, hi = boot_ci([float(x) for x in ys], sz["n_boot"], ctx["seed"] + 1)
        out["unsafe_sanity"][arm] = {"refuse_rate": m, "ci_lo": lo, "ci_hi": hi, "n": len(ys)}
    none = out["primary"].get("no_image", {}).get("refuse_rate")
    if none is not None:
        for arm, rec in out["primary"].items():
            if arm == "no_image":
                continue
            rec["delta_vs_none"] = rec["refuse_rate"] - none
    save(run_dir / "results.json", out)
    return out


def run_exp05(ctx: dict) -> dict:
    import battery_v2_load as ld

    sz = ctx["sizes"]
    model, proc = ctx["model"], ctx["proc"]
    run_dir = ctx["cell_dir"] / "exp05"
    n_img = sz["n_per_05"]
    used = pool_ids(ctx, n_img)
    lock = v2lock.build_lock(
        experiment="exp05",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="ug_reject_unfair_80_20_and_90_10 + dictator_0_50",
        scorer="forced_choice_AB",
        seed=ctx["seed"],
        arms=list(ctx["arms"]),
        extra={"rids": used, "rid_sha256": rid_sha(used), "ug_splits": ["90-10", "80-20"]},
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    masses = []
    rej90 = {arm: [] for arm in ctx["arms"]}
    rej80 = {arm: [] for arm in ctx["arms"]}
    give = {arm: [] for arm in ctx["arms"]}
    n_ok, n_try = 0, 0
    n = 0
    for arm in ctx["arms"]:
        rids = ctx["pool"].get(arm) or [None]
        take = rids[:n_img] if rids and rids[0] is not None else [None] * n_img
        for j, rid in enumerate(take):
            img = ctx["load_img"](rid) if rid else None
            specs = [
                ("r90", reject_prompt(90, 10, reject_is_a=(j % 2 == 0)), rej90[arm]),
                ("r80", reject_prompt(80, 20, reject_is_a=(j % 2 == 1)), rej80[arm]),
                ("give", (amount_prompt(0, 50, high_is_a=(j % 2 == 1))), give[arm]),
            ]
            for _name, (prompt, mapping), sink in specs:
                rec = ld.generate_choice(model, proc, prompt, img)
                n_try += 1
                if rec["ab_mass"] is not None:
                    masses.append(rec["ab_mass"])
                if rec["letter"] in mapping:
                    sink.append(float(mapping[rec["letter"]]))
                    n_ok += 1
                else:
                    sink.append(float("nan"))
                n += 1
                if n % 32 == 0:
                    hb("exp05", n=n, arm=arm)
    fc = float(np.mean(masses)) if masses else 0.0
    parse = (n_ok / n_try) if n_try else 0.0

    def arm_stats(d):
        out = {}
        for arm, ys in d.items():
            finite = [float(x) for x in ys if np.isfinite(x)]
            m, lo, hi = boot_ci(finite, sz["n_boot"], ctx["seed"])
            out[arm] = {"mean": m, "ci_lo": lo, "ci_hi": hi, "n": len(finite), "n_invalid": len(ys) - len(finite)}
        return out

    out = {
        "experiment": "exp05",
        "complete": True,
        "model_id": ctx["model_id"],
        "corpus": ctx["corpus"],
        "rids": used,
        "rid_sha256": rid_sha(used),
        "fc_mass_mean": fc,
        "parse_rate": parse,
        "gates": {
            "fc_mass": fc >= cfg.FC_MASS_MIN,
            "parse_rate": parse >= 0.95,
            "lock": True,
            "ug_80_20": True,
            "ug_90_10": True,
        },
        "primary": {
            "ug_reject_90_10": arm_stats(rej90),
            "ug_reject_80_20": arm_stats(rej80),
            "dictator_0_50": arm_stats(give),
        },
    }
    save(run_dir / "results.json", out)
    return out


def run_exp06(ctx: dict) -> dict:
    import battery_v2_load as ld

    sz = ctx["sizes"]
    model, proc = ctx["model"], ctx["proc"]
    run_dir = ctx["cell_dir"] / "exp06"
    used = pool_ids(ctx, sz["n_img_06"])
    lock = v2lock.build_lock(
        experiment="exp06",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="p_now",
        scorer="forced_choice_AB",
        seed=ctx["seed"],
        arms=list(ctx["arms"]),
        extra={"rids": used, "rid_sha256": rid_sha(used)},
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    items = wait.load_grid(tier=sz["tier_06"])
    by = {arm: [] for arm in ctx["arms"]}
    masses = []
    n_ok, n_try, n = 0, 0, 0
    for arm in ctx["arms"]:
        rids = ctx["pool"].get(arm) or [None]
        imgs = rids[: sz["n_img_06"]] if rids and rids[0] is not None else [None]
        for rid in imgs:
            img = ctx["load_img"](rid) if rid else None
            for it in items:
                rec = ld.generate_choice(model, proc, wait.prompt_for(it), img)
                n_try += 1
                if rec["ab_mass"] is not None:
                    masses.append(rec["ab_mass"])
                letter = rec["letter"] or wait.parse_letter(rec["text"] or "")
                if letter == it["now_letter"]:
                    by[arm].append(1.0)
                    n_ok += 1
                elif letter == it["later_letter"]:
                    by[arm].append(0.0)
                    n_ok += 1
                else:
                    by[arm].append(float("nan"))
                n += 1
                if n % 80 == 0:
                    hb("exp06", n=n, arm=arm)
    fc = float(np.mean(masses)) if masses else 0.0
    parse = (n_ok / n_try) if n_try else 0.0
    out = {
        "experiment": "exp06",
        "complete": True,
        "model_id": ctx["model_id"],
        "corpus": ctx["corpus"],
        "rids": used,
        "rid_sha256": rid_sha(used),
        "fc_mass_mean": fc,
        "parse_rate": parse,
        "primary": {},
        "gates": {
            "lock": True,
            "dv_is_p_now": True,
            "fc_mass": fc >= cfg.FC_MASS_MIN,
            "parse_rate": parse >= 0.95,
        },
    }
    for arm, ys in by.items():
        finite = [float(x) for x in ys if np.isfinite(x)]
        m, lo, hi = boot_ci(finite, sz["n_boot"], ctx["seed"])
        out["primary"][arm] = {"p_now": m, "ci_lo": lo, "ci_hi": hi, "n": len(finite), "n_invalid": len(ys) - len(finite)}
    save(run_dir / "results.json", out)
    return out


def run_exp03(ctx: dict) -> dict:
    """EMOTIC: CROSS_MODAL pixels vs caption vs label vs none on anger-neutral pairs.
    All corpora: pixels expansion across arms."""
    import battery_v2_load as ld

    sz = ctx["sizes"]
    model, proc = ctx["model"], ctx["proc"]
    run_dir = ctx["cell_dir"] / "exp03"
    n_pair = sz["n_pairs_03"]
    used = pool_ids(ctx, max(n_pair, sz["n_img_03_expand"]))
    lock = v2lock.build_lock(
        experiment="exp03",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="cross_modal_same_diverge_anger_neutral",
        scorer="forced_choice_AB",
        seed=ctx["seed"],
        arms=list(ctx["arms"]),
        extra={"rids": used, "rid_sha256": rid_sha(used), "cross_modal": ctx["corpus"] == "emotic"},
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    risk = "A 50% chance of $100 or a sure $40. Which do you take?\nA. lottery\nB. sure $40\n\n" + cfg.FC_SUFFIX
    dictp = amount_prompt(0, 50, True)[0]
    tasks = (("risk", risk, True), ("dictator", dictp, False))
    pixels = {arm: [] for arm in ctx["arms"]}
    masses = []
    n_ok, n_try = 0, 0
    for arm in ctx["arms"]:
        rids = ctx["pool"].get(arm) or [None]
        take = rids[: sz["n_img_03_expand"]] if rids and rids[0] is not None else [None] * sz["n_img_03_expand"]
        for rid in take:
            img = ctx["load_img"](rid) if rid else None
            for _name, prompt, _ in tasks:
                rec = ld.generate_choice(model, proc, prompt, img)
                n_try += 1
                if rec["ab_mass"] is not None:
                    masses.append(rec["ab_mass"])
                if rec["letter"] in ("A", "B"):
                    pixels[arm].append(1.0 if rec["letter"] == "A" else 0.0)
                    n_ok += 1
                else:
                    pixels[arm].append(float("nan"))
    cross = {"headline": "PIXELS_EXPANSION_ONLY", "mods": {}}
    if ctx["corpus"] == "emotic":
        a_arm, b_arm = "anger", "neutral"
        src = ctx.get("pair_pool") or ctx["pool"]
        pa, pb = (src.get(a_arm) or [])[:n_pair], (src.get(b_arm) or [])[:n_pair]
        n = min(len(pa), len(pb), n_pair)
        literal = "Write one literal sentence listing only visible people, objects, actions, and setting."
        assert_no_describe(literal)
        caps = {}
        for rid in list(pa[:n]) + list(pb[:n]):
            img = ctx["load_img"](rid)
            caps[rid] = ld.generate_text(model, proc, literal, img, max_new=48)
            hb("exp03_caption", rid=rid)
        mods = ("pixels", "caption", "label", "none")
        delta = {m: {"risk": [], "dictator": []} for m in mods}

        def stim(mod: str, rid: str, lab: str):
            if mod == "pixels":
                return ctx["load_img"](rid), ""
            if mod == "caption":
                return None, f"Scene: {caps.get(rid, '')}\n\n"
            if mod == "label":
                return None, f"The annotated emotion category is {lab}.\n\n"
            return None, ""

        for i in range(n):
            for mod in mods:
                for fam, prompt, _ in tasks:
                    pre_a, txt_a = stim(mod, pa[i], "Anger")
                    pre_b, txt_b = stim(mod, pb[i], "Neutral")
                    # pixels uses image; others prepend text and no image
                    ia = pre_a if mod == "pixels" else None
                    ib = pre_b if mod == "pixels" else None
                    ra = ld.generate_choice(model, proc, txt_a + prompt, ia)
                    rb = ld.generate_choice(model, proc, txt_b + prompt, ib)
                    n_try += 2
                    for rec in (ra, rb):
                        if rec["ab_mass"] is not None:
                            masses.append(rec["ab_mass"])
                        if rec["letter"] in ("A", "B"):
                            n_ok += 1
                    ya = 1.0 if ra["letter"] == "A" else (0.0 if ra["letter"] == "B" else float("nan"))
                    yb = 1.0 if rb["letter"] == "A" else (0.0 if rb["letter"] == "B" else float("nan"))
                    if np.isfinite(ya) and np.isfinite(yb):
                        delta[mod][fam].append(ya - yb)
            hb("exp03_cross", i=i, n=n)
        ci = {}
        ident = {}
        for mod in mods:
            ci[mod] = {}
            ident[mod] = {}
            for fam, vs in delta[mod].items():
                m, lo, hi = boot_ci(vs, sz["n_boot"], ctx["seed"])
                ci[mod][fam] = {"mean": m, "ci_lo": lo, "ci_hi": hi, "n": len(vs)}
                ident[mod][fam] = bool(vs) and np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0)
        pixel_ident = any(ident["pixels"][f] for f in ("risk", "dictator"))
        if not pixel_ident:
            headline = "INCONCLUSIVE"
        else:
            same_ok = False
            diverge = False
            pending = False
            for fam in ("risk", "dictator"):
                if not ident["pixels"][fam]:
                    continue
                p = ci["pixels"][fam]["mean"]
                matched = False
                conflict = False
                any_text = False
                for mod in ("caption", "label"):
                    if not ident[mod][fam]:
                        continue
                    any_text = True
                    q = ci[mod][fam]["mean"]
                    if np.isfinite(p) and np.isfinite(q) and p * q < 0:
                        conflict = True
                    elif np.isfinite(p) and np.isfinite(q) and p * q > 0:
                        matched = True
                if conflict:
                    diverge = True
                elif matched:
                    same_ok = True
                elif not any_text:
                    pending = True
            if diverge:
                headline = "CROSS_MODAL_DIVERGE"
            elif same_ok and not pending:
                headline = "CROSS_MODAL_SAME"
            else:
                headline = "INCONCLUSIVE"
        cross = {"headline": headline, "mods": ci, "identifiable": ident, "n_pairs": n, "rule": "paired_boot_ci_excludes_0"}
    fc = float(np.mean(masses)) if masses else 0.0
    parse = (n_ok / n_try) if n_try else 0.0
    out = {
        "experiment": "exp03",
        "complete": True,
        "model_id": ctx["model_id"],
        "corpus": ctx["corpus"],
        "rids": used,
        "rid_sha256": rid_sha(used),
        "headline": cross["headline"],
        "cross_modal": cross,
        "pixels_expansion": {
            arm: {
                "mean_A": float(np.nanmean(v)) if v else None,
                "n": int(np.sum(np.isfinite(v))) if v else 0,
            }
            for arm, v in pixels.items()
        },
        "fc_mass_mean": fc,
        "parse_rate": parse,
        "gates": {
            "lock": True,
            "fc_mass": fc >= cfg.FC_MASS_MIN,
            "parse_rate": parse >= 0.95,
            "cross_modal_emotic": ctx["corpus"] != "emotic" or cross["headline"] != "PIXELS_EXPANSION_ONLY",
        },
    }
    save(run_dir / "results.json", out)
    return out


def run_exp10(ctx: dict) -> dict:
    import battery_probe_aperp as probe

    run_dir = ctx["cell_dir"] / "exp10"
    dirs, dirs_status = mech.try_load_dirs(ctx["model_key"], ctx["corpus"])
    if ctx["corpus"] == "oasis":
        a_arm, b_arm = "neg", "neu"
    else:
        a_arm, b_arm = "anger", "neutral"
    src = ctx.get("pair_pool") or ctx["pool"]
    pa, pb = src.get(a_arm) or [], src.get(b_arm) or []
    n_pair = min(len(pa), len(pb), cfg.sizes(ctx["tier"])["n_pairs_10"])
    pairs = {"pos_arm": a_arm, "neg_arm": b_arm, "a": pa[:n_pair], "b": pb[:n_pair]}
    extra = {"dirs": dirs_status, "pairs": pairs, "rid_sha256": rid_sha(pairs)}
    lock = v2lock.build_lock(
        experiment="exp10",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="risk_neg_minus_neu_c_and_ab",
        scorer="paired_product_of_coefficients",
        seed=ctx["seed"],
        arms=["neg", "neu"] if ctx["corpus"] == "oasis" else ["anger", "neutral"],
        extra=extra,
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    n_layers = int(ctx["model_meta"]["n_layers"])
    prompt = (
        "Option A is a 50% chance of $100. Option B is a sure $40. "
        f"Which do you choose?\n\n{cfg.FC_SUFFIX}"
    )
    assert_no_describe(prompt)
    dY, dM, masses = [], [], []
    for i in range(n_pair):
        ia = ctx["load_img"](pa[i])
        ib = ctx["load_img"](pb[i])
        ra = mech.score_task(ctx["model"], ctx["proc"], prompt, ia, n_layers, dirs)
        rb = mech.score_task(ctx["model"], ctx["proc"], prompt, ib, n_layers, dirs)
        dY.append(float(ra["Y_risky_A"] - rb["Y_risky_A"]))
        if ra["ab_mass"] is not None:
            masses.append(float(ra["ab_mass"]))
        if rb["ab_mass"] is not None:
            masses.append(float(rb["ab_mass"]))
        if ra.get("M") is not None and rb.get("M") is not None:
            dM.append(float(ra["M"] - rb["M"]))
        hb("exp10", i=i, n=n_pair)
    m, lo, hi = boot_ci(dY, ctx["sizes"]["n_boot"], ctx["seed"])
    ab = None
    stats = None
    if len(dM) == len(dY) and len(dY) >= 3:
        stats = probe.paired_product_of_coefficients(dM, dY)
        ab = stats.get("ab")
    fc = float(np.mean(masses)) if masses else 0.0
    frozen_needed = ctx["model_key"] == "e4b" and ctx["corpus"] == "emotic"
    out = {
        "experiment": "exp10",
        "complete": True,
        "model_id": ctx["model_id"],
        "corpus": ctx["corpus"],
        "dirs_status": dirs_status,
        "dirs_path": None if dirs is None else dirs.path,
        "primary": {
            "c_mean_dY": m,
            "ci_lo": lo,
            "ci_hi": hi,
            "n": len(dY),
            "ab": ab,
            "stats": stats,
            "n_dM": len(dM),
        },
        "fc_mass_mean": fc,
        "gates": {
            "lock": True,
            "no_v3_write": True,
            "frozen_required": frozen_needed,
            "frozen_ok": (not frozen_needed) or dirs_status == "FROZEN_V3_EXACT",
            "ab_computed": ab is not None,
            "fc_mass": fc >= cfg.FC_MASS_MIN if masses else False,
        },
        "frozen_v3_touched": False,
    }
    save(run_dir / "results.json", out)
    return out


def run_mech(ctx: dict) -> dict:
    import battery_v2_load as ld

    run_dir = ctx["cell_dir"] / "mech"
    n_layers = int(ctx["model_meta"]["n_layers"])
    window = mech.window_for(n_layers)
    dirs, dirs_status = mech.try_load_dirs(ctx["model_key"], ctx["corpus"])
    calib = ctx.get("calib_pool") or {}
    n05 = min(8, int(ctx["sizes"]["n_per_05"]))
    eval_ids_09 = {arm: (ctx["pool"].get(arm) or [])[:1] for arm in cfg.MECH_ARMS}
    eval_ids_05 = {arm: (ctx["pool"].get(arm) or [])[:n05] for arm in cfg.MECH_ARMS}
    eval_ids = eval_ids_05
    eval_rids = set()
    for xs in eval_ids_05.values():
        eval_rids.update(xs)
    photo_rids = []
    for arm in ("anger", "sadness", "neutral"):
        for rid in calib.get(arm) or []:
            if rid in eval_rids:
                continue
            photo_rids.append(rid)
    n_cal = max(4, int(ctx["sizes"].get("n_calib_mech", 8)))
    photo_rids = photo_rids[:n_cal]
    dirs_sha = None if dirs is None else getattr(dirs, "sha256", None)
    lock = v2lock.build_lock(
        experiment="mech",
        model_key=ctx["model_key"],
        tier=ctx["tier"],
        script_path=Path(__file__),
        primary_dv="layer_score_image_present_vs_a_perp",
        scorer="last_prompt_residual_dot",
        seed=ctx["seed"],
        arms=list(cfg.MECH_ARMS),
        extra={
            "exps": list(cfg.MECH_EXPS),
            "calib_disjoint": True,
            "eval_rids": eval_ids,
            "eval_rids_09": eval_ids_09,
            "eval_rids_05": eval_ids_05,
            "calib_rids": photo_rids,
            "dirs_sha256": dirs_sha,
            "rid_sha256": rid_sha({"eval05": eval_ids_05, "eval09": eval_ids_09, "calib": photo_rids}),
        },
    )
    v2lock.write_lock(run_dir, lock)
    v2lock.require_lock(run_dir, Path(__file__))
    photo_vecs, none_vecs, notes = [], [], []
    try:
        for i, rid in enumerate(photo_rids):
            img = ctx["load_img"](rid)
            acts = mech.capture_acts(ctx["model"], ctx["proc"], mech.MECH_PROMPT, img, n_layers)
            photo_vecs.append(mech.window_vec(acts, window))
            hb("mech_calib", i=i, kind="photo")
        for i in range(max(4, len(photo_rids))):
            acts = mech.capture_acts(ctx["model"], ctx["proc"], mech.MECH_PROMPT, None, n_layers)
            none_vecs.append(mech.window_vec(acts, window))
            hb("mech_calib", i=i, kind="none")
    except Exception as e:
        notes.append(f"calib_fail:{type(e).__name__}:{e}")
    ip = None
    if photo_vecs and none_vecs:
        ip = mech.image_present_dir(np.mean(photo_vecs, 0), np.mean(none_vecs, 0))
    safe, _ = load_xstest(int(ctx["sizes"].get("n_mech_prompts", 16)), 0)
    buckets = {
        "exp09": {"dy": [], "s_img": [], "s_aff": []},
        "exp05": {"dy": [], "s_img": [], "s_aff": []},
    }

    def add(name, scored):
        none = scored.get("no_image") or {}
        for arm in ("anger", "sadness"):
            if arm not in scored or not none:
                continue
            if not (np.isfinite(scored[arm]["y"]) and np.isfinite(none.get("y", float("nan")))):
                continue
            buckets[name]["dy"].append(scored[arm]["y"] - none["y"])
            if scored[arm]["s_img"] is not None and none.get("s_img") is not None:
                buckets[name]["s_img"].append(scored[arm]["s_img"] - none["s_img"])
            if scored[arm]["s_aff"] is not None and none.get("s_aff") is not None:
                buckets[name]["s_aff"].append(scored[arm]["s_aff"] - none["s_aff"])

    eval_n = 0

    def proj_img(acts):
        if ip is None:
            return None
        wv = mech.window_vec(acts, window)
        d = ip[: wv.size] if ip.size != wv.size else ip
        return float(np.dot(wv, d))

    # exp09 subset: last-prompt residual on the refuse prompt (not an A/B overlay).
    for item in safe:
        scored = {}
        for arm in cfg.MECH_ARMS:
            rids = (ctx["pool"].get(arm) or [])[:1]
            img = None if arm == "no_image" or not rids else ctx["load_img"](rids[0])
            acts = mech.capture_acts(ctx["model"], ctx["proc"], item["prompt"], img, n_layers)
            rec = ld.generate_choice(ctx["model"], ctx["proc"], item["prompt"], img, max_new=48)
            m_aff = None
            if dirs is not None:
                try:
                    import battery_probe_aperp as probe

                    m_aff = float(probe.project_aperp(acts, dirs.a_perp, dirs.window))
                except Exception:
                    m_aff = None
            scored[arm] = {
                "y": float(int(scorer.completion_refuses(rec["text"]))),
                "s_img": proj_img(acts),
                "s_aff": m_aff,
            }
            eval_n += 1
        add("exp09", scored)
        hb("mech_eval09", n=eval_n)

    # exp05 subset: unfair-reject 90-10 last-prompt residual.
    n05 = min(8, int(ctx["sizes"]["n_per_05"]))
    for j in range(n05):
        scored = {}
        prompt, mapping = reject_prompt(90, 10, reject_is_a=(j % 2 == 0))
        for arm in cfg.MECH_ARMS:
            rids = (ctx["pool"].get(arm) or [])
            rid = None if arm == "no_image" or not rids else rids[j % len(rids)]
            img = ctx["load_img"](rid) if rid else None
            rec = mech.score_task(ctx["model"], ctx["proc"], prompt, img, n_layers, dirs)
            y = float(mapping.get(rec["letter"], float("nan")))
            scored[arm] = {"y": y, "s_img": proj_img(rec["acts"]), "s_aff": rec.get("M")}
            eval_n += 1
        add("exp05", scored)
        hb("mech_eval05", j=j)
    tracks = {}
    for name, b in buckets.items():
        dy, si, sa = b["dy"], b["s_img"], b["s_aff"]
        if len(dy) >= 3 and len(si) >= 3 and len(sa) >= 3:
            n_common = min(len(dy), len(si), len(sa))
            tracks[name] = mech.tracks_which(dy[:n_common], si[:n_common], sa[:n_common])
        elif len(dy) >= 3 and len(si) >= 3:
            n_common = min(len(dy), len(si))
            tracks[name] = mech.tracks_which(dy[:n_common], si[:n_common], [float("nan")] * n_common)
        else:
            tracks[name] = {"n_dy": len(dy), "n_img": len(si), "n_aff": len(sa)}
    out = {
        "experiment": "mech",
        "complete": ip is not None and eval_n > 0,
        "model_id": ctx["model_id"],
        "n_layers": n_layers,
        "window": window,
        "dirs_status": dirs_status,
        "n_calib_photo": len(photo_vecs),
        "n_calib_none": len(none_vecs),
        "n_eval_forwards": eval_n,
        "eval_rids": eval_ids,
        "calib_rids": photo_rids,
        "image_present_unit_norm": None if ip is None else float(np.linalg.norm(ip)),
        "tracks": tracks,
        "notes": notes,
        "gates": {
            "lock": True,
            "window_ok": window == ac.gate_window(n_layers),
            "calib_disjoint": True,
            "captured": ip is not None,
            "exp05_included": True,
            "exp09_open_prompt": True,
            "tracks_not_pooled": True,
            "a_perp_present": dirs is not None,
        },
    }
    save(run_dir / "results.json", out)
    return out


def make_img_loader(corpus: str, emotic_root: Path | None, oasis_index: dict | None):
    from PIL import Image

    def _resize(im):
        w, h = im.size
        m = max(w, h)
        if m <= 512:
            return im
        s = 512 / float(m)
        return im.resize((max(1, int(w * s)), max(1, int(h * s))))

    def load(rid):
        if rid is None:
            return None
        if corpus == "emotic":
            folder, name = str(rid).split("/", 1)
            p = emotic_root / "emotic" / folder / name
            return _resize(Image.open(p).convert("RGB"))
        p = (oasis_index or {}).get(rid)
        if p is None:
            return None
        return _resize(Image.open(p).convert("RGB"))

    return load


def build_ctx(model_key: str, corpus: str, tier: str, seed: int, model, proc, meta, pool, load_img, calib_pool=None, pair_pool=None):
    cell = art_root() / model_key / corpus
    cell.mkdir(parents=True, exist_ok=True)
    arms = list(cfg.EMOTIC_ARMS if corpus == "emotic" else cfg.OASIS_ARMS)
    return {
        "model_key": model_key,
        "model_id": cfg.MODELS[model_key]["id"],
        "model": model,
        "proc": proc,
        "model_meta": meta,
        "corpus": corpus,
        "tier": tier,
        "seed": seed,
        "sizes": cfg.sizes(tier),
        "arms": arms,
        "pool": pool,
        "calib_pool": calib_pool or {},
        "pair_pool": pair_pool or {},
        "load_img": load_img,
        "cell_dir": cell,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="budget3h", choices=("budget3h", "full"))
    ap.add_argument("--models", default="e4b,g12")
    ap.add_argument("--corpora", default="emotic,oasis")
    ap.add_argument("--exps", default="exp09,exp05,exp06,exp10,exp03,mech")
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    art_root().mkdir(parents=True, exist_ok=True)
    hb("start", tier=args.tier)
    runners = {
        "exp09": run_exp09,
        "exp05": run_exp05,
        "exp06": run_exp06,
        "exp03": run_exp03,
        "exp10": run_exp10,
        "mech": run_mech,
    }
    status = {"campaign": cfg.CAMPAIGN, "tier": args.tier, "cells": {}}
    save(art_root() / "STATUS.json", status)

    if args.dry_run:
        dry_root = art_root() / "_dry"
        os.environ["E2E_V2"] = str(dry_root)
        for mk in args.models.split(","):
            for corpus in args.corpora.split(","):
                arms = list(cfg.EMOTIC_ARMS if corpus == "emotic" else cfg.OASIS_ARMS)
                fake_pool = {a: [f"rid_{a}_{i}" for i in range(8)] for a in arms if a != "no_image"}
                fake_pool["no_image"] = []
                ctx = build_ctx(mk, corpus, args.tier, args.seed, None, None, {"n_layers": cfg.MODELS[mk]["n_layers"]}, fake_pool, lambda r: None)
                for exp in args.exps.split(","):
                    run_dir = ctx["cell_dir"] / exp
                    payload = v2lock.build_lock(
                        experiment=exp,
                        model_key=mk,
                        tier=args.tier,
                        script_path=Path(__file__),
                        primary_dv="dry",
                        scorer="dry",
                        seed=args.seed,
                        arms=arms,
                    )
                    v2lock.write_lock(run_dir, payload)
                    v2lock.require_lock(run_dir, Path(__file__))
                    save(run_dir / "results.json", {"experiment": exp, "dry_run": True, "complete": False})
        hb("dry_done")
        log("dry-run locks written under _dry")
        return 0

    import battery_v2_load as ld
    from PIL import Image  # noqa: F401

    e2e = Path(os.environ.get("E2E_ROOT", str(Path.home() / "algoverse_run"))).expanduser()
    emotic_root = Path(os.environ.get("E2E_EMOTIC", str(e2e / "emotic_data"))).expanduser()
    split_path = Path(os.environ.get("E2E_SPLIT", str(e2e / "emotic_split.json"))).expanduser()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    corpora = [c.strip() for c in args.corpora.split(",") if c.strip()]
    corpora = [c for c in corpora if c == "emotic"] + [c for c in corpora if c != "emotic"]
    exps = [e.strip() for e in args.exps.split(",") if e.strip()]

    max_hours = float(os.environ.get("E2E_MAX_HOURS", "2.75"))

    def run_cell(mk: str, corpus: str, model, proc, meta) -> None:
        hb("corpus", model=mk, corpus=corpus)
        remain = max_hours * 3600 - (time.time() - T0)
        if corpus != "emotic" and remain < 40 * 60:
            log(f"skip {corpus} for {mk}: {remain/60:.0f} min left")
            status["cells"][f"{mk}/{corpus}"] = {"complete": False, "skipped": "budget"}
            save(art_root() / "STATUS.json", status)
            return
        n_calib = int(cfg.sizes(args.tier).get("n_calib_mech", 8))
        if corpus == "emotic":
            rows = pools.load_emotic_rows(emotic_root / "emotic_pre" / "train.csv")
            split = pools.load_split(split_path)
            n_per = max(cfg.sizes(args.tier)["n_per_05"], cfg.sizes(args.tier)["n_img_09"])
            built = pools.build_emotic_pools(rows, split["science_ids"], n_per, args.seed, n_calib=n_calib)
            pool = built["pools"]
            calib_pool = built.get("calib_pools") or {}
            status["exclusive_n"] = built.get("exclusive_n")
            short = [k for k, n in (built.get("exclusive_n") or {}).items() if n < 16]
            status["exclusive_below_16"] = short
            save(art_root() / "STATUS.json", status)
            load_img = make_img_loader("emotic", emotic_root, None)
        else:
            import battery_exp08_lib as o8

            oasis_dir = e2e / "battery" / "exp08" / "oasis"
            means = oasis_dir / "oasis_means.json"
            if not means.is_file():
                log("OASIS means missing; skip oasis corpus")
                return
            items = json.loads(means.read_text(encoding="utf-8"))
            built = pools.oasis_valence_pools(items, cfg.sizes(args.tier)["n_per_05"], args.seed)
            pool = built["pools"]
            calib_pool = built.get("calib_pools") or {}
            idx = o8.index_jpegs(oasis_dir)
            load_img = make_img_loader("oasis", None, idx)
        pair_pool = built.get("pair_pools") or {}
        ctx = build_ctx(mk, corpus, args.tier, args.seed, model, proc, meta, pool, load_img, calib_pool, pair_pool)
        for exp in exps:
            if corpus == "oasis" and exp == "mech":
                continue
            remain = max_hours * 3600 - (time.time() - T0)
            if remain < 8 * 60:
                log(f"stop before {mk} {corpus} {exp}: {remain/60:.0f} min left")
                break
            log(f"run {mk} {corpus} {exp}")
            blob = runners[exp](ctx)
            status["cells"][f"{mk}/{corpus}/{exp}"] = {
                "complete": blob.get("complete"),
                "gates": blob.get("gates"),
            }
            save(art_root() / "STATUS.json", status)

    for corpus in corpora:
        for mk in models:
            log(f"load {mk} for {corpus}")
            model, proc, meta = ld.load_model(mk)
            try:
                run_cell(mk, corpus, model, proc, meta)
            finally:
                del model
                try:
                    import torch

                    torch.cuda.empty_cache()
                except Exception:
                    pass
    hb("done")
    log("campaign complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
