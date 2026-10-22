"""Deterministic per-sample analysis: XRD, then PDF, then EXAFS/XANES and virtual XAFS, then checks C1–C7.

Every number comes from a tool in concord.tools; the agents (generator, critic) only explain, challenge and
re-run tools. Inputs are what a user has: the data files plus the sample.json metadata (composition,
techniques, instrument). The ground truth and planted-fault records in sample.json are never read here.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from pymatgen.core import Composition, Element, Structure

from concord import checks
from concord.config import settings
from concord.data_builder.fetch import load_structures, systems
from concord.tools import pdf as pdft
from concord.tools import virtual_xafs, xafs, xrd

INPUT_KEYS = ("sample_id", "composition", "techniques", "instrument", "origin", "assumed")
B_BV = 0.37  # bond-valence softness b (Å), Brown & Altermatt (1985), doi:10.1107/S0108768185002063


FILES = {"xrd": ["xrd.xy"], "pdf": ["pdf.gr"], "xafs": ["xafs_mu.dat", "xafs_chi.k"]}
MIN_CRYSTALLITE_NM = 1.0  # a "peak" broader than a 1 nm sphere gives is amorphous scattering or background, not Bragg


def _header(path: Path) -> dict:
    return xrd._header(path) if path.exists() else {}


def infer_inputs(folder: Path, composition: str) -> dict:
    """sample.json-equivalent metadata for a folder of data files: techniques from the files present, instrument
    values from their '# key=value' headers, and defaults for the rest (listed under 'assumed')."""
    techs = [t for t, names in FILES.items() if any((folder / n).exists() for n in names)]
    if not techs:
        raise FileNotFoundError(f"{folder} has none of {sum(FILES.values(), [])}")
    hx, hp = _header(folder / "xrd.xy"), _header(folder / "pdf.gr")
    hxa = _header(folder / "xafs_mu.dat") or _header(folder / "xafs_chi.k")
    assumed = []

    def get(h: dict, key: str, default, label: str):
        if key in h:
            return float(h[key])
        assumed.append(f"{label}={default}")
        return default
    inst = {}
    if "xrd" in techs:
        inst["xrd"] = {"wavelength_A": get(hx, "wavelength_A", 1.5406, "xrd.wavelength_A"), "caglioti_deg2": None}
    if "pdf" in techs:
        inst["pdf"] = {"qmax": get(hp, "qmax", 25.0, "pdf.qmax"), "qdamp": get(hp, "qdamp", 0.04, "pdf.qdamp"),
                       "qbroad": get(hp, "qbroad", 0.0, "pdf.qbroad")}
    if "xafs" in techs:
        if "edge" not in hxa:
            raise ValueError("XAFS files need an '# edge=<El>_<edge>' header line, e.g. '# edge=Pt_L3'")
        assumed.append("xafs.s02=0.9")
        inst["xafs"] = {"edge": hxa["edge"].replace("_", " "), "s02": 0.9, "temperature_K": 300, "kmax": 12.0}
    return {"sample_id": folder.name, "composition": composition, "techniques": techs, "instrument": inst,
            "origin": "user", "assumed": assumed}


def load_inputs(folder: Path, composition: str | None = None) -> dict:
    """The analysis inputs: sample.json without its ground truth, or metadata inferred from the files."""
    folder = Path(folder)
    if (folder / "sample.json").exists():
        meta = json.loads((folder / "sample.json").read_text())
        out = {k: meta[k] for k in INPUT_KEYS if k in meta}
        return {**out, "composition": composition or out["composition"]}
    if not composition:
        raise ValueError(f"{folder} has no sample.json: give the composition, e.g. --composition Pt3Co")
    return infer_inputs(folder, composition)


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
    widest = lambda t: np.degrees(xrd.K_SPHERE_D * lam / (10 * MIN_CRYSTALLITE_NM * np.cos(np.radians(t / 2))))
    peaks = [p for p in xrd.find_and_fit_peaks(tt, y) if p["fwhm_deg"] <= widest(p["two_theta"])]
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
    calc = xrd.simulate_pattern(cands[ranking[0]["phase"]], tt, lam, size_nm=size_nm, instrument=inst, lorentz_fraction=size.get("lorentz_fraction"))
    (scale,), bkg = xrd.scale_with_background(tt, y, [calc])
    calc = scale * calc + bkg
    return {"wavelength_A": lam, "n_peaks": len(peaks), "n_indexed": len(indexed), "peaks": peaks, **size, "ranking": ranking,
            "reflections": [line["two_theta"] for line in ref],
            "peak_rel_intensity": max((p["height"] for p in indexed), default=0.0) / span,
            "curves": {"two_theta": tt, "obs": data["intensity"], "baseline": pre["baseline"], "corrected": y,
                       "calc": calc, "background": bkg, "diff": y - calc, "sigma": data["sigma"]}}


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
        raise ValueError(f"the XANES valence needs μ(E) of at least two {absorber} standards of known valence, as "
                         f"{absorber}_v<valence>.dat in a '{Path(references).name}' folder beside the sample folders")
    stds = [{"valence": v, "edge_eV": xafs.edge_position(*refs[v])} for v in refs]
    lcf = xafs.linear_combination_fit(e, norm, {f"{absorber}{v:+g}": refs[v] for v in refs}, e0=edge_e)
    return {"absorber": absorber, "edge_eV": edge_e, "valence_edge": xafs.oxidation_from_edge(edge_e, stds)["valence"],
            "valence": float(sum(w * v for w, v in zip(lcf["weights"].values(), refs))), "lcf_weights": lcf["weights"],
            "lcf_r_factor": lcf["r_factor"], "standards": stds, "curves": {"energy": e, "norm": norm}}


def default_edge(element: str) -> str:
    return "L3" if Element(element).Z >= 57 else "K"


def run_virtual_xafs(folder: Path, meta: dict, fits: list[dict], absorber: str, edge: str) -> dict:
    """Predicted EXAFS from the PDF-equivalent models; scored against the measured χ(k) when there is one (the
    prediction never sees it). C7 uses the per-candidate R-factors."""
    xa = meta["instrument"].get("xafs", {})
    s02, kmax = float(xa.get("s02", 0.9)), min(12.0, float(xa.get("kmax", 12.0)))
    pred = virtual_xafs.predict_exafs(fits, absorber, edge, s02=s02, kmax=kmax)
    measured = folder / "xafs_chi.k"
    if xa.get("edge") and xa["edge"].split()[0] != absorber:  # never score against another element's spectrum
        pred["recommendation"] = (f"The measured {xa['edge']} edge belongs to an element the refined model does not contain, so this "
                                  f"is the model's own {absorber} {edge} edge. " + pred["recommendation"])
    elif measured.exists():
        k, chi = np.loadtxt(measured, unpack=True)
        pred["vs_measured"] = virtual_xafs.score_against(pred, k, chi)
        pred["recommendation"] = "This edge was measured, so the prediction serves as a consistency check against the measurement."
        pred["per_candidate"] = {}
        for f in fits[:3]:
            try:
                one = virtual_xafs.predict_exafs([f], absorber, edge, s02=s02, kmax=kmax, n=4, rw_margin=0.0)
            except ValueError:  # absorber not in this candidate
                continue
            pred["per_candidate"][f["candidate"]] = virtual_xafs.score_against(one, k, chi)["rfactor_R"]
    return pred


def bond_valence(refined: Structure, reference: Structure, absorber: str, rcut: float = 3.0) -> dict:
    """Bond-valence sum of `absorber` in the refined structure. R0 is calibrated on the database structure so
    that it carries its charge-balance valence; the result is the valence implied by the refined bond lengths.
    Without anion neighbours (metals, alloys) the valence is 0."""
    if absorber not in {e.symbol for e in refined.composition.elements}:  # not a metal: the label or the edge is wrong
        return {"valence": 0.0, "formal_valence": 0.0, "absent": True,
                "method": f"{absorber} is not in the refined model {refined.composition.reduced_formula}"}
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


def analyze(folder: str | Path, references: str | Path | None = None, composition: str | None = None) -> dict:
    folder = Path(folder)
    references = Path(references) if references else folder.parent.parent / "references"
    meta = load_inputs(folder, composition)
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
    edge_meta = meta["instrument"].get("xafs", {}).get("edge", "").split()
    x_res = step("xrd", run_xrd, folder, meta, cands) if "xrd" in techs and cands else None
    p_res = step("pdf", run_pdf, folder, meta, cands, x_res) if "pdf" in techs and cands else None
    best = p_res["fits"][0] if p_res else None
    e_res = step("exafs", run_exafs, folder, meta, best["structure"]) if absorber and best else None
    n_res = step("xanes", run_xanes, folder, meta, references) if absorber else None
    b_res = step("bvs", bond_valence, best["structure"], cands[best["candidate"]], absorber) if absorber and best else None
    v_res = None
    if best:  # virtual XAFS for every sample: at the stated edge if the model has its element, else the heaviest cation's L3 or K edge
        heavy = max(_cations(best["structure"].composition.reduced_formula), key=lambda e: Element(e).Z)
        in_model = {e.symbol for e in best["structure"].composition.elements}
        v_abs, v_edge = edge_meta if len(edge_meta) == 2 and edge_meta[0] in in_model else (heavy, default_edge(heavy))
        v_res = step("virtual_xafs", run_virtual_xafs, folder, meta, p_res["fits"], v_abs, v_edge)
    out.update(xrd=x_res, pdf=p_res, exafs=e_res, xanes=n_res, bvs=b_res, virtual_xafs=v_res)
    out["checks"] = run_checks(out)
    good = best and best["rw"] <= 2 * settings()["checks"]["C1_phase"]["pdf_good_rw"]
    out["phase"] = best["candidate"] if good else (x_res["ranking"][0]["phase"] if x_res and not best else None)
    out["timings_s"]["total"] = round(sum(out["timings_s"].values()), 2)
    return out


def run_checks(res: dict) -> list[dict]:
    """C1-C7 from the technique results (also after a fit was improved by the visual-inspection loop)."""
    xa = res["inputs"]["instrument"].get("xafs", {})
    absorber = xa.get("edge", "").split()[0] if "xafs" in res["inputs"]["techniques"] and xa.get("edge") else None
    x, p, e, n, b, v = (res.get(k) for k in ("xrd", "pdf", "exafs", "xanes", "bvs", "virtual_xafs"))
    return [checks.c1_phase(x, p), checks.c2_bond_lengths(e, p, absorber), checks.c3_coordination(e, p, absorber),
            checks.c4_oxidation(n, b), checks.c5_disorder(e, p, absorber), checks.c6_size(x, p), checks.c7_joint(x, p, v)]


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
