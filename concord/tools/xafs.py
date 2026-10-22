"""XAFS tools on xraylarch: normalization, background removal, χ(k), Fourier transform, FEFF shell fits, XANES.

Shell fits fix S0² (from the beamline's reference foil, given in the sample metadata) and fit N, ΔR, σ² per
neighbour element plus one shared ΔE0, with FEFF6L paths computed from a candidate structure.
"""
import importlib
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

_feffit_mod = importlib.import_module("larch.xafs.feffit")  # the module, not the function larch.xafs exports
_propagate = _feffit_mod.propagate_uncertainties


def _safe_propagate(result, datasets, _larch=None):
    try:
        _propagate(result, datasets, _larch=_larch)
    except np.linalg.LinAlgError:  # singular covariance (an unconstrained background parameter): keep best fit, no stderr
        pass


_feffit_mod.propagate_uncertainties = _safe_propagate


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
    site can lack a neighbour shell the data contains. Each path carries `site_weight`, its site's share of the
    absorber atoms."""
    reps = [max(1, int(np.ceil(2 * 7.0 / x))) for x in structure.lattice.abc]
    try:
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        groups = SpacegroupAnalyzer(structure, symprec=0.1).get_symmetrized_structure().equivalent_indices
        reps_sites = [(g[0], len(g)) for g in groups if max(structure[g[0]].species.items(), key=lambda kv: kv[1])[0].symbol == absorber]
    except Exception:  # disordered cells: one site per absorber-bearing site is enough
        reps_sites = []
    reps_sites = reps_sites or [(i, 1) for i, st in enumerate(structure) if absorber in {sp.symbol for sp in st.species}][:1]
    if not reps_sites:
        raise ValueError(f"{absorber} not in structure {structure.composition.reduced_formula}")
    total = sum(m for _, m in reps_sites)
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
    for j, mult in reps_sites:
        site_frac = structure[j].frac_coords
        target = sc.lattice.get_cartesian_coords((site_frac + np.floor(np.array(reps) / 2)) / np.array(reps))
        cands = [i for i, s_ in enumerate(symbols) if s_ == absorber]
        i0 = min(cands, key=lambda i: np.linalg.norm(sc[i].coords - target) + 1e-3 * np.linalg.norm(sc[i].coords - center))
        sym, pos, ia = cluster_around(symbols, sc.cart_coords, i0, radius=rmax_path + 1.5)
        for f in run_feff(feff_input(sym, pos, ia, edge, rmax_path, nleg)):
            path = feffpath(str(f))
            path.site_weight = mult / total
            paths.append(path)
    return paths


def first_shell_paths(paths: list, rmin: float, rmax: float) -> dict:
    """Shortest single-scattering path per neighbour element with reff inside [rmin, rmax] (true distances)."""
    out = {}
    for p in sorted(paths, key=lambda p: p.reff):
        if p.nleg == 2 and rmin <= p.reff <= rmax:
            el = p.geom[1][0]
            out.setdefault(el, p)
    return out


@tool
def shell_fit(k: np.ndarray, chi: np.ndarray, paths: list, s02: float, kmin: float = 3.0, kmax: float = 12.0,
              rmin: float = 1.0, rmax: float | None = None, kweight: float = 2.0, dk: float = 1.0, shell_tol: float = 0.35,
              outer: float = 2.0, extra: list | None = None, staged: bool = False) -> dict:
    """First-coordination-shell fit: N, ΔR, σ² per neighbour element whose nearest path lies within `shell_tol`
    of the overall nearest neighbour (e.g. Pt and Co in Pt3Co), plus a shared ΔE0, in the R window [rmin, rmax]
    (default: nearest + 1.0 Å). Every other path out to nearest + `outer` Å enters as a structural background
    (degeneracy × site weight × spherical truncation γ0(R; D), ΔR = α·reff, one σ²): tails of strong outer shells leaking into a
    first-shell-only window bias N and σ² upward (+10–20 % for Co–O in Co3O4, from tests on noise-free spectra).
    `extra`: paths for a shell the structural model lacks (see probe_path), fitted with free N, ΔR and σ²."""
    ss = [p for p in paths if p.nleg == 2]
    nearest = min(p.reff for p in ss)
    shells = first_shell_paths(paths, 0.0, nearest + shell_tol)
    rmax = nearest + 1.0 if rmax is None else rmax
    if not shells:
        raise ValueError(f"no single-scattering path between {rmin} and {rmax} Å")
    pars = {"s02": param(s02, vary=False), "de0": param(0.0, vary=True, min=-15, max=15)}
    fit_paths = {}
    for i, (el, p) in enumerate(shells.items()):
        pars.update({f"n{i}": param(float(p.degen), vary=True, min=0.0, max=20.0),
                     f"dr{i}": param(0.0, vary=True, min=-0.3, max=0.3),
                     f"ss{i}": param(0.005, vary=True, min=0.0005, max=0.05)})
        fit_paths[el] = feffpath(p.filename, degen=1.0, s02=f"s02*n{i}", e0="de0", deltar=f"dr{i}", sigma2=f"ss{i}")
    for j, p in enumerate(extra or []):  # a test shell stays a plausible bond: ±0.15 Å, σ² of a stiff bond at most 0.01 Å²
        pars.update({f"nx{j}": param(0.5, vary=True, min=0.0, max=12.0), f"drx{j}": param(0.0, vary=True, min=-0.15, max=0.15),
                     f"ssx{j}": param(0.004, vary=True, min=0.001, max=0.01)})
        fit_paths[f"extra{j}"] = feffpath(p.filename, degen=1.0, s02=f"s02*nx{j}", e0="de0", deltar=f"drx{j}", sigma2=f"ssx{j}")
    background = [p for p in paths if p.reff <= nearest + outer and not (p.nleg == 2 and p.reff <= nearest + shell_tol)]
    if background:
        pars.update({"d_out": param(100.0, vary=True, min=8.0, max=3000.0), "alpha_out": param(0.0, vary=True, min=-0.05, max=0.05),
                     "ss_out": param(0.006, vary=True, min=0.001, max=0.04)})
        for j, p in enumerate(background):
            w = getattr(p, "site_weight", 1.0)  # spherical-particle truncation of the outer shells, γ0(R; D), as in the PDF envelope
            fit_paths[f"bg{j}"] = feffpath(p.filename, s02=f"s02*{w:.6f}*(1 - 1.5*reff/d_out + 0.5*(reff/d_out)**3)", e0="de0",
                                           deltar="alpha_out*reff", sigma2="ss_out")
    trans = feffit_transform(kmin=kmin, kmax=kmax, kweight=kweight, dk=dk, window="hanning", rmin=rmin, rmax=rmax, fitspace="r")
    dset = feffit_dataset(data=Group(k=np.asarray(k, float), chi=np.asarray(chi, float)), paths=fit_paths, transform=trans)

    def run(params):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return feffit(params, dset)

    def summary(out, val):
        rows = []
        for i, (el, p) in enumerate(shells.items()):
            (n, dn), (dr, ddr), (ss, dss) = val(f"n{i}"), val(f"dr{i}"), val(f"ss{i}")
            rows.append({"neighbor": el, "N": n, "N_err": dn, "R_A": float(p.reff + dr), "R_err": ddr, "sigma2": ss,
                         "sigma2_err": dss, "reff_A": float(p.reff), "N_model": float(p.degen)})
        for j, p in enumerate(extra or []):
            (n, dn), (dr, ddr), (ss, dss) = val(f"nx{j}"), val(f"drx{j}"), val(f"ssx{j}")
            rows.append({"neighbor": p.geom[1][0], "N": n, "N_err": dn, "R_A": float(p.reff + dr), "R_err": ddr, "sigma2": ss,
                         "sigma2_err": dss, "reff_A": float(p.reff), "N_model": 0.0, "extra": True})
        de0 = val("de0")
        d = out.datasets[0]
        curves = {"r": np.asarray(d.data.r), "chir_mag_data": np.asarray(d.data.chir_mag), "chir_mag_model": np.asarray(d.model.chir_mag),
                  "k": np.asarray(d.data.k), "chi_data": np.asarray(d.data.chi), "chi_model": np.asarray(d.model.chi)}
        return {"shells": rows, "e0_shift": de0[0], "e0_err": de0[1], "s02": s02, "rfactor": float(out.rfactor), "curves": curves,
                "chi2_reduced": float(out.chi2_reduced), "n_idp": float(out.n_independent), "n_varys": int(out.nvarys),
                "background": {"n_paths": len(background), **({k_: val(k_)[0] for k_ in ("d_out", "alpha_out", "ss_out")} if background else {})},
                "window": {"kmin": kmin, "kmax": kmax, "rmin": rmin, "rmax": rmax, "kweight": kweight}}

    if staged:
        return _staged(pars, run, summary)
    out = run(param_group(**pars))
    res = out.params
    return summary(out, lambda name: (float(res[name].value), float(res[name].stderr) if res[name].stderr is not None else None))


def _group(name: str) -> str:
    """shell_fit parameter name -> its stage group (exafs_specialist.STAGES)."""
    if name in ("d_out", "alpha_out", "ss_out"):
        return "background"
    if name == "de0":
        return "e0"
    return {"dr": "distances", "ss": "disorder", "n": "coordination"}[name.rstrip("0123456789").rstrip("x")]


def _staged(pars: dict, run, summary) -> dict:
    """The EXAFS ladder (exafs_specialist.STAGES): each stage starts from the best fit so far, frees only its
    groups, and is kept only if should_accept passes; otherwise its values are restored and its groups stay fixed.
    Uncertainties are those of the last kept fit that refined each parameter."""
    from concord.agents.exafs_specialist import STAGES, should_accept
    names = [n for n in pars if n != "s02"]
    values = {n: float(p.value) for n, p in pars.items()}
    bounds = {n: (p.min, p.max) for n, p in pars.items()}
    stderr, kept, stages, best, prev = {}, set(), [], None, None
    for st in STAGES:
        groups = set(st["free"]) | (kept if st.get("with_kept") else set())
        free = [n for n in names if _group(n) in groups]
        out = run(param_group(**{n: param(values[n], vary=n in free, min=bounds[n][0], max=bounds[n][1]) for n in pars}))
        res = out.params
        fitted = {n: float(res[n].value) for n in names}
        errs = {n: float(res[n].stderr) if res[n].stderr is not None else None for n in free}
        result = summary(out, lambda n: (fitted[n], errs.get(n, stderr.get(n))))
        ok, why = should_accept(prev, result)
        stages.append({"key": st["key"], "label": st["label"], "free": sorted(groups), "rfactor": result["rfactor"], "kept": ok, "why": why})
        if ok:
            values.update(fitted)
            stderr.update(errs)
            kept |= set(st["free"])
            best, prev = result, result["rfactor"]
    if best is None:  # no stage passed the gate: say so rather than return the start model as a fit
        raise ValueError("staged EXAFS fit: no stage passed the physical/R-factor gate: "
                         + "; ".join(f"{s['label']}: {s['why']}" for s in stages))
    return {**best, "stages": stages}

def probe_path(absorber: str, edge: str, neighbor: str = "O", r: float = 2.0):
    """Absorber–neighbour single-scattering path from a small octahedral cluster: a test shell for an
    environment the structural model lacks (e.g. Pt–O from a surface oxide on a metal particle)."""
    pos = np.array([[0.0, 0.0, 0.0]] + [[sign * r * (i == j) for j in range(3)] for i in range(3) for sign in (1, -1)])
    files = run_feff(feff_input([absorber] + [neighbor] * 6, pos, 0, edge, rmax_path=r + 0.1, nleg=2))
    return min((p for p in (feffpath(str(f)) for f in files) if p.nleg == 2), key=lambda p: p.reff)


def simulate_chi(paths: list, s02: float, temperature: float, theta_d: float, density: float, e0_shift: float = 0.0,
                 k: np.ndarray | None = None, sigma2_extra: float = 0.0, theta_pairs: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    """χ(k) from FEFF paths with correlated-Debye σ² per path; density in atoms/Å³. theta_pairs: Debye temperatures
    for specific absorber–scatterer pairs, e.g. {"Pt-O": 400}."""
    for p in paths:
        p.s02, p.e0 = s02, e0_shift
        theta = (theta_pairs or {}).get(f"{p.geom[0][0]}-{p.geom[1][0]}", theta_d)
        p.sigma2 = path_sigma2(p, theta, temperature, density) + sigma2_extra
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
