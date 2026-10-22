"""Deterministic re-runs that settle a critic's objection. Each action returns (result, finding): numbers from
tools, a one-line templated finding, and result["confirms"]: whether the re-run supports the objection, decided by
the same tolerances the checks use (config.yaml), never by the LLM. The critic may only request actions in ACTIONS.
Re-fits also return the new technique result under "_new" (private: never put into the evidence), which the
visual-inspection loop uses as a fix."""
import inspect
from pathlib import Path

import numpy as np
from pymatgen.core import Structure

from concord.analysis import candidates
from concord.config import settings
from concord.tools import pdf as pdft
from concord.tools import xafs, xrd

ACTIONS = {
    "pdf_fit_candidate": "Refine the PDF with another candidate phase. args: {candidate: name from sample.candidates}",
    "pdf_toggle_envelope": "Refit the best PDF candidate with the nanoparticle envelope switched on or off. args: {}",
    "exafs_probe_shell": "Add a shell the model lacks to the EXAFS fit. args: {neighbor: element symbol, distance_A: number}",
    "exafs_window_scan": "Refit EXAFS with kmax 10, 11 and 12 to test whether N and sigma2 are stable. args: {}",
    "xrd_size_strongest": "XRD sphere diameter from the strongest indexed reflection alone. args: {}",
    "xrd_add_phase": "Add a second candidate phase to the XRD model. args: {candidate: name from sample.candidates} or {} for the runner-up",
    "inspect_region": "Visual inspection of one fit zoomed on a window. args: {technique: xrd|pdf|exafs, x_min: number, x_max: number}",
}


def _pdf_args(run: dict) -> tuple:
    inst = run["meta"]["instrument"]["pdf"]
    r, g, dg = pdft.load_gr(run["folder"] / "pdf.gr")
    return (r, g, dg), {"qmax": inst["qmax"], "qdamp": inst["qdamp"], "qbroad": inst.get("qbroad", 0.0)}


def _fit_summary(f: dict) -> dict:
    return {"candidate": f["candidate"], "rw": f["rw"], "lattice": f["lattice"], "psize_nm": f["psize_nm"], "delta2": f["delta2"]}


def _structure(x) -> Structure:
    return x if isinstance(x, Structure) else Structure.from_str(x, fmt="cif")


def pdf_fit_candidate(run: dict, candidate: str) -> tuple[dict, str]:
    """Confirms when the other candidate fits the PDF better than the reported phase."""
    cands = candidates(run["meta"]["composition"])
    if candidate not in cands:
        return {"error": f"unknown candidate {candidate}", "confirms": False}, f"{candidate} is not in the candidate library {sorted(cands)}"
    data, kw = _pdf_args(run)
    fit = pdft.fit_pdf(*data, cands[candidate], label=candidate, **kw)
    best = run["res"]["pdf"]["fits"][0]
    better = candidate != best["candidate"] and fit["rw"] < best["rw"]
    return {**_fit_summary(fit), "confirms": better}, f"{candidate} refines to Rw {fit['rw']:.3f} against {best['rw']:.3f} for {best['candidate']}"


def pdf_toggle_envelope(run: dict) -> tuple[dict, str]:
    """Confirms when switching the particle envelope lowers Rw by more than 10 %."""
    best = run["res"]["pdf"]["fits"][0]
    data, kw = _pdf_args(run)
    nanoparticle = best["psize_nm"] is None
    fit = pdft.fit_pdf(*data, candidates(run["meta"]["composition"])[best["candidate"]], label=best["candidate"],
                       nanoparticle=nanoparticle, **kw)
    mode = "with" if nanoparticle else "without"
    fit["lattice_ref"] = best.get("lattice_ref")
    new = {**run["res"]["pdf"], "fits": sorted([fit] + run["res"]["pdf"]["fits"][1:], key=lambda f: f["rw"])}
    return ({**_fit_summary(fit), "confirms": fit["rw"] < 0.9 * best["rw"], "_new": new},
            f"{best['candidate']} {mode} the particle envelope: Rw {fit['rw']:.3f} (was {best['rw']:.3f})")


