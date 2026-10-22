"""PDF structure refinement with diffpy.srfit: periodic model × spherical envelope (attenuated crystal).

Profile generator: concord.tools.pdfcalc (diffpy.srreal's arm64 wheel cannot load). Refinement runs the PDF platform's
staged ladder (concord.agents.pdf_specialist, copied from fccubic/pdf_backend): scale + lattice, + U_iso, + particle
diameter, + δ2, then all kept groups together; each stage is kept only if the platform's should_accept passes it
(converged, Rw at least 1 % lower, physical), else its values are reverted. Qdamp and Qbroad are instrument
calibration values and stay fixed.
"""
import warnings

import numpy as np
from diffpy.srfit.fitbase import FitContribution, FitRecipe, FitResults, Profile
from pymatgen.core import Lattice, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from scipy.optimize import least_squares

from concord.agents.pdf_specialist.refinement import STAGES, as_result, should_accept
from concord.tools import tool
from concord.tools.pdfcalc import PDFCalculator, first_shells, site_label, spherical_envelope

# which lattice parameters are free, and how the others follow them
TIES = {
    "cubic": {"a": "a", "b": "a", "c": "a"},
    "tetragonal": {"a": "a", "b": "a", "c": "c"},
    "hexagonal": {"a": "a", "b": "a", "c": "c"},
    "trigonal": {"a": "a", "b": "a", "c": "c"},
    "orthorhombic": {"a": "a", "b": "b", "c": "c"},
    "monoclinic": {"a": "a", "b": "b", "c": "c"},
    "triclinic": {"a": "a", "b": "b", "c": "c"},
}


