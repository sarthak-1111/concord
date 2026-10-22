"""Visual-inspection loop. Every fit is plotted deterministically (XRD with reflection ticks, PDF, EXAFS in k and R
space, plus a zoom on the window of largest misfit), inspected by the eye module or the open fallback judge, and paired
with numerical and physicality criteria: a fit is accepted only if both pass. For a rejected fit, the inspector's
suggested fix (one of the deterministic re-fits in judge.FIXES) is tried; it is kept only when its own tolerance
confirms an improvement and the visual verdict does not get worse, otherwise it is reverted. At most
vision.max_iterations rounds per technique."""
from pathlib import Path

import numpy as np

from concord.config import settings
from concord.vision import eye_adapter, judge
from concord.vision.features import residual_features
from concord.vision.render import PREDICTED, exafs_plot, fit_curves, fit_plot, zoom_window

RANK = {"reject": 0, "accept": 1}


def virtual_plot(res: dict, out_dir: Path) -> str | None:
    """Predicted |χ(R)| band, with the measured |χ(R)| for comparison when there is one. Labelled as a prediction."""
    v = res.get("virtual_xafs")
    if not v:
        return None
    meas = (res.get("exafs") or {}).get("curves")
    obs = np.interp(v["r"], meas["r"], meas["chir_mag"]) if meas else None  # same transform, on the prediction's grid
    title = f"Virtual EXAFS {v['absorber']} {v['edge']} from the PDF model — {PREDICTED}"
    return fit_plot(v["r"], obs, v["chir_median"], out_dir / "virtual_xafs.png", xlabel="R (Å, not phase corrected)",
                    ylabel="|χ(R)| (Å⁻³)", title=title, band=(v["chir_lo"], v["chir_hi"]), predicted=True)


def _plot(tech: str, c: dict, path: Path, xlim=None) -> str:
    if tech == "exafs" and xlim is None:
        return exafs_plot(c, path, title=c["title"])
    title = c["title"] + (f", zoom {xlim[0]:.2f}–{xlim[1]:.2f}" if xlim else "")
    return fit_plot(c["x"], c["obs"], c["calc"], path, xlabel=c["xlabel"], ylabel=c["ylabel"], title=title, ticks=c.get("ticks"), xlim=xlim)


def _zoom(tech: str, c: dict, out_dir: Path) -> str:
    return _plot(tech, c, out_dir / f"{tech}_zoom.png", xlim=zoom_window(c["x"], c["obs"], c["calc"], c.get("sigma")))


def plots(res: dict, out_dir: Path) -> dict[str, str]:
    """Fit plots, a zoom on each fit's largest misfit and the virtual XAFS band, without inspection (fast mode, UI)."""
    out = {}
    for tech, c in fit_curves(res).items():
        out[tech], out[f"{tech}_zoom"] = _plot(tech, c, out_dir / f"{tech}_fit.png"), _zoom(tech, c, out_dir)
    if vp := virtual_plot(res, out_dir):
        out["virtual_xafs"] = vp
    return out


def physical(technique: str, res: dict) -> list[str]:
    """Physically impossible or undetermined parameters of a fit."""
    bad = []
    if technique == "pdf":
        f = res["pdf"]["fits"][0]
        for el, u in f["uiso"].items():
            if u <= 0:
                bad.append(f"U_iso({el}) {u:.4f} Å² is not positive")
            elif (err := f.get("uiso_err", {}).get(el)) and err > u:
                bad.append(f"U_iso({el}) {u:.4f} ± {err:.4f} Å² is undetermined")
        ref = f.get("lattice_ref") or {}
        bad += [f"lattice {k} at its ±3 % bound" for k, v in f["lattice"].items() if k in ref and abs(v / ref[k] - 1) > 0.0295]
        if f.get("psize_nm") is not None and (f["psize_nm"] <= 0 or (f.get("psize_err_nm") or 0) > f["psize_nm"]):
            bad.append(f"particle size {f['psize_nm']:.2f} nm is undetermined")
    if technique == "exafs":
        fit = res["exafs"]["fit"]
        for s in (s for s in fit["shells"] if not s.get("extra")):
            if s["N"] < 0 or (s.get("N_err") or 0) > max(s["N"], 1.0):
                bad.append(f"N({s['neighbor']}) {s['N']:.2f} is undetermined")
            if not 0.0005 + 1e-6 < s["sigma2"] < 0.05 - 1e-6:
                bad.append(f"σ²({s['neighbor']}) {s['sigma2']:.4f} Å² sits at a bound")
        if abs(fit["e0_shift"]) > 10:
            bad.append(f"E0 shift {fit['e0_shift']:.1f} eV beyond ±10 eV")
    return bad


