"""Candidate structures from the Crystallography Open Database (COD, CC0) for compositions the library lacks.

COD is searched for every entry with exactly the composition's elements; entries are grouped into phases by reduced
formula and space group (origin choices merged): the composition's most often determined phase first, then every
other phase by how often COD has it. One ordered structure per phase is kept, its CIF cached under data/cod_cache so a composition is fetched once.
"""
import json
import logging
import re
import time
from collections import defaultdict

from pymatgen.core import Composition, Structure

from concord.config import ROOT
from concord.data_builder.fetch import HTTP, _parse_cif

log = logging.getLogger("concord.cod")
CACHE = ROOT / "data" / "cod_cache"
MAX_PHASES = 5
MAX_SITES = 200  # larger cells make the PDF and FEFF steps slow


def _sg(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").split(":")[0])


def _formula(cod_formula: str) -> str | None:
    try:
        return Composition(cod_formula.strip("- ").replace(" ", "")).reduced_formula
    except Exception:
        return None


def pick(rows: list[dict], formula: str, limit: int = MAX_PHASES) -> list[list[dict]]:
    """COD result rows grouped into phases, best first; each group newest entry first."""
    groups = defaultdict(list)
    for r in rows:
        if (f := _formula(r.get("formula") or "")) and r.get("sg"):
            groups[(f, _sg(r["sg"]))].append(r)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    own = next((kv for kv in ranked if kv[0][0] == formula), None)  # the composition's best-known phase leads
    ranked = ([own] if own else []) + [kv for kv in ranked if kv is not own]
    return [sorted(g, key=lambda r: -int(r.get("year") or 0)) for _, g in ranked[:limit]]


def candidates(composition: str) -> dict[str, Structure]:
    """{name: Structure} of COD phases with exactly the composition's elements; {} when COD is unreachable."""
    comp = Composition(composition)
    els = sorted(e.symbol for e in comp.elements)
    index = CACHE / f"{'-'.join(els)}.json"
    if not index.exists():
        try:
            rows = HTTP.get("https://www.crystallography.net/cod/result", timeout=90,
                            params={**{f"el{i + 1}": e for i, e in enumerate(els)}, "strictmin": len(els), "strictmax": len(els), "format": "json"}).json()
        except Exception as exc:  # offline or COD down: the library alone decides
            log.warning("COD search for %s failed: %s", composition, exc)
            return {}
        chosen = []
        for group in pick(rows, comp.reduced_formula):
            for r in group[:3]:
                time.sleep(0.5)  # COD drops bursts of connections
                try:
                    text = HTTP.get(f"https://www.crystallography.net/cod/{r['file']}.cif", timeout=60).text
                    s = _parse_cif(text)
                except Exception:
                    continue
                if s.is_ordered and len(s) <= MAX_SITES:
                    CACHE.mkdir(parents=True, exist_ok=True)
                    (CACHE / f"{r['file']}.cif").write_text(text)
                    chosen.append({"cod_id": str(r["file"]), "formula": s.composition.reduced_formula, "sg": _sg(r["sg"]),
                                   "url": f"https://www.crystallography.net/cod/{r['file']}.html", "licence": "CC0-1.0"})
                    break
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(json.dumps(chosen, indent=1))
    chosen = json.loads(index.read_text())
    dup = {f for f in (c["formula"] for c in chosen) if [c["formula"] for c in chosen].count(f) > 1}
    return {(f"{c['formula']} ({c['sg']})" if c["formula"] in dup else c["formula"]): _parse_cif((CACHE / f"{c['cod_id']}.cif").read_text())
            for c in chosen}
