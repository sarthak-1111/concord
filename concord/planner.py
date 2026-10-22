"""Measurement planner: which technique would tell the candidate phases of a composition apart. SIMULATED, NOT MEASURED.

For a user with no data yet: XRD, PDF and EXAFS are simulated for each candidate structure at the stated particle
size with Concord's own simulators, every candidate pair is compared per technique, and the technique whose closest
pair is still the most different is recommended. Optionally a `realism` callable adds instrument effects, and each
difference is set against the noise it adds. The curves are never analysed as data.
"""
import time
from collections.abc import Callable

import numpy as np
from pymatgen.core import Element, Structure

from concord import analysis
from concord.data_builder.build import instruments
from concord.data_builder.simulate import biso_of
from concord.tools import xrd
from concord.tools.feff import debye_uiso
from concord.tools.pdfcalc import PDFCalculator, spherical_envelope
from concord.tools.virtual_xafs import _ensemble_chi
from concord.tools.xafs import structure_paths

LABEL = "SIMULATED, NOT MEASURED"
MAX_CANDIDATES = 4
QMAX, QDAMP, S02, TEMPERATURE = 25.0, 0.04, 0.9, 300.0
GRIDS = {"xrd": np.linspace(20.0, 80.0, 600),  # the realism GAN's XRD range, so clean and realistic curves cover the same 2θ
          "pdf": np.linspace(1.0, 30.0, 600), "exafs": np.arange(2.0, 12.0 + 1e-9, 0.05)}
AXES = {"xrd": ("2θ (°), Cu Kα", "intensity (a.u.)"), "pdf": ("r (Å)", "G(r) (Å⁻²)"), "exafs": ("k (Å⁻¹)", "k²χ(k) (Å⁻²)")}


def _uiso(st: Structure, theta: float) -> dict:
    return {el.symbol: debye_uiso(el.atomic_mass, theta, TEMPERATURE) for el in st.composition.elements}


def simulate(tech: str, st: Structure, theta: float, size_nm: float, absorber: str, edge: str) -> np.ndarray:
    """One candidate's clean curve on GRIDS[tech]; a sphere of `size_nm` with Debye-model thermal motion."""
    x = GRIDS[tech]
    if tech == "xrd":
        biso = {el: biso_of(u) for el, u in _uiso(st, theta).items()}
        return xrd.simulate_pattern(st, x, xrd.CU_KA1, size_nm=size_nm, debye_waller=biso)
    if tech == "pdf":  # periodic model x spherical envelope, the same attenuated-crystal model fit_pdf refines
        g = PDFCalculator(st, rmax=float(x[-1]), qmax=QMAX)(x, uiso=_uiso(st, theta), qdamp=QDAMP)
        return g * spherical_envelope(x, 10 * size_nm)
    paths = structure_paths(st, absorber, edge)
    return _ensemble_chi(paths, x, 0.0, theta, 10 * size_nm, S02, TEMPERATURE, st.composition.num_atoms / st.volume) * x ** 2


# Separation = RMS of the difference of the two curves, each scaled to unit RMS: blind to the overall scale (counts,
# S0², PDF scale are unknown before measuring) and in the same units as the realism noise scaled the same way, so
# separation / noise is a signal-to-noise ratio (1 - Pearson r has no such noise counterpart). 0 = same shape, √2 = unrelated.
def _unit(y) -> np.ndarray:
    y = np.asarray(y, float)
    return y / (np.sqrt(np.mean(y ** 2)) or 1.0)


def distance(a, b) -> float:
    return float(np.sqrt(np.mean((_unit(a) - _unit(b)) ** 2)))


