"""Residual features of a fit, per region, on independent points: oversampled data (G(r), χ(R)) are thinned to
their independent-point spacing first, or neighbouring residuals look correlated even for a perfect model."""
import numpy as np


def durbin_watson(e: np.ndarray) -> float:
    e = np.asarray(e, float)
    return float(np.sum(np.diff(e) ** 2) / max(float(np.sum(e ** 2)), 1e-30))


def residual_features(x, obs, calc, step: float | None = None, regions: int = 5, dw_min: float = 1.0,
                      peak_width: float = 1.0, peak_min: float = 0.15) -> dict:
    """step None means a diffraction pattern: positive residual peaks above peak_min of the data maximum are reported
    (grouped within two peak widths). The Durbin-Watson and concentration rules are not applied: misfit follows the
    peak intensity, and the peak-shape misfit of small particles makes them fire for the right phase (dev split,
    dataset_big s0060+: the concentration rule flagged 14/44 clean patterns, Durbin-Watson on residuals thinned to half
    a peak width 7/44; residual peaks flag 1/44)."""
    x, obs, calc = (np.asarray(v, float) for v in (x, obs, calc))
    thin = max(1, int(round(step / float(np.median(np.diff(x)))))) if step else 1
    xs, e = x[::thin], (obs - calc)[::thin]
    regions = max(1, min(regions, len(xs) // 10))  # Durbin-Watson needs ~10 points: a first-shell EXAFS window has 11-16
    total = float(np.sum(e ** 2)) or 1e-30
    scale = float(np.sqrt(np.mean(obs ** 2))) or 1.0
    rows = []
    for lo, hi in zip(np.linspace(xs[0], xs[-1], regions + 1)[:-1], np.linspace(xs[0], xs[-1], regions + 1)[1:]):
        m = (xs >= lo) & (xs <= hi)
        ee = e[m]
        rows.append({"region": f"{lo:.1f}-{hi:.1f}", "misfit_share": float(np.sum(ee ** 2) / total),
                     "rms_rel": float(np.sqrt(np.mean(ee ** 2)) / scale), "durbin_watson": durbin_watson(ee) if step and len(ee) > 2 else None})
    structured = [r["region"] for r in rows if r["durbin_watson"] is not None and r["durbin_watson"] < dw_min and r["misfit_share"] >= 1.5 / regions]
    typical = float(np.median([r["rms_rel"] for r in rows]))
    concentrated = [r["region"] for r in rows if step and r["misfit_share"] >= 3 / regions and r["rms_rel"] > 2 * typical]
    bumps = []
    if step is None:  # diffraction pattern: positive residual peaks the model does not explain
        idx = np.where((e[1:-1] > peak_min * float(np.max(obs))) & (e[1:-1] >= e[:-2]) & (e[1:-1] >= e[2:]))[0] + 1
        groups = []
        for i in idx:
            if groups and xs[i] - groups[-1][-1] <= 2 * peak_width:
                groups[-1].append(xs[i])
            else:
                groups.append([xs[i]])
        bumps = [round(float(np.mean(g)), 2) for g in groups]
    return {"n_independent": int(len(xs)), "thinned_by": thin, "rms_rel": float(np.sqrt(np.mean(e ** 2)) / scale),
            "durbin_watson": durbin_watson(e) if step else None, "regions": rows, "structured_regions": structured, "concentrated_regions": concentrated, "unexplained_peaks": bumps}
