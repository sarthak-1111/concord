"""concord.tweak on saved analyses: settings per technique, quick re-fits, and the full re-analysis with user settings."""
import json
from pathlib import Path

import pytest

from concord import tweak

ROOT = Path(__file__).resolve().parent.parent
SAMPLE, FAST = "s0019", "s0017"  # Pt3Co with every check passing; CeO2, one candidate (a full analysis in seconds)
KEYS = {"name", "label", "kind", "value", "default", "min", "max", "step", "choices", "unit", "help"}


def saved_run(sid: str) -> dict:
    path = ROOT / "results" / "runs" / f"{sid}.json"
    if not path.exists():
        pytest.skip(f"{sid} has not been analysed")
    return json.loads(path.read_text())


def statuses(checks: list[dict]) -> dict:
    return {c["id"]: c["status"] for c in checks}


@pytest.fixture(scope="module")
def saved() -> dict:
    return saved_run(SAMPLE)


def test_params_are_well_formed_and_match_the_analysis(saved):
    for tech in ("xrd", "pdf", "exafs"):
        ps = tweak.params(saved, tech)
        assert ps and len({p["name"] for p in ps}) == len(ps)
        for p in ps:
            assert set(p) == KEYS and p["kind"] in ("float", "int", "bool", "choice")
            assert p["help"].endswith(".") and "—" not in p["help"] and "–" not in p["help"]
            if p["kind"] == "choice":
                assert p["value"] in p["choices"] and p["default"] in p["choices"]
            elif p["kind"] != "bool":
                assert p["min"] <= p["value"] <= p["max"] and p["min"] <= p["default"] <= p["max"] and p["step"] > 0
    best, window, tt = saved["pdf"]["fits"][0], saved["exafs"]["fit"]["window"], saved["xrd"]["curves"]["two_theta"]
    value = lambda tech: {p["name"]: p["value"] for p in tweak.params(saved, tech)}
    assert value("pdf") == {"candidate": best["candidate"], "rmin": best["r_range"][0], "rmax": best["r_range"][1],
                            "qdamp": best["qdamp"], "envelope": best["psize_nm"] is not None}
    assert {k: value("exafs")[k] for k in window} == window
    assert (value("xrd")["two_theta_min"], value("xrd")["two_theta_max"]) == (tt[0], tt[-1])
    assert tweak.params(saved, "xanes") == []


@pytest.mark.slow
@pytest.mark.parametrize("tech, metric", [("xrd", "sphere_diameter_nm"), ("pdf", "rw"), ("exafs", "rfactor")])
def test_refit_with_own_values_reproduces_the_fit_and_checks(saved, tech, metric):
    own = {p["name"]: p["value"] for p in tweak.params(saved, tech)}
    r = tweak.refit(ROOT / "dataset" / "samples" / SAMPLE, saved, tech, own)
    want = {"xrd": saved["xrd"]["sphere_diameter_nm"], "pdf": saved["pdf"]["fits"][0]["rw"], "exafs": saved["exafs"]["fit"]["rfactor"]}
    assert r["metrics"][metric] == pytest.approx(want[tech], rel=1e-6)
    assert r["values"] == own and statuses(r["checks"]) == statuses(saved["checks"]) and r["changed"] == []
    c = r["curve"]
    assert 0 < len(c["x"]) == len(c["obs"]) == len(c["calc"]) == len(c["diff"]) <= tweak.MAX_POINTS
    assert json.loads(json.dumps(r, allow_nan=False)) == r


@pytest.mark.slow
def test_refit_pdf_with_another_candidate_reports_the_check_changes(saved):
    r = tweak.refit(ROOT / "dataset" / "samples" / SAMPLE, saved, "pdf", {"candidate": "Pt"})
    assert r["metrics"]["candidate"] == "Pt" and abs(r["metrics"]["rw"] - saved["pdf"]["fits"][0]["rw"]) > 0.01
    before = statuses(saved["checks"])
    assert r["changed"] == [{"id": c["id"], "from": before[c["id"]], "to": c["status"]} for c in r["checks"] if c["status"] != before[c["id"]]]
    assert {"id": "C1", "from": "pass", "to": "fail"} in r["changed"]  # XRD still prefers Pt3Co


@pytest.mark.parametrize("tech, values", [("pdf", {"rmax": 400.0}), ("pdf", {"rmin": 4.0, "rmax": 8.0}), ("pdf", {"candidate": "Au"}),
                                          ("exafs", {"kweight": 7}), ("exafs", {"probe": True}), ("xrd", {"peak_height": "high"}),
                                          ("xrd", {"background": 1.0}), ("xanes", {})])
def test_bad_values_raise(saved, tech, values):
    with pytest.raises(ValueError):
        tweak.refit(ROOT / "dataset" / "samples" / SAMPLE, saved, tech, values)
    if values:
        with pytest.raises(ValueError):
            tweak.apply(ROOT / "dataset" / "samples" / SAMPLE, saved, {tech: values})


@pytest.mark.slow
def test_apply_without_overrides_matches_the_saved_analysis_and_records_settings():
    a = saved_run(FAST)
    folder = ROOT / "dataset" / "samples" / FAST
    plain = tweak.apply(folder, a, {})
    assert statuses(plain["checks"]) == statuses(a["checks"]) and "user_settings" not in plain["inputs"]
    kept = tweak.apply(folder, a, {"exafs": {"kmax": 9}})
    assert kept["inputs"]["user_settings"] == {"exafs": {"kmax": 9.0}} and kept["exafs"]["fit"]["window"]["kmax"] == 9.0
    assert {p["name"]: p["value"] for p in tweak.params(kept, "exafs")}["kmax"] == 9.0