def plan(composition: str, candidates: list[str] | None = None, size_nm: float = 3.0,
         techniques: tuple = ("xrd", "pdf", "exafs"), realism: Callable | None = None) -> dict:
    t_start = time.perf_counter()
    if bad := [t for t in techniques if t not in GRIDS]:
        raise ValueError(f"unknown technique(s) {bad}; valid: {list(GRIDS)}")
    lib, want = analysis.candidates(composition), analysis._cations(composition)
    if candidates and (bad := [n for n in candidates if n not in lib]):
        raise ValueError(f"unknown candidate(s) {bad} for {composition}; valid: {list(lib)}")
    names = list(candidates) if candidates else sorted(lib, key=lambda n: -len(analysis._cations(lib[n].composition.reduced_formula) & want))
    notes = [f"Showing {MAX_CANDIDATES} of {len(names)} candidates: {', '.join(names[MAX_CANDIDATES:])} left out."] if len(names) > MAX_CANDIDATES else []
    names = names[:MAX_CANDIDATES]
    if len(names) < 2:
        raise ValueError(f"{composition} has {len(names) or 'no'} candidate phase{'' if len(names) == 1 else 's'} in the library"
                         f"{' (' + ', '.join(names) + ')' if names else ''}, so there is nothing to tell apart")
    absorber = max(want, key=lambda e: Element(e).Z)
    edge = analysis.default_edge(absorber)
    thetas = instruments()["debye_temperature_K"]
    conditions = {"xrd": {}, "pdf": {"qmax": QMAX, "qdamp": QDAMP}, "exafs": {"edge": f"{absorber} {edge}"}}
    out, timings = {}, {}
    for tech in techniques:
        t0 = time.perf_counter()
        x, curves, noisy, noise, use = GRIDS[tech], {}, {}, {}, realism
        for i, name in enumerate(names):
            if tech == "exafs" and absorber not in {e.symbol for e in lib[name].composition.elements}:
                notes.append(f"{name} contains no {absorber}, so it has no {absorber} {edge} EXAFS curve.")
                continue
            curves[name] = simulate(tech, lib[name], thetas[name], size_nm, absorber, edge)
            if use:
                try:
                    noisy[name] = np.asarray(use(tech, x, curves[name], composition=composition, seed=i, **conditions[tech]), float)
                    noise[name] = distance(noisy[name], curves[name])
                except (ValueError, TypeError) as exc:  # e.g. an edge the GAN was not trained on: no realism, never a fake one
                    notes.append(f"No instrument realism for {tech.upper()}: {exc}")
                    use, noisy, noise = None, {}, {}
        done, pairs = list(curves), []
        for j, a in enumerate(done):
            for b in done[j + 1:]:
                sep = distance(curves[a], curves[b])
                # against the noisier of the two: whichever phase the sample is, its measurement must resolve the pair
                on = round(sep / max(noise[a], noise[b], 1e-12), 2) if use else None
                pairs.append({"a": a, "b": b, "separation": round(sep, 3), "over_noise": on})
        if not pairs:
            notes.append(f"{tech.upper()} has fewer than two candidate curves, so it is not ranked.")
        out[tech] = {"x_label": AXES[tech][0], "y_label": AXES[tech][1], "x": x, "curves": curves,
                     "realistic": noisy if use else None, "pairs": pairs,
                     "score": min((p["separation"] for p in pairs), default=None)}
        timings[tech] = round(time.perf_counter() - t0, 2)
    ranking = sorted((t for t in out if out[t]["score"] is not None), key=lambda t: -out[t]["score"])
    timings["total"] = round(time.perf_counter() - t_start, 2)
    return analysis.to_json({"label": LABEL, "composition": composition, "size_nm": size_nm, "candidates": names,
                             "absorber": absorber, "edge": edge, "techniques": out, "ranking": ranking,
                             "recommendation": recommendation(out, ranking, f"{absorber} {edge}"), "notes": notes, "timings_s": timings})


def recommendation(techs: dict, ranking: list[str], edge: str) -> str:
    """Two or three sentences from the computed separations only."""
    if not ranking:
        return "No technique has two candidate curves to compare, so there is nothing to recommend."
    name = lambda t: f"{edge} EXAFS" if t == "exafs" else t.upper()
    closest = lambda t: min(techs[t]["pairs"], key=lambda p: p["separation"])
    best, p = ranking[0], closest(ranking[0])
    text = (f"{name(best)} tells the candidates apart best: even its closest pair, {p['a']} and {p['b']}, "
            f"differs by {p['separation']} (RMS difference of unit-RMS curves).")
    if p["over_noise"] is not None:
        verdict = "so it should survive a real measurement" if p["over_noise"] >= 1 else "so a real measurement may not resolve it"
        text += f" With realistic instrument effects that difference is {p['over_noise']} times the added noise, {verdict}."
    if len(ranking) > 1:
        w = closest(ranking[-1])
        text += f" {name(ranking[-1])} separates them least, struggling with {w['a']} and {w['b']} at {w['separation']}."
    return text