def numerical(technique: str, res: dict, features: dict) -> tuple[bool, str]:
    v = settings()["vision"]
    if technique != "xrd" and features["durbin_watson"] < v["durbin_watson_min"]:
        return False, f"Durbin-Watson {features['durbin_watson']:.2f} < {v['durbin_watson_min']} on independent points"
    if technique == "pdf" and (rw := res["pdf"]["fits"][0]["rw"]) > settings()["checks"]["C1_phase"]["pdf_good_rw"]:
        return False, f"Rw {rw:.3f} above {settings()['checks']['C1_phase']['pdf_good_rw']}"
    if technique == "exafs" and (rf := res["exafs"]["fit"]["rfactor"]) > v["exafs_rfactor_max"]:
        return False, f"R-factor {rf:.4f} above {v['exafs_rfactor_max']}"
    if technique == "xrd" and (a := res["xrd"]["ranking"][0]["obs_area_fraction_explained"]) < v["xrd_area_explained_min"]:
        return False, f"best phase explains {a:.2f} of the peak area, below {v['xrd_area_explained_min']}"
    if bad := physical(technique, res):
        return False, "; ".join(bad)
    return True, "within limits"


def _eye() -> tuple:
    try:
        return eye_adapter.load(), None
    except eye_adapter.EyeUnavailable as exc:
        return None, str(exc)


def inspect_one(tech: str, res: dict, out_dir: Path, xlim=None, eye: tuple | None = None) -> dict:
    """Plot one fit (zoomed on xlim if given), then the visual verdict (eye module or fallback judge) and the
    numerical and physicality verdict."""
    eye_mod, eye_error = eye or _eye()
    c = fit_curves(res)[tech]
    path = _plot(tech, c, out_dir / (f"{tech}_fit.png" if xlim is None else f"{tech}_{xlim[0]:.2f}-{xlim[1]:.2f}.png"), xlim)
    x, obs, calc = (np.asarray(c[k], float) for k in ("x", "obs", "calc"))
    if (lim := xlim or c.get("window")) is not None:  # judged inside the fit window; the plot shows a margin around it
        m = (x >= lim[0]) & (x <= lim[1])
        x, obs, calc = x[m], obs[m], calc[m]
    v = settings()["vision"]
    feats = residual_features(x, obs, calc, c["step"], dw_min=v["durbin_watson_min"], peak_width=c.get("peak_width", 1.0), peak_min=v["xrd_peak_min"])
    context = {"title": c["title"], "x_axis": c["xlabel"], "fit_window": c.get("window"), "zoom": xlim}
    visual = eye_adapter.inspect(eye_mod, path, context) if eye_mod else judge.judge(tech, feats, context)
    ok, why = numerical(tech, res, feats)
    return {"plot": path, "features": feats, "visual": visual, "numerical": {"ok": ok, "reason": why},
            "accepted": visual["verdict"] == "accept" and ok, **({"eye_error": eye_error} if eye_error else {})}


def inspect_fits(res: dict, out_dir: Path, run: dict | None = None) -> dict:
    """Inspect every fit. With `run` (folder, meta, res), a rejected fit gets the inspector's suggested fix; res is
    updated in place (and its checks recomputed) only for fixes that are kept."""
    from concord.agents.resolver import run_action  # the resolver imports the analysis: imported late
    eye, out, changed = _eye(), {}, False
    if vp := virtual_plot(res, out_dir):
        out["virtual_xafs"] = {"plot": vp}
    for tech in fit_curves(res):
        state, steps = inspect_one(tech, res, out_dir, eye=eye), []
        for i in range(settings()["vision"]["max_iterations"]):
            fix = next((x["suggested_action"] for x in state["visual"]["issues"] if x["suggested_action"] in judge.FIXES.get(tech, {})), None)
            if state["accepted"] or run is None or fix is None:
                break
            result, finding = run_action({**run, "res": res}, fix, {})
            step = {"iteration": i + 1, "action": fix, "finding": finding, "kept": False}
            if result.get("confirms") and result.get("_new") is not None:
                trial = inspect_one(tech, {**res, tech: result["_new"]}, out_dir / "trial", eye=eye)
                if RANK[trial["visual"]["verdict"]] >= RANK[state["visual"]["verdict"]]:
                    res[tech], changed, step["kept"] = result["_new"], True, True
                    state = {**trial, "plot": _plot(tech, fit_curves(res)[tech], out_dir / f"{tech}_fit.png")}
            steps.append(step)
            if not step["kept"]:  # reverted: the fit stays as it was and no further fix is tried
                break
        _zoom(tech, fit_curves(res)[tech], out_dir)
        out[tech] = {**state, "steps": steps}
    if changed:
        from concord.analysis import run_checks
        res["checks"] = run_checks(res)
    return out
