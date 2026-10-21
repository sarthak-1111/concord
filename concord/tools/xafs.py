"""XAFS tools on xraylarch: normalization, background removal, χ(k), Fourier transform, FEFF shell fits, XANES.

Shell fits fix S0² (from the beamline's reference foil, given in the sample metadata) and fit N, ΔR, σ² per
neighbour element plus one shared ΔE0, with FEFF6L paths computed from a candidate structure.
"""
import warnings

import numpy as np
from larch import Group
from larch.fitting import param, param_group
from larch.xafs import autobk, feffit, feffit_dataset, feffit_transform, feffpath, ff2chi, pre_edge, xftf
from pymatgen.core import Structure
from scipy.optimize import nnls

from concord.tools import tool
from concord.tools.feff import cluster_around, feff_input, path_sigma2, run_feff

KTOE = 3.8099821  # ħ²/2mₑ in eV·Å²: E - E0 = KTOE * k²


@tool
def normalize(energy: np.ndarray, mu: np.ndarray) -> dict:
    g = Group(energy=np.asarray(energy, float), mu=np.asarray(mu, float))
    pre_edge(g)
    return {"e0": float(g.e0), "edge_step": float(g.edge_step), "norm": np.asarray(g.norm), "flat": np.asarray(g.flat)}


@tool
def chi_from_mu(energy: np.ndarray, mu: np.ndarray, rbkg: float = 1.0, kweight: float = 2.0, kmax: float | None = None) -> dict:
    g = Group(energy=np.asarray(energy, float), mu=np.asarray(mu, float))
    pre_edge(g)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        autobk(g, rbkg=rbkg, kweight=kweight, kmax=kmax)
    return {"k": np.asarray(g.k), "chi": np.asarray(g.chi), "e0": float(g.e0), "edge_step": float(g.edge_step)}


@tool
def fourier_transform(k: np.ndarray, chi: np.ndarray, kmin: float = 3.0, kmax: float = 12.0, kweight: float = 2.0,
                      dk: float = 1.0, window: str = "hanning") -> dict:
    g = Group(k=np.asarray(k, float), chi=np.asarray(chi, float))
    xftf(g, kmin=kmin, kmax=kmax, kweight=kweight, dk=dk, window=window)
    return {"r": np.asarray(g.r), "chir_mag": np.asarray(g.chir_mag), "chir_re": np.asarray(g.chir_re), "chir_im": np.asarray(g.chir_im)}


def structure_paths(structure: Structure, absorber: str, edge: str, rmax_path: float = 5.5, nleg: int = 3) -> list:
    """FEFF paths for every symmetry-inequivalent absorber site of a periodic structure (clusters cut from a
    supercell). Multi-site structures (e.g. tetrahedral and octahedral Co in Co3O4) need all sites: a single
    site can lack a neighbour shell the data contains."""
    reps = [max(1, int(np.ceil(2 * 7.0 / x))) for x in structure.lattice.abc]
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        groups = SpacegroupAnalyzer(structure, symprec=0.1).get_symmetrized_structure().equivalent_indices
        reps_sites = [g[0] for g in groups if max(structure[g[0]].species.items(), key=lambda kv: kv[1])[0].symbol == absorber]
    except Exception:  # disordered cells: one site per absorber-bearing site is enough
        reps_sites = []
    reps_sites = reps_sites or [i for i, st in enumerate(structure) if absorber in {sp.symbol for sp in st.species}][:1]
    if not reps_sites:
        raise ValueError(f"{absorber} not in structure {structure.composition.reduced_formula}")
    sc = structure.copy()
    sc.make_supercell(reps)
    rng = np.random.default_rng(0)  # disordered sites (e.g. A1 PtNi) get one species each, drawn by occupancy
    symbols = []
    for site in sc:
        sp = list(site.species.items())
        p = np.array([o for _, o in sp]) / sum(o for _, o in sp)
        symbols.append(sp[rng.choice(len(sp), p=p)][0].symbol)
    center = sc.lattice.get_cartesian_coords([0.5, 0.5, 0.5])
    paths = []
    for j in reps_sites:
        site_frac = structure[j].frac_coords
        target = sc.lattice.get_cartesian_coords((site_frac + np.floor(np.array(reps) / 2)) / np.array(reps))
        cands = [i for i, s_ in enumerate(symbols) if s_ == absorber]
        i0 = min(cands, key=lambda i: np.linalg.norm(sc[i].coords - target) + 1e-3 * np.linalg.norm(sc[i].coords - center))
        sym, pos, ia = cluster_around(symbols, sc.cart_coords, i0, radius=rmax_path + 1.5)
        paths += [feffpath(str(f)) for f in run_feff(feff_input(sym, pos, ia, edge, rmax_path, nleg))]
    return paths


