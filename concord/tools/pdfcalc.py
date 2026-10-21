"""Real-space X-ray PDF calculator for periodic structures.

Replaces diffpy.srreal's PDFCalculator, whose macOS arm64 wheel (1.4.0) links a libdiffpy.dylib that is not
shipped. Same model: G(r) = R(r)/r - 4πrρ0 with Gaussian pair peaks of width
σ'_ij = sqrt(U_i + U_j) * sqrt(1 - δ1/r - δ2/r² + Qbroad² r²), a Qdamp envelope exp(-(Qdamp r)²/2) and Qmax
termination ripples. X-ray weights use f(0) = Z. Partial occupancies are weighted by occupancy.
"""
import numpy as np
from pymatgen.core import Lattice, Structure

LATTICE_KEYS = ("a", "b", "c", "alpha", "beta", "gamma")


def site_label(site) -> str:
    """Majority element on a (possibly disordered) site; Uiso is assigned per label."""
    return max(site.species.items(), key=lambda kv: kv[1])[0].symbol


class PDFCalculator:
    def __init__(self, structure: Structure, rmax: float, rstep: float = 0.01, qmax: float | None = None,
                 qmin: float = 0.0, extend: float = 8.0, margin: float = 1.12):
        self.structure = structure
        self.rmax, self.rstep, self.qmax, self.qmin, self.extend = rmax, rstep, qmax, qmin, extend
        r_cut = (rmax + extend) * margin
        center, point, images, _ = structure.get_neighbor_list(r_cut)
        self.frac = structure.frac_coords[point] + images - structure.frac_coords[center]
        z_site = np.array([sum(sp.Z * occ for sp, occ in site.species.items()) for site in structure])
        occ = np.array([sum(site.species.values()) for site in structure])
        self.n_atoms = float(occ.sum())
        mean_f = z_site.sum() / self.n_atoms
        self.w = z_site[center] * z_site[point] / (self.n_atoms * mean_f ** 2)
        labels = [site_label(s) for s in structure]
        self.labels = sorted(set(labels))
        idx = {lab: i for i, lab in enumerate(self.labels)}
        self.li = np.array([idx[labels[c]] for c in center])
        self.lj = np.array([idx[labels[p]] for p in point])
        self.r_int = np.arange(rstep, rmax + extend, rstep)  # internal grid, starts at one step to avoid r=0
        if qmax:
            q = np.arange(max(qmin, 0.005), qmax, 0.01)
            self._sin = np.sin(np.outer(q, self.r_int))  # (nq, nr)
            self._dq = 0.01
        taper = np.clip((rmax + extend - self.r_int) / (0.5 * extend), 0, 1)
        self._taper = 0.5 - 0.5 * np.cos(np.pi * taper)  # smooth cut so the sine transform does not ring

    def lattice(self, params: dict | None) -> Lattice:
        base = dict(zip(LATTICE_KEYS, self.structure.lattice.parameters))
        return Lattice.from_parameters(**{**base, **(params or {})})

    def __call__(self, r: np.ndarray, *, lattice: dict | None = None, uiso: dict | None = None, delta1: float = 0.0,
                 delta2: float = 0.0, qdamp: float = 0.0, qbroad: float = 0.0, scale: float = 1.0) -> np.ndarray:
        lat = self.lattice(lattice)
        dist = np.linalg.norm(self.frac @ lat.matrix, axis=1)
        u = np.array([max((uiso or {}).get(lab, 0.005), 1e-6) for lab in self.labels])
        keep = dist < self.r_int[-1] + 1.0
        d, w, s2 = dist[keep], self.w[keep], (u[self.li] + u[self.lj])[keep]
        corr = np.clip(1 - delta1 / d - delta2 / d ** 2 + (qbroad * d) ** 2, 1e-4, None)
        sigma = np.sqrt(s2 * corr)
        # merge pairs with identical (distance, width) before evaluating Gaussians
        key = np.round(d / 1e-4).astype(np.int64) * 4096 + np.round(sigma / 1e-4).astype(np.int64)
        uniq, inv = np.unique(key, return_inverse=True)
        wsum = np.bincount(inv, weights=w)
        first = np.zeros(len(uniq), dtype=np.int64)
        first[inv[::-1]] = np.arange(len(inv))[::-1]
        du, su = d[first], sigma[first]
        R = np.zeros_like(self.r_int)
        half = int(np.ceil(5 * su.max() / self.rstep)) + 1
        offsets = np.arange(-half, half + 1)
        c_idx = np.round((du - self.r_int[0]) / self.rstep).astype(np.int64)
        idx = c_idx[:, None] + offsets[None, :]
        valid = (idx >= 0) & (idx < len(self.r_int))
        rr = self.r_int[np.clip(idx, 0, len(self.r_int) - 1)]
        gauss = wsum[:, None] * np.exp(-0.5 * ((rr - du[:, None]) / su[:, None]) ** 2) / (np.sqrt(2 * np.pi) * su[:, None])
        R += np.bincount(idx[valid], weights=gauss[valid], minlength=len(self.r_int))
        rho0 = self.n_atoms / lat.volume
        G = R / self.r_int - 4 * np.pi * rho0 * self.r_int
        if qdamp:
            G *= np.exp(-0.5 * (qdamp * self.r_int) ** 2)
        if self.qmax:
            F = self._sin @ (G * self._taper) * self.rstep
            G = (2 / np.pi) * (self._sin.T @ F) * self._dq
        return scale * np.interp(r, self.r_int, G)


