"""Staged EXAFS shell fitting: the ladder, the physical bounds and the keep-or-revert gate.

Structure adapted from the reference PDF refinement harness (fccubic pdf_backend
app/modules/agent/refinement.py at 3bf4be1: STAGES, BOUNDS, check_physical, should_accept). The
reference has no EXAFS agent; the stages and bounds below are new.

The stage ORDER is fixed in code, not chosen by the model: E0 and R are correlated through the
phase, N and σ² through the amplitude, so freeing them in the wrong order stalls the fit. Each
stage starts from the best fit so far, frees only its groups, and is kept only when the R-factor
drops by at least 1 % and every refined value is physical; otherwise its values are restored and
its groups stay fixed. The tools compute every number; the model judges.
"""
from __future__ import annotations

import math

# Physical bounds on refined values; the feffit bounds are wider (they keep the minimiser alive),
# these say whether the answer means anything.
BOUNDS = {
    "sigma2": (0.001, 0.03),   # Å²: below a stiff bond at 0 K, or so disordered the shell is not there
    "e0_shift": (-10.0, 10.0),  # eV: a larger ΔE0 is a mis-set edge or ΔE0 absorbing a distance error
    "dR_model": (-0.1, 0.1),   # Å, model shells: a larger move means the structure is wrong, not refined
    "N_ratio": (0.0, 1.5),     # × the model's N: more neighbours than 1.5× the crystal is not that structure
    "N_probe": (0.0, 6.0),     # a test shell (e.g. surface Pt-O) holds at most an octahedron's 6 neighbours
}

# Parameter groups shell_fit knows: e0 (de0), distances (dr*), disorder (ss*), coordination (n*),
# background (the outer-shell tail: d_out, alpha_out, ss_out). The background is a nuisance term
# and rides along with every stage, as the reference's scale does, so no stage is judged on the
# outer-shell leakage it cannot model.
STAGES = [
    {"key": "e0", "label": "Energy origin", "free": ["e0", "background"],
     "why": "ΔE0 shifts the phase of every path at once; with it wrong every distance gradient is corrupted, so it goes first."},
    {"key": "distances", "label": "Distances", "free": ["e0", "distances", "background"],
     "why": "ΔR sets the phase per shell; ΔE0 moves with it because the two trade along the phase."},
    {"key": "disorder", "label": "Disorder", "free": ["disorder", "background"],
     "why": "σ² damps each shell's amplitude with k; the largest amplitude term left once the phases are right."},
    {"key": "coordination", "label": "Coordination", "free": ["coordination", "disorder", "background"],
     "why": "N scales each shell's amplitude and trades with σ², so σ² moves with it (N alone against a held σ² stalls)."},
    {"key": "consolidate", "label": "Consolidate", "free": ["background"], "with_kept": True,
     "why": "Refine every kept group together, so correlated parameters (E0-R, N-σ²) settle jointly."},
]


def check_physical(result: dict) -> list[str]:
    """Physical-plausibility problems of a shell_fit result; empty means fine."""
    problems = []
    de0 = result.get("e0_shift")
    lo, hi = BOUNDS["e0_shift"]
    if de0 is not None and not lo <= de0 <= hi:
        problems.append(f"ΔE0={de0:.2f} eV is outside [{lo:g}, {hi:g}] eV")
    for s in result.get("shells", []):
        name = f"{s['neighbor']}{' (probe)' if s.get('extra') else ''}"
        lo, hi = BOUNDS["sigma2"]
        if not lo <= s["sigma2"] <= hi:
            problems.append(f"{name} σ²={s['sigma2']:.4f} Å² is outside [{lo:g}, {hi:g}]")
        if s.get("extra"):
            lo, hi = BOUNDS["N_probe"]
            if not lo <= s["N"] <= hi:
                problems.append(f"{name} N={s['N']:.2f} is outside [{lo:g}, {hi:g}]")
            continue
        dr = s["R_A"] - s["reff_A"]
        lo, hi = BOUNDS["dR_model"]
        if not lo <= dr <= hi:
            problems.append(f"{name} ΔR={dr:+.3f} Å is outside [{lo:g}, {hi:g}] Å of the model")
        lo, hi = BOUNDS["N_ratio"]
        if not lo * s["N_model"] <= s["N"] <= hi * s["N_model"]:
            problems.append(f"{name} N={s['N']:.2f} is outside {lo:g}-{hi:g}× the model's {s['N_model']:g}")
    return problems


def should_accept(previous_rfactor: float | None, result: dict, min_relative_gain: float = 0.01) -> tuple[bool, str]:
    """Whether a stage's result survives: the fit returned a finite R-factor, every refined value is
    physical, and the R-factor dropped by at least `min_relative_gain` (relative)."""
    rf = result.get("rfactor")
    if rf is None or not math.isfinite(rf):
        return False, "No finite R-factor was returned."
    problems = check_physical(result)
    if problems:
        return False, "Unphysical refined values: " + "; ".join(problems[:3])
    if previous_rfactor is None:
        return True, f"Baseline established at R={rf:.5f}."
    gain = (previous_rfactor - rf) / previous_rfactor if previous_rfactor else 0.0
    if rf > previous_rfactor:
        return False, f"R-factor got worse ({previous_rfactor:.5f} -> {rf:.5f}); reverting."
    if gain < min_relative_gain:
        return False, (f"R-factor barely moved ({previous_rfactor:.5f} -> {rf:.5f}, {gain * 100:.1f}%); "
                       "not worth the extra parameters.")
    return True, f"R-factor improved {previous_rfactor:.5f} -> {rf:.5f} ({gain * 100:.1f}%)."


SYSTEM = """\
You are the EXAFS refinement specialist of the Concord fitting agents. You judge an EXAFS shell \
fit; the tools compute every number. Never state a value a tool did not return.

How the fit is run (fixed in code, not yours to change):
- S0² is fixed from the beamline's reference foil; it is never refined.
- A staged fit (the result has `stages`) is a ladder, each stage starting from the best fit so far: energy origin (ΔE0), distances \
(ΔE0 + ΔR per shell), disorder (σ² per shell), coordination (N per shell, with σ²), then \
consolidate (every kept group together). The outer-shell background rides along with each stage.
- A stage is kept only when the R-factor drops by at least 1 % AND every refined value is \
physical (σ² 0.001-0.03 Å², |ΔE0| <= 10 eV, |ΔR| <= 0.1 Å for model shells, N within 0-1.5x the \
model's N, a probe shell's N at most 6); otherwise its values are restored and its groups stay \
fixed. The result's `stages` lists each stage with its R-factor, whether it was kept, and why.

Your work, without asking the user anything:
1. Read the result: the R-factor, each shell's N, R, σ² with their uncertainties against the \
model's N and distance, ΔE0, and the stages kept and reverted.
2. Judge: a reverted stage is a finding, not a failure; say which group stayed fixed and the \
reason the gate gave. N far below the model's with a normal σ² points at small particles or \
vacancies; a large σ² with a normal N points at disorder; a significant probe shell (e.g. Pt-O) \
is an environment the model lacks.
3. You may propose another k or R window, or a probe shell, as a next step; you may not change \
the k-weight, free S0², or loosen a bound. A proposal is re-fitted by the tools and passes the \
same gate (should_accept) before it replaces the current fit.
4. Report: the window, the R-factor, the shells as the tool reported them (uncertainties in \
parentheses), the stages kept and reverted with their reasons, and your judgement."""

