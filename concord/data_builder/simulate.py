"""Simulate XRD, PDF and XAFS from one structural model (bulk Structure or nanoparticle ase.Atoms).

XRD: pymatgen stick pattern + TCH profiles (bulk) or the Debye scattering equation via DebyeCalculator (particles).
PDF: concord's real-space calculator (bulk) or DebyeCalculator G(r) (particles); noise is added in F(Q), so it is
correlated in r as in real data. EXAFS: FEFF6L around sampled absorber sites, averaged, with correlated-Debye σ².
μ(E): χ(k) on a simple arctan edge + white line; XANES from this model is lower fidelity and flagged as such.
"""
import warnings

import numpy as np
import xraydb
from ase import Atoms
from pymatgen.core import Element, Structure

from concord.tools import xrd as xrd_tools
from concord.tools.feff import cluster_around, feff_input, run_feff
from concord.tools.pdfcalc import PDFCalculator
from concord.tools.xafs import KTOE, simulate_chi

warnings.filterwarnings("ignore", module="debyecalculator")


def _u(rng, lo_hi):
    lo, hi = lo_hi
    return float(rng.uniform(lo, hi))


def q_of(two_theta, lam):
    return 4 * np.pi * np.sin(np.radians(np.asarray(two_theta) / 2)) / lam


# -- XRD -----------------------------------------------------------------------------------------------
def xrd_bulk(structure: Structure, tt: np.ndarray, lam: float, caglioti: dict, crystallite_nm: float, biso: dict) -> np.ndarray:
    return xrd_tools.simulate_pattern(structure, tt, lam, size_nm=crystallite_nm, instrument=caglioti, debye_waller=biso)


def xrd_cluster(atoms: Atoms, tt: np.ndarray, lam: float, caglioti: dict, biso: float) -> np.ndarray:
    from debyecalculator import DebyeCalculator
    dc = DebyeCalculator(qmin=float(q_of(tt[0], lam)) - 0.05, qmax=float(q_of(tt[-1], lam)) + 0.05, qstep=0.004,
                         biso=biso, device="cpu", radiation_type="xray")
    q, iq = dc.iq(atoms)
    two_theta = np.radians(tt)
    y = np.interp(q_of(tt, lam), q, iq) * (1 + np.cos(two_theta) ** 2) / 2
    fwhm = xrd_tools.caglioti_fwhm_deg(40.0, caglioti["U"], caglioti["V"], caglioti["W"])
    step = tt[1] - tt[0]
    sig = fwhm / 2.3548 / step
    kern = np.exp(-0.5 * (np.arange(-int(5 * sig) - 1, int(5 * sig) + 2) / sig) ** 2)
    return np.convolve(y, kern / kern.sum(), mode="same")


def xrd_measure(tt: np.ndarray, clean: np.ndarray, rng, bg: dict, counts_max: float) -> tuple[np.ndarray, np.ndarray]:
    """Scale to counts, add constant + amorphous hump + decaying background, then Poisson noise."""
    y = clean / clean.max()
    span = (tt - tt[0]) / (tt[-1] - tt[0])
    back = (_u(rng, bg["constant"]) + _u(rng, bg["hump"]) * np.exp(-0.5 * ((tt - 25) / 8) ** 2)
            + _u(rng, bg["decay"]) * np.exp(-3 * span))
    lam = (y + back) * counts_max
    counts = rng.poisson(lam).astype(float)
    return counts, np.sqrt(np.maximum(counts, 1.0))


# -- PDF -----------------------------------------------------------------------------------------------
def pdf_bulk(structure: Structure, r: np.ndarray, qmax: float, qdamp: float, qbroad: float, uiso: dict, delta2: float) -> np.ndarray:
    calc = PDFCalculator(structure, rmax=float(r[-1]), rstep=float(r[1] - r[0]), qmax=qmax)
    return calc(r, uiso=uiso, qdamp=qdamp, qbroad=qbroad, delta2=delta2)


def pdf_cluster(atoms: Atoms, r: np.ndarray, qmin: float, qmax: float, qdamp: float, biso: float) -> np.ndarray:
    from debyecalculator import DebyeCalculator
    dc = DebyeCalculator(qmin=qmin, qmax=qmax, qdamp=qdamp, rmin=float(r[0]), rmax=float(r[-1]) + 0.01,
                         rstep=float(r[1] - r[0]), biso=biso, device="cpu", radiation_type="xray")
    rr, g = dc.gr(atoms)
    return np.interp(r, rr, g)


def pdf_measure(r: np.ndarray, g: np.ndarray, rng, qmin: float, qmax: float, noise_rel: float) -> tuple[np.ndarray, np.ndarray]:
    """White noise in F(Q) transformed to r: correlated over ~π/Qmax, like measured PDFs."""
    dq = 0.02
    q = np.arange(qmin, qmax, dq)
    w = q / qmax  # F(Q) = Q[S(Q)-1]: errors grow with Q
    s = np.sin(np.outer(r, q))
    noise = (2 / np.pi) * dq * (s @ (rng.normal(0, 1, len(q)) * w))
    sigma = (2 / np.pi) * dq * np.sqrt((s ** 2) @ w ** 2)
    scale = noise_rel * np.abs(g).max() / sigma.mean()
    return g + noise * scale, sigma * scale


