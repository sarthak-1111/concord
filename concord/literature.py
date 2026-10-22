"""Paper miner: quantitative priors for a composition from open literature APIs (OpenAlex, arXiv, Crossref).

Abstracts are split into sentences and embedded on CPU (BAAI/bge-small-en-v1.5) into a FAISS index; the sentences
closest to each quantity (bond length, coordination number, oxidation state, particle size) are parsed with fixed
patterns. Every prior carries the DOI and the sentence it was read from, and its value is literally in that
sentence: no value without a source, and no LLM in the loop. HTTP responses are cached in .cache/literature,
mined priors in results/priors/<composition>.json.

Priors describe other samples, so they never constrain a fit directly: they are evidence the critic can cite
(and use as arguments to a re-run, e.g. the distance of a probe shell) and context in the report.
"""
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import requests
from pymatgen.core import Composition, Element

from concord.config import ROOT, env

CACHE = ROOT / ".cache" / "literature"
OUT = ROOT / "results" / "priors"
MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PROMPT = "Represent this sentence for searching relevant passages: "  # BGE's retrieval instruction
QUANTITIES = {
    "bond_length": "interatomic distance (bond length, in Å) of a neighbour shell determined by EXAFS",
    "coordination_number": "coordination number of a neighbour shell determined by EXAFS fitting",
    "oxidation_state": "oxidation state or valence of the metal determined by XANES",
    "particle_size": "average particle size or crystallite diameter in nm",
}
ELEMENTS = {e.symbol for e in Element}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}
_NUM = r"(\d+(?:\.\d+)?)"
_PM = r"(?:\s?(?:±|\+/-)\s?(\d+(?:\.\d+)?))?"
_PAIR = re.compile(r"(?<![A-Za-z])([A-Z][a-z]?)\s?[-–—]\s?([A-Z][a-z]?)(?![a-z])")
_LENGTH = re.compile(r"(?<![\w.])" + _NUM + r"(?:\((\d+)\))?" + _PM + r"\s?Å")  # 2.876(28) Å or 2.88 ± 0.03 Å
_CN = re.compile(r"(?:coordination numbers?|\bCNs?\b)[^.;]{0,60}?(?<![\w.])" + _NUM + _PM + r"(?![\w.]*\s?(?:nm|Å|%|K\b|eV|°))")
_SIZE = re.compile(r"(?<![\w.])" + _NUM + r"(?:\s?[-–]\s?" + _NUM + r")?" + _PM + r"[\s-]?nm\b")
_SIZE_WORDS = re.compile(r"\b(?:size|diameter|particles?|nanoparticles?|NPs?|crystallites?|clusters?|grains?)\b", re.I)
_ION = re.compile(r"(?<![A-Za-z])([A-Z][a-z]?)\s?(\d)\+")
_ION_ROMAN = re.compile(r"(?<![A-Za-z])([A-Z][a-z]?)\s?\((I{1,3}|IV|VI{0,2})\)")
_VALENCE = re.compile(r"(?:oxidation state|valence)[^.;]{0,30}?(?<![\w.])\+?" + _NUM + r"(?![\w.]*\s?(?:nm|Å|%|eV))")


# -- open literature APIs (cached) -------------------------------------------------------------------------------
def _get(url: str, params: dict, secret: tuple[str, ...] = ()) -> object:
    """Cached GET. Secret parameters (API keys) are left out of the cache key and the cache file."""
    public = {k: v for k, v in params.items() if k not in secret}
    path = CACHE / "http" / (hashlib.sha256((url + json.dumps(public, sort_keys=True)).encode()).hexdigest()[:24] + ".json")
    if path.exists():
        return json.loads(path.read_text())["body"]
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=30, headers={"User-Agent": "concord-paper-miner (open-source research tool)"})
            if r.status_code not in (429, 500, 502, 503, 504):
                break
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
        time.sleep(3 * 2 ** attempt)  # arXiv asks for at least 3 s between requests
    r.raise_for_status()
    body = r.json() if "json" in r.headers.get("content-type", "") else r.text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"url": url, "params": public, "body": body}))
    return body


