"""Fitting agents: one LLM agent per technique drives its fit; a deterministic tool does every fitting step.

The idea follows the PDF platform's agent (fccubic/pdf_backend): what may be tried and the guardrails live in code, and
the model makes the judgment calls, namely which candidate or data window to try next, whether a refit is acceptable,
and when nothing is left worth trying. The PDF agent is that platform's Refinement specialist, copied by the author's
decision on 2026-10-23 (concord.agents.pdf_specialist): its prompt, and its should_accept gate for every refit. Every
number comes from concord.tweak.refit, never from the model.
"""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from concord import tweak
from concord.agents.pdf_specialist import prompts as pdf_prompts
from concord.agents.pdf_specialist.refinement import as_result, should_accept
from concord.llm.adk_model import shared_client

TECHS = ("xrd", "pdf", "exafs")
LABEL = {"xrd": "XRD", "pdf": "PDF", "exafs": "EXAFS"}
METRIC = {"xrd": ("score", 1), "pdf": ("rw", -1), "exafs": ("rfactor", -1)}  # (metric, +1 when higher is better)
FREE = {"xrd": {"two_theta_min", "two_theta_max", "baseline_log10_lambda", "peak_height", "peak_prominence"},
        "pdf": {"candidate", "rmin", "rmax", "envelope"},  # qdamp is the instrument's calibration: never fitted here
        "exafs": {"kmin", "kmax", "rmax", "probe", "probe_neighbor"}}  # not kweight: the R-factor is not comparable across k-weights
MAX_STEPS, MAX_CHANGES = 3, 2
MIN_GAIN = 0.02  # relative improvement an XRD or EXAFS refit needs to be kept; PDF uses the specialist's should_accept
MIN_SPAN = 0.7  # a data window may not shrink below this share of its default span

SYSTEM = """You are Concord's {T} fitting agent. A tested, deterministic tool fits the data; you decide what to try next and judge the result.
Each turn, either try new settings (action "try", at most two changes, values as strings) or stop (action "accept") when the fit is good or nothing is left worth trying.
Rules enforced in code: values outside the ranges are clipped; a data window may not shrink below 70 % of its default span, since a smaller window lowers the metric without fitting better; a refit is kept only if {metric} improves by at least 2 % and is physical.
{good}
Reason only from the numbers given; never invent one. Reply with JSON only."""
GOOD = {"exafs": "An R-factor below 0.05 is a good EXAFS fit. A misfit at low R can need a light-neighbour probe shell; noise at high k can need a shorter k range.",
        "xrd": "A score near 1 is good. Unindexed weak peaks can need a lower peak threshold; a broad hump under the peaks a stiffer baseline (higher baseline_log10_lambda)."}


class Change(BaseModel):
    name: str
    value: str


class Decision(BaseModel):
    action: Literal["try", "accept"]
    changes: list[Change] = Field(default_factory=list)
    reason: str


def _value(p: dict, raw: str):
    if p["kind"] == "bool":
        return str(raw).strip().lower() in ("true", "on", "1", "yes")
    if p["kind"] == "choice":
        if raw not in (p["choices"] or []):
            raise ValueError(f"{p['name']} must be one of {', '.join(map(str, p['choices']))}")
        return raw
    v = float(raw)
    v = min(max(v, p["min"]), p["max"]) if p["min"] is not None else v
    return int(round(v)) if p["kind"] == "int" else v


def _window(tech: str, spec: list[dict], values: dict) -> None:
    d = {p["name"]: p["default"] for p in spec}
    for lo, hi, _ in tweak.SPANS.get(tech, []):
        if None not in (d.get(lo), d.get(hi), values.get(lo), values.get(hi)) and values[hi] - values[lo] < MIN_SPAN * (d[hi] - d[lo]):
            raise ValueError(f"the {lo} to {hi} window would shrink below {MIN_SPAN:.0%} of its default span")


