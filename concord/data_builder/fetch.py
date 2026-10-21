"""Fetch open crystal structures: COD first, then Materials Project (if MP_API_KEY), then JARVIS and OQMD via OPTIMADE.

Writes data/structures/*.cif and data/manifest.csv (source, ID and licence of every structure considered).
Run: uv run python -m concord.data_builder.fetch
"""
import csv
import hashlib
import logging
import warnings
from pathlib import Path

import time

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from concord.config import ROOT, env

log = logging.getLogger("concord.fetch")
DATA = ROOT / "data"
LICENCES = {
    "COD": "CC0-1.0 (COD public-domain dedication)",
    "MP": "CC-BY-4.0 (Materials Project)",
    "JARVIS": "NIST public data (jarvis.nist.gov terms)",
    "OQMD": "CC-BY-4.0 (OQMD)",
}
OPTIMADE = {"JARVIS": "https://jarvis.nist.gov/optimade/jarvisdft/v1/structures",
            "OQMD": "https://oqmd.org/optimade/v1/structures"}
MAX_PER_SYSTEM = 3
HTTP = requests.Session()
HTTP.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])))
FIELDS = ["system", "source", "source_id", "licence", "url", "formula", "space_group", "a", "b", "c",
          "alpha", "beta", "gamma", "cif_file", "sha256", "status", "library", "note"]


def systems() -> list[dict]:
    return yaml.safe_load((Path(__file__).parent / "systems.yaml").read_text())["systems"]


def _sg_ok(sg: str, accepted: list[str]) -> bool:
    norm = lambda s: s.split(":")[0].replace(" ", "").lower()
    return norm(sg) in {norm(a) for a in accepted}


def _parse_cif(text: str) -> Structure:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return Structure.from_str(text, fmt="cif")


def cod(system: dict) -> list[dict]:
    rows = HTTP.get("https://www.crystallography.net/cod/result",
                        params={"formula": system["cod_formula"], "format": "json"}, timeout=60).json()
    rows = [r for r in rows if _sg_ok(r.get("sg") or "", system["space_groups"])]
    rows.sort(key=lambda r: -int(r.get("year") or 0))  # newest determinations first
    out = []
    for r in rows[: MAX_PER_SYSTEM * 3]:
        url = f"https://www.crystallography.net/cod/{r['file']}.cif"
        time.sleep(0.5)  # COD drops bursts of connections
        text = HTTP.get(url, timeout=60).text
        try:
            out.append({"source": "COD", "source_id": str(r["file"]), "url": url, "cif": text, "structure": _parse_cif(text)})
        except Exception as exc:  # unparsable CIFs are recorded, not fatal
            out.append({"source": "COD", "source_id": str(r["file"]), "url": url, "error": f"{type(exc).__name__}: {exc}"})
    return out


def materials_project(system: dict) -> list[dict]:
    key = env().get("MP_API_KEY")
    if not key:
        return []
    from mp_api.client import MPRester
    with MPRester(key) as mpr:
        docs = mpr.materials.summary.search(formula=system["formula"], fields=["material_id", "structure", "symmetry"])
    out = []
    for d in docs:
        if _sg_ok(d.symmetry.symbol, system["space_groups"]):
            out.append({"source": "MP", "source_id": str(d.material_id), "url": f"https://next-gen.materialsproject.org/materials/{d.material_id}",
                        "structure": d.structure})
    return out


def optimade(system: dict, provider: str) -> list[dict]:
    filt = f'chemical_formula_reduced="{_optimade_formula(system["formula"])}"'
    resp = HTTP.get(OPTIMADE[provider], params={"filter": filt, "page_limit": 20}, timeout=60).json()
    out = []
    for d in resp.get("data", []):
        a = d["attributes"]
        s = Structure(a["lattice_vectors"], [sp for sp in a["species_at_sites"]], a["cartesian_site_positions"], coords_are_cartesian=True)
        if _sg_ok(SpacegroupAnalyzer(s, symprec=0.1).get_space_group_symbol(), [g.replace(" ", "") for g in system["space_groups"]]):
            out.append({"source": provider, "source_id": str(d["id"]), "url": f"{OPTIMADE[provider]}/{d['id']}", "structure": s})
    return out


def _optimade_formula(formula: str) -> str:
    """OPTIMADE wants the reduced formula with elements in alphabetical order: TiO2 -> O2Ti."""
    comp = Composition(Composition(formula).reduced_formula)
    return "".join(f"{el}{'' if comp[el] == 1 else int(comp[el])}" for el in sorted(str(e) for e in comp.elements))


def fetch_all() -> list[dict]:
    (DATA / "structures").mkdir(parents=True, exist_ok=True)
    matcher = StructureMatcher()
    rows = []
    for system in systems():
        found = []
        for source in (cod, materials_project, lambda s: optimade(s, "JARVIS"), lambda s: optimade(s, "OQMD")):
            try:
                found = source(system)
            except Exception as exc:
                log.warning("%s: %s failed: %s", system["name"], getattr(source, "__name__", "optimade"), exc)
                found = []
            if any("structure" in f for f in found):
                break
        if not found:
            log.warning("%s: no openly available structure, skipped", system["name"])
            rows.append({"system": system["name"], "status": "missing", "note": "no open structure found"})
            continue
        kept: list[Structure] = []
        for f in found:
            row = {"system": system["name"], "source": f["source"], "source_id": f["source_id"], "licence": LICENCES[f["source"]],
                   "url": f["url"], "library": system.get("library", True)}
            if "error" in f:
                rows.append({**row, "status": "rejected", "note": f["error"][:120]})
                continue
            s: Structure = f["structure"]
            lat = s.lattice
            row.update({"formula": s.composition.reduced_formula, "space_group": SpacegroupAnalyzer(s, symprec=0.1).get_space_group_symbol(),
                        **{k: round(v, 5) for k, v in zip(("a", "b", "c", "alpha", "beta", "gamma"), lat.parameters)}})
            if any(matcher.fit(s, k) for k in kept) and kept:
                rows.append({**row, "status": "duplicate", "note": "matches an already selected structure (pymatgen StructureMatcher)"})
                continue
            if len(kept) >= MAX_PER_SYSTEM:
                rows.append({**row, "status": "skipped", "note": "enough structures for this system"})
                continue
            name = f"{system['name']}__{f['source'].lower()}-{f['source_id']}.cif"
            text = f.get("cif") or s.to(fmt="cif")
            (DATA / "structures" / name).write_text(text)
            kept.append(s)
            rows.append({**row, "cif_file": f"structures/{name}", "sha256": hashlib.sha256(text.encode()).hexdigest(), "status": "selected"})
        log.info("%s: %d selected", system["name"], len(kept))
    with (DATA / "manifest.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def load_structures(library_only: bool = False) -> dict[str, list[tuple[str, Structure]]]:
    """{system: [(cif_file, Structure), ...]} for every selected structure in data/manifest.csv.
    library_only: skip fault-only polymorphs (the analysis candidate library)."""
    out: dict = {}
    with (DATA / "manifest.csv").open() as fh:
        for row in csv.DictReader(fh):
            if row["status"] == "selected" and not (library_only and row.get("library") == "False"):
                out.setdefault(row["system"], []).append((row["cif_file"], _parse_cif((DATA / row["cif_file"]).read_text())))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rows = fetch_all()
    print(f"{sum(r['status'] == 'selected' for r in rows)} structures selected, {len(rows)} considered -> data/manifest.csv")
