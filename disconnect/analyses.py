"""The two analyses: three Brezzo et al. stroke models, and a multi-study comparison."""
from __future__ import annotations

import pandas as pd
from scipy import stats

from .scores import check_regions, circuit_scores, lesion_vector, region_contributions


def score_models(W: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, dict]:
    """Direct damage and network disconnection for every stroke model x circuit.

    Returns the long-format score table and, for one circuit, the top lesioned regions
    driving its disconnection in each model.
    """
    lesions, circuits = config["lesions"], config["circuits"]
    for c in circuits.values():
        check_regions(W, c, "Circuit region")
    rows = []
    for model, les in lesions.items():
        f = lesion_vector(W, les)
        for cname, circ in circuits.items():
            direct, network = circuit_scores(W, f, circ)
            rows.append({"model": model, "circuit": cname,
                         "direct_damage": direct, "network_disconnection": network})
    scores = pd.DataFrame(rows)

    target = config.get("contributors_circuit", next(iter(circuits)))
    contributors = {
        model: {r: round(float(v), 4) for r, v in
                region_contributions(W, les, circuits[target], top=4).items()}
        for model, les in lesions.items()
    }
    return scores, {"circuit": target, "top_contributors": contributors}


def score_studies(W: pd.DataFrame, coding: dict) -> pd.DataFrame:
    """Score each coded study on its tested circuit and on the motor circuit."""
    levels = coding["coding_rules"]
    circuits = coding["circuits"]
    if "motor" not in circuits:
        raise KeyError("study coding must define a 'motor' circuit (used as a control).")
    rows = []
    for s in coding["studies"]:
        try:
            les = {r: levels[lvl] for r, lvl in s["lesion"].items()}
        except KeyError as e:
            raise KeyError(f"study {s['id']}: unknown lesion level {e}; "
                           f"use one of {sorted(levels)}") from None
        f = lesion_vector(W, les)
        d, n = circuit_scores(W, f, circuits[s["circuit"]])
        md, mn = circuit_scores(W, f, circuits["motor"])
        rows.append({"id": s["id"], "paper": s["paper"], "model": s["model"], "test": s["test"],
                     "circuit": s["circuit"], "deficit": int(s["deficit"]),
                     "direct_damage": d, "network_disconnection": n,
                     "cognitive_score": d + n, "motor_score": md + mn})
    return pd.DataFrame(rows)


def compare_deficit_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Do studies that found a cognitive deficit have higher scores than those that did not?

    Mann-Whitney U (two-sided) and point-biserial correlation for each score, plus the
    same test using one row per paper to reduce non-independence.
    """
    rows = []
    for label, data in [("all rows", df), ("one row per paper", df.groupby("paper", sort=False).head(1))]:
        for col in ["cognitive_score", "network_disconnection", "direct_damage", "motor_score"]:
            a = data.loc[data.deficit == 1, col]
            b = data.loc[data.deficit == 0, col]
            row = {"sample": label, "score": col, "n_deficit": len(a), "n_no_deficit": len(b),
                   "mean_deficit": a.mean(), "mean_no_deficit": b.mean(),
                   "mwu_p": float("nan"), "r_pointbiserial": float("nan")}
            if len(a) and len(b):
                row["mwu_p"] = stats.mannwhitneyu(a, b, alternative="two-sided").pvalue
                if data[col].nunique() > 1:
                    row["r_pointbiserial"] = stats.pointbiserialr(data.deficit, data[col]).statistic
            rows.append(row)
    return pd.DataFrame(rows)
