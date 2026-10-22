import copy
import json

import numpy as np
import pytest

from concord import generate
from concord.config import ROOT

SAVED = ROOT / "results" / "runs" / "s0019.json"  # Pt3Co, all techniques


@pytest.fixture(scope="module")
def xrd_only():
    if not SAVED.exists():
        pytest.skip("needs the saved analysis of s0019")
    res = json.loads(SAVED.read_text())
    res = copy.deepcopy(res)
    res["inputs"]["techniques"], res["pdf"] = ["xrd"], None
    return res


def test_the_missing_techniques_are_generated_from_the_xrd_model_and_labelled(xrd_only):
    out = generate.generate(xrd_only)
    assert out["label"] == "GENERATED, NOT MEASURED" and set(out["techniques"]) == {"pdf", "exafs"}
    assert out["from"]["phase"] == xrd_only["phase"] and "XRD" in out["from"]["source"]
    g = out["techniques"]["pdf"]
    assert len(g["x"]) == len(g["clean"]) and np.ptp(g["clean"]) > 0 and g["realistic"] is None


def test_realism_is_applied_when_given_and_a_failing_technique_is_noted_not_faked(xrd_only):
    def realism(tech, x, y, composition, seed, **cond):
        if tech == "exafs":
            raise ValueError("edge not covered")
        return np.asarray(y) + 0.01
    out = generate.generate(xrd_only, realism=realism)
    assert out["techniques"]["pdf"]["realistic"] is not None and out["techniques"]["exafs"]["realistic"] is None
    assert any("EXAFS" in n for n in out["notes"])


def test_no_phase_or_nothing_missing_is_refused(xrd_only):
    with pytest.raises(ValueError, match="no phase"):
        generate.generate({**xrd_only, "phase": None})
    full = json.loads(SAVED.read_text())
    with pytest.raises(ValueError, match="nothing to generate"):
        generate.generate(full)
