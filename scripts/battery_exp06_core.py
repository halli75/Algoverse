"""exp06 temporal discounting — numpy core (no GPU).

Frozen LLM Economicus Waiting Game grid (rossjillian/llm-economicus,
Rachlin et al. 1991). Hyperbolic U(x, d) = x / (1 + k d), d in years.

[[EMOTIC]] [[battery-exp06]]
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

EXPERIMENT = "exp06"
SOURCE_REPO = "https://github.com/rossjillian/llm-economicus"
SOURCE_SHA = "b0cd44f586c427b3bad2ef52cb687480f547874a"
EXPECTED_SPLIT = "1e8ea1c22144dd9d"
PRIMARY_MODEL = "google/gemma-4-E4B-it"
PREMISE = "You are given two monetary options. You must choose one."
FC_SUFFIX = "Reply with exactly one letter: A or B."
# Locked: never prepend DESCRIBE / image-talk in the behavioral prompt.
FORBIDDEN_STEMS = (
    "Describe what is happening",
    "Look at the image",
    "What emotion",
    "in this image",
)

DELAYS: tuple[tuple[str, float], ...] = (
    ("1 month", 1.0 / 12.0),
    ("6 months", 0.5),
    ("1 year", 1.0),
    ("5 years", 5.0),
    ("10 years", 10.0),
    ("25 years", 25.0),
    ("50 years", 50.0),
)
# Exact Economicus `experiments/wait/de_novo.py` comps() amounts.
AMOUNTS: tuple[int, ...] = (
    1000, 990, 980, 960, 940, 920, 900,
    850, 800, 750, 700, 650, 600, 550, 500,
    450, 400, 350, 300, 250, 200, 150, 100,
    80, 60, 40, 20, 10, 5, 1, 0,
)
SMOKE_DELAYS = ("1 month", "1 year", "10 years", "50 years")
SMOKE_AMOUNTS = (1000, 900, 700, 500, 300, 100, 20, 0)

CONDITIONS = ("fear", "anger", "sad", "happy", "peace", "neutral", "no-image")
EMOTIC_TARGET = {
    "fear": "Fear",
    "anger": "Anger",
    "sad": "Sadness",
    "happy": "Happiness",
    "peace": "Peace",
}
RIVAL_LABELS = frozenset(EMOTIC_TARGET.values())
LL_AMOUNT = 1000.0
K_FLOOR = 1e-6
K_CEIL = 1e5

GRID_NAME = "exp06_waiting.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def grid_path() -> Path:
    return _repo_root() / "data" / "battery" / GRID_NAME


def delay_years(label: str) -> float:
    for name, years in DELAYS:
        if name == label:
            return float(years)
    raise KeyError(label)


def implied_k(ss: float, ll: float, d_years: float) -> float:
    """Indifference k for SS now vs LL in d years. k=inf if SS<=0; k=0 if SS>=LL."""
    if d_years <= 0:
        raise ValueError("delay must be positive")
    if ss <= 0:
        return float("inf")
    if ss >= ll:
        return 0.0
    return (ll / ss - 1.0) / d_years


def item_id(delay_label: str, ss: int, flip: bool) -> str:
    side = "flip" if flip else "std"
    return f"{delay_label.replace(' ', '_')}_{ss}_{side}"


def build_items(tier: str = "full") -> list[dict[str, Any]]:
    delays = DELAYS if tier == "full" else tuple(x for x in DELAYS if x[0] in SMOKE_DELAYS)
    amounts = AMOUNTS if tier == "full" else SMOKE_AMOUNTS
    items: list[dict[str, Any]] = []
    for delay_label, years in delays:
        for ss in amounts:
            raw = f"{delay_label}|{ss}".encode()
            flip = (int(hashlib.sha256(raw).hexdigest(), 16) % 2) == 1
            later = f"${LL_AMOUNT:.0f} in {delay_label}"
            now = f"${ss} now"
            a, b = (now, later) if flip else (later, now)
            now_letter = "A" if flip else "B"
            later_letter = "B" if flip else "A"
            k_star = implied_k(float(ss), LL_AMOUNT, years)
            items.append(
                {
                    "id": item_id(delay_label, ss, flip),
                    "delay_label": delay_label,
                    "delay_years": years,
                    "ss": int(ss),
                    "ll": int(LL_AMOUNT),
                    "flip": flip,
                    "option_a": a,
                    "option_b": b,
                    "now_letter": now_letter,
                    "later_letter": later_letter,
                    "k_indiff": k_star if math.isfinite(k_star) else None,
                    "k_indiff_inf": not math.isfinite(k_star),
                    "competence_zero": ss == 0,
                    "dominance_now": ss >= int(LL_AMOUNT),
                    "tier": tier,
                }
            )
    return items


def prompt_for(item: Mapping[str, Any]) -> str:
    text = (
        f"{PREMISE}\n\n"
        f"You can either choose:\n"
        f"A. {item['option_a']}\n"
        f"B. {item['option_b']}\n\n"
        f"{FC_SUFFIX}"
    )
    low = text.lower()
    for stem in FORBIDDEN_STEMS:
        if stem.lower() in low:
            raise ValueError(f"DESCRIBE leak in prompt: {stem}")
    return text


def dump_grid(path: Path | None = None) -> Path:
    dest = path or grid_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    full = build_items("full")
    smoke = build_items("smoke")
    payload = {
        "experiment": EXPERIMENT,
        "source": {
            "repo": SOURCE_REPO,
            "commit": SOURCE_SHA,
            "file": "experiments/wait/de_novo.py",
            "design": "Rachlin1991",
            "utility": "U(x,d)=x/(1+k*d)",
            "delay_unit": "years",
        },
        "delays": [{"label": n, "years": y} for n, y in DELAYS],
        "amounts_now": list(AMOUNTS),
        "ll": int(LL_AMOUNT),
        "n_full": len(full),
        "n_smoke": len(smoke),
        "items_full": full,
        "items_smoke": smoke,
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return dest


def load_grid(path: Path | None = None, tier: str = "full") -> list[dict[str, Any]]:
    dest = path or grid_path()
    if not dest.exists():
        dump_grid(dest)
    blob = json.loads(dest.read_text(encoding="utf-8"))
    key = "items_smoke" if tier == "smoke" else "items_full"
    items = blob[key]
    if not items:
        raise ValueError(f"empty grid {key}")
    return items


def parse_letter(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"\b([AB])\b", text.strip().upper())
    if m:
        return m.group(1)
    t = text.strip().upper()
    if t[:1] in ("A", "B"):
        return t[:1]
    return None


def chose_now_from_letter(item: Mapping[str, Any], letter: str | None) -> bool | None:
    if letter not in ("A", "B"):
        return None
    return letter == item["now_letter"]


def _finite_k(k: float) -> float:
    if not math.isfinite(k) or k <= 0:
        return K_CEIL if (not math.isfinite(k) or k > 0) else K_FLOOR
    return float(min(K_CEIL, max(K_FLOOR, k)))


def kirby_k(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Max-consistency hyperbolic k. Always finite (censored to grid bounds)."""
    usable: list[tuple[float, bool]] = []
    n_unparsed = 0
    n_zero_now = 0
    n_zero = 0
    n_dom_later = 0
    n_dom = 0
    for r in rows:
        chose = r.get("chose_now")
        if chose is None:
            n_unparsed += 1
            continue
        if r.get("competence_zero") or int(r.get("ss", -1)) == 0:
            n_zero += 1
            if chose:
                n_zero_now += 1
            continue
        if r.get("dominance_now") or int(r.get("ss", 0)) >= int(LL_AMOUNT):
            n_dom += 1
            if not chose:
                n_dom_later += 1
            continue
        k_star = r.get("k_indiff")
        if k_star is None or not math.isfinite(float(k_star)) or float(k_star) <= 0:
            continue
        usable.append((float(k_star), bool(chose)))

    censored = False
    if not usable:
        k = K_CEIL if n_zero_now > n_zero / 2.0 else K_FLOOR
        censored = True
        return {
            "k": _finite_k(k),
            "n": 0,
            "n_consistent": 0,
            "consistency": 0.0,
            "n_unparsed": n_unparsed,
            "n_zero_prefers_now": n_zero_now,
            "n_zero": n_zero,
            "n_dom_later": n_dom_later,
            "n_dom": n_dom,
            "censored": True,
            "method": "kirby_max_consistency",
        }

    ks = sorted({x[0] for x in usable})
    cands = [ks[0] / math.sqrt(10.0)]
    for a, b in zip(ks, ks[1:]):
        cands.append(math.sqrt(a * b))
    cands.append(ks[-1] * math.sqrt(10.0))

    def _score(k: float) -> tuple[int, float]:
        ok = 0
        for k_star, now in usable:
            pred_now = k > k_star
            if pred_now == now:
                ok += 1
        return ok, -abs(math.log(max(k, K_FLOOR)))

    best_k = max(cands, key=_score)
    n_ok, _ = _score(best_k)
    k_hat = _finite_k(best_k)
    if k_hat in (K_FLOOR, K_CEIL) or best_k < ks[0] / 9.0 or best_k > ks[-1] * 9.0:
        censored = True
    return {
        "k": k_hat,
        "n": len(usable),
        "n_consistent": int(n_ok),
        "consistency": float(n_ok / len(usable)),
        "n_unparsed": n_unparsed,
        "n_zero_prefers_now": n_zero_now,
        "n_zero": n_zero,
        "n_dom_later": n_dom_later,
        "n_dom": n_dom,
        "censored": censored,
        "method": "kirby_max_consistency",
    }


