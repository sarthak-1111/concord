"""Deterministic fit plots: fixed size, dpi and style, no timestamps, so the same fit gives the same image."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

STYLE = {"figure.figsize": (7.0, 5.0), "figure.dpi": 110, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
         "svg.hashsalt": "concord"}
PREDICTED = "PREDICTED, NOT MEASURED"


def fit_plot(x, obs, calc, path: Path, *, xlabel: str, ylabel: str, title: str, band=None, predicted: bool = False,
             ticks=None, xlim=None) -> str:
    """Data + model (top) and difference (bottom). obs may be None (model only). band: optional (low, high) envelope
    drawn behind the model. predicted: the model is a prediction, and the plot is stamped PREDICTED, NOT MEASURED.
    ticks: reflection positions of the model, drawn under the pattern. xlim: zoom window (y scaled to it)."""
    x, calc = np.asarray(x, float), np.asarray(calc, float)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        fig, (top, bottom) = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        if band is not None:
            top.fill_between(x, band[0], band[1], color="#e8a33d", alpha=0.35, lw=0, label="ensemble band (5-95 %)")
        if obs is not None:
            obs = np.asarray(obs, float)
            top.plot(x, obs, ".", ms=2, color="#1f4e79", label="measured" if predicted else "data")
            bottom.plot(x, obs - calc, "-", lw=0.8, color="#555555")
        else:
            bottom.text(0.5, 0.5, "nothing measured to compare", ha="center", va="center", transform=bottom.transAxes, color="#555555")
        top.plot(x, calc, "-", lw=1.2, color="#c0392b", label="prediction (median)" if predicted else "model")
        if xlim is not None:
            m = (x >= xlim[0]) & (x <= xlim[1])
            ys = np.concatenate([calc[m]] + ([np.asarray(obs, float)[m]] if obs is not None else []))
            pad = 0.08 * (ys.max() - ys.min() or 1.0)
            top.set_ylim(ys.min() - pad, ys.max() + pad)
            if obs is not None:
                dm = (np.asarray(obs, float) - calc)[m]
                bottom.set_ylim(dm.min() - 0.1 * (np.ptp(dm) or 1.0), dm.max() + 0.1 * (np.ptp(dm) or 1.0))
            bottom.set_xlim(*xlim)
        if ticks is not None and len(ticks):
            lo, hi = top.get_ylim()
            top.set_ylim(lo - 0.08 * (hi - lo), hi)
            top.plot(ticks, np.full(len(ticks), lo - 0.04 * (hi - lo)), "|", ms=14, mew=1.6, color="#1b5e20", label="reflections (model)")
        top.set_ylabel(ylabel)
        top.set_title(title)
        top.legend(loc="upper right")
        if predicted:
            top.text(0.02, 0.92, PREDICTED, transform=top.transAxes, color="#c0392b", weight="bold")
        bottom.axhline(0, color="k", lw=0.5)
        bottom.set_xlabel(xlabel)
        bottom.set_ylabel("measured - predicted" if predicted else "difference")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
    return str(path)


def exafs_plot(c: dict, path: Path, *, title: str) -> str:
    """EXAFS fit in k space (k²χ) and R space (|χ(R)|), each with its difference."""
    k, chi_d, chi_m = (np.asarray(c[key], float) for key in ("k", "chi_data", "chi_model"))
    with plt.rc_context({**STYLE, "figure.figsize": (10.0, 5.0)}):
        fig, ax = plt.subplots(2, 2, sharex="col", gridspec_kw={"height_ratios": [3, 1]})
        for col, (x, d, m, xl, yl) in enumerate([(k, k ** 2 * chi_d, k ** 2 * chi_m, "k (Å⁻¹)", "k²χ(k) (Å⁻²)"),
                                                 (c["x"], c["obs"], c["calc"], c["xlabel"], c["ylabel"])]):
            x, d, m = (np.asarray(v, float) for v in (x, d, m))
            ax[0, col].plot(x, d, ".", ms=2, color="#1f4e79", label="data")
            ax[0, col].plot(x, m, "-", lw=1.2, color="#c0392b", label="model")
            ax[0, col].set_ylabel(yl)
            ax[1, col].plot(x, d - m, "-", lw=0.8, color="#555555")
            ax[1, col].axhline(0, color="k", lw=0.5)
            ax[1, col].set_xlabel(xl)
            ax[1, col].set_ylabel("difference")
        ax[0, 1].legend(loc="upper right")
        fig.suptitle(title)
        fig.tight_layout()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path)
        plt.close(fig)
    return str(path)


def zoom_window(x, obs, calc, sigma=None, frac: float = 0.15) -> tuple[float, float]:
    """The x window (frac of the span) where the mean |obs - calc| / uncertainty is largest. Without an uncertainty,
    a robust estimate of the residual noise stands in for it."""
    x, d = np.asarray(x, float), np.abs(np.asarray(obs, float) - np.asarray(calc, float))
    s = np.asarray(sigma, float) if sigma is not None else np.full_like(d, 1.4826 * np.median(np.abs(d - np.median(d))) or 1.0)
    n = max(3, int(frac * len(x)))
    i = int(np.argmax(np.convolve(d / np.where(s > 0, s, np.inf), np.ones(n) / n, mode="valid")))
    return float(x[i]), float(x[i + n - 1])


def fit_curves(res: dict) -> dict[str, dict]:
    """{technique: {x, obs, calc, xlabel, ylabel, title, step}} from an analysis result. `step` is the spacing of
    independent points (for residual statistics on oversampled data)."""
    out = {}
    if (x := res.get("xrd")) and "calc" in x["curves"]:
        c = x["curves"]
        out["xrd"] = {"x": c["two_theta"], "obs": c["corrected"], "calc": c["calc"], "xlabel": "2θ (deg)", "ylabel": "intensity (bkg removed)",
                      "title": f"XRD vs simulated {x['ranking'][0]['phase']}" + (f" + {x['second_phase']}" if x.get("second_phase") else ""),
                      "step": None, "sigma": c.get("sigma"), "ticks": x.get("reflections"),
                      "peak_width": float(np.median([p["fwhm_deg"] for p in x["peaks"]])) if x.get("peaks") else 1.0}
    if p := res.get("pdf"):
        f = p["fits"][0]
        c = f["curves"]
        out["pdf"] = {"x": c["r"], "obs": c["obs"], "calc": c["calc"], "xlabel": "r (Å)", "ylabel": "G(r) (Å⁻²)",
                      "title": f"PDF fit, {f['candidate']} (Rw {f['rw']:.3f})", "step": np.pi / f["qmax"], "sigma": c.get("sigma")}
    if e := res.get("exafs"):
        c, w = e["fit"]["curves"], e["fit"]["window"]
        r = np.asarray(c["r"])
        m = (r >= w["rmin"] - 0.5) & (r <= w["rmax"] + 0.5)
        out["exafs"] = {"x": r[m], "obs": np.asarray(c["chir_mag_data"])[m], "calc": np.asarray(c["chir_mag_model"])[m],
                        "xlabel": "R (Å, not phase corrected)", "ylabel": "|χ(R)| (Å⁻³)",
                        "title": f"EXAFS fit, {e['absorber']} {e['edge']} (R-factor {e['fit']['rfactor']:.4f})",
                        "step": np.pi / (2 * (w["kmax"] - w["kmin"])), "window": (w["rmin"], w["rmax"]),
                        "k": c["k"], "chi_data": c["chi_data"], "chi_model": c["chi_model"]}
    return out
