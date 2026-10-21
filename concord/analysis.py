"""Deterministic per-sample analysis: XRD, then PDF, then EXAFS/XANES, then cross-technique checks C1–C6.

Every number comes from a tool in concord.tools; the agents (generator, critic) only explain, challenge and
re-run tools. Inputs are what a user has: the data files plus the sample.json metadata (composition,
techniques, instrument). The ground truth and planted-fault records in sample.json are never read here.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from pymatgen.core import Composition, Structure

from concord import checks
from concord.config import settings
from concord.data_builder.fetch import load_structures, systems
from concord.tools import pdf as pdft
from concord.tools import xafs, xrd

INPUT_KEYS = ("sample_id", "composition", "techniques", "instrument", "origin")
B_BV = 0.37  # bond-valence softness b (Å), Brown & Altermatt (1985), doi:10.1107/S0108768185002063


def load_inputs(folder: Path) -> dict:
    meta = json.loads((Path(folder) / "sample.json").read_text())
    return {k: meta[k] for k in INPUT_KEYS if k in meta}


def _cations(formula: str) -> set[str]:
    return {el.symbol for el in Composition(formula).elements} - {"O"}


def candidates(composition: str) -> dict[str, Structure]:
    """Library phases sharing a cation with the stated composition: its polymorphs, alloys and oxides."""
    want = _cations(composition)
    formulas = {s["name"]: s["formula"] for s in systems()}
    return {name: entries[0][1] for name, entries in load_structures(library_only=True).items() if _cations(formulas[name]) & want}


def run_xrd(folder: Path, meta: dict, cands: dict) -> dict:
    inst = meta["instrument"]["xrd"].get("caglioti_deg2")
    data = xrd.load_pattern(folder / "xrd.xy")
    lam = data["meta"]["wavelength_A"]
    # stiff baseline: on 168 train/val nanoparticles (dataset_big) the CrystaLenz default (λ=1e5) followed broad
    # peaks and gave sphere-size MAE 10x; λ=1e8, p=0.001 gives MAE 0.098 (median +4.9 %)
    pre = xrd.preprocess(data["intensity"], baseline_lambda=1e8, baseline_p=0.001)
    tt, y = data["two_theta_deg"], pre["intensity_corr"]
    peaks = xrd.find_and_fit_peaks(tt, y)
    amax = max((p["area"] for p in peaks), default=0.0)  # drop noise spikes: narrower than the instrument, or tiny
    peaks = [p for p in peaks if p["area"] >= 0.01 * amax and (not inst or p["fwhm_deg"] >= 0.7 * xrd.caglioti_fwhm_deg(p["two_theta"], **inst))]
    size_nm = xrd.scherrer_wh(peaks, lam, instrument=inst)["scherrer_median_nm"]
    for _ in range(2):  # rank, size from the peaks the best phase indexes, rank again at that size
        ranking = xrd.rank_phases(tt, y, peaks, cands, lam, size_nm=size_nm, instrument=inst)
        ref = xrd.reference_lines(cands[ranking[0]["phase"]], lam, (float(tt.min()), float(tt.max())))
        matched = {m["exp_two_theta"] for m in xrd.match_reference(peaks, ref, lam)["matches"]}
        indexed = [p for p in peaks if p["two_theta"] in matched]
        size = xrd.scherrer_wh(indexed, lam, instrument=inst)
        size_nm = size["scherrer_median_nm"] or size_nm
    span = float(data["intensity"].max() - data["intensity"].min()) or 1.0
    return {"wavelength_A": lam, "n_peaks": len(peaks), "n_indexed": len(indexed), "peaks": peaks, **size, "ranking": ranking,
            "peak_rel_intensity": max((p["height"] for p in indexed), default=0.0) / span,
            "curves": {"two_theta": tt, "obs": data["intensity"], "baseline": pre["baseline"], "corrected": y}}


def run_pdf(folder: Path, meta: dict, cands: dict, xrd_res: dict | None) -> dict:
    inst = meta["instrument"]["pdf"]
    r, g, dg = pdft.load_gr(folder / "pdf.gr")
    d_xrd = xrd_res.get("sphere_diameter_nm") if xrd_res else None
    psize0 = float(np.clip(10 * d_xrd, 10.0, 380.0)) if d_xrd else None
    fits = []
    for name, structure in cands.items():
        kw = dict(qmax=inst["qmax"], qdamp=inst["qdamp"], qbroad=inst.get("qbroad", 0.0), label=name)
        fit = pdft.fit_pdf(r, g, dg, structure, psize0_A=psize0, **kw)
        if fit["psize_nm"] >= 38.0:  # envelope ran to its 40 nm bound: no finite size inside the fitted r-range
            fit = pdft.fit_pdf(r, g, dg, structure, nanoparticle=False, **kw)
        fit["lattice_ref"] = dict(zip("abc", structure.lattice.abc))
        fits.append(fit)
    return {"fits": sorted(fits, key=lambda f: f["rw"])}


def run_exafs(folder: Path, meta: dict, structure: Structure) -> dict:
    xa = meta["instrument"]["xafs"]
    absorber, edge = xa["edge"].split()
    if absorber not in {el.symbol for el in structure.composition.elements}:
        raise ValueError(f"absorber {absorber} is not in the refined model {structure.composition.reduced_formula}")
    if (folder / "xafs_chi.k").exists():
        k, chi = np.loadtxt(folder / "xafs_chi.k", unpack=True)
        source = "xafs_chi.k"
    else:
        e, mu = np.loadtxt(folder / "xafs_mu.dat", unpack=True)
        c = xafs.chi_from_mu(e, mu)
        k, chi, source = c["k"], c["chi"], "autobk(xafs_mu.dat)"
    kmax = min(12.0, float(xa.get("kmax", 12.0)))
    paths = xafs.structure_paths(structure, absorber, edge)
    fit = xafs.shell_fit(k, chi, paths, s02=xa["s02"], kmin=3.0, kmax=kmax)
    out = {"absorber": absorber, "edge": edge, "chi_source": source, "model": structure.composition.reduced_formula,
           "fit": fit, "extra_shell": None}
    if "O" not in {s["neighbor"] for s in fit["shells"]}:  # metal model: test for an oxide shell it lacks
        tol = settings()["checks"]["C3_coordination"]
        with_o = xafs.shell_fit(k, chi, paths, s02=xa["s02"], kmin=3.0, kmax=kmax, extra=[xafs.probe_path(absorber, edge)])
        x = next(s for s in with_o["shells"] if s.get("extra"))
        significant = bool(x["N_err"] and x["N"] / x["N_err"] >= tol["extra_min_sigma"]
                           and with_o["rfactor"] <= (1 - tol["extra_min_rfactor_drop"]) * fit["rfactor"])
        out["extra_shell"] = {"pair": f"{absorber}-O", "N": x["N"], "N_err": x["N_err"], "R_A": x["R_A"], "sigma2": x["sigma2"],
                              "rfactor_without": fit["rfactor"], "rfactor_with": with_o["rfactor"], "significant": significant}
        if significant:
            out["fit"], out["fit_without_extra"] = with_o, fit
    ft = xafs.fourier_transform(k, chi, kmin=3.0, kmax=kmax)
    out["curves"] = {"k": k, "chi": chi, "r": ft["r"], "chir_mag": ft["chir_mag"]}
    return out


def run_xanes(folder: Path, meta: dict, references: Path) -> dict:
    absorber = meta["instrument"]["xafs"]["edge"].split()[0]
    e, mu = np.loadtxt(folder / "xafs_mu.dat", unpack=True)
    norm = xafs.normalize(e, mu)["norm"]
    edge_e = xafs.edge_position(e, norm)
    refs = {float(f.stem.split("_v")[1]): tuple(np.loadtxt(f, unpack=True)) for f in sorted(Path(references).glob(f"{absorber}_v*.dat"))}
    if len(refs) < 2:
        raise ValueError(f"need at least two {absorber} valence standards in {references}")
    stds = [{"valence": v, "edge_eV": xafs.edge_position(*refs[v])} for v in refs]
    lcf = xafs.linear_combination_fit(e, norm, {f"{absorber}{v:+g}": refs[v] for v in refs}, e0=edge_e)
    return {"absorber": absorber, "edge_eV": edge_e, "valence_edge": xafs.oxidation_from_edge(edge_e, stds)["valence"],
            "valence": float(sum(w * v for w, v in zip(lcf["weights"].values(), refs))), "lcf_weights": lcf["weights"],
            "lcf_r_factor": lcf["r_factor"], "standards": stds, "curves": {"energy": e, "norm": norm}}


def bond_valence(refined: Structure, reference: Structure, absorber: str, rcut: float = 3.0) -> dict:
    """Bond-valence sum of `absorber` in the refined structure. R0 is calibrated on the database structure so
    that it carries its charge-balance valence; the result is the valence implied by the refined bond lengths.
    Without anion neighbours (metals, alloys) the valence is 0."""
    guess = reference.composition.oxi_state_guesses()
    formal = float(guess[0].get(absorber, 0.0)) if guess else 0.0

    def site_sums(st: Structure) -> list[float]:  # Σ exp(-d/b) over O neighbours, per absorber site
        return [sum(nb.species.get_atomic_fraction("O") * np.exp(-nb.nn_distance / B_BV) for nb in st.get_neighbors(site, rcut))
                for site in st if absorber in {sp.symbol for sp in site.species}]

    ref_sums = site_sums(reference)
    if formal <= 0 or not any(ref_sums):
        return {"valence": 0.0, "formal_valence": formal, "method": "no anion neighbours: metallic, valence 0"}
    r0 = B_BV * np.log(formal / np.mean(ref_sums))
    return {"valence": float(np.exp(r0 / B_BV) * np.mean(site_sums(refined))), "formal_valence": formal, "R0_A": float(r0),
            "b_A": B_BV, "method": "R0 calibrated so the database structure has its charge-balance valence"}


def analyze(folder: str | Path, references: str | Path | None = None) -> dict:
    folder = Path(folder)
    references = Path(references) if references else folder.parent.parent / "references"
    meta = load_inputs(folder)
    techs = set(meta["techniques"])
    cands = candidates(meta["composition"])
    out = {"sample_id": meta["sample_id"], "inputs": meta, "candidates": list(cands), "timings_s": {}, "errors": {}}

    def step(name, fn, *args):
        t0 = time.time()
        try:
            return fn(*args)
        except Exception as exc:  # one failed technique must not stop the others; the error is reported
            out["errors"][name] = f"{type(exc).__name__}: {exc}"
            return None
        finally:
            out["timings_s"][name] = round(time.time() - t0, 2)

    absorber = meta["instrument"].get("xafs", {}).get("edge", "").split()[0] if "xafs" in techs else None
    x_res = step("xrd", run_xrd, folder, meta, cands) if "xrd" in techs and cands else None
    p_res = step("pdf", run_pdf, folder, meta, cands, x_res) if "pdf" in techs and cands else None
    best = p_res["fits"][0] if p_res else None
    e_res = step("exafs", run_exafs, folder, meta, best["structure"]) if absorber and best else None
    n_res = step("xanes", run_xanes, folder, meta, references) if absorber else None
    b_res = step("bvs", bond_valence, best["structure"], cands[best["candidate"]], absorber) if absorber and best else None
    out.update(xrd=x_res, pdf=p_res, exafs=e_res, xanes=n_res, bvs=b_res)
    out["checks"] = [checks.c1_phase(x_res, p_res), checks.c2_bond_lengths(e_res, p_res, absorber),
                     checks.c3_coordination(e_res, p_res, absorber), checks.c4_oxidation(n_res, b_res),
                     checks.c5_disorder(e_res, p_res, absorber), checks.c6_size(x_res, p_res)]
    good = best and best["rw"] <= 2 * settings()["checks"]["C1_phase"]["pdf_good_rw"]
    out["phase"] = best["candidate"] if good else (x_res["ranking"][0]["phase"] if x_res and not best else None)
    out["timings_s"]["total"] = round(sum(out["timings_s"].values()), 2)
    return out


def to_json(obj):
    """JSON-safe copy: arrays to lists, structures to CIF text, non-finite floats to null."""
    if isinstance(obj, dict):
        return {str(k): to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [to_json(v) for v in obj.tolist()]
    if isinstance(obj, Structure):
        return obj.to(fmt="cif")
    if isinstance(obj, (np.floating, float)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, (np.integer, np.bool_)):
        return obj.item()
    return obj


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the deterministic XRD + PDF + XAFS analysis and checks C1-C6 on one sample folder.")
    ap.add_argument("sample", type=Path)
    ap.add_argument("--references", type=Path, default=None, help="folder with <El>_v<valence>.dat XANES standards")
    ap.add_argument("--out", type=Path, default=None, help="write analysis.json here")
    a = ap.parse_args()
    res = analyze(a.sample, a.references)
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / "analysis.json").write_text(json.dumps(to_json(res)))
    print(f"{res['sample_id']}: phase {res['phase']}  ({res['timings_s']['total']} s)")
    for c in res["checks"]:
        print(f"  {c['id']} {c['status']:<4} {c['name']}: {c['explanation']}")
    for k, v in res["errors"].items():
        print(f"  error in {k}: {v}")


if __name__ == "__main__":
    main()
