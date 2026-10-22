import pytest

from concord.agents.exafs_specialist import STAGES, check_physical, should_accept

GOOD = {"rfactor": 0.002, "e0_shift": 0.3, "shells": [
    {"neighbor": "Pt", "N": 7.8, "N_model": 8.0, "R_A": 2.710, "reff_A": 2.709, "sigma2": 0.0048},
    {"neighbor": "O", "N": 0.4, "N_model": 0.0, "R_A": 2.0, "reff_A": 2.0, "sigma2": 0.004, "extra": True}]}


def test_check_physical_flags_each_bound():
    assert check_physical(GOOD) == []
    pt = GOOD["shells"][0]
    for change, word in [({"sigma2": 0.0005}, "σ²"), ({"R_A": 2.85}, "ΔR"), ({"N": 12.5}, "N=")]:
        problems = check_physical({**GOOD, "shells": [{**pt, **change}]})
        assert len(problems) == 1 and word in problems[0]
    assert "ΔE0" in check_physical({**GOOD, "e0_shift": -11.0})[0]
    assert check_physical({**GOOD, "shells": [{**GOOD["shells"][1], "N": 7.0}]})  # probe shell: at most 6


def test_should_accept_needs_one_percent_and_physical_values():
    assert should_accept(None, GOOD)[0]  # first fit: baseline
    assert should_accept(0.0021, GOOD)[0]  # 4.8 % better
    assert not should_accept(0.00201, GOOD)[0]  # 0.5 %: not worth it
    assert not should_accept(0.0019, GOOD)[0]  # worse
    assert not should_accept(0.1, {**GOOD, "e0_shift": 12.0})[0]  # better but unphysical
    assert not should_accept(0.1, {**GOOD, "rfactor": float("nan")})[0]
    assert [s["key"] for s in STAGES][-1] == "consolidate"


@pytest.mark.slow
def test_staged_shell_fit_recovers_model(pt_fcc):
    import numpy as np
    from concord.tools import xafs
    paths = xafs.structure_paths(pt_fcc, "Pt", "L3")
    k, chi = xafs.simulate_chi(paths, s02=0.9, temperature=300, theta_d=240, density=4 / pt_fcc.volume)
    chi = chi + np.random.default_rng(0).normal(0, 0.002, len(chi))
    fit = xafs.shell_fit(k, chi, paths, s02=0.9, kmin=3, kmax=14, rmin=1.8, rmax=3.2, staged=True)
    pt = next(s for s in fit["shells"] if s["neighbor"] == "Pt")
    assert abs(pt["N"] - 12) < 1.5 and abs(pt["R_A"] - 3.924 / np.sqrt(2)) < 0.01
    assert [s["key"] for s in fit["stages"]] == [s["key"] for s in STAGES] and fit["stages"][0]["kept"]