def _keep(tech: str, best: dict, r: dict, name: str, sign: int) -> tuple[bool, str | None]:
    """Whether a refit is kept, and the error to report when it is unphysical."""
    if tech == "pdf":
        m = r["metrics"]
        ok, why = should_accept(best["metrics"]["rw"], as_result(m["rw"], m["lattice"], m["uiso"], m["delta2"],
                                                                 m["psize_nm"] and 10 * m["psize_nm"]), m["lattice_ref"])
        return ok, why if why.startswith("Unphysical") else None
    gain = sign * (r["metrics"][name] - best["metrics"][name]) / max(abs(best["metrics"][name]), 1e-9)
    return gain >= MIN_GAIN, None


def fit(folder: str | Path, analysis: dict, tech: str) -> dict | None:
    """Let the technique's agent drive its fit for up to MAX_STEPS refits. Returns what it tried, kept and why."""
    spec = tweak.params(analysis, tech)
    if not spec:
        return None
    by = {p["name"]: p for p in spec}
    free = [p for p in spec if p["name"] in FREE[tech]]
    name, sign = METRIC[tech]
    values = {p["name"]: p["value"] for p in spec}
    best = tweak.refit(folder, analysis, tech, values)
    start, steps, verdict = best["metrics"][name], [], "step budget used"
    for i in range(1, MAX_STEPS + 1):
        state = {"settings": [{k: p[k] for k in ("name", "label", "kind", "min", "max", "choices", "help")} | {"value": values[p["name"]]} for p in free],
                 "current_fit": best["metrics"], "checks": [{k: c[k] for k in ("id", "status", "explanation")} for c in best["checks"]],
                 "steps_so_far": steps, "steps_left": MAX_STEPS - i + 1}
        system = pdf_prompts.SYSTEM if tech == "pdf" else SYSTEM.format(T=LABEL[tech], metric=name, good=GOOD[tech])
        d = shared_client().chat("fitter", [{"role": "system", "content": system},
                                            {"role": "user", "content": json.dumps(state, default=str)}], schema=Decision).data
        if d.action == "accept" or not d.changes:
            verdict = d.reason
            break
        rec = {"step": i, "changes": {}, "metric": None, "kept": False, "reason": d.reason, "error": None}
        try:
            rec["changes"] = {c.name: _value(by[c.name], c.value) for c in d.changes[:MAX_CHANGES] if c.name in FREE[tech] and c.name in by}
            if not rec["changes"]:
                raise ValueError("none of the requested settings may be changed")
            trial = {**values, **rec["changes"]}
            _window(tech, spec, trial)
            r = tweak.refit(folder, analysis, tech, trial)
            rec["metric"] = r["metrics"][name]
            ok, rec["error"] = _keep(tech, best, r, name, sign)
            if ok:
                best, values, rec["kept"] = r, trial, True
        except (ValueError, KeyError, TypeError) as exc:  # a bad request is reported back to the agent, never applied
            rec["error"] = str(exc)
        steps.append(rec)
    return {"agent": f"{tech}_fitter", "metric": name, "start": start, "end": best["metrics"][name],
            "values": {k: v for k, v in values.items() if v != by[k]["value"]}, "steps": steps, "verdict": verdict}


def _g(x) -> str:
    return f"{x:.4g}" if isinstance(x, float) else str(x)


def summary(tech: str, f: dict) -> str:
    tried = "; ".join(f"step {s['step']}: {', '.join(f'{k} {_g(v)}' for k, v in s['changes'].items()) or 'no change'}"
                      f" → {_g(s['metric']) if s['metric'] is not None else s['error']} ({'kept' if s['kept'] else 'reverted'})" for s in f["steps"])
    return (f"{LABEL[tech]} fitting agent: {f['metric']} {_g(f['start'])} → {_g(f['end'])}"
            + (f"; {tried}" if tried else "; kept the default fit") + f". {f['verdict']}")
