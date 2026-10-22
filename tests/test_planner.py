import json
import math

import numpy as np
import pytest

from concord.planner import LABEL, plan


def noisy(technique, x, y, composition=None, seed=0, **conditions):
    rng = np.random.default_rng(seed)
    return np.asarray(y) + 0.05 * np.sqrt(np.mean(np.asarray(y) ** 2)) * rng.normal(size=len(y))


@pytest.fixture(scope="module")
def pt3co():
    return plan("Pt3Co", ["Pt", "Pt3Co", "PtNi"])


def test_pt3co_plan_is_labelled_ranked_and_json_safe(pt3co):
    assert len(pt3co["candidates"]) >= 2 and pt3co["label"] == LABEL
    assert pt3co["ranking"] and set(pt3co["ranking"]) <= {"xrd", "pdf", "exafs"}
    assert pt3co["recommendation"] and not {"–", "—"} & set(pt3co["recommendation"])
    assert all(len(c) <= 600 for t in pt3co["techniques"].values() for c in t["curves"].values())
    json.dumps(pt3co)


def test_xrd_separates_pt_from_pt3co(pt3co):
    pair = next(p for p in pt3co["techniques"]["xrd"]["pairs"] if {p["a"], p["b"]} == {"Pt", "Pt3Co"})
    assert pair["separation"] > 0


def test_unknown_candidate_raises():
    with pytest.raises(ValueError, match="Pt3Co"):
        plan("Pt3Co", ["Pt", "Unobtainium"])


def test_over_noise_only_with_realism(pt3co):
    real = plan("Pt3Co", ["Pt", "Pt3Co"], techniques=("xrd", "pdf"), realism=noisy)
    assert all(math.isfinite(p["over_noise"]) for t in real["techniques"].values() for p in t["pairs"])
    assert real["techniques"]["xrd"]["realistic"]["Pt"]
    assert all(p["over_noise"] is None for t in pt3co["techniques"].values() for p in t["pairs"])
