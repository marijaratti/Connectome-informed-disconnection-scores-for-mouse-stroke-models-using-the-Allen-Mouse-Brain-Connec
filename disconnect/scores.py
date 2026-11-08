"""Core scoring: how much of a circuit is damaged, directly and through its connections.

Notation
--------
W      region x region connection strengths (rows = source, columns = target),
       diagonal ignored.
f      lesion vector: fraction of each region damaged (0 = intact, 1 = destroyed).
C      the set of regions that make up a functional circuit.

direct_damage(C)         = mean of f over the regions in C
network_disconnection(C) = sum_j s_j * f_j / sum_j s_j,  over regions j outside C,
                           where s_j = sum_{i in C} (W[j, i] + W[i, j])
                           is region j's total input to and output from the circuit.

So network disconnection is the share of the circuit's external wiring that runs to or
from damaged tissue, weighted by how badly each partner region is damaged.
"""
from __future__ import annotations

from typing import Iterable, Mapping

import numpy as np
import pandas as pd


def prepare_connectome(W: pd.DataFrame) -> pd.DataFrame:
    """Return a float copy of W with self-connections removed."""
    arr = W.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(arr, 0.0)
    W = pd.DataFrame(arr, index=W.index, columns=W.columns)
    if (W.values < 0).any():
        raise ValueError("Connection strengths must be non-negative.")
    return W


def check_regions(W: pd.DataFrame, regions: Iterable[str], what: str = "region") -> None:
    missing = [r for r in regions if r not in W.index]
    if missing:
        raise KeyError(f"{what} not found in connectome: {', '.join(missing)}")


def lesion_vector(W: pd.DataFrame, lesion: Mapping[str, float]) -> pd.Series:
    """Fraction damaged for every region in W (unlisted regions are 0)."""
    check_regions(W, lesion, "Lesioned region")
    f = pd.Series(0.0, index=W.index)
    for region, frac in lesion.items():
        if not 0.0 <= float(frac) <= 1.0:
            raise ValueError(f"Lesion fraction for {region} must be between 0 and 1, got {frac}")
        f[region] = float(frac)
    return f


def _partner_strength(W: pd.DataFrame, circuit: list[str]) -> pd.Series:
    others = [r for r in W.index if r not in circuit]
    return W.loc[others, circuit].sum(axis=1) + W.loc[circuit, others].sum(axis=0)


def circuit_scores(W: pd.DataFrame, f: pd.Series, circuit: Iterable[str]) -> tuple[float, float]:
    """(direct_damage, network_disconnection) for one circuit."""
    circuit = list(circuit)
    check_regions(W, circuit, "Circuit region")
    direct = float(f[circuit].mean())
    s = _partner_strength(W, circuit)
    total = s.sum()
    network = float((s * f[s.index]).sum() / total) if total > 0 else 0.0
    return direct, network


def region_contributions(W: pd.DataFrame, lesion: Mapping[str, float],
                         circuit: Iterable[str], top: int | None = None) -> pd.Series:
    """How much each lesioned region outside the circuit adds to its disconnection.

    contribution_j = f_j * s_j  (unnormalised; divide by sum(s) for the share).
    """
    circuit = list(circuit)
    s = _partner_strength(W, circuit)
    contrib = pd.Series({r: float(v) * s[r] for r, v in lesion.items() if r not in circuit},
                        dtype=float).sort_values(ascending=False)
    return contrib.head(top) if top else contrib
