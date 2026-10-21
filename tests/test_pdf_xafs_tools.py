import numpy as np
import pytest
from pymatgen.core import Lattice, Structure

from concord.tools.feff import debye_uiso, sigma2_correlated_debye
from concord.tools.pdfcalc import PDFCalculator, first_shells, spherical_envelope


def test_pdf_first_peak_and_coordination(pt_fcc):
    r = np.arange(1.0, 20.0, 0.01)
    calc = PDFCalculator(pt_fcc, rmax=20.0)
    g = calc(r, uiso={"Pt": 0.005})
    R = (g + 4 * np.pi * calc.n_atoms / pt_fcc.volume * r) * r
    m = (r > 2.4) & (r < 3.1)
    assert abs(r[m][np.argmax(g[m])] - 3.924 / np.sqrt(2)) < 0.01
    assert abs(np.trapezoid(R[m], r[m]) - 12.0) < 0.1


def test_pdf_lattice_parameter_moves_peaks(pt_fcc):
    r = np.arange(1.0, 10.0, 0.01)
    calc = PDFCalculator(pt_fcc, rmax=10.0)
    g = calc(r, lattice={"a": 4.0, "b": 4.0, "c": 4.0}, uiso={"Pt": 0.004})
    m = (r > 2.4) & (r < 3.1)
    assert abs(r[m][np.argmax(g[m])] - 4.0 / np.sqrt(2)) < 0.015


def test_qmax_termination_conserves_peak_area(pt_fcc):
    r = np.arange(1.0, 15.0, 0.01)
    plain = PDFCalculator(pt_fcc, rmax=15.0)(r, uiso={"Pt": 0.005})
    term = PDFCalculator(pt_fcc, rmax=15.0, qmax=20.0)(r, uiso={"Pt": 0.005})
    m = (r > 2.3) & (r < 3.3)
    assert np.trapezoid(term[m], r[m]) == pytest.approx(np.trapezoid(plain[m], r[m]), rel=0.05)
    assert np.abs(term - plain).max() > 0.5  # but the ripples are there


def test_spherical_envelope():
    r = np.array([0.0, 10.0, 20.0, 30.0])
    env = spherical_envelope(r, 20.0)
    assert env[0] == 1.0 and env[2] == 0.0 and env[3] == 0.0 and 0 < env[1] < 1


def test_first_shells_partial_occupancy():
    s = Structure.from_spacegroup("Fm-3m", Lattice.cubic(3.785), [{"Pt": 0.5, "Ni": 0.5}], [[0, 0, 0]])
    shells = {x["neighbor"]: x for x in first_shells(s, "Pt")}
    assert shells["Pt"]["N"] == pytest.approx(6.0) and shells["Ni"]["N"] == pytest.approx(6.0)


def test_correlated_debye_limits():
    n = 4 / 3.924 ** 3
    near = sigma2_correlated_debye(2.775, 195.08, 195.08, 240, 300, n)
    far = sigma2_correlated_debye(1000.0, 195.08, 195.08, 240, 300, n)
    assert far == pytest.approx(2 * debye_uiso(195.08, 240, 300), rel=0.01)  # uncorrelated limit
    assert 0.004 < near < 0.0055 and near < far  # neighbours move together


@pytest.mark.slow
def test_exafs_shell_fit_recovers_model(pt_fcc):
    from concord.tools import xafs
    paths = xafs.structure_paths(pt_fcc, "Pt", "L3")
    k, chi = xafs.simulate_chi(paths, s02=0.9, temperature=300, theta_d=240, density=4 / pt_fcc.volume)
    chi = chi + np.random.default_rng(0).normal(0, 0.002, len(chi))
    fit = xafs.shell_fit(k, chi, paths, s02=0.9, kmin=3, kmax=14, rmin=1.8, rmax=3.2)
    pt = next(s for s in fit["shells"] if s["neighbor"] == "Pt")
    assert abs(pt["N"] - 12) < 1.5 and abs(pt["R_A"] - 3.924 / np.sqrt(2)) < 0.01
    assert abs(pt["sigma2"] - paths[0].sigma2) < 0.0006


@pytest.mark.slow
def test_fit_pdf_recovers_lattice_adp_and_size(pt_fcc, ceo2):
    from concord.tools.pdf import fit_pdf
    r = np.arange(1.0, 25.0, 0.01)
    calc = PDFCalculator(pt_fcc, rmax=26.0, qmax=24.0)
    g = calc(r, lattice={"a": 3.95, "b": 3.95, "c": 3.95}, uiso={"Pt": 0.006}, delta2=1.5, qdamp=0.03) * spherical_envelope(r, 50.0)
    dg = np.full_like(r, 0.01 * np.abs(g).max())
    g = g + np.random.default_rng(0).normal(0, dg)
    fit = fit_pdf(r, g, dg, pt_fcc, qmax=24.0, qdamp=0.03, psize0_A=40.0, label="Pt")
    assert fit["rw"] < 0.1
    assert abs(fit["lattice"]["a"] - 3.95) < 0.003 and abs(fit["uiso"]["Pt"] - 0.006) < 0.0008
    assert abs(fit["psize_nm"] - 5.0) < 0.5
    assert fit_pdf(r, g, dg, ceo2, qmax=24.0, qdamp=0.03, psize0_A=40.0, label="CeO2")["rw"] > 3 * fit["rw"]


@pytest.mark.slow
def test_virtual_exafs_matches_its_own_model_and_rejects_a_wrong_one(pt_fcc):
    from concord.tools import virtual_xafs as vx
    from concord.tools import xafs
    mass = pt_fcc.composition.elements[0].atomic_mass
    fit = {"candidate": "Pt", "rw": 0.05, "structure": pt_fcc, "lattice": {"a": 3.924}, "lattice_err": {"a": 0.001},
           "uiso": {"Pt": debye_uiso(mass, 240, 300)}, "uiso_err": {"Pt": 0.0001}, "psize_nm": None}
    pred = vx.predict_exafs([fit], "Pt", "L3", n=6)
    assert pred["label"] == "PREDICTED, NOT MEASURED" and abs(np.mean(pred["theta_K_range"]) - 240) < 15
    paths = xafs.structure_paths(pt_fcc, "Pt", "L3")
    same = xafs.simulate_chi(paths, s02=0.9, temperature=300, theta_d=240, density=4 / pt_fcc.volume)
    hotter = xafs.simulate_chi(paths, s02=0.9, temperature=300, theta_d=150, density=4 / pt_fcc.volume)
    good, bad = vx.score_against(pred, *same)["rfactor_R"], vx.score_against(pred, *hotter)["rfactor_R"]
    assert good < 0.01 and bad > 5 * good