def _exafs_data(run: dict):
    k, chi = np.loadtxt(run["folder"] / "xafs_chi.k", unpack=True)
    xa = run["meta"]["instrument"]["xafs"]
    absorber, edge = xa["edge"].split()
    paths = xafs.structure_paths(_structure(run["res"]["pdf"]["fits"][0]["structure"]), absorber, edge)
    return k, chi, paths, xa["s02"], absorber, edge, min(12.0, float(xa.get("kmax", 12.0)))


def exafs_probe_shell(run: dict, neighbor: str = "O", distance_A: float = 2.0) -> tuple[dict, str]:
    """Confirms by the rule check C3 uses for a missing shell (N above extra_min_sigma σ, R-factor drop)."""
    k, chi, paths, s02, absorber, edge, kmax = _exafs_data(run)
    base = xafs.shell_fit(k, chi, paths, s02=s02, kmax=kmax)
    fit = xafs.shell_fit(k, chi, paths, s02=s02, kmax=kmax, extra=[xafs.probe_path(absorber, edge, neighbor, float(distance_A))])
    x = next(s for s in fit["shells"] if s.get("extra"))
    tol = settings()["checks"]["C3_coordination"]
    res = {"pair": f"{absorber}-{neighbor}", "N": x["N"], "N_err": x["N_err"], "R_A": x["R_A"],
           "rfactor_without": base["rfactor"], "rfactor_with": fit["rfactor"],
           "confirms": bool(x["N_err"] and x["N"] / x["N_err"] >= tol["extra_min_sigma"]
                            and fit["rfactor"] <= (1 - tol["extra_min_rfactor_drop"]) * base["rfactor"])}
    res["_new"] = {**run["res"]["exafs"], "fit": fit, "fit_without_extra": base,
                   "extra_shell": {k: res[k] for k in ("pair", "N", "N_err", "R_A", "rfactor_without", "rfactor_with")}
                   | {"sigma2": x["sigma2"], "significant": res["confirms"]}}
    err = f" ± {x['N_err']:.2f}" if x["N_err"] else ""
    return res, (f"adding {absorber}-{neighbor} gives N {x['N']:.2f}{err} at {x['R_A']:.2f} Å; R-factor "
                 f"{base['rfactor']:.4f} → {fit['rfactor']:.4f}")


def exafs_window_scan(run: dict) -> tuple[dict, str]:
    """Confirms (N not robust) when N moves by more than the C3 warning tolerance across the k ranges."""
    k, chi, paths, s02, *_ = _exafs_data(run)
    rows = []
    for kmax in (10.0, 11.0, 12.0):
        fit = xafs.shell_fit(k, chi, paths, s02=s02, kmax=kmax)
        rows += [{"kmax": kmax, "neighbor": s["neighbor"], "N": s["N"], "sigma2": s["sigma2"], "R_A": s["R_A"]} for s in fit["shells"]]
    span = {el: (min(r["N"] for r in rows if r["neighbor"] == el), max(r["N"] for r in rows if r["neighbor"] == el))
            for el in {r["neighbor"] for r in rows}}
    unstable = any(hi - lo > settings()["checks"]["C3_coordination"]["warn_abs"] for lo, hi in span.values())
    return ({"fits": rows, "N_range": span, "confirms": unstable},
            "N over kmax 10-12: " + ", ".join(f"{el} {lo:.2f}-{hi:.2f}" for el, (lo, hi) in span.items()))


def xrd_size_strongest(run: dict) -> tuple[dict, str]:
    """Confirms when the strongest reflection alone differs from the reported size by more than the C6 warning."""
    x = run["res"]["xrd"]
    rows = x["scherrer"]
    if not rows:
        return {"error": "no indexed reflection", "confirms": False}, "no reflection was indexed, so XRD gives no size"
    inst = run["meta"]["instrument"]["xrd"].get("caglioti_deg2")
    strongest = max((p for p in x["peaks"] if any(abs(p["two_theta"] - r["two_theta"]) < 1e-9 for r in rows)), key=lambda p: p["area"])
    d = xrd.scherrer_wh([strongest], x["wavelength_A"], instrument=inst)["sphere_diameter_nm"]
    off = abs(d - x["sphere_diameter_nm"]) / x["sphere_diameter_nm"] > settings()["checks"]["C6_size"]["warn_rel"]
    return ({"two_theta": strongest["two_theta"], "sphere_diameter_nm": d, "confirms": off},
            f"strongest reflection ({strongest['two_theta']:.2f}°) alone gives {d:.2f} nm against {x['sphere_diameter_nm']:.2f} nm")


