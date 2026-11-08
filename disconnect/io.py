"""Loading connectome matrices and JSON configs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .scores import prepare_connectome

PACKAGE_DIR = Path(__file__).resolve().parent
DEMO_CONNECTOME = PACKAGE_DIR / "data" / "demo_connectome_ipsi.csv"


def load_connectome(path: str | Path) -> pd.DataFrame:
    """Read a square region x region CSV with region acronyms as row and column labels.

    Tolerates stray whitespace in labels and drops any non-numeric extra columns
    (e.g. a 'major division' column left over from a spreadsheet export).
    """
    W = pd.read_csv(path, index_col=0)
    W.index = W.index.astype(str).str.strip()
    W.columns = W.columns.astype(str).str.strip()
    W = W.apply(pd.to_numeric, errors="coerce")
    W = W.loc[:, W.notna().any(axis=0)].dropna(how="all")
    common = [r for r in W.index if r in W.columns]
    if not common:
        raise ValueError(f"{path}: row labels and column labels share no region names.")
    if len(common) < max(len(W.index), len(W.columns)):
        W = W.loc[common, common]
    W = W.fillna(0.0)
    return prepare_connectome(W)


def load_json(path: str | Path) -> dict:
    with open(path) as fh:
        return json.load(fh)