def spherical_envelope(r: np.ndarray, psize: float) -> np.ndarray:
    """Characteristic function of a sphere of diameter psize (same as diffpy.srfit's sphericalCF)."""
    x = np.asarray(r) / psize
    return np.where(x < 1, 1 - 1.5 * x + 0.5 * x ** 3, 0.0)


def neighbour_shells(structure: Structure, absorber: str, rmax: float = 4.0, tol: float = 0.05) -> list[dict]:
    """Coordination shells around `absorber` sites: [{neighbor, N, R_A}], averaged over absorber sites, by element."""
    sites = [i for i, s in enumerate(structure) if site_label(s) == absorber]
    if not sites:
        return []
    shells: dict = {}
    for i in sites:
        for nb in structure.get_neighbors(structure[i], rmax):
            for sp, occ in nb.species.items():
                shells.setdefault(sp.symbol, []).append((nb.nn_distance, occ))
    out = []
    for el, pairs in shells.items():
        pairs.sort()
        group = [pairs[0]]
        for d, occ in pairs[1:] + [(np.inf, 0)]:
            if d - group[-1][0] > tol:
                ds = np.array([g[0] for g in group]); ws = np.array([g[1] for g in group])
                out.append({"neighbor": el, "N": float(ws.sum() / len(sites)), "R_A": float((ds * ws).sum() / ws.sum())})
                group = []
            group.append((d, occ))
    return sorted(out, key=lambda s: s["R_A"])


def first_shells(structure: Structure, absorber: str, rmax: float = 4.0, tol: float = 0.25) -> list[dict]:
    """First shell per neighbour element (distances within `tol` of the nearest one), averaged over absorber
    sites and weighted by occupancy. Same definition as the data builder's cluster_shells, for periodic cells."""
    sites = [s for s in structure if site_label(s) == absorber]
    per_el: dict = {}
    for site in sites:
        for nb in structure.get_neighbors(site, rmax):
            for sp, occ in nb.species.items():
                per_el.setdefault(sp.symbol, []).append((nb.nn_distance, occ))
    out = []
    for el, pairs in per_el.items():
        d = np.array([p[0] for p in pairs]); w = np.array([p[1] for p in pairs])
        m = d < d.min() + tol
        out.append({"absorber": absorber, "neighbor": el, "N": float(w[m].sum() / len(sites)), "R_A": float((d[m] * w[m]).sum() / w[m].sum())})
    return sorted(out, key=lambda s: s["R_A"])
