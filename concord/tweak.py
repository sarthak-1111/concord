"""Tweak and re-fit: the settings a user may change per technique, a quick re-fit of one technique with the checks
C1–C7 recomputed against the rest of a saved analysis, and a full re-analysis with the settings the user keeps.

Parameter names are the keyword arguments of the runners in concord.analysis (run_xrd, run_pdf, run_exafs), so
values pass straight through. Not adjustable: which PDF parameters are refined (fit_pdf refines a fixed staged set)
and the XANES fit (it has no fit curve to show).
"""
import time
from pathlib import Path

import numpy as np
from pymatgen.core import Lattice, Structure

from concord.analysis import analyze, candidates, from_pdf_model, run_checks, run_exafs, run_pdf, run_xrd, to_json
from concord.vision.render import fit_curves

TECHNIQUES = ("xrd", "pdf", "exafs", "xanes")
MAX_POINTS = 1500
# (low, high, smallest span) pairs checked after merging the values
SPANS = {"xrd": [("two_theta_min", "two_theta_max", 10.0)], "pdf": [("rmin", "rmax", 5.0)],
         "exafs": [("kmin", "kmax", 4.0), ("rmin", "rmax", 0.5)]}
PROBE_NEIGHBORS = ["O", "N", "C", "S", "Cl"]


def _p(name, label, kind, value, default, lo=None, hi=None, step=None, unit=None, help="", choices=None) -> dict:
    if lo is not None:  # the analysis's own values always validate
        lo, hi = min(lo, value, default), max(hi, value, default)
    return {"name": name, "label": label, "kind": kind, "value": value, "default": default, "min": lo, "max": hi, "step": step,
            "choices": choices, "unit": unit, "help": help}


def params(analysis: dict, technique: str) -> list[dict]:
    """The settings a user may change for `technique`, with the values this analysis used ([] when the technique
    was not fitted or has nothing adjustable)."""
    if technique not in TECHNIQUES:
        raise ValueError(f"unknown technique '{technique}'; one of {', '.join(TECHNIQUES)}")
    res = analysis.get(technique)
    if not res or technique == "xanes":
        return []
    user = (analysis["inputs"].get("user_settings") or {}).get(technique, {})
    if technique == "xrd":
        tt = res["curves"]["two_theta"]
        # shortcut: an upload (no two_theta_range) whose 2θ range a kept setting narrowed cannot widen it again; read the data if needed
        r = analysis["inputs"]["instrument"]["xrd"].get("two_theta_range") or (tt[0], tt[-1])
        lo, hi = float(min(tt[0], r[0])), float(max(tt[-1], r[1]))  # the data span, also where sample.json rounds it
        return [
            _p("two_theta_min", "2θ from", "float", float(tt[0]), lo, lo, hi, 0.1, "deg", "Lowest diffraction angle used in the fit."),
            _p("two_theta_max", "2θ to", "float", float(tt[-1]), hi, lo, hi, 0.1, "deg", "Highest diffraction angle used in the fit."),
            _p("baseline_log10_lambda", "Background stiffness (log10 λ)", "float", user.get("baseline_log10_lambda", 8.0), 8.0, 4.0, 10.0, 0.25,
               None, "Higher values make the subtracted background follow only slow trends, lower values let it eat into broad peaks."),
            _p("smoothing_window", "Smoothing window", "int", user.get("smoothing_window", 11), 11, 5, 51, 2, "points",
               "Width of the Savitzky-Golay smoothing applied before peak search, rounded up to an odd number."),
            _p("peak_height", "Peak detection height", "float", user.get("peak_height", 0.03), 0.03, 0.005, 0.5, 0.005, "of max",
               "Smallest peak height searched for, as a fraction of the strongest point of the pattern."),
            _p("peak_prominence", "Peak detection prominence", "float", user.get("peak_prominence", 0.02), 0.02, 0.005, 0.5, 0.005, "of max",
               "How far a peak must rise above its surroundings, as a fraction of the strongest point of the pattern."),
        ]
    if technique == "pdf":
        f = res["fits"][0]
        return [
            _p("candidate", "Candidate phase", "choice", f["candidate"], min(res["fits"], key=lambda x: x["rw"])["candidate"],
               help="Structure refined as the PDF model; the default is the one with the lowest Rw.", choices=list(analysis["candidates"])),
            _p("rmin", "r from", "float", f["r_range"][0], 1.5, 0.5, 5.0, 0.1, "Å", "Shortest distance of G(r) included in the fit."),
            _p("rmax", "r to", "float", f["r_range"][1], 25.0, 8.0, 40.0, 0.5, "Å",
               "Longest distance of G(r) included in the fit; longer ranges fit more slowly."),
            _p("qdamp", "Qdamp", "float", f["qdamp"], analysis["inputs"]["instrument"]["pdf"]["qdamp"], 0.0, 0.1, 0.001, "Å⁻¹",
               "Instrument resolution damping of G(r), normally fixed by a calibration standard."),
            _p("envelope", "Nanoparticle envelope", "bool", f["psize_nm"] is not None, True,
               help="Multiply the model by a spherical particle envelope and refine the particle diameter."),
        ]
    w, shells = res["fit"]["window"], [s for s in res["fit"]["shells"] if not s.get("extra")]
    kmax0 = min(12.0, float(analysis["inputs"]["instrument"]["xafs"].get("kmax", 12.0)))
    return [
        _p("kmin", "k from", "float", w["kmin"], 3.0, 1.5, 6.0, 0.1, "Å⁻¹", "Lowest photoelectron wavenumber used in the fit."),
        _p("kmax", "k to", "float", w["kmax"], kmax0, 6.0, float(max(res["curves"]["k"])), 0.1, "Å⁻¹",
           "Highest photoelectron wavenumber used; noisy data at high k widen the error bars."),
        _p("rmin", "R from", "float", w["rmin"], 1.0, 0.5, 3.0, 0.05, "Å", "Start of the R window fitted in the Fourier transform."),
        _p("rmax", "R to", "float", w["rmax"], min(s["reff_A"] for s in shells) + 1.0, 1.5, 6.0, 0.05, "Å",
           "End of the R window fitted; the default is the nearest neighbour distance plus 1 Å."),
        _p("kweight", "k-weight", "int", int(w["kweight"]), 2, 1, 3, 1, None, "Power of k that weights χ(k); higher values stress the high-k data."),
        _p("probe", "Probe shell", "choice", user.get("probe", "auto"), "auto",
           help="Test for a shell the model lacks: auto keeps it only when significant, on always keeps it, off skips the test.",
           choices=["auto", "on", "off"]),
        _p("probe_neighbor", "Probe neighbour", "choice", user.get("probe_neighbor", "O"), "O",
           help="Element of the probe shell, for example O for a surface oxide.", choices=PROBE_NEIGHBORS),
        _p("probe_r", "Probe distance", "float", user.get("probe_r", 2.0), 2.0, 1.6, 2.8, 0.05, "Å",
           "Starting distance of the probe shell, which may move by 0.15 Å in the fit."),
    ]


