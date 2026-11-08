"""Figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def model_heatmaps(scores: pd.DataFrame, path: Path, note: str | None = None) -> None:
    """Side-by-side heatmaps: direct damage vs network disconnection, model x circuit."""
    metrics = [("direct_damage", "Direct damage"), ("network_disconnection", "Network disconnection")]
    models = list(dict.fromkeys(scores["model"]))
    circuits = list(dict.fromkeys(scores["circuit"]))
    vmax = max(scores[m].max() for m, _ in metrics) or 1.0
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True, constrained_layout=True)
    for ax, (col, title) in zip(axes, metrics):
        M = scores.pivot(index="model", columns="circuit", values=col).loc[models, circuits]
        im = ax.imshow(M.values, cmap="Reds", vmin=0, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(circuits)), [c.replace(" (", "\n(") for c in circuits], fontsize=8)
        ax.set_yticks(range(len(models)), models)
        ax.set_title(title)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9,
                        color="white" if v > 0.6 * vmax else "black")
    fig.colorbar(im, ax=axes, shrink=0.8, label="fraction")
    if note:
        fig.suptitle(note, fontsize=8, color="0.4")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def deficit_strip(df: pd.DataFrame, path: Path, note: str | None = None) -> None:
    """Score by whether the study reported a cognitive deficit."""
    cols = [("cognitive_score", "Cognitive circuit score"), ("motor_score", "Motor circuit score (control)")]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.6), sharey=True, constrained_layout=True)
    rng = np.random.default_rng(0)
    for ax, (col, title) in zip(axes, cols):
        for x, grp in enumerate([0, 1]):
            y = df.loc[df.deficit == grp, col]
            ax.scatter(x + rng.uniform(-0.08, 0.08, len(y)), y, s=30, alpha=0.8,
                       color=["0.55", "#c0392b"][grp])
            if len(y):
                ax.hlines(y.median(), x - 0.2, x + 0.2, color="k", lw=2)
        ax.set_xticks([0, 1], ["No deficit", "Deficit"])
        ax.set_xlim(-0.5, 1.5)
        ax.set_title(title, fontsize=10)
    axes[0].set_ylabel("direct damage + network disconnection")
    if note:
        fig.suptitle(note, fontsize=8, color="0.4")
    fig.savefig(path, dpi=150)
    plt.close(fig)