def _uninvert(inv: dict | None) -> str:
    """OpenAlex abstracts come as {word: [positions]}."""
    return " ".join(w for _, w in sorted((p, w) for w, ps in (inv or {}).items() for p in ps))


def openalex(query: str, n: int = 25) -> list[dict]:
    params = {"search": query, "filter": "has_abstract:true", "per_page": n,
              "select": "doi,title,publication_year,abstract_inverted_index"}
    if key := env().get("OPENALEX_API_KEY"):
        params["api_key"] = key
    body = _get("https://api.openalex.org/works", params, secret=("api_key",))
    return [{"doi": w["doi"].removeprefix("https://doi.org/"), "title": w.get("title") or "", "year": w.get("publication_year"),
             "abstract": _uninvert(w.get("abstract_inverted_index")), "source": "OpenAlex"}
            for w in body.get("results", []) if w.get("doi")]


def crossref(query: str, n: int = 20) -> list[dict]:
    body = _get("https://api.crossref.org/works", {"query.bibliographic": query, "filter": "has-abstract:true", "rows": n,
                                                   "select": "DOI,title,abstract,issued"})
    out = []
    for it in body.get("message", {}).get("items", []):
        text = html.unescape(re.sub(r"<[^>]+>", " ", it.get("abstract", "")))
        year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        out.append({"doi": it["DOI"], "title": " ".join(it.get("title") or []), "year": year,
                    "abstract": re.sub(r"\s+", " ", text).strip().removeprefix("Abstract "), "source": "Crossref"})
    return out


def arxiv(query: str, n: int = 25) -> list[dict]:
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(_get("https://export.arxiv.org/api/query", {"search_query": query, "max_results": n}))
    out = []
    for e in root.findall("a:entry", ns):
        arxiv_id = re.sub(r"v\d+$", "", e.findtext("a:id", "", ns).rsplit("/abs/", 1)[-1])
        doi = e.findtext("x:doi", None, ns) or f"10.48550/arXiv.{arxiv_id}"  # every arXiv paper has a DataCite DOI
        out.append({"doi": doi, "title": " ".join(e.findtext("a:title", "", ns).split()), "year": int(e.findtext("a:published", "0000", ns)[:4]),
                    "abstract": " ".join(e.findtext("a:summary", "", ns).split()), "source": "arXiv"})
    return out


# -- what to search for ------------------------------------------------------------------------------------------
def material_name(composition: str, phase: str | None = None) -> str:
    """'TiO2-anatase' → 'anatase TiO2'; otherwise the reduced formula."""
    if phase and "-" in phase:
        formula, polymorph = phase.split("-", 1)
        return f"{polymorph} {formula}"
    return composition  # as written ('Pt3Co'); pymatgen would reorder it to 'CoPt3'


def queries(composition: str, phase: str | None = None) -> dict[str, list[str]]:
    name, formula = material_name(composition, phase), composition
    return {"openalex": [f"{name} EXAFS coordination number bond length", f"{name} XANES oxidation state", f"{name} nanoparticles size"],
            "crossref": [f"{name} EXAFS", f"{name} nanoparticles XANES"],
            "arxiv": [f'all:"{formula}" AND (all:EXAFS OR all:XAFS OR all:XANES OR all:nanoparticles)']}


def mentions(text: str, composition: str, phase: str | None = None) -> bool:
    """Does the text name this material? Formulas may be split by subscripts ('Pt 3 Co')."""
    comp = Composition(composition)
    for formula in {composition, comp.reduced_formula}:
        tokens = re.findall(r"[A-Z][a-z]?|\d+(?:\.\d+)?", formula)
        if re.search(r"(?<![A-Za-z])" + r"\s?".join(map(re.escape, tokens)) + r"(?![A-Za-z0-9])", text):  # 'Pt' is not 'PtNi'
            return True
    names = [e.long_name for e in comp.elements] if len(comp.elements) == 1 else []
    if phase and "-" in phase:
        names.append(phase.split("-", 1)[1])
    return any(re.search(rf"\b{re.escape(n)}\b", text, re.I) for n in names)


