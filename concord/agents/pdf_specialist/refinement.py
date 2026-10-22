# Copied from fccubic/pdf_backend app/modules/agent/refinement.py at commit 3bf4be1, by the author's decision on
# 2026-10-23, adapted to Concord's srfit engine: the unused app.* logger and AgentContext imports dropped; the pdffit2 request builder, symmetry
# helpers and free-text instruction parser left out (Concord fits through concord.tools.pdf.fit_pdf); as_result added.
"""
Staged PDF refinement: the ladder, the guardrails, and the request builder.

The stage ORDER is fixed in code rather than chosen by the model. The sequence
below is settled crystallographic practice, and re-deriving it every run would
be both slower and less reliable -- one bad ordering choice produces a singular
matrix. What the model *does* decide is the judgment: which sites or elements to
tie, whether a stage's result is physically acceptable, which region of the
residual to attack next, and when there is nothing left worth trying.

Everything in this module that could produce a singular matrix or an unphysical
answer is enforced here, in code, not asked of the prompt:

* qmax / rcut / stepcut are never refined. qmax is registered but never
  constrained by the engine, so freeing it creates a zero-derivative column;
  pdffit2 documents the other two as non-refinable.
* Symmetry-equivalent lattice edges share one @N. Independent a/b/c under cubic
  symmetry is the textbook way to get linearly dependent Jacobian columns.
* delta1 and delta2 are mutually exclusive -- they are near-degenerate.
* Per-atom parameters can ONLY be freed by constraint string; there is no
  `refine` flag for atoms in the request schema.
* Refined values are bounds-checked afterwards, because the backend validates
  none of them.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Parameters the engine cannot refine. Freeing any of these is a silent path to
# a singular matrix or an inert parameter.
NEVER_REFINE = {"qmax", "rcut", "stepcut"}

# Physical bounds. The backend checks none of these, so the agent is the only
# thing standing between a "converged" fit and a meaningless one.
BOUNDS: Dict[str, Tuple[float, float]] = {
    "u": (1e-4, 0.1),          # thermal displacement, A^2
    "occ": (0.0, 1.0),
    "sratio": (0.0, 1.0),
    "delta1": (0.0, 5.0),
    "delta2": (0.0, 20.0),
    "qdamp": (0.0, 0.2),
    "qbroad": (0.0, 0.2),
    "scale": (1e-6, 100.0),
    "spdiameter": (0.0, 1000.0),
}

# Lattice may not drift far from the source structure; a large drift means the
# phase is wrong, or scale and lattice are trading against each other.
MAX_LATTICE_DRIFT = 0.03  # 3%


# ---------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------

# Each stage starts from the best fit so far as a whole, and frees the scale
# with what it adds: a stage that widens or damps the peaks with the scale held
# where the sharp-peaked first fit put it pushes them into odd corners. Measured
# on a user's Pt nanoparticle G(r) over 1.5-20 A: these stages with the scale
# held ended at Rw 0.37 (an ADP of 0.069 A^2); with it, at 0.166; with the
# particle-size stage as well, at 0.158 (a diameter of 27 A, qdamp held).
STAGES: List[Dict[str, Any]] = [
    {
        "key": "scale_lattice",
        "label": "Scale and lattice",
        "free": ["scale", "lattice"],
        "why": "Scale is a pure amplitude term and the lattice sets peak positions. "
               "If either is wrong every later gradient is corrupted, so these go first.",
    },
    {
        "key": "adp",
        "label": "Thermal factors",
        "free": ["scale", "adp"],
        "why": "ADPs set peak widths and are the largest remaining amplitude term. "
               "Tied per element so each site stays isotropic-equivalent; the scale "
               "moves with them, as wider peaks are lower ones.",
    },
    {
        "key": "particle_size",
        "label": "Particle size",
        "free": ["scale", "spdiameter"],
        "why": "A nanoparticle's G(r) fades to nothing at its diameter, as no two of "
               "its atoms are farther apart; spdiameter is that fading.",
        # Only where the data's signal ends well before the data does
        # (particle_size_estimate), starting from where it ends.
        "requires_particle_size": True,
    },
    {
        "key": "delta",
        "label": "Correlated motion",
        "free": ["scale", "delta2"],
        "why": "delta sharpens low-r peaks where ADPs broaden all of them. Only "
               "separable once the ADPs are near their basin. delta1 and delta2 "
               "are near-degenerate, so only one is ever freed.",
    },
    {
        "key": "instrument",
        "label": "Instrument resolution",
        "free": ["scale", "qdamp"],
        "why": "The damping envelope is only observable over a long r-range, and "
               "qdamp is degenerate with ADPs on a short one.",
        "requires_rmax": 18.0,
        # qdamp damps G(r) along r as a particle size does: with one fitted,
        # the data cannot tell the two apart, so qdamp stays at the
        # instrument's value. Freed with the size, on the Pt data above, it
        # took the size from 29 to 42 A for 4% in Rw.
        "unless_kept": "particle_size",
    },
    {
        "key": "consolidate",
        "label": "Consolidate",
        "free": ["scale", "lattice", "adp", "delta2"],
        "why": "Refine everything that survived together, so correlated parameters "
               "settle jointly rather than in sequence.",
        # With every other group a kept stage freed (the particle size, qdamp).
        "with_kept": True,
    },
]


def stage_by_key(key: str) -> Optional[Dict[str, Any]]:
    return next((s for s in STAGES if s["key"] == key), None)


# ---------------------------------------------------------------------------
# Judging a result
# ---------------------------------------------------------------------------

def check_physical(
    result: Any, source_lattice: Any = None
) -> List[str]:
    """Return a list of physical-plausibility violations; empty means fine.

    Nothing in the backend validates refined values, so a fit can converge to a
    negative thermal parameter and still report success.

    `source_lattice` is the structure file's cell for the first phase, or a list
    with one per phase: each phase's cell is compared with its own file's.
    """
    problems: List[str] = []
    data = result.model_dump() if hasattr(result, "model_dump") else (result or {})
    sources = source_lattice if isinstance(source_lattice, list) else [source_lattice]

    for number, (_, phase) in enumerate((data.get("refinedPhases") or {}).items()):
        source = sources[number] if number < len(sources) else None
        if number:
            pscale = ((phase.get("additionalParameters") or {}).get("scaleFactor") or {}).get("refined")
            if pscale is not None and pscale <= 0:
                problems.append(f"phase {number + 1} scale={pscale:.4f} is not positive - the phase is not there.")
        for atom in phase.get("atoms") or []:
            elem = atom.get("elem", "?")
            for key in ("u11", "u22", "u33"):
                val = (atom.get(key) or {}).get("refined")
                if val is None:
                    continue
                lo, hi = BOUNDS["u"]
                if val < lo:
                    problems.append(
                        f"{elem} {key}={val:.5f} is non-positive - unphysical "
                        "(usually means qdamp or delta absorbed the amplitude)."
                    )
                elif val > hi:
                    problems.append(f"{elem} {key}={val:.4f} exceeds {hi} A^2 - implausibly large.")
            occ = (atom.get("occ") or {}).get("refined")
            if occ is not None and not (0.0 <= occ <= 1.0):
                problems.append(f"{elem} occupancy={occ:.3f} is outside [0,1].")

        add = phase.get("additionalParameters") or {}
        for key in ("delta1", "delta2", "sratio", "spdiameter"):
            val = (add.get(key) or {}).get("refined")
            if val is None:
                continue
            lo, hi = BOUNDS.get(key, (float("-inf"), float("inf")))
            if not (lo <= val <= hi):
                problems.append(f"{key}={val:.4f} is outside the plausible range [{lo}, {hi}].")

        if source:
            lat = phase.get("latticeParameters") or {}
            for edge in ("a", "b", "c"):
                refined = (lat.get(edge) or {}).get("refined")
                original = source.get(edge)
                if refined and original:
                    drift = abs(refined - original) / original
                    if drift > MAX_LATTICE_DRIFT:
                        problems.append(
                            f"lattice {edge} moved {drift*100:.1f}% from the source "
                            f"structure ({original:.4f} -> {refined:.4f}) - beyond "
                            f"{MAX_LATTICE_DRIFT*100:.0f}%, which suggests the wrong phase."
                        )

    for _, ds in (data.get("refinedDatasets") or {}).items():
        for key in ("qdamp", "qbroad"):
            val = (ds.get(key) or {}).get("refined")
            if val is None:
                continue
            lo, hi = BOUNDS[key]
            if not (lo <= val <= hi):
                problems.append(f"{key}={val:.4f} is outside [{lo}, {hi}].")
    return problems


def should_accept(
    previous_rw: Optional[float],
    result: Any,
    source_lattice: Optional[Dict[str, float]] = None,
    min_relative_gain: float = 0.01,
) -> Tuple[bool, str]:
    """Decide whether a stage's result survives.

    Three conditions, all required: the engine converged, Rw improved
    meaningfully, and every refined value is physical.
    """
    data = result.model_dump() if hasattr(result, "model_dump") else (result or {})
    status = data.get("convergenceStatus")
    rw = data.get("finalRw")

    if status == "stagnating":
        return False, ("The engine threw partway through (status 'stagnating'), so this "
                       "result is not trustworthy despite the reported Rw.")
    if status == "cancelled":
        return False, "Cancelled."
    if rw is None:
        return False, "No Rw was returned."

    problems = check_physical(result, source_lattice)
    if problems:
        return False, "Unphysical refined values: " + "; ".join(problems[:3])

    if previous_rw is None:
        return True, f"Baseline established at Rw={rw:.4f}."

    gain = (previous_rw - rw) / previous_rw if previous_rw else 0.0
    if rw > previous_rw:
        return False, f"Rw got worse ({previous_rw:.4f} -> {rw:.4f}); reverting."
    if gain < min_relative_gain:
        return False, (f"Rw barely moved ({previous_rw:.4f} -> {rw:.4f}, "
                       f"{gain*100:.1f}%); not worth the extra parameters.")

    accepted = f"Rw improved {previous_rw:.4f} -> {rw:.4f} ({gain*100:.1f}%)"
    if status == "max_iterations":
        accepted += " but the fit hit the step ceiling rather than converging"
    return True, accepted + "."


def as_result(rw: float, lattice: Dict[str, float], uiso: Dict[str, float], delta2: float,
              psize_A: Optional[float] = None, status: str = "converged") -> Dict[str, Any]:
    """Concord's srfit values in the result schema check_physical and should_accept read (Concord addition)."""
    add = {"delta2": {"refined": delta2}} | ({"spdiameter": {"refined": psize_A}} if psize_A is not None else {})
    return {"convergenceStatus": status, "finalRw": rw,
            "refinedPhases": {"1": {"atoms": [{"elem": el, **{k: {"refined": u} for k in ("u11", "u22", "u33")}} for el, u in uiso.items()],
                                    "latticeParameters": {k: {"refined": v} for k, v in lattice.items()},
                                    "additionalParameters": add}},
            "refinedDatasets": {}}  # qdamp is the instrument's calibration in Concord, never refined