def xrd_add_phase(run: dict, candidate: str | None = None) -> tuple[dict, str]:
    """Confirms when a second candidate phase (scales and background refined together, as for the first phase) lowers
    the residual RMS of the background-corrected pattern by more than 20 %."""
    x, cands = run["res"]["xrd"], candidates(run["meta"]["composition"])
    c, best = x["curves"], x["ranking"][0]["phase"]
    others = [o for o in ([candidate] if candidate else [r["phase"] for r in x["ranking"][1:]]) if o in cands and o != best]
    if not others:
        return {"error": "no other candidate phase", "confirms": False}, "there is no second candidate phase to try"
    tt, y, calc = (np.asarray(c[k], float) for k in ("two_theta", "corrected", "calc"))
    sim = lambda name: xrd.simulate_pattern(cands[name], tt, x["wavelength_A"], size_nm=x.get("scherrer_median_nm"),
                                            instrument=run["meta"]["instrument"]["xrd"].get("caglioti_deg2"),
                                            lorentz_fraction=x.get("lorentz_fraction"))
    s1, rms0 = sim(best), float(np.sqrt(np.mean((y - calc) ** 2)))
    trials = []
    for o in others:
        s2 = sim(o)
        coef, bkg = xrd.scale_with_background(tt, y, [s1, s2])
        trials.append((float(np.sqrt(np.mean((y - coef[0] * s1 - coef[1] * s2 - bkg) ** 2))), o, coef, s2, bkg))
    rms1, o, coef, s2, bkg = min(trials, key=lambda t: t[0])
    fit = coef[0] * s1 + coef[1] * s2 + bkg
    share = float(coef[1] * s2.sum() / max((coef[0] * s1 + coef[1] * s2).sum(), 1e-12))
    res = {"second_phase": o, "intensity_share": share, "rms_before": rms0, "rms_after": rms1, "confirms": bool(coef[1] > 0 and rms1 < 0.8 * rms0),
           "_new": {**x, "second_phase": o, "curves": {**c, "calc": fit, "background": bkg, "diff": y - fit}}}
    return res, f"adding {o} ({100 * share:.0f} % of the simulated intensity) takes the XRD residual RMS from {rms0:.4g} to {rms1:.4g}"


def inspect_region(run: dict, technique: str, x_min: float, x_max: float) -> tuple[dict, str]:
    """The critic's call to the eye module (or the fallback judge): one fit zoomed on [x_min, x_max]. Confirms
    (the fit is wrong there) when the verdict is reject."""
    from concord.vision.check import inspect_one  # the vision package imports this module: imported late
    v = inspect_one(technique, run["res"], Path(run["out_dir"]) / "zoom", xlim=(float(x_min), float(x_max)))
    res = {"technique": technique, "window": [float(x_min), float(x_max)], "verdict": v["visual"]["verdict"],
           "inspector": v["visual"]["inspector"], "issues": v["visual"]["issues"], "plot": v["plot"], "confirms": v["visual"]["verdict"] == "reject"}
    return res, f"{technique} fit between {float(x_min):g} and {float(x_max):g}: {v['visual']['verdict']} ({v['visual']['inspector']})"


def run_action(run: dict, action: str, args: dict | None) -> tuple[dict, str]:
    fn = globals().get(action) if action in ACTIONS else None
    if fn is None:
        return {"error": f"unknown action {action}", "confirms": False}, f"no such re-run: {action}"
    params = inspect.signature(fn).parameters
    args = {k: v for k, v in (args or {}).items() if k in params and k != "run"}  # the LLM may add arguments
    try:
        return fn(run, **args)
    except Exception as exc:  # a failed re-run is reported, not fatal
        return {"error": f"{type(exc).__name__}: {exc}", "confirms": False}, f"re-run {action} failed: {type(exc).__name__}"
