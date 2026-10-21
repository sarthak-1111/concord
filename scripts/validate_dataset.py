"""Validate the dataset: data contract, hashes, splits, value ranges and physics sanity. Exits non-zero on failure.

Physics: bulk XRD peaks sit at the Bragg positions of the true lattice; the first PDF peak sits at the
nearest-neighbour distance; an EXAFS first-shell fit with FEFF paths from the true structure recovers N and R.
Tolerances are fixed here, before looking at results.

Two method details, both physics rather than tolerance: (1) at finite Qmax, termination ripples of strong M-M
peaks move weak M-O peaks by up to ~0.1 Å, so the position test uses the strongest X-ray-weighted near shell
(N·Za·Zb/R), and the nearest-neighbour shell must show a significant peak within 0.15 Å with nothing strong before
it; (2) planted faults are built to break single-model assumptions (e.g. the bimodal 2.77/2.90 Å first shell of
icosahedra), so physics recovery is required for clean samples and only reported for faulty ones.
"""
import argparse
import csv
import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ValidationError
from scipy.signal import find_peaks

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from concord.data_builder.build import FAULTS  # noqa: E402
from concord.data_builder.fetch import load_structures  # noqa: E402

TOL = {"bragg_deg": 0.05, "pdf_first_peak_A": 0.08, "exafs_R_A": 0.03, "exafs_N_rel": 0.20}


class Shell(BaseModel):
    absorber: str
    neighbor: str
    N: float
    R_A: float
    sigma2: float


class GroundTruth(BaseModel):
    phases: list[dict]
    lattice: dict
    size_nm: float | None
    shells: list[Shell]
    oxidation_state: dict[str, float]
    notes: str


class Fault(BaseModel):
    type: str
    detail: str


class Sample(BaseModel):
    sample_id: str
    composition: str
    techniques: list[Literal["xrd", "pdf", "xafs"]]
    instrument: dict
    origin: Literal["simulated", "simulated+realism", "experimental"]
    ground_truth: GroundTruth
    faults: list[Fault]


