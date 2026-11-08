"""A small synthetic mouse 'connectome' so the code runs without downloading anything.

It uses real Allen Reference Atlas acronyms and loosely follows known anatomy
(dense within-system wiring plus a few textbook pathways), but the numbers are random.
Do not interpret results computed on it. For real analyses use the Oh et al. (2014)
matrices; see the README.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SYSTEMS = {
    "somatomotor": ["MOp", "MOs", "SSp-bfd", "SSp-ul", "SSp-ll", "SSp-tr", "SSp-n", "SSp-m", "SSs"],
    "assoc_cortex": ["PTLp", "AId", "AIp", "GU", "AUDp", "AUDd", "TEa", "VISp", "ACAd", "ORBl"],
    "prefrontal": ["PL", "ILA"],
    "hippocampal": ["CA1", "CA3", "DG", "SUBd", "SUBv", "PRE", "POST", "PAR"],
    "entorhinal": ["ENTl", "ENTm"],
    "parahippocampal": ["PERI", "ECT"],
    "retrosplenial": ["RSPagl", "RSPd", "RSPv"],
    "striatum": ["CP", "ACB"],
    "thalamus": ["VAL", "VPM", "VPL", "LD", "AV", "MD"],
}

# (sources, targets, strength) pathways added on top of the random background
PATHWAYS = [
    (["VPM", "VPL"], ["SSp-bfd", "SSp-ul", "SSp-ll", "SSp-tr", "SSp-n", "SSp-m", "SSs"], 2.0),
    (["SSp-bfd", "SSp-ul", "SSp-ll", "SSs", "MOp", "MOs"], ["CP"], 2.0),
    (["VAL"], ["MOp", "MOs"], 2.0),
    (["AV", "LD"], ["RSPagl", "RSPd", "RSPv", "PRE", "POST"], 1.5),
    (["ENTl", "ENTm"], ["DG", "CA3", "CA1", "SUBd"], 2.0),
    (["CA1", "SUBd", "SUBv"], ["ENTl", "ENTm"], 1.5),
    (["PERI", "ECT"], ["ENTl"], 1.5),
    (["TEa", "AUDd", "AIp"], ["ECT", "PERI"], 1.0),
    (["CA1", "SUBv"], ["PL", "ILA"], 1.0),
    (["RSPagl", "RSPd", "PTLp"], ["POST", "PRE", "ENTm"], 1.0),
    (["PL", "ILA", "AId"], ["MD", "ACB"], 1.0),
]


def make_demo_connectome(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regions = [r for rs in SYSTEMS.values() for r in rs]
    system = {r: s for s, rs in SYSTEMS.items() for r in rs}
    n = len(regions)
    same = np.array([[system[a] == system[b] for b in regions] for a in regions])
    p = np.where(same, 0.6, 0.12)
    W = (rng.random((n, n)) < p) * rng.lognormal(mean=-2.5, sigma=1.0, size=(n, n))
    W = W * np.where(same, 3.0, 1.0)
    idx = {r: i for i, r in enumerate(regions)}
    for sources, targets, strength in PATHWAYS:
        for s in sources:
            for t in targets:
                W[idx[s], idx[t]] += strength * rng.lognormal(-1.5, 0.4)
    np.fill_diagonal(W, 0.0)
    return pd.DataFrame(W.round(5), index=regions, columns=regions)


if __name__ == "__main__":  # regenerate the bundled CSV
    from .io import DEMO_CONNECTOME
    DEMO_CONNECTOME.parent.mkdir(parents=True, exist_ok=True)
    make_demo_connectome().to_csv(DEMO_CONNECTOME)
    print(f"wrote {DEMO_CONNECTOME}")