# -- sentences, embeddings, FAISS ----------------------------------------------------------------------------------
def sentences(abstract: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", abstract)
    return [p.strip() for p in parts if 20 <= len(p.strip()) <= 600]


_MODEL = None


def embedder():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # slow import, only when mining
        _MODEL = SentenceTransformer(MODEL, device="cpu")
    return _MODEL


def build_index(texts: list[str]):
    x = np.asarray(embedder().encode_document(texts, normalize_embeddings=True, batch_size=64), dtype="float32")
    import faiss  # only after torch: on macOS arm64, faiss loaded first gives two OpenMP runtimes and a segfault
    index = faiss.IndexFlatIP(x.shape[1])  # inner product of unit vectors = cosine similarity
    index.add(x)
    return index


def search(index, query: str, k: int) -> list[tuple[int, float]]:
    q = np.asarray(embedder().encode_query([query], prompt=QUERY_PROMPT, normalize_embeddings=True), dtype="float32")
    scores, ids = index.search(q, min(k, index.ntotal))
    return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]


# -- extraction: fixed patterns, values copied from the sentence -------------------------------------------------
def _pairs(text: str) -> list[tuple[int, str]]:
    return [(m.start(), f"{m.group(1)}–{m.group(2)}") for m in _PAIR.finditer(text) if {m.group(1), m.group(2)} <= ELEMENTS]


def _nearest(pairs: list[tuple[int, str]], pos: int, reach: int = 80) -> str | None:
    """The pair named closest before the value ('Pt–O bond length of 2.02 Å'), else the first one after it."""
    before = [p for p in pairs if pos - reach <= p[0] < pos]
    after = [p for p in pairs if pos < p[0] <= pos + reach]
    return before[-1][1] if before else after[0][1] if after else None


def _uncertainty(m: re.Match) -> float | None:
    if m.re is _LENGTH and m.group(2):  # digits in parentheses apply to the last decimals: 2.876(28) → 0.028
        return int(m.group(2)) * 10.0 ** -len(m.group(1).split(".")[1] if "." in m.group(1) else "")
    pm = m.group(3) if m.re is _LENGTH else m.group(2)
    return float(pm) if pm else None


def extract(text: str, quantity: str, elements: set[str]) -> list[dict]:
    """Priors of one quantity stated in one sentence. elements: the sample's elements; pairs start at one of its
    cations and end at one of its elements or O (an oxide shell)."""
    out, cations = [], (elements - {"O"}) or elements
    if quantity in ("bond_length", "coordination_number"):
        pairs, partners = _pairs(text), elements | {"O"}
        for m in (_LENGTH if quantity == "bond_length" else _CN).finditer(text):
            v, (lo, hi, unit) = float(m.group(1)), ((1.5, 3.6, "Å") if quantity == "bond_length" else (0.5, 14.0, ""))
            pair = _nearest(pairs, m.start(1))  # among all pairs named, so a Pt–P value is never given to Pt–Pt
            if lo <= v <= hi and pair and pair.split("–")[0] in cations and pair.split("–")[1] in partners:
                out.append({"pair": pair, "value": v, "uncertainty": _uncertainty(m), "unit": unit})
    elif quantity == "oxidation_state":
        for m in _ION.finditer(text):
            if m.group(1) in cations:
                out.append({"element": m.group(1), "value": int(m.group(2)), "unit": "", "form": m.group(0)})
        for m in _ION_ROMAN.finditer(text):
            if m.group(1) in cations:
                out.append({"element": m.group(1), "value": ROMAN[m.group(2)], "unit": "", "form": m.group(0)})
        for m in _VALENCE.finditer(text):
            near = [e for e in cations if re.search(rf"(?<![A-Za-z]){e}(?![a-z])", text)]
            if 0 <= float(m.group(1)) <= 8 and len(near) == 1:
                out.append({"element": near[0], "value": float(m.group(1)), "unit": "", "form": m.group(0)})
    elif quantity == "particle_size" and _SIZE_WORDS.search(text):
        for m in _SIZE.finditer(text):
            lo_, hi_ = float(m.group(1)), float(m.group(2)) if m.group(2) else None
            if 0.5 <= lo_ <= 200 and (hi_ is None or lo_ < hi_ <= 200):
                out.append({"value": lo_ if hi_ is None else [lo_, hi_], "uncertainty": float(m.group(3)) if m.group(3) else None, "unit": "nm"})
    return out


