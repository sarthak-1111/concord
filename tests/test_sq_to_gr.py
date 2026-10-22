import json
import time
from pathlib import Path

import numpy as np
import pytest

from concord.analysis import infer_inputs
from concord.tools import pdf as pdft
from concord.tools.sq_to_gr import load_raw, reduce, write_gr

SAMPLES = Path(__file__).resolve().parent.parent / "dataset" / "samples"
pytestmark = pytest.mark.skipif(not (SAMPLES / "s0000" / "pdf_iq.dat").exists(), reason="run scripts/make_raw_pdf.py")
RW_MAX = 0.03  # measured 0.006-0.023 on these samples; bulk is highest (pdf.gr transforms from Q = 0 within a 38 Å window)
# composition in the beam: oxide sphere cuts keep every cation's anions, so small particles are O-rich (the nominal
# TiO2 and Co3O4 give Rw 0.085 and 0.15, a real normalisation error, not a reduction one)
ROUND_TRIP = {"s0000": None, "s0004": None, "s0005": None, "s0007": None, "s0009": None, "s0020": None,
              "s0032": "O474Ti176", "s0025": "Co99O212"}


def _sample(sid: str):
    d = SAMPLES / sid
    raw, bkg = load_raw(d / "pdf_iq.dat"), load_raw(d / "pdf_bkg.dat")
    return raw, bkg, json.loads((d / "sample.json").read_text())["composition"], np.loadtxt(d / "pdf.gr")


def _reduce(sid: str, **kw) -> dict:
    raw, bkg, comp, _ = _sample(sid)
    kw = {"composition": comp, "background": np.c_[bkg["q"], bkg["i"]], "qmax": float(raw["header"]["qmax"]), **kw}
    return reduce(raw["q"], raw["i"], **kw)


@pytest.mark.parametrize("sid", list(ROUND_TRIP))  # bulk Pt, CeO2, TiO2, Co3O4; particles Pt, PtNi, TiO2, Co3O4
def test_raw_intensity_reduces_to_the_stored_gr(sid):
    raw, _, comp, ref = _sample(sid)
    out = _reduce(sid, composition=ROUND_TRIP[sid] or comp, rmin=1.0, rmax=30.0, rstep=0.01)
    g = np.array(out["gr_full"]["y"])
    assert np.allclose(out["gr_full"]["r"], ref[:, 0])
    rw = float(np.sqrt(np.sum((g - ref[:, 1]) ** 2) / np.sum(ref[:, 1] ** 2)))
    assert rw < RW_MAX, f"{sid} Rw {rw:.4f}"
    assert out["warnings"] == [] and abs(out["quality"]["sq_high_q_offset"]) < 0.1
    assert 0.5 < np.median(np.array(out["gr_full"]["dy"]) / ref[:, 2]) < 2.5  # σ_G from the F(Q) noise


def test_steps_have_the_documented_keys_and_lengths():
    out = _reduce("s0009")
    keys = {"raw": {"q", "sample", "background"}, "corrected": {"q", "y"}, "sq": {"q", "y"}, "fq": {"q", "y", "uncorrected"},
            "gr": {"r", "y"}}
    assert set(out) == {"params", "steps", "quality", "warnings", "gr_full"} and set(out["steps"]) == set(keys)
    for name, k in keys.items():
        step = out["steps"][name]
        assert set(step) == k and len({len(v) for v in step.values()}) == 1 and 100 <= len(step[next(iter(k))]) <= 800
    assert len(out["gr_full"]["r"]) == len(out["gr_full"]["y"]) == len(out["gr_full"]["dy"]) == 3001
    p = out["params"]
    assert p["qmin"] == 0.6 and p["qmax"] == 24.881 and p["qmaxinst"] == 26.88 and p["poly_degree"] == 8 and p["rpoly"] == 0.9
    json.dumps(out, allow_nan=False)


def test_one_call_on_3000_points_is_fast():
    raw, bkg, comp, _ = _sample("s0009")
    q = np.linspace(raw["q"][0], raw["q"][-1], 3000)
    args = (q, np.interp(q, raw["q"], raw["i"]))
    kw = {"composition": comp, "background": np.interp(q, bkg["q"], bkg["i"]), "qmax": 24.0}
    reduce(*args, **kw)
    t0 = time.perf_counter()
    reduce(*args, **kw)
    assert time.perf_counter() - t0 < 0.5


@pytest.mark.parametrize("sid", ["s0000", "s0009", "s0032"])
def test_larger_rpoly_flattens_low_r_and_lorch_damps_termination_ripples(sid):
    def low_r(**kw):
        out = _reduce(sid, rmax=5.0, **kw)
        return np.array(out["gr_full"]["r"]), np.array(out["gr_full"]["y"])

    def off_line(rpoly):  # rms of G(r <= 0.9 Å) about its best line through the origin
        r, g = low_r(rpoly=rpoly)
        m = (r > 0) & (r <= 0.9)
        return np.sqrt(np.mean((g[m] - (g[m] @ r[m]) / (r[m] @ r[m]) * r[m]) ** 2))

    def ripple(lorch):  # rms about a straight line between rpoly and the first peak
        r, g = low_r(lorch=lorch)
        m = (r >= 1.0) & (r <= 1.6)
        return np.std(g[m] - np.polyval(np.polyfit(r[m], g[m], 1), r[m]))

    assert off_line(0.9) < 0.75 * off_line(0.3)
    assert ripple(True) < 0.5 * ripple(False)


def test_missing_background_warns_and_unknown_element_raises():
    out = _reduce("s0009", background=None)
    assert any(w.startswith("no background given") for w in out["warnings"]) and out["params"]["background"] is False
    assert "—" not in json.dumps(out, ensure_ascii=False) and "–" not in json.dumps(out, ensure_ascii=False)
    with pytest.raises(ValueError, match="unknown element Xx"):
        _reduce("s0009", composition="XxO2")
    with pytest.raises(ValueError, match="background has 3 points"):
        _reduce("s0009", background=[1.0, 2.0, 3.0])


def test_two_theta_input_needs_a_wavelength():
    raw, *_ = _sample("s0009")
    lam = 0.1665
    tt = 2 * np.degrees(np.arcsin(raw["q"] * lam / (4 * np.pi)))
    body = "".join(f"{a:.6f} {b:.3f}\n" for a, b in zip(tt, raw["i"])).encode()
    got = load_raw(f"# x=2theta_deg wavelength_A={lam}\n".encode() + body, "scan.xy")
    assert np.allclose(got["q"], raw["q"], atol=1e-5) and got["header"]["wavelength_A"] == str(lam)
    with pytest.raises(ValueError, match="no wavelength"):
        load_raw(b"# x=2theta_deg\n" + body, "scan.xy")


def test_written_gr_loads_like_a_dataset_sample(tmp_path):
    out = _reduce("s0009", rmin=1.0)
    write_gr(tmp_path / "pdf.gr", out["gr_full"]["r"], out["gr_full"]["y"], {**out["params"], "qdamp": 0.0324},
             out["gr_full"]["dy"])
    r, g, dg = pdft.load_gr(tmp_path / "pdf.gr")
    assert np.allclose(g, out["gr_full"]["y"], atol=1e-6) and (dg > 0).all() and r[0] == 1.0
    inst = infer_inputs(tmp_path, "Pt")
    assert inst["instrument"]["pdf"]["qmax"] == 24.881 and inst["instrument"]["pdf"]["qdamp"] == 0.0324
    assert not any(a.startswith(("pdf.qmax", "pdf.qdamp")) for a in inst["assumed"])
