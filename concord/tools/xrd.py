"""XRD tools.

Loading, ALS baseline, Savitzky–Golay smoothing, Voigt peak fitting, Scherrer/Williamson–Hall and reference
matching are refactored from CrystaLenz (src/agents/xrd_agent/sub_agents/*/tools.py) into pure functions.
Fixed on the way: the Voigt model passed sigma/gamma positionally into lmfit's amplitude/center slots, so peak
widths were never fitted (fixed at σ=γ=1°); Williamson–Hall regressed against 4 sinθ/λ, which made the reported "strain" ε·λ; Voigt widths
were capped at 0.2°, which cannot fit nanoparticle peaks; np.trapz no longer exists in numpy 2.
"""
import math
from pathlib import Path

import lmfit
import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from lmfit.lineshapes import voigt
from scipy.optimize import lsq_linear
from scipy.signal import find_peaks, peak_widths, savgol_filter

from concord.tools import tool

CU_KA1 = 1.5406
K_SCHERRER = 0.9
# FWHM Scherrer constant for spheres relative to the diameter D, from the sphere's common-volume function
# A(L) = 1 - 3L/2D + L³/2D³ (Stokes & Wilson 1942); equals 0.892 relative to V^(1/3), and K_β = 4/3.
K_SPHERE_D = 1.1067


# -- loading (CrystaLenz data_loader: inspect_xrd_file / load_xrd_data) ---------------------------------
def read_table(path: str | Path) -> pd.DataFrame:
    path = str(path)
    low = path.lower()
    if low.endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    if low.endswith(".csv"):
        return pd.read_csv(path)
    # .xy / .dat / .txt: whitespace columns, '#' comments, optional header line
    df = pd.read_csv(path, sep=r"\s+|,", engine="python", comment="#", header=None)
    if not np.issubdtype(df.iloc[:, 0].dtype, np.number):
        df.columns = df.iloc[0].astype(str)
        df = df.iloc[1:].astype(float).reset_index(drop=True)
    else:
        df.columns = ["x", "intensity", "sigma"][: df.shape[1]] + [f"c{i}" for i in range(3, df.shape[1])]
    return df


def _header(path: str | Path) -> dict:
    """key=value pairs from leading '#' lines, e.g. '# x=2theta_deg wavelength_A=1.5406'."""
    out = {}
    try:
        with open(path, errors="replace") as f:
            for line in f:
                if not line.startswith("#"):
                    break
                out.update(tok.split("=", 1) for tok in line[1:].split() if "=" in tok)
    except (OSError, UnicodeDecodeError):
        pass
    return out


def guess_columns(df: pd.DataFrame) -> tuple[str, str, str]:
    """(x column, intensity column, unit): name hints first, else the first two numeric columns."""
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric) < 2:
        raise ValueError("need at least two numeric columns (2θ and intensity)")
    names = {c: str(c).lower().replace(" ", "") for c in numeric}
    x = next((c for c in numeric if names[c] in ("q", "q_inv_a") or any(h in names[c] for h in ("2theta", "two_theta", "tth", "angle", "2th"))), numeric[0])
    y = next((c for c in numeric if c != x and any(h in names[c] for h in ("int", "count", "i(", "y"))), None)
    y = y if y is not None else next(c for c in numeric if c != x)
    xmax = float(df[x].max())
    unit = "q" if names[x] in ("q", "q_inv_a") else ("rad" if xmax < 3.2 else "deg")
    return x, y, unit


@tool
def load_pattern(path: str | Path, x_col: str | None = None, y_col: str | None = None, unit: str | None = None,
                 wavelength_A: float = CU_KA1) -> dict:
    """Load an XRD pattern; columns and unit are detected when not given. Returns 2θ in degrees."""
    df = read_table(path)
    gx, gy, gu = guess_columns(df)
    header = _header(path)
    if "q_inv_A" in header.get("x", ""):
        gu = "q"
    elif "2theta" in header.get("x", ""):
        gu = "deg"
    wavelength_A = float(header.get("wavelength_A", wavelength_A))
    x_col, y_col, unit = x_col or gx, y_col or gy, unit or gu
    x = df[x_col].to_numpy(float)
    if unit == "rad":
        x = np.degrees(x)
    elif unit == "q":
        x = 2 * np.degrees(np.arcsin(np.clip(x * wavelength_A / (4 * np.pi), -1, 1)))
    y = df[y_col].to_numpy(float)
    sigma = df["sigma"].to_numpy(float) if "sigma" in df.columns else np.sqrt(np.clip(y, 1.0, None))
    order = np.argsort(x)
    return {"two_theta_deg": x[order], "intensity": y[order], "sigma": sigma[order],
            "meta": {"path": str(path), "x_col": str(x_col), "y_col": str(y_col), "unit": unit,
                     "wavelength_A": wavelength_A, "two_theta_min": float(x.min()), "two_theta_max": float(x.max())}}


