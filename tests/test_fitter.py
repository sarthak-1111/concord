"""Fitting agents: the guardrails in code, and the keep-or-revert loop with the LLM replaced by scripted decisions."""
import json
from types import SimpleNamespace

import pytest

from concord.agents import fitter
from concord.config import ROOT

SID = "s0019"
FOLDER, SAVED = ROOT / "dataset" / "samples" / SID, ROOT / "results" / "runs" / f"{SID}.json"
need = pytest.mark.skipif(not SAVED.exists(), reason="needs the saved analysis of s0019")


def test_values_are_clipped_and_checked():
    p = {"name": "rmax", "kind": "float", "min": 8.0, "max": 40.0, "choices": None}
    assert fitter._value(p, "99") == 40.0
    assert fitter._value({"name": "w", "kind": "int", "min": 5, "max": 51, "choices": None}, "7.6") == 8
    assert fitter._value({"name": "envelope", "kind": "bool", "min": None, "max": None, "choices": None}, "false") is False
    with pytest.raises(ValueError):
        fitter._value({"name": "candidate", "kind": "choice", "min": None, "max": None, "choices": ["Pt", "Pt3Co"]}, "Au")


def test_window_may_not_shrink_much():
    spec = [{"name": "rmin", "default": 1.5}, {"name": "rmax", "default": 25.0}]
    fitter._window("pdf", spec, {"rmin": 1.5, "rmax": 20.0})
    with pytest.raises(ValueError):
        fitter._window("pdf", spec, {"rmin": 1.5, "rmax": 12.0})


class Scripted:
    def __init__(self, decisions):
        self.decisions = list(decisions)

    def chat(self, role, msgs, schema=None):
        assert role == "fitter" and json.loads(msgs[1]["content"])["settings"]
        return SimpleNamespace(data=schema(**self.decisions.pop(0)))


@need
def test_worse_candidate_is_reverted_and_bad_request_reported(monkeypatch):
    llm = Scripted([
        {"action": "try", "changes": [{"name": "candidate", "value": "Pt"}], "reason": "try the runner-up"},
        {"action": "try", "changes": [{"name": "qdamp", "value": "0.05"}], "reason": "not allowed"},
        {"action": "accept", "reason": "Pt3Co fits best"}])
    monkeypatch.setattr(fitter, "shared_client", lambda: llm)
    f = fitter.fit(FOLDER, json.loads(SAVED.read_text()), "pdf")
    assert f["metric"] == "rw" and f["start"] == pytest.approx(f["end"])
    assert f["steps"][0]["changes"] == {"candidate": "Pt"} and not f["steps"][0]["kept"] and f["steps"][0]["metric"] > f["start"]
    assert f["steps"][1]["error"] and not f["steps"][1]["kept"]  # qdamp is the instrument's: never fitted by an agent
    assert f["values"] == {} and f["verdict"] == "Pt3Co fits best"
