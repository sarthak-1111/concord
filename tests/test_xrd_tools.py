import numpy as np

from concord.tools import xrd


# Upstream CrystaLenz tests, ported to the refactored functions.
def test_load_xrd_data_shapes(raw_payload: dict):
    theta, intensity = raw_payload["two_theta_deg"], raw_payload["intensity"]
    assert len(theta) == len(intensity) > 100
    assert raw_payload["meta"]["path"].endswith("sample_xrd.csv")
    assert raw_payload["meta"]["unit"] == "deg"


def test_preprocess_outputs(raw_payload: dict, processed_payload: dict):
    n = len(raw_payload["intensity"])
    assert len(processed_payload["intensity_smooth"]) == len(processed_payload["intensity_corr"]) == n
    assert processed_payload["intensity_corr"].min() >= 0


def test_find_and_fit_peaks_detects_prominent_peak(peaks_payload: list):
    # the sample has a strong synthetic peak around ~28.3 deg
    assert any(27.5 <= p["two_theta"] <= 29.0 for p in peaks_payload), "Expected peak near 28.3° not found"
    assert all(p["fwhm_deg"] > 0 and p["area"] > 0 for p in peaks_payload)


def test_scherrer_outputs(peaks_payload: list):
    out = xrd.scherrer_wh(peaks_payload)
    assert out["scherrer"] and all(r["L_nm"] > 0 for r in out["scherrer"])
    wh = out["williamson_hall"]
    assert wh is None or {"strain", "size_nm", "r2"} <= set(wh)


# New: physics on synthetic patterns with known answers.
def test_scherrer_recovers_simulated_size(pt_fcc):
    tt = np.arange(20, 100, 0.02)
    inst = {"U": 0.0, "V": 0.0, "W": 0.0001}
    y = xrd.simulate_pattern(pt_fcc, tt, size_nm=6.0, instrument=inst)
    peaks = xrd.find_and_fit_peaks(tt, y)
    out = xrd.scherrer_wh(peaks, instrument=inst)
    assert abs(out["scherrer_median_nm"] - 6.0) / 6.0 < 0.15


def test_sphere_diameter_from_debye_pattern(pt_fcc):
    """Diameter of a 5 nm Pt sphere from its Debye-scattering pattern (the physics the dataset uses)."""
    from ase.build import bulk
    from debyecalculator import DebyeCalculator
    atoms = bulk("Pt", "fcc", a=3.924, cubic=True).repeat(16)
    atoms.translate(-atoms.positions.mean(axis=0))
    atoms = atoms[np.linalg.norm(atoms.positions, axis=1) <= 25.0]
    tt = np.arange(30, 90, 0.02)
    q = 4 * np.pi * np.sin(np.radians(tt / 2)) / 1.5406
    qq, iq = DebyeCalculator(qmin=q[0] - 0.05, qmax=q[-1] + 0.05, qstep=0.004, biso=0.3, device="cpu").iq(atoms)
    y = np.interp(q, qq, iq)
    peaks = xrd.find_and_fit_peaks(tt, y - y.min())
    matched = {m["exp_two_theta"] for m in xrd.match_reference(peaks, xrd.reference_lines(pt_fcc, two_theta_range=(30, 90)))["matches"]}
    out = xrd.scherrer_wh([p for p in peaks if p["two_theta"] in matched])
    assert abs(out["sphere_diameter_nm"] - 5.0) / 5.0 < 0.15


def test_williamson_hall_strain_is_dimensionless(pt_fcc):
    tt = np.arange(20, 120, 0.02)
    inst = {"U": 0.0, "V": 0.0, "W": 0.0001}
    peaks = xrd.find_and_fit_peaks(tt, xrd.simulate_pattern(pt_fcc, tt, size_nm=30.0, strain=0.003, instrument=inst))
    wh = xrd.scherrer_wh(peaks, instrument=inst)["williamson_hall"]
    assert 0.0015 < wh["strain"] < 0.006  # upstream reported strain*lambda (~1e-13) here


def test_reference_match_and_phase_ranking(pt_fcc, ceo2):
    tt = np.arange(20, 90, 0.02)
    y = xrd.simulate_pattern(pt_fcc, tt, size_nm=10.0)
    peaks = xrd.find_and_fit_peaks(tt, y)
    m = xrd.match_reference(peaks, xrd.reference_lines(pt_fcc, two_theta_range=(20, 90)))
    assert m["ref_fraction_matched"] == 1.0 and m["obs_area_fraction_explained"] > 0.95
    first_peak = min(p["two_theta"] for p in peaks)
    assert abs(first_peak - 2 * np.degrees(np.arcsin(1.5406 / (2 * 3.924 / np.sqrt(3))))) < 0.05  # Pt(111)
    ranking = xrd.rank_phases(tt, y, peaks, {"Pt": pt_fcc, "CeO2": ceo2}, size_nm=10.0)
    assert ranking[0]["phase"] == "Pt" and ranking[0]["score"] > ranking[1]["score"] + 0.3


def test_xy_loader_reads_q_header(tmp_path):
    q = np.linspace(1, 8, 200)
    path = tmp_path / "xrd.xy"
    np.savetxt(path, np.c_[q, np.exp(-q), np.ones_like(q)], header="x=q_inv_A wavelength_A=1.5406")
    data = xrd.load_pattern(path)
    assert data["meta"]["unit"] == "q"
    expected = 2 * np.degrees(np.arcsin(8 * 1.5406 / (4 * np.pi)))
    assert abs(data["two_theta_deg"].max() - expected) < 1e-6


def test_scale_with_background_separates_pattern_from_hump_and_low_angle_rise():
    tt = np.arange(10, 90, 0.02)
    pattern = sum(xrd.tch_pseudo_voigt(tt, c, 1.5, 0.2) for c in (39.8, 46.2, 67.5))
    pattern *= 100 / pattern.max()
    bkg = 40 * np.exp(-0.5 * ((tt - 25) / 8) ** 2) + 900 / tt  # amorphous hump + low-angle rise, peaks of 300 on top
    (scale,), fitted = xrd.scale_with_background(tt, 3.0 * pattern + bkg, [pattern])
    assert abs(scale - 3.0) < 0.06
    assert np.max(np.abs(fitted - bkg)) < 0.05 * 300
    (neg,), _ = xrd.scale_with_background(tt, bkg - pattern, [pattern])
    assert neg == 0.0  # scales are non-negative
