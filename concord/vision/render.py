"""Deterministic fit plots: fixed size, dpi and style, no timestamps, so the same fit gives the same image."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

STYLE = {"figure.figsize": (7.0, 5.0), "figure.dpi": 110, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
         "svg.hashsalt": "concord"}
PREDICTED = "PREDICTED, NOT MEASURED"


def fit_plot(x, obs, calc, path: Path, *, xlabel: str, ylabel: str, title: str, band=None, predicted: bool = False) -> str:
    """Data + model (top) and difference (bottom). band: optional (low, high) envelope drawn behind the model."""
    x, obs, calc = (np.asarray(v, float) for v in (x, obs, calc))
    with plt.rc_context(STYLE):
        fig, (top, bottom) = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        if band is not None:
            top.fill_between(x, band[0], band[1], color="#e8a33d", alpha=0.35, lw=0, label="ensemble band")
        if not predicted:
            top.plot(x, obs, ".", ms=2, color="#1f4e79", label="data")
        top.plot(x, calc, "-", lw=1.2, color="#c0392b", label="prediction" if predicted else "model")
        top.set_ylabel(ylabel)
        top.set_title(title)
        top.legend(loc="upper right")
        if predicted:
            top.text(0.02, 0.92, PREDICTED, transform=top.transAxes, color="#c0392b", weight="bold")
        else:
            bottom.plot(x, obs - calc, "-", lw=0.8, color="#555555")
        bottom.axhline(0, color="k", lw=0.5)
        bottom.set_xlabel(xlabel)
        bottom.set_ylabel("difference")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    return str(path)


def fit_curves(res: dict) -> dict[str, dict]:
    """{technique: {x, obs, calc, xlabel, ylabel, title, step}} from an analysis result. `step` is the spacing of
    independent points (for residual statistics on oversampled data)."""
    out = {}
    if (x := res.get("xrd")) and "calc" in x["curves"]:
        c = x["curves"]
        out["xrd"] = {"x": c["two_theta"], "obs": c["corrected"], "calc": c["calc"], "xlabel": "2θ (deg)", "ylabel": "intensity (bkg removed)",
                      "title": f"XRD vs simulated {x['ranking'][0]['phase']}", "step": None}
    if p := res.get("pdf"):
        f = p["fits"][0]
        c = f["curves"]
        out["pdf"] = {"x": c["r"], "obs": c["obs"], "calc": c["calc"], "xlabel": "r (Å)", "ylabel": "G(r) (Å⁻²)",
                      "title": f"PDF fit, {f['candidate']} (Rw {f['rw']:.3f})", "step": np.pi / f["qmax"]}
    if e := res.get("exafs"):
        c, w = e["fit"]["curves"], e["fit"]["window"]
        r = np.asarray(c["r"])
        m = (r >= w["rmin"] - 0.5) & (r <= w["rmax"] + 0.5)
        out["exafs"] = {"x": r[m], "obs": np.asarray(c["chir_mag_data"])[m], "calc": np.asarray(c["chir_mag_model"])[m],
                        "xlabel": "R (Å, not phase corrected)", "ylabel": "|χ(R)| (Å⁻³)",
                        "title": f"EXAFS fit, {e['absorber']} {e['edge']} (R-factor {e['fit']['rfactor']:.4f})",
                        "step": np.pi / (2 * (w["kmax"] - w["kmin"])), "window": (w["rmin"], w["rmax"])}
    return out