def _check(spec: list[dict], technique: str, values: dict) -> dict:
    """The given values, validated against `spec` and coerced to their kind."""
    by = {p["name"]: p for p in spec}
    out = {}
    for name, v in values.items():
        if (p := by.get(name)) is None:
            raise ValueError(f"{technique} has no setting '{name}'" + (f"; it has {', '.join(by)}" if by else ""))
        if p["kind"] == "bool":
            if not isinstance(v, bool):
                raise ValueError(f"{p['label']} must be true or false")
        elif p["kind"] == "choice":
            if v not in p["choices"]:
                raise ValueError(f"{p['label']} must be one of {', '.join(map(str, p['choices']))}")
        else:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or (p["kind"] == "int" and v != int(v)):
                raise ValueError(f"{p['label']} must be {'a whole number' if p['kind'] == 'int' else 'a number'}")
            v = int(v) if p["kind"] == "int" else float(v)
            if not p["min"] <= v <= p["max"]:
                raise ValueError(f"{p['label']} {v:g} is outside the allowed range {p['min']:g} to {p['max']:g}" + (f" {p['unit']}" if p["unit"] else ""))
        out[name] = v
    merged = {**{p["name"]: p["value"] for p in spec}, **out}
    for lo, hi, span in SPANS.get(technique, []):
        if merged[hi] - merged[lo] < span:
            raise ValueError(f"{by[lo]['label']} {merged[lo]:g} to {merged[hi]:g} is too narrow: the range must span at least {span:g}"
                             + (f" {by[lo]['unit']}" if by[lo]["unit"] else ""))
    return out


