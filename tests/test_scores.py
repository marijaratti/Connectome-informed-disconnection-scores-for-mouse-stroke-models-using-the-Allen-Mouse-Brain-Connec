import json

import numpy as np
import pandas as pd
import pytest

from disconnect.__main__ import main
from disconnect.analyses import score_models, score_studies
from disconnect.io import DEMO_CONNECTOME, load_connectome, load_json
from disconnect.scores import circuit_scores, lesion_vector, prepare_connectome

REGIONS = ["A", "B", "C", "D"]


@pytest.fixture
def W():
    # A and B form the circuit. C connects to it with strength 3 in total, D with strength 1.
    m = np.zeros((4, 4))
    m[0, 1] = m[1, 0] = 5     # within the circuit (not part of the network score)
    m[2, 0] = 2; m[1, 2] = 1  # C <-> circuit: 3
    m[3, 1] = 1               # D -> circuit: 1
    m[0, 0] = 9               # self-connection, must be ignored
    return prepare_connectome(pd.DataFrame(m, index=REGIONS, columns=REGIONS))


def test_hand_calculation(W):
    f = lesion_vector(W, {"C": 1.0, "A": 0.5})
    direct, network = circuit_scores(W, f, ["A", "B"])
    assert direct == pytest.approx(0.25)    # mean(0.5, 0)
    assert network == pytest.approx(3 / 4)  # C carries 3 of the 4 units of external wiring


def test_partial_lesion_scales(W):
    f = lesion_vector(W, {"D": 0.5})
    assert circuit_scores(W, f, ["A", "B"])[1] == pytest.approx(0.5 * 1 / 4)


def test_no_lesion_is_zero(W):
    assert circuit_scores(W, lesion_vector(W, {}), ["A", "B"]) == (0.0, 0.0)


def test_bad_inputs(W):
    with pytest.raises(KeyError):
        lesion_vector(W, {"Z": 0.3})
    with pytest.raises(ValueError):
        lesion_vector(W, {"C": 1.5})


def test_loader_tolerates_messy_csv(tmp_path):
    df = pd.DataFrame(np.ones((3, 3)), index=[" A", "B", "C "], columns=["A ", "B", " C"])
    df["division"] = "Isocortex"
    p = tmp_path / "w.csv"
    df.to_csv(p)
    W = load_connectome(p)
    assert list(W.index) == ["A", "B", "C"] and list(W.columns) == ["A", "B", "C"]
    assert np.diag(W.values).sum() == 0


def test_demo_runs_end_to_end(tmp_path):
    W = load_connectome(DEMO_CONNECTOME)
    scores, contrib = score_models(W, load_json("configs/brezzo_models.json"))
    assert len(scores) == 9
    assert scores[["direct_damage", "network_disconnection"]].le(1).all().all()
    df = score_studies(W, load_json("examples/study_coding_example.json"))
    assert {"cognitive_score", "motor_score"} <= set(df.columns)
    main(["models", "--out", str(tmp_path / "m")])
    main(["studies", "--out", str(tmp_path / "s")])
    assert (tmp_path / "m" / "model_scores.png").exists()
    assert json.loads((tmp_path / "m" / "top_contributors.json").read_text())["top_contributors"]