# -- XAFS ----------------------------------------------------------------------------------------------
def kmax_for(element: str, edge: str, kmax: float) -> float:
    """Stop the EXAFS 20 eV before the next edge of the same element (Ce L3 -> L2 is only 441 eV)."""
    nxt = {"L3": "L2", "L2": "L1"}.get(edge)
    if nxt:
        gap = xraydb.xray_edge(element, nxt).energy - xraydb.xray_edge(element, edge).energy
        kmax = min(kmax, float(np.sqrt((gap - 20) / KTOE)))
    return kmax


def exafs_chi(symbols: list[str], positions: np.ndarray, absorber: str, edge: str, sites: list[int], s02: float,
              theta_d: float, temperature: float, density: float, k: np.ndarray, radius: float, rmax_path: float) -> np.ndarray:
    """χ(k) averaged over absorber sites; each site's cluster runs through FEFF6L (cached by environment)."""
    chis = []
    for i in sites:
        sym, pos, ia = cluster_around(symbols, positions, i, radius)
        from larch.xafs import feffpath
        paths = [feffpath(str(f)) for f in run_feff(feff_input(sym, pos, ia, edge, rmax_path, nleg=3))]
        chis.append(simulate_chi(paths, s02, temperature, theta_d, density, k=k)[1])
    return np.mean(chis, axis=0)


def absorber_sites(symbols: list[str], positions: np.ndarray, absorber: str, n: int, rng, periodic_center: np.ndarray | None = None) -> list[int]:
    idx = np.array([i for i, s in enumerate(symbols) if s == absorber])
    if periodic_center is not None:  # bulk supercell: the absorber nearest the middle represents every site
        return [int(idx[np.argmin(np.linalg.norm(positions[idx] - periodic_center, axis=1))])]
    return [int(i) for i in rng.choice(idx, size=min(n, len(idx)), replace=False)]


def edge_model(energy: np.ndarray, e_edge: float, width: float, white_line: float) -> np.ndarray:
    """Normalized edge: arctan step plus a Lorentzian white line just above the edge."""
    x = energy - e_edge
    step = 0.5 + np.arctan(2 * x / width) / np.pi
    wl = white_line * (width / 2) ** 2 / ((x - 0.6 * width) ** 2 + (width / 2) ** 2)
    return step + wl * step


def energy_grid(e_edge: float, kmax: float) -> np.ndarray:
    pre = np.arange(e_edge - 150, e_edge - 20, 5.0)
    xanes = np.arange(e_edge - 20, e_edge + 40, 0.25)
    kk = np.arange(np.sqrt(40 / KTOE), kmax, 0.05)
    return np.concatenate([pre, xanes, e_edge + KTOE * kk ** 2])


def mu_spectrum(k: np.ndarray, chi: np.ndarray, element: str, edge: str, valences: dict, xanes: dict, e0_shift: float,
                kmax: float, rng, noise: float) -> tuple[np.ndarray, np.ndarray, float]:
    """μ(E) = background + edge_step·[Σ_v f_v·edge_v(E)]·(1 + χ(k)). valences: {valence: fraction}."""
    e_tab = xraydb.xray_edge(element, edge).energy
    shift = xanes["chemical_shift_eV_per_valence"][element]
    width = xanes["core_width_eV"][element]
    e_edge = e_tab + shift * sum(v * f for v, f in valences.items())
    energy = energy_grid(e_edge, kmax)
    norm = sum(f * edge_model(energy, e_tab + shift * v, width, xanes["white_line"]["base"] + xanes["white_line"]["per_valence"] * v)
               for v, f in valences.items())
    kE = np.sqrt(np.clip(energy - e_edge - e0_shift, 0, None) / KTOE)
    chi_e = np.where(energy > e_edge + e0_shift, np.interp(kE, k, chi), 0.0)
    step = 1.0
    pre = 0.15 - 2e-4 * (energy - e_edge)
    post = 1 - 1e-4 * np.clip(energy - e_edge, 0, None)
    mu = pre + step * norm * post * (1 + chi_e)
    return energy, mu + rng.normal(0, noise * step, len(mu)), float(e_edge)


def standards(element: str, edge: str, valences: list[float], xanes: dict) -> dict:
    """Simulated valence standards (normalized edges, same model as the samples)."""
    e_tab = xraydb.xray_edge(element, edge).energy
    shift, width = xanes["chemical_shift_eV_per_valence"][element], xanes["core_width_eV"][element]
    energy = np.arange(e_tab - 30, e_tab + 60, 0.25)
    out = {}
    for v in valences:
        out[v] = (energy, edge_model(energy, e_tab + shift * v, width, xanes["white_line"]["base"] + xanes["white_line"]["per_valence"] * v))
    return out


def biso_of(uiso: float) -> float:
    return float(8 * np.pi ** 2 * uiso)


def mass(el: str) -> float:
    return float(Element(el).atomic_mass)