class Report:
    def __init__(self):
        self.errors, self.passed = [], 0

    def check(self, ok: bool, msg: str):
        if ok:
            self.passed += 1
        else:
            self.errors.append(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def true_structure(sample: dict):
    """The sample's source structure scaled to the ground-truth lattice."""
    name = sample["ground_truth"]["notes"].split("system ")[-1].strip()
    s = load_structures()[name][0][1].copy()
    lat = sample["ground_truth"]["lattice"]
    from pymatgen.core import Lattice
    s.lattice = Lattice.from_parameters(lat["a"], lat["b"], lat["c"], lat["alpha"], lat["beta"], lat["gamma"])
    return s


def physics(sample: dict, folder: Path, rep: Report, stats: dict):
    from concord.tools import xafs, xrd
    sid, gt = sample["sample_id"], sample["ground_truth"]
    if gt["size_nm"] is None and not sample["faults"]:  # bulk: Bragg positions
        data = xrd.load_pattern(folder / "xrd.xy")
        pre = xrd.preprocess(data["intensity"])
        peaks = sorted(xrd.find_and_fit_peaks(data["two_theta_deg"], pre["intensity_corr"], height_rel=0.05), key=lambda p: -p["height"])[:6]
        ref = [l for l in xrd.reference_lines(true_structure(sample), sample["instrument"]["xrd"]["wavelength_A"], (10, 90)) if l["intensity"] >= 5]
        lines = [l["two_theta"] for l in ref]
        isolated = [t for t in lines if not any(0 < abs(t - u) < 0.3 for u in lines)]  # overlapping reflections shift fitted maxima
        nearest = [min(lines, key=lambda t: abs(p["two_theta"] - t)) for p in peaks]
        worst = max((abs(p["two_theta"] - t) for p, t in zip(peaks, nearest) if t in isolated), default=0.0)
        stats["bragg"].append(worst)
        rep.check(worst <= TOL["bragg_deg"], f"{sid}: XRD peak {worst:.3f}° from the nearest Bragg line")
    from pymatgen.core import Element
    g = np.loadtxt(folder / "pdf.gr")
    shells = [s for s in gt["shells"] if s["N"] >= 1.0]  # planted minority shells (N < 1) are not "the" first peak
    nn = min(s["R_A"] for s in shells)
    m = (g[:, 0] > 1.5) & (g[:, 0] < 4.5)
    idx, _ = find_peaks(g[m, 1], prominence=4 * np.median(g[m, 2]))
    r_pk, h_pk = g[m, 0][idx], g[m, 1][idx]
    Z = lambda el: Element(el).Z
    strong = max(shells, key=lambda s: s["N"] * Z(s["absorber"]) * Z(s["neighbor"]) / s["R_A"])
    near = np.abs(r_pk - strong["R_A"]) <= 0.25
    pos = r_pk[near][np.argmax(h_pk[near])] if near.any() else np.nan
    found_nn = bool((np.abs(r_pk - nn) <= 0.15).any())
    early = (r_pk < nn - 0.3) & (h_pk > 0.3 * g[m, 1].max())
    results = [(abs(pos - strong["R_A"]) <= TOL["pdf_first_peak_A"], f"strongest near-shell PDF peak {pos:.3f} Å vs {strong['R_A']:.3f} Å ({strong['absorber']}-{strong['neighbor']})"),
               (found_nn, f"no significant PDF peak within 0.15 Å of the nearest neighbour {nn:.3f} Å"),
               (not early.any(), f"strong PDF peak at {r_pk[early]} Å, below the nearest neighbour {nn:.3f} Å")]
    for ok, msg in results:
        if sample["faults"]:
            if not ok:
                stats.setdefault("fault_info", []).append(f"{sid} [{sample['faults'][0]['type']}]: {msg}")
        else:
            rep.check(ok, f"{sid}: {msg}")
    if not sample["faults"]:
        stats["pdf"].append(abs(pos - strong["R_A"]))
    if "xafs" in sample["techniques"]:
        chi = np.loadtxt(folder / "xafs_chi.k")
        absorber = sample["instrument"]["xafs"]["edge"].split()[0]
        st = true_structure(sample)
        paths = xafs.structure_paths(st, absorber, sample["instrument"]["xafs"]["edge"].split()[1])
        present = {el.symbol for el in st.composition.elements}  # planted additions (e.g. an oxide shell) have no path
        model = [s for s in gt["shells"] if s["neighbor"] in present]
        r1 = min(s["R_A"] for s in model)
        first = [s for s in model if s["R_A"] <= r1 + 0.35]  # first coordination shell, as fitted
        fit = xafs.shell_fit(chi[:, 0], chi[:, 1], paths, s02=sample["instrument"]["xafs"]["s02"], kmin=3.0,
                             kmax=min(12.0, sample["instrument"]["xafs"]["kmax"]))
        fitted = {s["neighbor"]: s for s in fit["shells"]}
        if not all(s["neighbor"] in fitted for s in first):
            rep.check(False, f"{sid}: fit lacks {[s['neighbor'] for s in first]} paths")
            return
        # unlike neighbours at the same distance (Pt-Pt/Pt-Co in Pt3Co) trade N; their total is the robust number
        shell = max(first, key=lambda s: s["N"])
        got = {**fitted[shell["neighbor"]], "N": sum(fitted[s["neighbor"]]["N"] for s in first)}
        shell = {**shell, "N": sum(s["N"] for s in first)}
        dR, dN = got["R_A"] - shell["R_A"], (got["N"] - shell["N"]) / shell["N"]
        msg = f"EXAFS N {got['N']:.2f} vs model {shell['N']:.2f}, R {got['R_A']:.3f} vs {shell['R_A']:.3f} Å ({shell['absorber']}-{shell['neighbor']})"
        if sample["faults"]:
            if abs(dR) > TOL["exafs_R_A"] or abs(dN) > TOL["exafs_N_rel"]:
                stats.setdefault("fault_info", []).append(f"{sid} [{sample['faults'][0]['type']}]: {msg}")
            return
        stats["exafs_R"].append(abs(dR)); stats["exafs_N"].append(abs(dN))
        rep.check(abs(dR) <= TOL["exafs_R_A"], f"{sid}: {msg}")
        rep.check(abs(dN) <= TOL["exafs_N_rel"], f"{sid}: {msg}")


def main(root: Path, skip_physics: bool) -> int:
    rep = Report()
    stats = {"bragg": [], "pdf": [], "exafs_R": [], "exafs_N": []}
    manifest = list(csv.DictReader((root / "manifest.csv").open()))
    splits = json.loads((root / "splits.json").read_text())
    rep.check(set(splits) == {"train", "val", "test", "faults"}, f"splits.json keys {sorted(splits)}")
    in_split = [s for v in splits.values() for s in v]
    rep.check(len(in_split) == len(set(in_split)), "a sample appears in more than one split")
    ids = [r["sample_id"] for r in manifest]
    rep.check(set(ids) == set(in_split), "manifest and splits list different samples")
    for col in ("sample_id", "source", "licence", "generator", "params_hash"):
        rep.check(all(r.get(col) for r in manifest), f"manifest column {col} missing or empty")
    n_fault = 0
    for row in manifest:
        sid = row["sample_id"]
        folder = root / "samples" / sid
        try:
            sample = Sample.model_validate_json((folder / "sample.json").read_text()).model_dump()
        except (ValidationError, OSError) as exc:
            rep.check(False, f"{sid}: sample.json invalid: {str(exc)[:200]}")
            continue
        for key, val in row.items():
            if key.startswith("sha256_") and val:
                f = folder / key[7:]
                rep.check(f.exists() and sha(f) == val, f"{sid}: hash mismatch for {key[7:]}")
        needed = {"xrd.xy", "pdf.gr"} | ({"xafs_mu.dat", "xafs_chi.k"} if "xafs" in sample["techniques"] else set())
        rep.check(all((folder / f).exists() for f in needed), f"{sid}: missing files {needed}")
        x = np.loadtxt(folder / "xrd.xy")
        rep.check(np.all(np.diff(x[:, 0]) > 0) and 5 <= x[0, 0] and x[-1, 0] <= 150 and (x[:, 1] >= 0).all() and (x[:, 2] > 0).all(), f"{sid}: XRD ranges")
        g = np.loadtxt(folder / "pdf.gr")
        rep.check(np.all(np.diff(g[:, 0]) > 0) and np.isfinite(g).all() and (g[:, 2] > 0).all(), f"{sid}: PDF ranges")
        pdf = sample["instrument"]["pdf"]
        rep.check(10 <= pdf["qmax"] <= 40 and 0 <= pdf["qdamp"] <= 0.1, f"{sid}: PDF instrument ranges")
        if "xafs" in sample["techniques"]:
            mu, chi = np.loadtxt(folder / "xafs_mu.dat"), np.loadtxt(folder / "xafs_chi.k")
            rep.check(np.all(np.diff(mu[:, 0]) > 0) and np.all(np.diff(chi[:, 0]) > 0) and np.isfinite(mu).all(), f"{sid}: XAFS ranges")
        gt = sample["ground_truth"]
        rep.check(gt["size_nm"] is None or 1.0 <= gt["size_nm"] <= 10.0, f"{sid}: size {gt['size_nm']}")
        rep.check(all(0 < s["N"] <= 14 and 1.5 <= s["R_A"] <= 4.0 and 0.0005 <= s["sigma2"] <= 0.03 for s in gt["shells"]), f"{sid}: shell ranges")
        rep.check(all(-3 <= v <= 8 for v in gt["oxidation_state"].values()), f"{sid}: oxidation states")
        rep.check(all(f["type"] in FAULTS for f in sample["faults"]), f"{sid}: unknown fault type")
        rep.check(bool(sample["faults"]) == (sid in splits["faults"]), f"{sid}: fault split mismatch")
        n_fault += bool(sample["faults"])
        if not skip_physics:
            try:
                physics(sample, folder, rep, stats)
            except Exception as exc:
                rep.check(False, f"{sid}: physics check crashed: {type(exc).__name__}: {exc}")
    frac = n_fault / max(1, len(manifest))
    rep.check(0.10 <= frac <= 0.20, f"fault fraction {frac:.2f} outside 10-20 %")
    print(f"{len(manifest)} samples, {n_fault} with planted faults; {rep.passed} checks passed, {len(rep.errors)} failed")
    for k, v in stats.items():
        if v and k != "fault_info":
            print(f"  {k:8s} n={len(v):3d} median={np.median(v):.4f} max={np.max(v):.4f}")
    for line in stats.get("fault_info", []):
        print("INFO single-shell model does not describe planted fault", line)
    for e in rep.errors:
        print("FAIL", e)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "dataset"))
    ap.add_argument("--skip-physics", action="store_true")
    a = ap.parse_args()
    sys.exit(main(Path(a.root), a.skip_physics))
