"""Virtual XAFS: the EXAFS a sample should show, predicted from its PDF refinement. PREDICTED, NOT MEASURED.

FEFF paths come from the PDF-refined structure once; an ensemble of PDF-equivalent models then varies what the PDF
fit leaves uncertain: isotropic lattice expansion (lattice error), U_iso (its error, mapped to a Debye temperature
that sets each path's correlated-Debye σ²), the particle diameter (spherical truncation of every shell), and other
candidate phases whose Rw is within `rw_margin` of the best. The band is the 5–95 % range over the ensemble.
"""
import numpy as np
from larch.xafs import ff2chi, xftf
from larch import Group
from pymatgen.core import Element, Structure
from scipy.optimize import brentq

from concord.tools import tool
from concord.tools.feff import debye_uiso, sigma2_correlated_debye
from concord.tools.pdfcalc import spherical_envelope
from concord.tools.xafs import structure_paths

LABEL = "PREDICTED, NOT MEASURED"


def theta_from_uiso(mass: float, uiso: float, temperature: float = 300.0) -> float:
    """Debye temperature whose U_iso equals the PDF's (clipped to 80-2000 K)."""
    f = lambda t: debye_uiso(mass, t, temperature) - uiso
    lo, hi = 80.0, 2000.0
    if f(lo) < 0:
        return lo
    if f(hi) > 0:
        return hi
    return float(brentq(f, lo, hi))


def _ensemble_chi(paths: list, k: np.ndarray, alpha: float, theta: float, d_A: float | None, s02: float, temperature: float,
                  density: float) -> np.ndarray:
    for p in paths:
        a, b = p.geom[0][0], p.geom[1][0]
        r = float(p.reff) * (1 + alpha)
        p.deltar = alpha * float(p.reff)
        p.sigma2 = sigma2_correlated_debye(r, Element(a).atomic_mass, Element(b).atomic_mass, theta, temperature, density)
        p.s02 = s02 * getattr(p, "site_weight", 1.0) * (float(spherical_envelope(r, d_A)) if d_A else 1.0)
        p.e0 = 0.0
    return np.asarray(ff2chi(paths, k=k).chi)


def _chir(k: np.ndarray, chi: np.ndarray, kmin: float, kmax: float) -> tuple[np.ndarray, np.ndarray]:
    g = Group(k=k, chi=chi)
    xftf(g, kmin=kmin, kmax=kmax, kweight=2, dk=1, window="hanning")
    return np.asarray(g.r), np.asarray(g.chir_mag)


@tool
def predict_exafs(fits: list[dict], absorber: str, edge: str, *, s02: float = 0.9, temperature: float = 300.0,
                  kmax: float = 12.0, n: int = 24, rw_margin: float = 0.02, seed: int = 0) -> dict:
    """fits: PDF fits sorted by Rw (concord.tools.pdf.fit_pdf outputs, with refined `structure`)."""
    best = fits[0]
    members = [f for f in fits if f["rw"] <= best["rw"] + rw_margin and absorber in {e.symbol for e in _st(f).composition.elements}]
    if not members:
        raise ValueError(f"{absorber} is not in the refined model")
    rng = np.random.default_rng(seed)
    k = np.arange(0.0, kmax + 1.0, 0.05)
    chis, used = [], []
    for j, f in enumerate(members):
        st = _st(f)
        paths = structure_paths(st, absorber, edge)
        density = st.composition.num_atoms / st.volume
        rel = max(f["lattice_err"].get("a") or 0.0, 1e-4) / f["lattice"]["a"]
        u, du = f["uiso"][absorber], f["uiso_err"].get(absorber) or 0.1 * f["uiso"][absorber]
        mass = Element(absorber).atomic_mass
        for _ in range(max(2, n // len(members))):
            theta = theta_from_uiso(mass, max(rng.normal(u, du), 1e-4), temperature)
            d = rng.normal(10 * f["psize_nm"], 10 * (f["psize_err_nm"] or 0.05 * f["psize_nm"])) if f.get("psize_nm") else None
            chis.append(_ensemble_chi(paths, k, rng.normal(0, rel), theta, max(d, 5.0) if d else None, s02, temperature, density))
            used.append({"candidate": f["candidate"], "theta_K": theta})
    chis = np.array(chis)
    kmin = 3.0
    rs, mags = zip(*(_chir(k, c, kmin, kmax) for c in chis))
    mags = np.array(mags)
    q = lambda x: np.percentile(x, [5, 50, 95], axis=0)
    lo, med, hi = q(chis * k ** 2)
    rlo, rmed, rhi = q(mags)
    thetas = [u["theta_K"] for u in used]
    return {"label": LABEL, "absorber": absorber, "edge": edge, "members": len(chis), "candidates": sorted({u["candidate"] for u in used}),
            "theta_K_range": [float(min(thetas)), float(max(thetas))], "s02": s02, "kmin": kmin, "kmax": kmax,
            "k": k, "k2chi_lo": lo, "k2chi_median": med, "k2chi_hi": hi, "r": rs[0], "chir_lo": rlo, "chir_median": rmed, "chir_hi": rhi,
            "recommendation": recommendation(rs[0], rlo, rmed, rhi, absorber, edge, kmax, sorted({u["candidate"] for u in used}))}


def _st(f: dict) -> Structure:
    s = f["structure"]
    return s if isinstance(s, Structure) else Structure.from_str(s, fmt="cif")


def recommendation(r, lo, med, hi, absorber: str, edge: str, kmax: float, candidates: list[str]) -> str:
    """Templated measurement advice from the band: where the prediction is least certain, and what to resolve."""
    m = (r > 1.0) & (r < 4.0)
    spread = (hi - lo)[m] / np.maximum(med[m], 1e-9)
    worst = float(r[m][np.argmax(spread)])
    text = (f"Measure the {absorber} {edge} edge to k ≥ {kmax:.0f} Å⁻¹. The prediction is least certain near R ≈ {worst:.1f} Å "
            f"(band ±{50 * float(spread.max()):.0f} % of the median |χ(R)|)")
    if len(candidates) > 1:
        text += f"; the measurement would discriminate the PDF-equivalent phases {', '.join(candidates)}"
    return text + "."


def score_against(pred: dict, k: np.ndarray, chi: np.ndarray, rmin: float = 1.0, rmax: float = 3.5) -> dict:
    """R-factor of the predicted median |χ(R)| against a measured or hidden χ(k), and band coverage of k²χ."""
    k, chi = np.asarray(k, float), np.asarray(chi, float)
    r, mag = _chir(k, chi, pred["kmin"], pred["kmax"])
    rp = np.asarray(pred["r"])
    m = (r >= rmin) & (r <= rmax)
    med = np.interp(r[m], rp, np.asarray(pred["chir_median"]))
    rfac = float(np.sum((med - mag[m]) ** 2) / np.sum(mag[m] ** 2))
    kk = (k >= pred["kmin"]) & (k <= pred["kmax"])
    kp = np.asarray(pred["k"])
    lo, hi = (np.interp(k[kk], kp, np.asarray(pred[x])) for x in ("k2chi_lo", "k2chi_hi"))
    y = chi[kk] * k[kk] ** 2
    return {"rfactor_R": rfac, "band_coverage_k": float(np.mean((y >= lo) & (y <= hi))), "r_window": [rmin, rmax]}
