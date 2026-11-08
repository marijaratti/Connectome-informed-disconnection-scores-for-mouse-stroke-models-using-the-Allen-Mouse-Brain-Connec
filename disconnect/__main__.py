"""Command-line interface.

    python -m disconnect models  [--w-ipsi W.csv] [--config configs/brezzo_models.json] [--out results/models]
    python -m disconnect studies [--w-ipsi W.csv] --coding study_coding.json [--out results/studies]

Without --w-ipsi the bundled synthetic demo connectome is used (results are not meaningful).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .analyses import compare_deficit_groups, score_models, score_studies
from .io import DEMO_CONNECTOME, load_connectome, load_json
from .plots import deficit_strip, model_heatmaps

REPO = Path(__file__).resolve().parent.parent
DEMO_NOTE = "DEMO: synthetic connectome, numbers are not meaningful"


def _connectome(args) -> tuple[pd.DataFrame, str | None]:
    if args.w_ipsi:
        return load_connectome(args.w_ipsi), None
    print(f"No --w-ipsi given: using the synthetic demo connectome ({DEMO_CONNECTOME.name}).")
    print("Results are for testing the pipeline only.\n")
    return load_connectome(DEMO_CONNECTOME), DEMO_NOTE


def run_models(args) -> None:
    W, note = _connectome(args)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    scores, contrib = score_models(W, load_json(args.config))
    scores.round(4).to_csv(out / "model_scores.csv", index=False)
    (out / "top_contributors.json").write_text(json.dumps(contrib, indent=2))
    model_heatmaps(scores, out / "model_scores.png", note)
    pd.set_option("display.width", 200)
    print("Network disconnection (share of circuit wiring touching damaged tissue)")
    print(scores.pivot(index="model", columns="circuit", values="network_disconnection").round(3), "\n")
    print("Direct damage (mean fraction of circuit regions damaged)")
    print(scores.pivot(index="model", columns="circuit", values="direct_damage").round(3), "\n")
    print(f"Top lesioned regions driving '{contrib['circuit']}' disconnection:")
    print(json.dumps(contrib["top_contributors"], indent=1))
    print(f"\nWrote {out}/model_scores.csv, top_contributors.json, model_scores.png")


def run_studies(args) -> None:
    W, note = _connectome(args)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df = score_studies(W, load_json(args.coding))
    tests = compare_deficit_groups(df)
    df.round(4).to_csv(out / "study_scores.csv", index=False)
    tests.round(4).to_csv(out / "deficit_tests.csv", index=False)
    deficit_strip(df, out / "study_scores.png", note)
    pd.set_option("display.width", 200)
    print(df[["id", "paper", "deficit", "direct_damage", "network_disconnection",
              "cognitive_score", "motor_score"]].round(3).to_string(index=False), "\n")
    print(tests.round(3).to_string(index=False))
    print(f"\nWrote {out}/study_scores.csv, deficit_tests.csv, study_scores.png")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m disconnect",
                                description="Connectome-informed disconnection scores for mouse stroke models.")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("models", help="score stroke models against functional circuits")
    m.add_argument("--w-ipsi", help="ipsilateral connectome CSV (default: synthetic demo)")
    m.add_argument("--config", default=str(REPO / "configs" / "brezzo_models.json"))
    m.add_argument("--out", default="results/models")
    m.set_defaults(func=run_models)

    s = sub.add_parser("studies", help="score coded studies and compare deficit vs no-deficit")
    s.add_argument("--w-ipsi", help="ipsilateral connectome CSV (default: synthetic demo)")
    s.add_argument("--coding", default=str(REPO / "examples" / "study_coding_example.json"))
    s.add_argument("--out", default="results/studies")
    s.set_defaults(func=run_studies)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
