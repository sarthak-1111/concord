"""Visual-inspection step: deterministic plot → eye module (or the open fallback judge) → verdict. A fit is accepted
only if the visual verdict and the numerical criteria both pass."""
from pathlib import Path

from concord.config import settings
from concord.vision import eye_adapter, judge
from concord.vision.features import residual_features
from concord.vision.render import fit_curves, fit_plot


def numerical(technique: str, res: dict, features: dict) -> tuple[bool, str]:
    v = settings()["vision"]
    if features["durbin_watson"] < v["durbin_watson_min"] and technique != "xrd":
        return False, f"Durbin-Watson {features['durbin_watson']:.2f} < {v['durbin_watson_min']} on independent points"
    if technique == "pdf" and (rw := res["pdf"]["fits"][0]["rw"]) > settings()["checks"]["C1_phase"]["pdf_good_rw"]:
        return False, f"Rw {rw:.3f} above {settings()['checks']['C1_phase']['pdf_good_rw']}"
    if technique == "exafs" and (rf := res["exafs"]["fit"]["rfactor"]) > v["exafs_rfactor_max"]:
        return False, f"R-factor {rf:.4f} above {v['exafs_rfactor_max']}"
    if technique == "xrd" and (a := res["xrd"]["ranking"][0]["obs_area_fraction_explained"]) < v["xrd_area_explained_min"]:
        return False, f"best phase explains {a:.2f} of the peak area, below {v['xrd_area_explained_min']}"
    return True, "within limits"


def inspect_fits(res: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        eye = eye_adapter.load()
    except eye_adapter.EyeUnavailable as exc:
        eye, eye_error = None, str(exc)
    else:
        eye_error = None
    out = {}
    for tech, c in fit_curves(res).items():
        path = fit_plot(c["x"], c["obs"], c["calc"], out_dir / f"{tech}_fit.png", xlabel=c["xlabel"], ylabel=c["ylabel"], title=c["title"])
        feats = residual_features(c["x"], c["obs"], c["calc"], c["step"], dw_min=settings()["vision"]["durbin_watson_min"])
        context = {"title": c["title"], "x_axis": c["xlabel"], "fit_window": c.get("window")}
        visual = eye_adapter.inspect(eye, path, context) if eye else judge.judge(tech, feats, context)
        ok, why = numerical(tech, res, feats)
        out[tech] = {"plot": path, "features": feats, "visual": visual, "numerical": {"ok": ok, "reason": why},
                     "accepted": visual["verdict"] == "accept" and ok, **({"eye_error": eye_error} if eye_error else {})}
    return out
