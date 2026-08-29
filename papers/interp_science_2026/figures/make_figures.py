"""Build NeurIPS figures from locked JSON. No invented numbers."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PEEK = ROOT / "artifacts" / "battery_v2" / "peek"
V3 = ROOT / "artifacts" / "colab" / "e2e_mechanism_results_full_v3.json"
OUT = Path(__file__).resolve().parent

ARMS = [
    "no_image",
    "neutral",
    "fear",
    "anger",
    "sadness",
    "excitement",
    "happiness",
    "peace",
]
LABELS = ["none", "neu", "fear", "ang", "sad", "exc", "hap", "peace"]


def _load_primary(name: str) -> dict:
    return json.loads((PEEK / name).read_text(encoding="utf-8"))["primary"]


def fig_exp09() -> None:
    e4b = _load_primary("e4b_emotic_exp09_results.json")
    g12 = _load_primary("g12_emotic_exp09_results.json")
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.55), sharey=False)
    for ax, data, title in (
        (axes[0], e4b, "Gemma-4-E4B-it (encoder)"),
        (axes[1], g12, "Gemma-4-12B-it (unified)"),
    ):
        means = [data[a]["refuse_rate"] for a in ARMS]
        lo = [data[a]["refuse_rate"] - data[a]["ci_lo"] for a in ARMS]
        hi = [data[a]["ci_hi"] - data[a]["refuse_rate"] for a in ARMS]
        colors = ["#4d4d4d"] + ["#6b8cae"] * 7
        x = np.arange(len(ARMS))
        ax.bar(x, means, color=colors, width=0.72, zorder=2)
        ax.errorbar(x, means, yerr=[lo, hi], fmt="none", ecolor="black", elinewidth=0.8, capsize=2, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(LABELS, rotation=40, ha="right", fontsize=7)
        ax.set_title(title, fontsize=9)
        ax.set_ylabel("full-answer refuse", fontsize=8)
        ax.set_ylim(0, 0.72)
        ax.axhline(means[0], color="#4d4d4d", lw=0.6, ls=":", zorder=1)
        ax.tick_params(labelsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_exp09.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_exp09.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_layers() -> None:
    v3 = json.loads(V3.read_text(encoding="utf-8"))
    desc = np.array(v3["phases"]["phase2"]["layer_delta_desc_a"], dtype=float)
    harm = np.array(v3["phases"]["phase2"]["layer_delta_harm_a"], dtype=float)
    win = list(range(10, 25))
    x = np.arange(len(desc))
    fig, ax = plt.subplots(figsize=(6.6, 2.35))
    ax.axvspan(9.5, 24.5, color="#d9e2ec", zorder=0)
    ax.plot(x, desc, color="#1f4e79", lw=1.4, label=r"$\Delta$ DESCRIBE")
    ax.plot(x, harm, color="#8b2e2e", lw=1.4, label=r"$\Delta$ harmful")
    ax.set_xlabel("layer", fontsize=8)
    ax.set_ylabel(r"neg$-$neu projection on $a_\perp$", fontsize=8)
    ax.set_xlim(0, 41)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.tick_params(labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(17, max(desc) * 0.12, "gate $[10,25)$", fontsize=7, color="#1f4e79")
    fig.tight_layout()
    fig.savefig(OUT / "fig_layers.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig_layers.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    _ = win


if __name__ == "__main__":
    fig_exp09()
    fig_layers()
    print("wrote", OUT / "fig_exp09.pdf", OUT / "fig_layers.pdf")
