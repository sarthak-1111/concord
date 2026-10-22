"""PDF data reduction: raw total-scattering intensity I(Q) -> S(Q) -> F(Q) -> G(r), one small function per step.

Theory: Egami & Billinge, "Underneath the Bragg Peaks" (2nd ed., ch. 3 and 5); the ad hoc correction of Juhás et al.
(2013), J. Appl. Cryst. 46, 560. Per atom, with atomic fractions c_i and f_i = f0_i(Q) from xraydb:

  a) I_s(Q) = I(Q) - b I_bkg(Q)                               container and air scattering, scale b
  b) I_s /= (1 + cos² 2θ)/2,  2θ = 2 asin(Qλ/4π)              polarisation of an unpolarised beam (optional)
  c) I_s = α [⟨f²⟩ + ⟨f⟩²(S(Q) - 1) + C(Q)]                   Faber-Ziman; ⟨f²⟩ = Σ c_i f_i², ⟨f⟩² = (Σ c_i f_i)²
     C(Q) = Σ c_i (Z_i - f_i²/Z_i)                           incoherent (Compton) scattering, independent-electron estimate
     α from the high-Q limit S -> 1: least squares of I_s against ⟨f²⟩ + C on [Qmaxinst/2, Qmaxinst], Hann-weighted so
     the S(Q) oscillations average out instead of biasing α (a box window leaves ~0.5 %)
  d) F(Q) = Q [S(Q) - 1]
  e) ad hoc correction: F_c = F - P_n(Q), P_n = Σ_{k=1..n} c_k (Q/Qmaxinst)^k, n = ceil(rpoly Qmaxinst / π): the
     polynomial cannot oscillate faster than r = rpoly, so every slowly varying error (normalisation, Compton, multiple
     or residual container scattering) lives in G(r < rpoly). c_k are fitted on Qmin..Qmaxinst by least squares so that
     G(r <= rpoly) of F_c is a straight line through the origin, the -4πρ0 r baseline of a region with no atoms (slope
     free: a nanoparticle with a finite Qmin has a shallower one), while P_n's own G(r) stays small on rpoly < r < 10 Å
     (its values at the Qmin and Qmax cuts would otherwise ripple into the first peaks). Fitting P_n to F(Q) itself, as
     a plain fit, also removes the true low-Q signal and tilts that baseline positive.
  f) F_c is kept on Qmin <= Q <= Qmax; Qmaxinst bounds the normalisation and polynomial fits
  g) G(r) = (2/π) ∫ F_c(Q) M(Q) sin(Qr) dQ, M = 1 or Lorch's sin(πQ/Qmax)/(πQ/Qmax); σ_G from σ_F(Q) ∝ Q, scaled to
     the F(Q) noise measured at high Q from the median second difference
"""
import math
import tempfile
from pathlib import Path

import numpy as np
import xraydb
from pymatgen.core import Composition, Element

from concord.tools import tool, xrd

MAX_POINTS = 800


def load_raw(path_or_bytes, name: str | None = None, wavelength_A: float | None = None) -> dict:
    """Two-column I(Q) or I(2θ) with optional '# key=value' header; 2θ (degrees) becomes Q with the wavelength from the
    header or the argument. Returns {"q", "i", "header"}, sorted by Q."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        suffix = Path(name or "raw.dat").suffix.lower() or ".dat"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / f"raw{suffix}"
            p.write_bytes(path_or_bytes)
            return load_raw(p, name, wavelength_A)
    df, header = xrd.read_table(path_or_bytes), xrd._header(path_or_bytes)
    xc, yc, _ = xrd.guess_columns(df)
    x, y = df[xc].to_numpy(float), df[yc].to_numpy(float)
    hx, cx = header.get("x", "").lower(), str(xc).lower()
    if "2theta" in hx or any(h in cx for h in ("2theta", "two_theta", "tth", "angle")):
        lam = wavelength_A or (float(header["wavelength_A"]) if "wavelength_A" in header else None)
        if not lam:
            raise ValueError("x is 2θ but no wavelength is known: give wavelength_A or a '# wavelength_A=' header line")
        x = 4 * np.pi * np.sin(np.radians(x / 2)) / lam
    ok = np.isfinite(x) & np.isfinite(y)
    order = np.argsort(x[ok], kind="stable")
    return {"q": x[ok][order], "i": y[ok][order], "header": header}


# -- steps ---------------------------------------------------------------------------------------------
def scattering_factors(composition: str, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(⟨f²⟩, ⟨f⟩², Compton C(Q)) per atom for a formula such as 'Pt3Co' or 'TiO2'."""
    try:
        comp = Composition(composition).fractional_composition
    except Exception as exc:
        raise ValueError(f"could not read the composition {composition!r}") from exc
    bad = [str(e) for e in comp if not isinstance(e, Element) or e.Z > 98]
    if bad:
        raise ValueError(f"unknown element {', '.join(bad)} in composition {composition!r}: no X-ray form factor")
    s = np.asarray(q) / (4 * np.pi)  # xraydb's f0 takes sinθ/λ
    f2, fa, compton = 0.0, 0.0, 0.0
    for el, c in comp.items():
        f = xraydb.f0(el.symbol, s)
        f2, fa, compton = f2 + c * f ** 2, fa + c * f, compton + c * (el.Z - f ** 2 / el.Z)
    return f2, fa ** 2, compton