def _metrics(technique: str, res: dict) -> dict:
    if technique == "xrd":
        r0 = res["ranking"][0]
        return {"phase": r0["phase"], "score": r0["score"], "profile_corr": r0["profile_corr"], "area_explained": r0["obs_area_fraction_explained"],
                "ranking": [{"phase": r["phase"], "score": r["score"]} for r in res["ranking"]], "n_peaks": res["n_peaks"],
                "n_indexed": res["n_indexed"], "sphere_diameter_nm": res["sphere_diameter_nm"], "scherrer_median_nm": res["scherrer_median_nm"],
                "peak_rel_intensity": res["peak_rel_intensity"]}
    if technique == "pdf":
        f = res["fits"][0]
        return {"candidate": f["candidate"], "rw": f["rw"], "chi2_reduced": f["chi2_reduced"], "lattice": f["lattice"],
                "lattice_ref": f["lattice_ref"], "psize_nm": f["psize_nm"], "psize_err_nm": f["psize_err_nm"], "delta2": f["delta2"],
                "uiso": f["uiso"], "r_range": f["r_range"], "ranking": [{"candidate": x["candidate"], "rw": x["rw"]} for x in res["fits"]]}
    fit = res["fit"]
    return {"rfactor": fit["rfactor"], "chi2_reduced": fit["chi2_reduced"], "e0_shift": fit["e0_shift"],
            "shells": [{k: s[k] for k in ("neighbor", "N", "N_err", "R_A", "R_err", "sigma2")} | {"extra": bool(s.get("extra"))} for s in fit["shells"]],
            "extra_shell": res["extra_shell"], "window": fit["window"]}


def _model(fit: dict, cands: dict) -> Structure:
    """The refined structure of a saved PDF fit, rebuilt as fit_pdf builds it: unlike its CIF text, this reproduces
    the saved EXAFS fit exactly."""
    s = cands[fit["candidate"]].copy()
    s.lattice = Lattice.from_parameters(*(fit["lattice"][k] for k in "abc"), *s.lattice.angles)
    return s


def refit(folder: str | Path, analysis: dict, technique: str, values: dict) -> dict:
    """Re-fit one technique with `values` (other settings as in `analysis`) and recompute C1–C7 against the rest of
    the saved analysis. A PDF re-fit refines only the chosen candidate (the others keep their saved fits) and also
    recomputes the bond-valence sum and virtual XAFS, which read only the PDF model; the EXAFS fit keeps its saved
    model. `apply` re-runs everything."""
    t0 = time.time()
    spec = params(analysis, technique)
    if not spec:
        raise ValueError(f"{technique} has no adjustable settings in this analysis")
    used = {**{p["name"]: p["value"] for p in spec}, **_check(spec, technique, values)}
    folder, meta, new = Path(folder), analysis["inputs"], dict(analysis)
    cands = candidates(meta["composition"])
    if technique == "xrd":
        new["xrd"] = run_xrd(folder, meta, cands, **used)
    elif technique == "pdf":
        fit = run_pdf(folder, meta, {used["candidate"]: cands[used["candidate"]]}, analysis.get("xrd"), **used)["fits"][0]
        others = sorted(({**f, "structure": _model(f, cands)} for f in analysis["pdf"]["fits"] if f["candidate"] != fit["candidate"]),
                        key=lambda f: f["rw"])
        new["pdf"] = {**analysis["pdf"], "fits": [fit] + others}
        new["bvs"], new["virtual_xafs"] = from_pdf_model(folder, meta, new["pdf"], cands)
    else:
        new["exafs"] = run_exafs(folder, meta, _model(analysis["pdf"]["fits"][0], cands), **used)
    checks = to_json(run_checks(new))
    c = fit_curves(new)[technique]
    idx = np.unique(np.linspace(0, len(c["x"]) - 1, min(len(c["x"]), MAX_POINTS)).round().astype(int))
    x, obs, calc = (np.asarray(c[k], float)[idx] for k in ("x", "obs", "calc"))
    before = {ch["id"]: ch["status"] for ch in analysis["checks"]}
    return to_json({"technique": technique, "values": used,
                    "curve": {"title": c["title"], "x_label": c["xlabel"], "y_label": c["ylabel"], "x": x, "obs": obs, "calc": calc,
                              "diff": obs - calc, "ticks": c.get("ticks"), "window": c.get("window")},
                    "metrics": _metrics(technique, new[technique]), "checks": checks,
                    "changed": [{"id": ch["id"], "from": before.get(ch["id"]), "to": ch["status"]} for ch in checks if before.get(ch["id"]) != ch["status"]],
                    "timing_s": round(time.time() - t0, 2)})


def apply(folder: str | Path, analysis: dict, overrides: dict[str, dict]) -> dict:
    """Full re-analysis with the user's settings ({technique: {name: value}}, validated as in refit), as analyze's
    JSON with the settings under inputs.user_settings. Settings not given keep analyze's defaults."""
    used = {tech: _check(params(analysis, tech), tech, vals) for tech, vals in (overrides or {}).items() if vals}
    return to_json(analyze(folder, composition=analysis["inputs"]["composition"], overrides=used or None))
