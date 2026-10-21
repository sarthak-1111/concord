from pathlib import Path

import pytest
from pymatgen.core import Lattice, Structure

from concord.tools import xrd

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def sample_path() -> str:
    path = ROOT / "sample_data" / "sample_xrd.csv"
    assert path.exists(), f"Sample file not found: {path}"
    return str(path)


@pytest.fixture(scope="session")
def raw_payload(sample_path: str) -> dict:
    return xrd.load_pattern(sample_path)


@pytest.fixture(scope="session")
def processed_payload(raw_payload: dict) -> dict:
    return xrd.preprocess(raw_payload["intensity"], smoothing_window=11, smoothing_polyorder=3)


@pytest.fixture(scope="session")
def peaks_payload(raw_payload: dict, processed_payload: dict) -> list:
    return xrd.find_and_fit_peaks(raw_payload["two_theta_deg"], processed_payload["intensity_corr"])


@pytest.fixture(scope="session")
def pt_fcc() -> Structure:
    return Structure.from_spacegroup("Fm-3m", Lattice.cubic(3.924), ["Pt"], [[0, 0, 0]])


@pytest.fixture(scope="session")
def ceo2() -> Structure:
    return Structure.from_spacegroup("Fm-3m", Lattice.cubic(5.411), ["Ce", "O"], [[0, 0, 0], [0.25, 0.25, 0.25]])