def background_on(q: np.ndarray, background) -> np.ndarray | None:
    """The background on the sample's Q grid: an array of the same length, or (q, i) pairs interpolated."""
    if background is None:
        return None
    b = np.asarray(background, float)
    if b.ndim == 1:
        if len(b) != len(q):
            raise ValueError(f"the background has {len(b)} points and the sample {len(q)}: give (q, intensity) pairs to interpolate")
        return b
    bq, bi = (b[:, 0], b[:, 1]) if b.shape[1] == 2 else (b[0], b[1])
    order = np.argsort(bq)
    return np.interp(q, bq[order], bi[order])


def subtract_background(i: np.ndarray, bkg: np.ndarray | None, scale: float) -> np.ndarray:
    return i if bkg is None else i - scale * bkg


def oversubtracted(q: np.ndarray, i: np.ndarray) -> bool:
    """Some 0.5 Å⁻¹ window of the corrected intensity averages 4σ below zero (noise alone dips a crystal's
    near-empty low-Q region below zero, so the sign of single points says nothing)."""
    k = max(3, int(0.5 / np.median(np.diff(q))))
    if len(q) < 3 * k:
        return False
    mean = np.convolve(i, np.ones(k) / k, mode="valid")
    sd = np.sqrt(np.clip(np.convolve(i ** 2, np.ones(k) / k, mode="valid") - mean ** 2, 0, None))
    return bool((mean < -4 * sd / np.sqrt(k)).any())


def polarization_correct(q: np.ndarray, i: np.ndarray, wavelength_A: float) -> np.ndarray:
    tt = 2 * np.arcsin(np.clip(q * wavelength_A / (4 * np.pi), 0, 1))
    return i / ((1 + np.cos(tt) ** 2) / 2)


def normalize(q: np.ndarray, i: np.ndarray, f2: np.ndarray, fa2: np.ndarray, compton: np.ndarray) -> tuple[np.ndarray, float]:
    """(S(Q), α) with α from the high-Q half, where I_s -> α(⟨f²⟩ + C)."""
    selfc = f2 + compton
    m = q >= q[0] + 0.5 * (q[-1] - q[0])
    w = np.sin(np.pi * (q[m] - q[m][0]) / (q[m][-1] - q[m][0])) ** 2
    alpha = float(np.sum(w * i[m] * selfc[m]) / np.sum(w * selfc[m] ** 2))
    return 1 + (i / alpha - selfc) / fa2, alpha


def sine_matrix(r: np.ndarray, q: np.ndarray) -> np.ndarray:
    """(2/π) sin(Qr) dQ, so that G = M @ F."""
    return (2 / np.pi) * np.sin(np.outer(r, q)) * np.gradient(q)