def first_shell_paths(paths: list, rmin: float, rmax: float) -> dict:
    """Shortest single-scattering path per neighbour element with reff inside [rmin, rmax] (true distances)."""
    out = {}
    for p in sorted(paths, key=lambda p: p.reff):
        if p.nleg == 2 and rmin <= p.reff <= rmax:
            el = p.geom[1][0]
            out.setdefault(el, p)
    return out


def auto_rmax(k: np.ndarray, chi: np.ndarray, reff: float, kmin: float, kmax: float, kweight: float = 2.0) -> float:
    """End of the first-shell R window: the |χ(R)| minimum between the first-shell peak and reff + 0.45 Å.
    Searching that far keeps both lobes of a Ramsauer–Townsend split peak (Pt) inside the window."""
    ft = fourier_transform(k, chi, kmin=kmin, kmax=kmax, kweight=kweight)
    r, mag = ft["r"], ft["chir_mag"]
    m = (r >= reff - 1.0) & (r <= reff + 0.1)
    peak = r[m][np.argmax(mag[m])]
    s = (r >= peak + 0.25) & (r <= reff + 0.45)
    return float(r[s][np.argmin(mag[s])]) if s.any() else float(reff + 0.45)


@tool
def shell_fit(k: np.ndarray, chi: np.ndarray, paths: list, s02: float, kmin: float = 3.0, kmax: float = 12.0,
              rmin: float = 1.0, rmax: float | None = None, kweight: float = 2.0, dk: float = 1.0, shell_tol: float = 0.35) -> dict:
    """First-coordination-shell fit: N, ΔR, σ² per neighbour element whose nearest path lies within `shell_tol`
    of the overall nearest neighbour (e.g. Pt and Co in Pt3Co), plus a shared ΔE0, in the R window [rmin, rmax]
    of the Fourier transform. rmax defaults to the |χ(R)| minimum after the first-shell peak, so the next shell
    does not leak into the fit."""
    ss = [p for p in paths if p.nleg == 2]
    nearest = min(p.reff for p in ss)
    shells = first_shell_paths(paths, 0.0, nearest + shell_tol)
    if rmax is None:
        rmax = auto_rmax(k, chi, nearest, kmin, kmax, kweight)
    if not shells:
        raise ValueError(f"no single-scattering path between {rmin} and {rmax} Å")
    pars = {"s02": param(s02, vary=False), "de0": param(0.0, vary=True, min=-15, max=15)}
    fit_paths = {}
    for i, (el, p) in enumerate(shells.items()):
        pars.update({f"n{i}": param(float(p.degen), vary=True, min=0.0, max=20.0),
                     f"dr{i}": param(0.0, vary=True, min=-0.3, max=0.3),
                     f"ss{i}": param(0.005, vary=True, min=0.0005, max=0.05)})
        fit_paths[el] = feffpath(p.filename, degen=1.0, s02=f"s02*n{i}", e0="de0", deltar=f"dr{i}", sigma2=f"ss{i}")
    params = param_group(**pars)
    trans = feffit_transform(kmin=kmin, kmax=kmax, kweight=kweight, dk=dk, window="hanning", rmin=rmin, rmax=rmax, fitspace="r")
    dset = feffit_dataset(data=Group(k=np.asarray(k, float), chi=np.asarray(chi, float)), paths=fit_paths, transform=trans)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = feffit(params, dset)
    res = out.params
    val = lambda name: (float(res[name].value), float(res[name].stderr) if res[name].stderr is not None else None)
    rows = []
    for i, (el, p) in enumerate(shells.items()):
        (n, dn), (dr, ddr), (ss, dss) = val(f"n{i}"), val(f"dr{i}"), val(f"ss{i}")
        rows.append({"neighbor": el, "N": n, "N_err": dn, "R_A": float(p.reff + dr), "R_err": ddr, "sigma2": ss,
                     "sigma2_err": dss, "reff_A": float(p.reff), "N_model": float(p.degen)})
    de0 = val("de0")
    return {"shells": rows, "e0_shift": de0[0], "e0_err": de0[1], "s02": s02, "rfactor": float(out.rfactor),
            "chi2_reduced": float(out.chi2_reduced), "n_idp": float(out.n_independent), "n_varys": int(out.nvarys),
            "window": {"kmin": kmin, "kmax": kmax, "rmin": rmin, "rmax": rmax, "kweight": kweight}}