# -- preprocessing (CrystaLenz data_preprocessor) ------------------------------------------------------
def als_baseline(y: np.ndarray, lam: float = 1e5, p: float = 0.01, niter: int = 10) -> np.ndarray:
    """Asymmetric Least Squares baseline correction."""
    L = len(y)
    D = sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(L - 2, L))
    w = np.ones(L)
    for _ in range(niter):
        W = sp.diags(w, 0)
        Z = W + lam * (D.T @ D)
        z = spla.spsolve(Z.tocsc(), w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z


@tool
def preprocess(intensity: np.ndarray, smoothing_window: int = 11, smoothing_polyorder: int = 3,
               baseline_lambda: float = 1e5, baseline_p: float = 0.01) -> dict:
    win = max(5, int(smoothing_window) | 1)
    poly = min(int(smoothing_polyorder), win - 2)
    smooth = savgol_filter(np.asarray(intensity, float), win, poly)
    baseline = als_baseline(smooth, lam=baseline_lambda, p=baseline_p)
    return {"intensity_smooth": smooth, "baseline": baseline, "intensity_corr": np.clip(smooth - baseline, 0, None),
            "params": {"smoothing_window": win, "smoothing_polyorder": poly,
                       "baseline_lambda": baseline_lambda, "baseline_p": baseline_p}}


# -- peaks (CrystaLenz peak_finder) --------------------------------------------------------------------
def _voigt(x, amp, center, sigma, gamma, offset):
    # keywords matter: upstream passed sigma/gamma positionally into lmfit's amplitude/center slots
    return voigt(x, amplitude=amp, center=center, sigma=sigma, gamma=gamma) + offset


def voigt_fwhm(sigma: float, gamma: float) -> float:
    """Olivero–Longbothum approximation; lmfit's gamma is the Lorentzian HWHM."""
    fl, fg = 2 * gamma, 2.3548 * sigma
    return 0.5346 * fl + math.sqrt(0.2166 * fl ** 2 + fg ** 2)


@tool
def find_and_fit_peaks(two_theta: np.ndarray, y: np.ndarray, height_rel: float = 0.03, prominence_rel: float = 0.02,
                       min_distance_deg: float = 0.3, fit_window_deg: float | None = None) -> list[dict]:
    """Detect peaks and fit each with a Voigt profile; the window adapts to the peak width unless given."""
    x_all, y_all = np.asarray(two_theta, float), np.asarray(y, float)
    step = float(np.median(np.diff(x_all)))
    top = float(y_all.max()) if np.ptp(y_all) > 0 else 1.0
    idx, _ = find_peaks(y_all, height=height_rel * top, prominence=prominence_rel * top,
                        distance=max(1, int(min_distance_deg / step)))
    est_fwhm = peak_widths(y_all, idx, rel_height=0.5)[0] * step if len(idx) else []
    peaks = []
    for p, w in zip(idx, est_fwhm):
        win = fit_window_deg or float(np.clip(3.0 * w, 0.4, 12.0))
        mask = np.abs(x_all - x_all[p]) <= win / 2
        x, yy = x_all[mask], y_all[mask]
        if len(x) < 7:
            continue
        model = lmfit.Model(_voigt)
        c0 = float(x_all[p])
        pars = model.make_params(amp=max(float(yy.max() - yy.min()), 1e-9) * max(w, step), center=c0,
                                 sigma=max(w / 4, step), gamma=max(w / 4, step), offset=float(np.percentile(yy, 5)))
        pars["center"].set(min=c0 - max(w / 2, 2 * step), max=c0 + max(w / 2, 2 * step))
        pars["sigma"].set(min=step / 4, max=win)
        pars["gamma"].set(min=step / 4, max=win)
        pars["amp"].set(min=0)
        pars["offset"].set(min=0)
        out = model.fit(yy, pars, x=x)
        bv = out.best_values
        if not (bv["amp"] > 0 and np.isfinite(bv["amp"])):
            continue  # fit collapsed onto the background: not a peak
        err = out.params["center"].stderr
        peaks.append({"two_theta": float(bv["center"]), "two_theta_err": float(err) if err else None,
                      "height": float(out.best_fit.max() - bv["offset"]), "fwhm_deg": voigt_fwhm(bv["sigma"], bv["gamma"]),
                      "sigma_deg": float(bv["sigma"]), "gamma_deg": float(bv["gamma"]), "area": float(bv["amp"]), "model": "voigt"})
    return peaks


# -- size and strain (CrystaLenz scherrer_and_wh) ------------------------------------------------------
def caglioti_fwhm_deg(two_theta_deg: float, U: float, V: float, W: float) -> float:
    t = math.tan(math.radians(two_theta_deg / 2))
    return math.sqrt(max(U * t * t + V * t + W, 1e-12))


def _weighted_median(values: list[float], weights: list[float]) -> float:
    order = np.argsort(values)
    cum = np.cumsum(np.asarray(weights, float)[order])
    return float(np.asarray(values)[order][np.searchsorted(cum, 0.5 * cum[-1])])


@tool
def scherrer_wh(peaks: list[dict], wavelength_A: float = CU_KA1, instrument: dict | None = None,
                K: float = K_SCHERRER) -> dict:
    """Crystallite size and strain from peak widths.

    The instrument (Caglioti, Gaussian) is removed from each Voigt fit by subtracting Gaussian widths in quadrature
    and keeping the Lorentzian width (exact for Voigt profiles); peaks without Voigt parameters fall back to
    subtracting FWHMs in quadrature.
    scherrer: column length L = Kλ/(β cosθ) per peak (CrystaLenz convention, K = 0.9).
    sphere_diameter_nm: D = K_SPHERE_D·λ/(β cosθ), area-weighted median over peaks (strong reflections dominate).
    williamson_hall: β cosθ = Kλ/L + 4ε sinθ.
    instrument: optional {"U","V","W"} Caglioti terms (deg²) or {"fwhm_deg"}.
    """
    rows, X, Y = [], [], []
    for pk in peaks:
        tt = float(pk["two_theta"])
        inst = 0.0
        if instrument:
            inst = instrument.get("fwhm_deg") or caglioti_fwhm_deg(tt, instrument["U"], instrument["V"], instrument["W"])
        if "sigma_deg" in pk:
            beta_deg = voigt_fwhm(math.sqrt(max(pk["sigma_deg"] ** 2 - (inst / 2.3548) ** 2, 0.0)), pk["gamma_deg"])
            lorentz = min(1.0, 2 * pk["gamma_deg"] / max(beta_deg, 1e-9))  # Lorentzian share of the sample broadening
        else:
            beta_deg, lorentz = math.sqrt(max(float(pk["fwhm_deg"]) ** 2 - inst ** 2, 1e-12)), None
        theta, beta = math.radians(tt / 2), math.radians(max(beta_deg, 1e-6))
        rows.append({"two_theta": tt, "beta_deg": beta_deg, "L_nm": K * wavelength_A / (beta * math.cos(theta)) / 10,
                     "D_sphere_nm": K_SPHERE_D * wavelength_A / (beta * math.cos(theta)) / 10, "lorentz_fraction": lorentz})
        X.append(4 * math.sin(theta))
        Y.append(beta * math.cos(theta))
    out = {"scherrer": rows, "K": K, "wavelength_A": wavelength_A,
           "scherrer_median_nm": float(np.median([r["L_nm"] for r in rows])) if rows else None,
           "sphere_diameter_nm": _weighted_median([r["D_sphere_nm"] for r in rows], [pk.get("area", 1.0) for pk in peaks]) if rows else None,
           "lorentz_fraction": _weighted_median([r["lorentz_fraction"] for r in rows], [pk.get("area", 1.0) for pk in peaks])
           if rows and all(r["lorentz_fraction"] is not None for r in rows) else None,
           "williamson_hall": None}
    if len(X) >= 3:
        slope, intercept = np.polyfit(X, Y, 1)
        yhat = np.polyval([slope, intercept], X)
        ss = float(((np.array(Y) - np.mean(Y)) ** 2).sum())
        r2 = 1 - float(((np.array(Y) - yhat) ** 2).sum()) / ss if ss > 0 else 0.0
        out["williamson_hall"] = {"strain": float(slope), "size_nm": float(K * wavelength_A / intercept / 10) if intercept > 0 else None,
                                  "r2": r2, "n_points": len(X)}
    return out


# -- reference patterns and matching (CrystaLenz reference_check, without the Materials Project dependency) -----
def reference_lines(structure, wavelength_A: float = CU_KA1, two_theta_range=(10.0, 90.0), min_intensity: float = 1.0,
                    debye_waller: dict | None = None) -> list[dict]:
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    calc = XRDCalculator(wavelength=wavelength_A, debye_waller_factors=debye_waller)
    patt = calc.get_pattern(structure, two_theta_range=tuple(two_theta_range))
    lines = []
    for tt, inten, hkls, d in zip(patt.x, patt.y, patt.hkls, patt.d_hkls):
        if inten >= min_intensity:
            lines.append({"two_theta": float(tt), "d_A": float(d), "intensity": float(inten),
                          "hkl": [list(h["hkl"]) for h in hkls]})
    return lines


def d_spacing(two_theta_deg: float, wavelength_A: float = CU_KA1) -> float:
    return wavelength_A / (2 * math.sin(math.radians(two_theta_deg / 2)))


@tool
def match_reference(peaks: list[dict], ref_lines: list[dict], wavelength_A: float = CU_KA1, min_ref_intensity: float = 5.0) -> dict:
    """Match observed peaks to reference lines in d-spacing: tolerance max(0.02 Å, 0.5 % d) as in CrystaLenz, widened
    for broad peaks to 15 % of the FWHM in 2θ, since overlapping nanoparticle reflections shift fitted centres."""
    exp = [(p, d_spacing(p["two_theta"], wavelength_A)) for p in peaks]
    widen = [d / math.tan(math.radians(p["two_theta"] / 2)) * math.radians(0.15 * p.get("fwhm_deg", 0.0) / 2) for p, d in exp]
    strong = [r for r in ref_lines if r["intensity"] >= min_ref_intensity]
    matches, used = [], set()
    for r in strong:
        tol = max(0.02, 0.005 * r["d_A"])
        cands = [(abs(d - r["d_A"]), i) for i, (_, d) in enumerate(exp) if abs(d - r["d_A"]) <= max(tol, widen[i])]
        if cands:
            delta, i = min(cands)
            used.add(i)
            matches.append({"ref_two_theta": r["two_theta"], "exp_two_theta": exp[i][0]["two_theta"], "ref_d": r["d_A"],
                            "exp_d": exp[i][1], "delta_d": exp[i][1] - r["d_A"], "tol_d": max(tol, widen[i]), "hkl": r["hkl"][:1],
                            "ref_intensity": r["intensity"]})
    total_area = sum(p["area"] for p in peaks) or 1.0
    unexplained = [exp[i][0] for i in range(len(exp)) if i not in used]
    return {"matched": len(matches), "n_ref": len(strong), "n_obs": len(peaks),
            "ref_fraction_matched": len(matches) / max(1, len(strong)),
            "obs_area_fraction_explained": sum(exp[i][0]["area"] for i in used) / total_area,
            "unexplained_peaks": [{"two_theta": p["two_theta"], "area_fraction": p["area"] / total_area} for p in unexplained],
            "matches": matches}


# -- pattern simulation (used for phase scoring, C7 and the data builder) ------------------------------
def scale_with_background(two_theta: np.ndarray, y: np.ndarray, patterns: list[np.ndarray], terms: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Non-negative scales of simulated patterns refined together with a smooth background, as in Rietveld refinement:
    Chebyshev terms for amorphous and diffuse scattering plus a 1/2θ term for the low-angle rise of small particles,
    both left in by the stiff baseline. 8 terms: on the dev split (dataset_big s0060+) 1/44 clean patterns keep a
    residual peak above 15 % of the maximum, against 3/44 with 6 terms. Returns (scales, background)."""
    tt = np.asarray(two_theta, float)
    bkg = np.column_stack([np.polynomial.chebyshev.chebvander(np.interp(tt, (tt.min(), tt.max()), (-1.0, 1.0)), terms - 1), 1.0 / np.maximum(tt, 1.0)])  # 2θ from Q can start at 0
    a, k = np.column_stack([*patterns, bkg]), len(patterns)
    sol = lsq_linear(a, np.asarray(y, float), bounds=(np.r_[np.zeros(k), np.full(bkg.shape[1], -np.inf)], np.inf), method="bvls")
    return sol.x[:k], bkg @ sol.x[k:]


def tch_pseudo_voigt(x: np.ndarray, center: float, h_g: float, h_l: float) -> np.ndarray:
    """Unit-area pseudo-Voigt with Thompson–Cox–Hastings mixing (doi:10.1107/S0021889887087090)."""
    h = (h_g ** 5 + 2.69269 * h_g ** 4 * h_l + 2.42843 * h_g ** 3 * h_l ** 2 + 4.47163 * h_g ** 2 * h_l ** 3
         + 0.07842 * h_g * h_l ** 4 + h_l ** 5) ** 0.2
    q = h_l / h
    eta = 1.36603 * q - 0.47719 * q ** 2 + 0.11116 * q ** 3
    dx = x - center
    gauss = np.sqrt(4 * np.log(2) / np.pi) / h * np.exp(-4 * np.log(2) * dx ** 2 / h ** 2)
    lor = 2 / (np.pi * h) / (1 + 4 * dx ** 2 / h ** 2)
    return eta * lor + (1 - eta) * gauss


@tool
def simulate_pattern(structure, two_theta: np.ndarray, wavelength_A: float = CU_KA1, size_nm: float | None = None,
                     strain: float = 0.0, instrument: dict | None = None, debye_waller: dict | None = None,
                     lorentz_fraction: float | None = None) -> np.ndarray:
    """Powder pattern of a periodic structure: pymatgen stick pattern broadened by size, strain and instrument.
    Size broadening is Lorentzian unless lorentz_fraction (the Lorentzian share of the size FWHM measured on the
    pattern's own peaks) gives its shape."""
    inst = instrument or {"U": 0.004, "V": -0.002, "W": 0.002}
    x = np.asarray(two_theta, float)
    y = np.zeros_like(x)
    for line in reference_lines(structure, wavelength_A, (max(1.0, x.min() - 5), min(179.0, x.max() + 5)), min_intensity=0.01,
                                debye_waller=debye_waller):
        tt = line["two_theta"]
        theta = math.radians(tt / 2)
        h_g = caglioti_fwhm_deg(tt, inst["U"], inst["V"], inst["W"])
        h_g = math.sqrt(h_g ** 2 + math.degrees(4 * strain * math.tan(theta)) ** 2)
        h_l = math.degrees(K_SCHERRER * wavelength_A / (size_nm * 10 * math.cos(theta))) if size_nm else 1e-4
        if size_nm and lorentz_fraction is not None:  # split the size FWHM into Voigt parts (Olivero–Longbothum inverted)
            beta, h_l = h_l, max(lorentz_fraction * h_l, 1e-4)
            h_g = math.sqrt(h_g ** 2 + max((beta - 0.5346 * h_l) ** 2 - 0.2166 * h_l ** 2, 0.0))
        y += line["intensity"] * tch_pseudo_voigt(x, tt, h_g, h_l)
    return y


def profile_correlation(y_obs: np.ndarray, y_calc: np.ndarray) -> float:
    a, b = np.asarray(y_obs, float), np.asarray(y_calc, float)
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


@tool
def rank_phases(two_theta: np.ndarray, y_corr: np.ndarray, peaks: list[dict], candidates: dict, wavelength_A: float = CU_KA1,
                size_nm: float | None = None, instrument: dict | None = None) -> list[dict]:
    """Score candidate structures against the pattern: whole-profile correlation plus CrystaLenz-style line matching."""
    ranking = []
    for name, structure in candidates.items():
        calc = simulate_pattern(structure, two_theta, wavelength_A, size_nm=size_nm, instrument=instrument)
        match = match_reference(peaks, reference_lines(structure, wavelength_A, (float(np.min(two_theta)), float(np.max(two_theta)))), wavelength_A)
        corr = profile_correlation(y_corr, calc)
        ranking.append({"phase": name, "profile_corr": corr, "ref_fraction_matched": match["ref_fraction_matched"],
                        "obs_area_fraction_explained": match["obs_area_fraction_explained"],
                        "score": 0.6 * max(corr, 0) + 0.4 * match["obs_area_fraction_explained"]})
    return sorted(ranking, key=lambda r: -r["score"])