def adhoc_correction(q: np.ndarray, fq: np.ndarray, rpoly: float, qmax: float) -> tuple[np.ndarray, np.ndarray, float, int]:
    """(corrected F, polynomial, low-r slope of G, degree): F - P_n with G(r <= rpoly) a line through the origin and
    P_n's own G(r), transformed to qmax, small out to 10 Å."""
    n = max(1, math.ceil(rpoly * q[-1] / np.pi))
    rl = np.arange(0.01, rpoly + 1e-9, 0.01)
    if rpoly <= 0 or len(rl) < n + 2:
        return fq, np.zeros_like(fq), float("nan"), 0
    basis = (q / q[-1])[:, None] ** np.arange(1, n + 1)
    k = sine_matrix(rl, q)
    rh, w = np.arange(rpoly + 0.05, 10.0, 0.05), q <= qmax
    leak = sine_matrix(rh, q[w]) @ basis[w] * np.sqrt(0.01 / 0.05)  # same weight per Å as the low-r rows
    a = np.vstack([np.c_[k @ basis, rl], np.c_[leak, np.zeros(len(rh))]])
    c = np.linalg.lstsq(a, np.r_[k @ fq, np.zeros(len(rh))], rcond=None)[0]
    poly = basis @ c[:-1]
    return fq - poly, poly, float(c[-1]), n