def load_gr(path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    d = np.loadtxt(path)
    return d[:, 0], d[:, 1], d[:, 2] if d.shape[1] > 2 else np.full(len(d), max(np.std(d[:, 1]) * 0.02, 1e-4))


@tool
def fit_pdf(r: np.ndarray, g: np.ndarray, dg: np.ndarray, structure: Structure, *, qmax: float, qdamp: float,
            qbroad: float = 0.0, rmin: float = 1.5, rmax: float = 25.0, nanoparticle: bool = True,
            psize0_A: float | None = None, label: str = "") -> dict:
    """Refine a candidate structure against G(r). Returns refined values with 1σ uncertainties, Rw, the refined
    structure's first shells per element pair, and the observed/calculated/difference curves."""
    m = (r >= rmin) & (r <= rmax)
    r, g, dg = r[m], g[m], np.maximum(dg[m], 1e-6)
    system = SpacegroupAnalyzer(structure, symprec=0.1).get_crystal_system()
    ties = TIES[system]
    free_lat = sorted(set(ties.values()))
    base = dict(zip(("a", "b", "c", "alpha", "beta", "gamma"), structure.lattice.parameters))
    elements = sorted({site_label(s) for s in structure})
    calc = PDFCalculator(structure, rmax=rmax + 1.0, rstep=float(np.median(np.diff(r))), qmax=qmax)
    names = [f"lat_{x}" for x in free_lat] + [f"u_{el}" for el in elements] + ["delta2"]

    def gcalc(r, *vals):
        v = dict(zip(names, vals))
        lattice = {k: v[f"lat_{ties[k]}"] for k in ("a", "b", "c")}
        return calc(r, lattice=lattice, uiso={el: v[f"u_{el}"] for el in elements}, delta2=v["delta2"], qdamp=qdamp, qbroad=qbroad)

    profile = Profile()
    profile.setObservedProfile(r, g, dg)
    contrib = FitContribution("pdf")
    contrib.setProfile(profile, xname="r")
    contrib.registerFunction(gcalc, name="gcalc", argnames=["r"] + names)
    if nanoparticle:
        contrib.registerFunction(spherical_envelope, name="envelope", argnames=["r", "psize"])
        contrib.setEquation("scale * gcalc * envelope")
    else:
        contrib.setEquation("scale * gcalc")
    recipe = FitRecipe()
    recipe.addContribution(contrib)
    recipe.fithooks[0].verbose = 0
    recipe.addVar(contrib.scale, float(np.abs(g).max() / max(np.abs(calc(r, uiso={e: 0.005 for e in elements})).max(), 1e-9)), tag="scale")
    for x in free_lat:
        # ±3 %: dopants, strain and temperature move lattices < 2 %; wider bounds let another phase stretch onto the
        # sample's lattice (PtNi onto Pt) and win phase identification
        recipe.addVar(getattr(contrib, f"lat_{x}"), base[x], tag="lat").boundRange(0.97 * base[x], 1.03 * base[x])
    for el in elements:
        recipe.addVar(getattr(contrib, f"u_{el}"), 0.006, tag="adp").boundRange(0.0005, 0.05)
    recipe.addVar(contrib.delta2, 0.5, tag="d2").boundRange(0.0, 8.0)
    if nanoparticle:
        recipe.addVar(contrib.psize, psize0_A or 40.0, tag="size").boundRange(8.0, 400.0)
    tags = {"scale": "scale", "lattice": "lat", "adp": "adp", "spdiameter": "size", "delta2": "d2"}
    yw2 = float(np.sum((g / dg) ** 2))

    def judged():  # the current values in the reference's result schema, for its should_accept
        v = dict(zip(recipe.names, recipe.values)) | dict(zip(recipe.fixednames, recipe.fixedvalues))
        return dict(lattice={k: v[f"lat_{ties[k]}"] for k in ("a", "b", "c")}, uiso={el: v[f"u_{el}"] for el in elements},
                    delta2=v["delta2"], psize_A=v.get("psize"))

    ladder, best_rw, kept = [], None, set()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for stage in STAGES:  # the reference ladder; a stage is kept only if should_accept passes it
            if stage["key"] == "instrument" or (stage.get("requires_particle_size") and not nanoparticle):
                continue  # qdamp is the instrument's calibration, never fitted in Concord
            free = stage["free"] + (["spdiameter"] if stage.get("with_kept") and "spdiameter" in kept else [])
            recipe.fix("all")
            recipe.free(*[tags[x] for x in free])
            x0 = np.array(recipe.values)
            sol = least_squares(recipe.residual, x0, bounds=recipe.getBounds2(), x_scale="jac", max_nfev=400)
            rw = float(np.sqrt(np.sum(recipe.residual(sol.x) ** 2) / yw2))  # residual(p) also sets the free values to p
            status = "converged" if sol.status > 0 else "max_iterations" if sol.status == 0 else "stagnating"
            ok, why = should_accept(best_rw, as_result(rw, status=status, **judged()), base)
            if ok:
                best_rw, kept = rw, kept | set(free)
            else:
                recipe.residual(x0)  # revert: back to the values before this stage, the group stays where it was
            ladder.append({"key": stage["key"], "label": stage["label"], "free": free, "rw": rw, "kept": ok, "why": why})
        recipe.fix("all")
        recipe.free(*[tags[x] for x in kept] or ["scale"])  # uncertainties for what the kept stages refined
        lo, hi = recipe.getBounds2()
        pinned = [n for n, v, a, b in zip(recipe.get_names(), recipe.values, lo, hi) if min(v - a, b - v) <= 1e-6 * max(abs(v), 1.0)]
        if pinned:  # a parameter on its bound has no uncertainty and makes the covariance singular (seen: U_iso ± 0.7 Å²)
            recipe.fix(*pinned)
        res = FitResults(recipe)
    vals = {**dict(zip(res.fixednames, map(float, res.fixedvals))), **dict(zip(res.varnames, map(float, res.varvals)))}
    unc = {**dict.fromkeys(res.fixednames), **dict(zip(res.varnames, map(float, res.varunc)))}
    lattice = {k: vals[f"lat_{ties[k]}"] for k in ("a", "b", "c")}
    refined = structure.copy()
    refined.lattice = Lattice.from_parameters(lattice["a"], lattice["b"], lattice["c"], base["alpha"], base["beta"], base["gamma"])
    gfit = contrib.evaluate()
    shells = {el: first_shells(refined, el) for el in elements}
    return {
        "candidate": label, "crystal_system": system, "rw": float(res.rw), "chi2_reduced": float(res.rchi2),
        "lattice": {k: v for k, v in lattice.items()}, "lattice_err": {k: unc[f"lat_{ties[k]}"] for k in lattice},
        "uiso": {el: vals[f"u_{el}"] for el in elements}, "uiso_err": {el: unc[f"u_{el}"] for el in elements},
        "delta2": vals["delta2"], "delta2_err": unc["delta2"], "scale": vals["scale"],
        "psize_nm": vals["psize"] / 10 if nanoparticle else None, "psize_err_nm": unc["psize"] / 10 if nanoparticle and unc["psize"] is not None else None,
        "qmax": qmax, "qdamp": qdamp, "qbroad": qbroad, "r_range": [float(r[0]), float(r[-1])],
        "shells": shells, "structure": refined, "stages": ladder,
        "curves": {"r": r, "obs": g, "calc": np.asarray(gfit), "diff": g - np.asarray(gfit), "sigma": dg},
    }