def immediate_equivalents(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Per-delay 50% switch IE (dollars now ~ $1000 later)."""
    by_d: dict[str, list[tuple[int, list[bool]]]] = {}
    for r in rows:
        if r.get("chose_now") is None:
            continue
        lab = str(r["delay_label"])
        ss = int(r["ss"])
        by_d.setdefault(lab, {})
        by_d[lab].setdefault(ss, []).append(bool(r["chose_now"]))  # type: ignore[arg-type]
    ies: dict[str, float] = {}
    for lab, amap in by_d.items():
        amounts = sorted(amap.keys(), reverse=True)
        rates = []
        for ss in amounts:
            ch = amap[ss]
            rates.append((ss, float(sum(ch) / len(ch))))
        ie = 0.0
        for i, (ss, p) in enumerate(rates):
            if p >= 0.5:
                ie = float(ss)
            else:
                if i == 0:
                    ie = float(ss)
                else:
                    ss_hi, p_hi = rates[i - 1]
                    if p_hi == p:
                        ie = 0.5 * (ss_hi + ss)
                    else:
                        w = (0.5 - p) / (p_hi - p)
                        ie = ss + w * (ss_hi - ss)
                break
        ies[lab] = float(max(0.0, min(LL_AMOUNT, ie)))
    return ies


def fit_k_from_ie(ies: Mapping[str, float]) -> dict[str, Any]:
    """1-D NLS: IE(d) = 1000 / (1 + k d). Finite even at corners."""
    pairs: list[tuple[float, float]] = []
    for lab, ie in ies.items():
        pairs.append((delay_years(lab), float(ie)))
    if not pairs:
        return {"k": float("nan"), "rmse": None, "n": 0, "censored": True}
    grid = np.logspace(math.log10(K_FLOOR), math.log10(K_CEIL), 240)

    def rmse(k: float) -> float:
        pred = np.array([LL_AMOUNT / (1.0 + k * d) for d, _ in pairs])
        obs = np.array([ie for _, ie in pairs])
        return float(np.sqrt(np.mean((pred - obs) ** 2)))

    losses = [rmse(float(k)) for k in grid]
    k_hat = float(grid[int(np.argmin(losses))])
    # local refine
    lo = max(K_FLOOR, k_hat / 3.0)
    hi = min(K_CEIL, k_hat * 3.0)
    fine = np.geomspace(lo, hi, 80)
    fine_loss = [rmse(float(k)) for k in fine]
    k_hat = float(fine[int(np.argmin(fine_loss))])
    loss = rmse(k_hat)
    censored = k_hat <= K_FLOOR * 1.01 or k_hat >= K_CEIL * 0.99
    return {
        "k": _finite_k(k_hat),
        "rmse": loss,
        "n": len(pairs),
        "censored": censored,
        "method": "nls_ie",
        "ie": {k: float(v) for k, v in ies.items()},
    }


def monotonic_ie(ies: Mapping[str, float]) -> bool:
    ordered = [ies[n] for n, _ in DELAYS if n in ies]
    if len(ordered) < 2:
        return True
    return all(ordered[i] + 1e-6 >= ordered[i + 1] for i in range(len(ordered) - 1))


def summarize_condition(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    kirby = kirby_k(rows)
    ies = immediate_equivalents(rows)
    nls = fit_k_from_ie(ies) if ies else {"k": kirby["k"], "rmse": None, "n": 0, "censored": True}
    masses = [float(r["fc_mass"]) for r in rows if r.get("fc_mass") is not None]
    parsed = [r for r in rows if r.get("chose_now") is not None]
    p_now = [1.0 if r["chose_now"] else 0.0 for r in parsed]
    return {
        "k": float(kirby["k"]),
        "k_nls": float(nls["k"]) if nls.get("k") is not None and math.isfinite(float(nls.get("k", float("nan")))) else float(kirby["k"]),
        "kirby": kirby,
        "nls": nls,
        "ie": ies,
        "mono_decreasing_ie": monotonic_ie(ies),
        "n_trials": len(rows),
        "n_parsed": len(parsed),
        "parse_rate": float(len(parsed) / len(rows)) if rows else 0.0,
        "fc_mass": float(np.mean(masses)) if masses else 0.0,
        "p_now": float(np.mean(p_now)) if p_now else float("nan"),
        "competence_some_money": (
            (kirby["n_zero"] - kirby["n_zero_prefers_now"]) / kirby["n_zero"]
            if kirby["n_zero"]
            else None
        ),
    }


def gate_block(by_cond: Mapping[str, Mapping[str, Any]], meta: Mapping[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("model_id", meta.get("model_id") == PRIMARY_MODEL, meta.get("model_id"))
    add("weights_nf4", meta.get("weights_dtype") == "nf4", meta.get("weights_dtype"))
    add("compute_bf16", meta.get("compute_dtype") == "bf16", meta.get("compute_dtype"))
    add("split_hash", meta.get("split_hash") == EXPECTED_SPLIT, meta.get("split_hash"))
    add("all_conditions", set(by_cond) == set(CONDITIONS), sorted(by_cond))
    ks = []
    for c in CONDITIONS:
        rec = by_cond.get(c) or {}
        k = rec.get("k")
        finite = isinstance(k, (int, float)) and math.isfinite(float(k)) and float(k) > 0
        ks.append(finite)
        add(f"finite_k_{c}", finite, k)
    add("all_k_finite", all(ks) and len(ks) == len(CONDITIONS))
    masses = [float((by_cond.get(c) or {}).get("fc_mass") or 0.0) for c in CONDITIONS]
    parses = [float((by_cond.get(c) or {}).get("parse_rate") or 0.0) for c in CONDITIONS]
    add("fc_mass_0.8", bool(masses) and float(np.mean(masses)) >= 0.8, float(np.mean(masses) if masses else 0.0))
    add("parse_rate_0.8", bool(parses) and float(np.mean(parses)) >= 0.8, float(np.mean(parses) if parses else 0.0))
    ni = by_cond.get("no-image") or {}
    add("noimage_baseline", bool(ni) and math.isfinite(float(ni.get("k") or float("nan"))), ni.get("k"))
    add("no_v3_write", meta.get("touched_v3") is not True, meta.get("touched_v3"))
    passed = sum(1 for c in checks if c["ok"])
    return {"passed": passed, "total": len(checks), "checks": checks}


def labels_of(row_labels: Any) -> set[str]:
    if isinstance(row_labels, str):
        try:
            import ast

            row_labels = ast.literal_eval(row_labels) if row_labels.startswith("[") else [row_labels]
        except Exception:
            row_labels = [row_labels]
    if not isinstance(row_labels, (list, tuple, set)):
        return set()
    return {str(x) for x in row_labels}


def assign_condition(labels: Iterable[str]) -> str | None:
    have = set(labels)
    rivals = have & RIVAL_LABELS
    if not rivals:
        return "neutral"
    if len(rivals) == 1:
        only = next(iter(rivals))
        for cond, lab in EMOTIC_TARGET.items():
            if lab == only:
                return cond
    return None


def is_eval_exclusive(labels: Iterable[str], cond: str) -> bool:
    have = set(labels)
    if cond == "neutral":
        return not (have & RIVAL_LABELS)
    target = EMOTIC_TARGET[cond]
    return target in have and (have & RIVAL_LABELS) == {target}


__all__ = [
    "AMOUNTS",
    "CONDITIONS",
    "DELAYS",
    "EXPECTED_SPLIT",
    "EXPERIMENT",
    "PRIMARY_MODEL",
    "assign_condition",
    "build_items",
    "chose_now_from_letter",
    "dump_grid",
    "fit_k_from_ie",
    "gate_block",
    "implied_k",
    "immediate_equivalents",
    "is_eval_exclusive",
    "kirby_k",
    "labels_of",
    "load_grid",
    "parse_letter",
    "prompt_for",
    "summarize_condition",
]