def simulate_chi(paths: list, s02: float, temperature: float, theta_d: float, density: float, e0_shift: float = 0.0,
                 k: np.ndarray | None = None, sigma2_extra: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """χ(k) from FEFF paths with correlated-Debye σ² per path; density in atoms/Å³."""
    for p in paths:
        p.s02, p.e0 = s02, e0_shift
        p.sigma2 = path_sigma2(p, theta_d, temperature, density) + sigma2_extra
    k = np.arange(0, 18.0, 0.05) if k is None else k
    g = ff2chi(paths, k=k)
    return np.asarray(g.k), np.asarray(g.chi)


# -- XANES ---------------------------------------------------------------------------------------------
def edge_position(energy: np.ndarray, norm: np.ndarray) -> float:
    """Energy where the normalized absorption first crosses 0.5 (half edge step)."""
    e, n = np.asarray(energy, float), np.asarray(norm, float)
    i = int(np.argmax(n >= 0.5))
    return float(np.interp(0.5, n[i - 1:i + 1], e[i - 1:i + 1])) if i > 0 else float(e[0])


@tool
def oxidation_from_edge(edge_eV: float, standards: list[dict]) -> dict:
    """Oxidation state by linear interpolation of the edge position between reference standards [{valence, edge_eV}]."""
    pts = sorted(standards, key=lambda s: s["edge_eV"])
    x = [s["edge_eV"] for s in pts]
    y = [s["valence"] for s in pts]
    slope = (y[-1] - y[0]) / (x[-1] - x[0])
    return {"valence": float(y[0] + slope * (edge_eV - x[0])), "edge_eV": edge_eV, "standards": standards}


@tool
def linear_combination_fit(energy: np.ndarray, norm: np.ndarray, references: dict, emin: float = -20, emax: float = 40,
                           e0: float | None = None) -> dict:
    """Non-negative LCF of a normalized XANES against references {name: (energy, norm)}, weights summing to ~1."""
    e = np.asarray(energy, float)
    e0 = e0 if e0 is not None else e[np.argmax(np.gradient(norm, e))]
    m = (e >= e0 + emin) & (e <= e0 + emax)
    A = np.column_stack([np.interp(e[m], *references[n]) for n in references])
    w, rnorm = nnls(A, np.asarray(norm, float)[m])
    total = w.sum() or 1.0
    resid = np.asarray(norm)[m] - A @ w
    return {"weights": {n: float(wi / total) for n, wi in zip(references, w)}, "sum_weights": float(w.sum()),
            "r_factor": float(np.sum(resid ** 2) / np.sum(np.asarray(norm)[m] ** 2))}