# -- the miner ---------------------------------------------------------------------------------------------------
def _slug(composition: str, phase: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", material_name(composition, phase)).strip("_")


def mine(composition: str, phase: str | None = None, per_quantity: int = 6, k: int = 60, refresh: bool = False) -> dict:
    """Search, index and extract; the result is cached in results/priors/<material>.json."""
    out_file = OUT / f"{_slug(composition, phase)}.json"
    if out_file.exists() and not refresh:
        return json.loads(out_file.read_text())
    papers, errors = {}, []
    for source, fn in (("openalex", openalex), ("crossref", crossref), ("arxiv", arxiv)):
        for q in queries(composition, phase)[source]:
            try:
                for p in fn(q):
                    if p["abstract"] and mentions(p["title"] + " " + p["abstract"], composition, phase):
                        papers.setdefault(p["doi"].lower(), p)
            except (requests.RequestException, ET.ParseError, ValueError) as exc:
                errors.append(f"{source}: {type(exc).__name__}")
    sents = [{"text": s, "doi": p["doi"]} for p in papers.values() for s in sentences(p["abstract"])]
    elements = {e.symbol for e in Composition(composition).elements}
    priors = []
    if sents:
        index = build_index([s["text"] for s in sents])
        for quantity, query in QUANTITIES.items():
            seen, found = set(), []
            for i, score in search(index, query, k):
                s = sents[i]
                for x in extract(s["text"], quantity, elements):
                    key = (s["doi"].lower(), json.dumps(x["value"]), x.get("pair") or x.get("element"))
                    if key in seen:
                        continue
                    seen.add(key)
                    p = papers[s["doi"].lower()]
                    found.append({"quantity": quantity, **x, "doi": p["doi"], "title": p["title"], "year": p["year"],
                                  "source": p["source"], "snippet": s["text"], "relevance": round(score, 3)})
            priors += found[:per_quantity]
    result = {"composition": composition, "phase": phase, "material": material_name(composition, phase), "model": MODEL,
              "queries": queries(composition, phase), "papers": len(papers), "sentences": len(sents), "errors": errors,
              "priors": priors, "mined": time.strftime("%Y-%m-%d")}
    OUT.mkdir(parents=True, exist_ok=True)  # cached even when a source failed: `errors` says so; refresh=True completes it
    out_file.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def cached(composition: str, phase: str | None = None) -> dict | None:
    """Priors mined earlier, without any network access (for the analysis, the UI and the eval)."""
    f = OUT / f"{_slug(composition, phase)}.json"
    return json.loads(f.read_text()) if f.exists() else None


def for_result(res: dict, mine_missing: bool = False) -> list[dict]:
    """Priors for the material of an analysis result: from the cache, or mined when missing (network)."""
    comp, phase = res["inputs"]["composition"], res.get("phase")
    r = cached(comp, phase) or (mine(comp, phase) if mine_missing else None)
    return (r or {}).get("priors", [])


def describe(p: dict) -> str:
    """'Pt–O bond length 2.02 ± 0.02 Å' for one prior."""
    v = "–".join(f"{x:g}" for x in p["value"]) if isinstance(p["value"], list) else f"{p['value']:g}"
    unc = f" ± {p['uncertainty']:g}" if p.get("uncertainty") else ""
    return f"{p.get('pair') or p.get('element') or ''} {p['quantity'].replace('_', ' ')} {v}{unc} {p['unit']}".strip()