def sine_transform(q: np.ndarray, fq: np.ndarray, r: np.ndarray, qmax: float, lorch: bool,
                   sigma_fq: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    """G(r) and, given σ_F, its σ_G."""
    m = np.sinc(q / qmax) if lorch else 1.0  # np.sinc(x) = sin(πx)/(πx)
    s = sine_matrix(r, q)
    g = s @ (fq * m)
    return g, (None if sigma_fq is None else np.sqrt((s ** 2) @ (sigma_fq * m) ** 2))


def fq_noise(fq: np.ndarray) -> float:
    """Noise of F(Q) from second differences (smooth signal cancels), median-based so sharp Bragg peaks count less."""
    if len(fq) < 5:
        return float("nan")
    return float(1.4826 * np.median(np.abs(np.diff(fq, 2))) / np.sqrt(6))


# -- the reduction --------------------------------------------------------------------------------------
def _thin(**cols) -> dict:
    n = len(next(iter(cols.values())))
    idx = np.unique(np.linspace(0, n - 1, min(n, MAX_POINTS)).round().astype(int)) if n else np.array([], int)
    return {k: (None if v is None else np.round(np.asarray(v, float)[idx], 6).tolist()) for k, v in cols.items()}


@tool
def reduce(q, i, *, composition: str, background=None, bkg_scale: float = 1.0, qmin: float | None = None,
           qmax: float | None = None, qmaxinst: float | None = None, rpoly: float = 0.9, rmin: float = 0.0,
           rmax: float = 30.0, rstep: float = 0.01, lorch: bool = False, wavelength_A: float | None = None,
           polarization: bool = False, rho0: float | None = None) -> dict:
    """Raw I(Q) to G(r). Q limits default to the data's; qmaxinst bounds the normalisation and polynomial fits.
    rho0 (atoms/Å³), when known, is only compared with the low-r slope. Returns thinned curves per step, the
    full-resolution G(r), diagnostics and plain-English warnings (see the module docstring for the equations)."""
    q, i = np.asarray(q, float), np.asarray(i, float)
    ok = np.isfinite(q) & np.isfinite(i) & (q > 0)
    order = np.argsort(q[ok], kind="stable")
    bkg = background_on(np.asarray(q, float), background)
    q, i = q[ok][order], i[ok][order]
    bkg = None if bkg is None else bkg[ok][order]
    if len(q) < 20:
        raise ValueError(f"only {len(q)} usable points: need a measured I(Q) of at least 20 points")
    warnings = []
    qmaxinst = float(min(qmaxinst or q[-1], q[-1]))
    qmin = float(max(qmin or q[0], q[0]))
    qmax = float(min(qmax or qmaxinst, qmaxinst))
    if not qmin < qmax:
        raise ValueError(f"qmin {qmin:g} must be below qmax {qmax:g} (and inside the data, {q[0]:g} to {q[-1]:g} 1/Å)")
    if rstep <= 0 or rmax <= rmin:
        raise ValueError("need rstep > 0 and rmax > rmin")
    keep = q <= qmaxinst
    q, i, bkg = q[keep], i[keep], None if bkg is None else bkg[keep]

    if bkg is None:
        warnings.append("no background given: container and air scattering stay in the data and only their smooth part "
                        "is removed by the polynomial correction")
    corrected = subtract_background(i, bkg, bkg_scale)
    if bkg is not None and oversubtracted(q, corrected):
        warnings.append(f"the background is larger than the sample over part of the Q range: lower bkg_scale (now {bkg_scale:g})")
    applied_pol = bool(polarization and wavelength_A)
    if polarization and not wavelength_A:
        warnings.append("polarization correction skipped: it needs the wavelength")
    elif applied_pol:
        corrected = polarization_correct(q, corrected, wavelength_A)

    f2, fa2, compton = scattering_factors(composition, q)
    sq, alpha = normalize(q, corrected, f2, fa2, compton)
    fit = q >= qmin
    qf, fq_raw = q[fit], q[fit] * (sq[fit] - 1)
    fq, _, slope, degree = adhoc_correction(qf, fq_raw, rpoly, qmax)
    win = qf <= qmax
    noise = fq_noise(fq[(qf >= 0.8 * qmax) & win])
    sigma_fq = noise * qf[win] / (0.9 * qmax) if np.isfinite(noise) else None  # shortcut: σ_F ∝ Q, as for counting noise in Q(S-1)
    r = np.arange(rmin, rmax + rstep / 2, rstep)
    g, dg = sine_transform(qf[win], fq[win], r, qmax, lorch, sigma_fq)

    hi = (q >= 0.8 * qmax) & (q <= qmax)
    s_hi = float(np.mean(sq[hi]) - 1) if hi.any() else float("nan")
    quality = {"scale": alpha, "sq_high_q_offset": s_hi, "fq_noise_high_q": noise, "low_r_slope": slope,
               "rho0_from_slope": -slope / (4 * np.pi) if np.isfinite(slope) else None,
               "slope_vs_density": slope / (-4 * np.pi * rho0) if rho0 and np.isfinite(slope) else None}
    if abs(s_hi) > 0.1:
        warnings.append(f"S(Q) averages {1 + s_hi:.2f} near Qmax instead of 1: check the composition and the background scale")
    if np.isfinite(slope) and slope > 0:
        warnings.append(f"G(r) below rpoly rises with r (slope {slope:.2f}): the normalisation is off, check composition and background")
    if rpoly > 1.5:
        warnings.append(f"rpoly {rpoly:g} Å is above most nearest-neighbour distances: the correction can remove real peaks")
    if rpoly <= 0 or degree == 0:
        warnings.append("no ad hoc polynomial correction (rpoly too small)")
    params = {"composition": composition, "background": bkg is not None, "bkg_scale": bkg_scale, "qmin": qmin,
              "qmax": qmax, "qmaxinst": qmaxinst, "rpoly": rpoly, "poly_degree": degree, "rmin": rmin, "rmax": rmax,
              "rstep": rstep, "lorch": lorch, "wavelength_A": wavelength_A, "polarization": applied_pol, "rho0": rho0}
    clean = lambda d: {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in d.items()}
    return {
        "params": params,
        "steps": {"raw": _thin(q=q, sample=i, background=bkg), "corrected": _thin(q=q, y=corrected),
                  "sq": _thin(q=q, y=sq), "fq": _thin(q=qf, y=fq, uncorrected=fq_raw), "gr": _thin(r=r, y=g)},
        "gr_full": {"r": r.tolist(), "y": g.tolist(), "dy": None if dg is None else dg.tolist()},
        "quality": clean(quality),
        "warnings": warnings,
    }


def write_gr(path, r, g, params: dict, dg=None) -> None:
    """pdf.gr as in the dataset: '# key=value' header (qmax, qmin first, then the other scalar parameters, e.g. the
    instrument qdamp) and r, G, σ columns."""
    r, g = np.asarray(r, float), np.asarray(g, float)
    dg = np.full(len(g), max(np.std(g) * 0.02, 1e-4)) if dg is None else np.asarray(dg, float)  # pdf.load_gr's default
    keys = ["qmax", "qmin"] + [k for k in params if k not in ("qmax", "qmin")]
    tok = [f"{k}={params[k]:g}" if isinstance(params[k], float) else f"{k}={params[k]}" for k in keys
           if k in params and params[k] is not None and not isinstance(params[k], (list, dict)) and " " not in str(params[k])]
    np.savetxt(path, np.c_[r, g, dg], fmt="%.3f %.6f %.6f", header=" ".join(tok) + "\ncolumns: r_A G sigma")
