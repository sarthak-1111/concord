"""Citable evidence for the agents, and the number guard.

The bundle is a flat {id: value} view of an analysis result (tool outputs and checks). Agents cite ids from it;
every number they write must match a number in it (rounding allowed), otherwise the number guard reports it.
"""
import math
import re
from typing import Any

SMALL_INTS = {0, 1, 2, 3}  # counts in plain prose ("two candidates", "3 rounds") need no citation
_NUM = re.compile(r"(?<![\w.])([-+−]?\d+(?:\.\d+)?)(?!\w|\.\d)(?:\s?(%))?")


def _r(x: Any) -> Any:
    """Round floats to 4 significant digits, recursively (keeps the prompt short)."""
    if isinstance(x, float):
        return float(f"{x:.4g}") if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _r(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_r(v) for v in x]
    return x


def bundle(res: dict) -> dict[str, Any]:
    """Evidence ids → values from a concord.analysis result (JSON form)."""
    inp = res["inputs"]
    ev: dict[str, Any] = {"sample": {"composition": inp["composition"], "techniques": inp["techniques"], "candidates": res["candidates"],
                                     "xafs_edge": inp["instrument"].get("xafs", {}).get("edge")}}
    if x := res.get("xrd"):
        ev["xrd.ranking"] = [{k: q[k] for k in ("phase", "score", "profile_corr", "obs_area_fraction_explained")} for q in x["ranking"][:3]]
        wh = x.get("williamson_hall") or {}
        ev["xrd.size"] = {"sphere_diameter_nm": x["sphere_diameter_nm"], "scherrer_median_nm": x["scherrer_median_nm"],
                          "williamson_hall_strain": wh.get("strain"), "n_indexed_peaks": x["n_indexed"]}
    if p := res.get("pdf"):
        for f in p["fits"][:3]:
            ev[f"pdf.fit.{f['candidate']}"] = {k: f[k] for k in ("rw", "lattice", "lattice_ref", "uiso", "delta2", "psize_nm", "r_range")}
        ev["pdf.best"] = p["fits"][0]["candidate"]
    if e := res.get("exafs"):
        ev["exafs.fit"] = {"absorber": e["absorber"], "edge": e["edge"], "model": e["model"], "rfactor": e["fit"]["rfactor"],
                           "e0_shift_eV": e["fit"]["e0_shift"], "window": e["fit"]["window"],
                           "shells": [{k: s.get(k) for k in ("neighbor", "N", "N_err", "R_A", "R_err", "sigma2", "extra")} for s in e["fit"]["shells"]]}
        if e.get("extra_shell"):
            ev["exafs.extra_shell"] = e["extra_shell"]
    if n := res.get("xanes"):
        ev["xanes"] = {k: n[k] for k in ("absorber", "edge_eV", "valence", "valence_edge", "lcf_weights")}
    if b := res.get("bvs"):
        ev["bvs"] = {k: b.get(k) for k in ("valence", "formal_valence")}
    if v := res.get("virtual_xafs"):
        ev["virtual_xafs"] = {"label": v["label"], "edge": f"{v['absorber']} {v['edge']}", "candidates": v["candidates"],
                              "theta_K_range": v["theta_K_range"], "vs_measured": v.get("vs_measured"),
                              "per_candidate_rfactor": v.get("per_candidate"), "recommendation": v["recommendation"]}
    for c in res["checks"]:
        ev[f"check.{c['id']}"] = {k: c[k] for k in ("name", "status", "values", "tolerance", "explanation")}
    for name, err in res.get("errors", {}).items():
        ev[f"error.{name}"] = err
    for name, val in res.get("extra_evidence", {}).items():
        ev[name] = val
    for i, p in enumerate(res.get("priors") or [], 1):  # literature values for other samples, with their source
        ev[f"prior.{i}"] = {k: p[k] for k in ("quantity", "pair", "element", "value", "uncertainty", "unit", "doi") if p.get(k) is not None} | {
            "snippet": p["snippet"][:300]}
    return _r(ev)


def numbers_in(value: Any) -> list[float]:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)] if math.isfinite(value) else []
    if isinstance(value, dict):
        return [x for v in value.values() for x in numbers_in(v)]
    if isinstance(value, (list, tuple)):
        return [x for v in value for x in numbers_in(v)]
    if isinstance(value, str):
        return [float(m.group(1).replace("−", "-")) for m in _NUM.finditer(value)]
    return []


def _matches(x: float, decimals: int, v: float) -> bool:
    return abs(x - v) <= 0.5 * 10 ** -decimals + 1e-12 or (v != 0 and abs(x - v) / abs(v) <= 0.005)


def number_guard(text: str, evidence: dict) -> list[str]:
    """Numbers in `text` that no evidence value supports (after rounding; x % may match the fraction x/100)."""
    known = numbers_in(evidence)
    bad = []
    for m in _NUM.finditer(text):
        raw, pct = m.group(1).replace("−", "-"), m.group(2)
        x = float(raw)
        decimals = len(raw.split(".")[1]) if "." in raw else 0
        if not pct and decimals == 0 and abs(x) in SMALL_INTS:
            continue
        cands = [x / 100, x] if pct else [x]
        if not any(_matches(c, decimals + (2 if pct and c != x else 0), v) or _matches(abs(c), decimals, abs(v))
                   for c in cands for v in known):
            bad.append(m.group(0))
    return bad
