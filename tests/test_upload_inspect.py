import json
import random
from pathlib import Path

import numpy as np
import pytest

from concord.upload_inspect import inspect_file

SAMPLES = Path(__file__).resolve().parent.parent / "dataset" / "samples"
FILES = {"xrd.xy": ("xrd", "2θ (°)"), "pdf.gr": ("pdf", "r (Å)"), "xafs_mu.dat": ("xafs_mu", "E (eV)"), "xafs_chi.k": ("xafs_chi", "k (Å⁻¹)")}


def _data(sample: str, file: str, header: bool = True) -> bytes:
    raw = (SAMPLES / sample / file).read_bytes()
    return raw if header else b"".join(line for line in raw.splitlines(keepends=True) if not line.startswith(b"#"))


@pytest.mark.parametrize("sample", ["s0000", "s0001", "s0003", "s0004", "s0007"])  # Pt, Pt3Co, TiO2, CeO2, Co3O4
@pytest.mark.parametrize("file", list(FILES))
def test_every_technique_is_told_from_the_content_alone(sample, file):
    r = inspect_file("data.txt", _data(sample, file))
    tech, x_label = FILES[file]
    assert (r["technique"], r["confidence"], r["x_label"]) == (tech, "high", x_label), r["reason"]
    assert r["n_points"] == len(np.loadtxt(SAMPLES / sample / file)) and r["x_range"][0] < r["x_range"][1]
    p = r["preview"]
    assert 2 <= len(p["x"]) == len(p["y"]) <= 240 and min(p["y"]) == 0.0 and max(p["y"]) == 1.0
    assert p["x"][0] == r["x_range"][0] and p["x"][-1] == r["x_range"][1]
    text = json.dumps(r, ensure_ascii=False)
    assert "—" not in text and "–" not in text


@pytest.mark.parametrize("sample, composition, edge", [("s0000", "Pt", "Pt L3"), ("s0001", "Pt3Co", "Pt L3"),
                                                       ("s0003", "TiO2", "Ti K"), ("s0007", "Co3O4", "Co K"), ("s0004", "CeO2", "Ce L3")])
def test_mu_edge_is_found_from_the_energies(sample, composition, edge):
    r = inspect_file("scan.dat", _data(sample, "xafs_mu.dat", header=False), composition)  # no '# edge=' line to lean on
    assert (r["technique"], r["edge"], r["warnings"]) == ("xafs_mu", edge, [])


def test_mu_edge_of_an_element_outside_the_composition_is_flagged():
    r = inspect_file("xafs_mu.dat", _data("s0045", "xafs_mu.dat"), "TiO2")  # a Ce L3 scan labelled TiO2
    assert r["edge"] == "Ce L3" and "the edge element is not in the composition" in r["warnings"]


def test_chi_edge_comes_from_the_header_else_a_low_confidence_guess():
    r = inspect_file("xafs_chi.k", _data("s0003", "xafs_chi.k"), "TiO2")
    assert (r["edge"], r["confidence"], r["header"]) == ("Ti K", "high", {"edge": "Ti_K"})
    r = inspect_file("data.txt", _data("s0001", "xafs_chi.k", header=False), "Pt3Co")
    assert (r["technique"], r["edge"], r["confidence"]) == ("xafs_chi", "Pt L3", "low") and r["warnings"]


def test_a_misleading_name_is_overruled_by_the_content():
    r = inspect_file("xrd.xy", _data("s0000", "pdf.gr"))
    assert (r["technique"], r["confidence"]) == ("pdf", "medium")
    assert any("name suggests an XRD pattern" in w for w in r["warnings"])
    assert r["header"]["qmax"] == "18.519"
    assert inspect_file("pdf.gr", _data("s0000", "pdf.gr"))["warnings"] == []


@pytest.mark.parametrize("data", [bytes(random.Random(0).randrange(256) for _ in range(5000)), b"", b"1\n2\n3\n",
                                  b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n"])
def test_unreadable_bytes_give_no_technique(data):
    r = inspect_file("xrd.xy", data)
    assert r["technique"] is None and r["n_points"] == 0 and r["preview"] == {"x": [], "y": []} and r["reason"]


@pytest.mark.parametrize("name", ["pattern.csv", "pattern.txt"])
def test_csv_with_a_text_header_row_and_three_columns(name):
    rows = np.loadtxt(SAMPLES / "s0003" / "xrd.xy")
    csv = "two_theta,intensity,sigma\n" + "".join(f"{a},{b},{c}\n" for a, b, c in rows)
    r = inspect_file(name, csv.encode())
    assert (r["technique"], r["x_label"], r["n_points"], r["x_range"]) == ("xrd", "2θ (°)", 4001, [10.0, 90.0])


def test_short_q_space_pattern_is_flagged():
    rows = np.loadtxt(SAMPLES / "s0003" / "xrd.xy")[::50]
    q = 4 * np.pi * np.sin(np.radians(rows[:, 0] / 2)) / 1.5406
    r = inspect_file("data.txt", "".join(f"{a} {b}\n" for a, b in zip(q, rows[:, 1])).encode())
    assert (r["technique"], r["confidence"], r["x_label"]) == ("xrd", "medium", "Q (Å⁻¹)")
    assert "only 81 points" in r["warnings"]


RAW = pytest.mark.skipif(not (SAMPLES / "s0000" / "pdf_iq.dat").exists(), reason="run scripts/make_raw_pdf.py")


@RAW
@pytest.mark.parametrize("sample", ["s0000", "s0004", "s0009", "s0032"])  # bulk Pt, bulk CeO2, Pt and TiO2 particles
@pytest.mark.parametrize("file", ["pdf_iq.dat", "pdf_bkg.dat"])
def test_raw_total_scattering_is_told_from_the_content(sample, file):
    r = inspect_file("data.txt", _data(sample, file))
    assert (r["technique"], r["confidence"], r["x_label"], r["y_label"]) == ("pdf_iq", "high", "Q (Å⁻¹)", "Intensity"), r["reason"]
    assert r["x_range"][1] >= 15 and r["edge"] is None and r["warnings"] == []
    assert inspect_file(file, _data(sample, file))["warnings"] == []  # pdf_iq / pdf_bkg names agree, unlike pdf.gr's "pdf"


@RAW
def test_raw_total_scattering_without_a_header():
    data = _data("s0009", "pdf_iq.dat", header=False)
    r = inspect_file("data.txt", data)
    assert (r["technique"], r["confidence"]) == ("pdf_iq", "medium") and any("read as Q" in w for w in r["warnings"])
    r = inspect_file("sample.iq", data)
    assert (r["technique"], r["confidence"], r["warnings"]) == ("pdf_iq", "high", [])
    r = inspect_file("xrd.xy", _data("s0009", "pdf_iq.dat"))
    assert r["technique"] == "pdf_iq" and any("name suggests an XRD pattern" in w for w in r["warnings"])
