"""What a dropped file holds: XRD, PDF G(r), raw total scattering I(Q) for a PDF, XAFS μ(E) or χ(k), told from its
name and checked against its numbers,
with a small preview and the XAFS edge pre-filled for the upload form. Parsing reuses the XRD loader's table and
'# key=value' header readers; nothing here is analysis, every call is fast."""
import re
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xraydb
from pymatgen.core import Composition, Element

from concord.analysis import default_edge
from concord.tools import xafs, xrd

LABELS = {"xrd": ("2θ (°)", "Intensity"), "pdf": ("r (Å)", "G(r)"), "pdf_iq": ("Q (Å⁻¹)", "Intensity"),
          "xafs_mu": ("E (eV)", "μ(E)"), "xafs_chi": ("k (Å⁻¹)", "χ(k)")}
WHAT = {"xrd": "an XRD pattern", "pdf": "a PDF G(r)", "pdf_iq": "a raw total-scattering I(Q) for a PDF",
        "xafs_mu": "an XAFS μ(E) scan", "xafs_chi": "an EXAFS χ(k)"}
NAMES = {"pdf": r"\.gr$|(?<![a-z])pdf(?![a-z]|_(iq|sq|bkg))", "pdf_iq": r"(?<![a-z])(iq|sq|bkg)(?![a-z])|\.(iq|sq)$|total.?scatter",
         "xafs_chi": r"(?<![a-z])chi|\.k$", "xafs_mu": r"(?<![a-z])x?mu(?![a-z])", "xrd": r"xrd|\.xye?$"}
TOTAL_SCATTERING_QMAX = 15.0  # Å⁻¹; lab XRD stops at 8.2 (Cu Kα) or 17.7 (Mo Kα, only at 2θ = 180°)
LEVELS = ("low", "medium", "high")
EDGES = ("K", "L1", "L2", "L3")  # the edges the upload form accepts
PREVIEW = 240
MIN_POINTS = 100


def _n(v: float) -> str:
    return f"{v:.6g}"


def _table(data: bytes, suffix: str) -> tuple[pd.DataFrame | None, tuple | None, dict]:
    """(table, xrd.guess_columns of it, header) via the XRD loader's readers, which take paths."""
    suffix = suffix if re.fullmatch(r"\.[a-z0-9]{1,5}", suffix) else ".txt"
    with tempfile.TemporaryDirectory() as tmp:
        paths = [Path(tmp) / f"upload{s}" for s in dict.fromkeys((suffix, ".txt"))]
        for p in paths:
            p.write_bytes(data)
        # a .csv with '#' lines parses only on read_table's whitespace/comma path, and there a text header row trips its
        # dtype check under pandas 3 (StringDtype), hence the plain header-row read last
        readers = [lambda p=p: xrd.read_table(p) for p in paths]
        readers.append(lambda: pd.read_csv(paths[-1], sep=r"\s+|,", engine="python", comment="#"))
        for read in readers:
            try:
                df = read()
                return df, xrd.guess_columns(df), xrd._header(paths[0])
            except Exception:
                continue
        return None, None, xrd._header(paths[0])


def columns(name: str, data: bytes) -> tuple[np.ndarray, np.ndarray] | None:
    """The x and y columns as the inspection reads them, so an upload can be saved in the plain form the loaders take."""
    df, cols, _ = _table(data, Path(name).suffix.lower())
    if df is None or not cols:
        return None
    x, y = df[cols[0]].to_numpy(float), df[cols[1]].to_numpy(float)
    ok = np.isfinite(x) & np.isfinite(y)
    return x[ok], y[ok]


def _by_name(name: str) -> str | None:
    hits = [t for t, pat in NAMES.items() if re.search(pat, Path(name).name.lower())]
    return hits[0] if len(hits) == 1 else None


def _by_content(x: np.ndarray, y: np.ndarray, q_hint: bool | None) -> tuple[str | None, str, str, bool]:
    """(technique, confidence, reason, XRD x is Q) from the numbers alone."""
    lo, hi, step = float(x[0]), float(x[-1]), float(np.median(np.diff(x)))
    span = f"x runs {_n(lo)} to {_n(hi)}"
    if lo > 1000:
        tail = max(1, len(y) // 10)
        rises = y[-tail:].mean() > y[:tail].mean()
        return ("xafs_mu", "high" if rises else "medium",
                f"{span} eV{' with a rising absorption step' if rises else ''}: an XAFS μ(E) scan", False)
    neg = float((y < 0).mean())
    if 0.2 <= neg <= 0.85 and -y.min() >= 0.15 * y.max():  # oscillates around zero; noise under XRD peaks stays smaller
        if lo <= 3 and y[x <= lo + 0.5].mean() < 0 and (step < 0.03 or hi > 25):
            return "pdf", "high", f"{span} Å in steps of {_n(step)}, oscillating around zero and negative at low r: a PDF G(r)", False
        if hi <= 25 and 0.03 <= step <= 0.08:
            return "xafs_chi", "high", f"{span} in steps of {_n(step)}, oscillating around zero: an EXAFS χ(k)", False
        if hi <= 25:
            return "xafs_chi", "low", f"{span}, oscillating around zero but with an unusual step of {_n(step)}: perhaps an EXAFS χ(k)", False
        if lo <= 3:
            return "pdf", "low", f"{span}, oscillating around zero but not negative at low r: perhaps a PDF G(r)", False
        return None, "low", f"{span}, oscillating around zero, which fits neither a PDF nor a χ(k)", False
    if lo < 0 or hi > 180:
        return None, "low", f"{span} with mostly positive values, outside any 2θ, Q or XAFS energy range", False
    q = q_hint if q_hint is not None else hi <= 30
    if q and hi >= TOTAL_SCATTERING_QMAX:
        return ("pdf_iq", "high" if q_hint else "medium", f"{span} Å⁻¹ with {'non-negative' if neg == 0 else 'mostly positive'} "
                f"intensities, past the Q a lab diffractometer reaches: raw total scattering for a PDF", True)
    peaks = y.max() - y.min() > 2 * (np.median(y) - y.min())  # peaks over the background, unlike a μ(E) step
    conf = "low" if not peaks else "medium" if q_hint is None and q else "high"
    sign = "non-negative" if neg == 0 else "mostly non-negative"
    return ("xrd", conf, f"{span} with {sign} intensities{'' if peaks else ' but no clear peaks'}: an XRD pattern in "
            f"{'Q' if q else '2θ'}", q)


def _elements(composition: str | None, warnings: list) -> dict:
    try:
        return {e.symbol: e.Z for e in Composition(composition).elements if Element.is_valid_symbol(e.symbol)} if composition else {}
    except ValueError:
        warnings.append(f"could not read the composition {composition}")
        return {}


def _edge(technique: str, x: np.ndarray, y: np.ndarray, header: dict, elements: dict, warnings: list) -> tuple[str | None, bool]:
    """(edge like 'Pt L3', guessed from the composition alone)."""
    stated = header.get("edge", "").replace("_", " ")
    stated = stated if re.fullmatch(r"[A-Z][a-z]? (K|L1|L2|L3)", stated) else None
    edge, guessed = None, False
    if technique == "xafs_mu" and x[0] > 1000:  # energies in eV; a μ(E) named so but in other units gets no edge
        try:
            e0 = xafs.normalize(x, y)["e0"]
        except Exception:  # larch's pre_edge fails on odd scans; the steepest rise of the raw μ is close enough
            e0 = float(x[np.argmax(np.gradient(y, x))])
        near = [(abs(ed.energy - e0), f"{el} {k}") for el in elements for k, ed in xraydb.xray_edges(el).items()
                if k in EDGES and x[0] <= ed.energy <= x[-1]]
        dist, edge = min(near) if near else (np.inf, None)
        if dist > 30:  # chemical shifts stay within ~20 eV: a farther edge is another element's
            nearest = " ".join(xraydb.guess_edge(e0, edges=EDGES))
            if nearest == edge:
                warnings.append(f"the steepest rise at {e0:.0f} eV is {dist:.0f} eV from the tabulated {edge} edge")
            edge = nearest
        if stated and stated != edge:
            warnings.append(f"the header says {stated} but the edge in the data is {edge}")
    elif technique == "xafs_chi":
        if stated:
            edge = stated
        elif elements:
            heavy = max(elements, key=elements.get)
            edge, guessed = f"{heavy} {default_edge(heavy)}", True
            warnings.append(f"edge {edge} is a guess from the heaviest element: check it")
    if edge and elements and edge.split()[0] not in elements:
        warnings.append("the edge element is not in the composition")
    return edge, guessed


def _preview(x: np.ndarray, y: np.ndarray) -> dict:
    if len(x) > PREVIEW:  # each bucket's min and max keep the peaks; the end points keep the x range
        buckets = np.array_split(np.arange(1, len(x) - 1), PREVIEW // 2 - 1)
        idx = np.unique([0, len(x) - 1] + [i for b in buckets for i in (b[np.argmin(y[b])], b[np.argmax(y[b])])])
        x, y = x[idx], y[idx]
    return {"x": np.round(x, 4).tolist(), "y": np.round((y - y.min()) / (np.ptp(y) or 1.0), 4).tolist()}


def inspect_file(name: str, data: bytes, composition: str | None = None) -> dict:
    """Technique, confidence, reason, axis labels, range, preview, XAFS edge, header and warnings for one upload."""
    out = {"name": name, "technique": None, "confidence": "low", "reason": "", "x_label": None, "y_label": None,
           "x_range": None, "n_points": 0, "preview": {"x": [], "y": []}, "edge": None, "header": {}, "warnings": []}
    df, cols, out["header"] = _table(data, Path(name).suffix.lower())
    if df is None:
        return {**out, "reason": "no two numeric columns could be read from the file"}
    xc, yc, unit = cols
    x, y = df[xc].to_numpy(float), df[yc].to_numpy(float)
    ok = np.isfinite(x) & np.isfinite(y)
    order = np.argsort(x[ok], kind="stable")
    x, y = x[ok][order], y[ok][order]
    if len(x) < 2:
        return {**out, "reason": "the file has fewer than two rows of numbers"}
    warnings = out["warnings"]
    hx, xname = out["header"].get("x", ""), str(xc).lower()
    q_hint = True if "q_inv_A" in hx or unit == "q" else False if "2theta" in hx or "th" in xname or "angle" in xname else None
    tech, conf, reason, q = _by_content(x, y, q_hint)
    named = _by_name(name)
    if named and named == tech:
        conf = LEVELS[min(2, LEVELS.index(conf) + 1)]
    elif named and (tech is None or conf == "low"):
        warnings.append(f"the numbers do not clearly look like {WHAT[named]}: going by the file name")
        tech, conf, reason, q = named, "low", f"the file name says {WHAT[named]}; the numbers do not clearly confirm it", False
    elif named:
        warnings.append(f"the name suggests {WHAT[named]} but the content is {WHAT[tech]}")
        conf = "medium" if conf == "high" else "low"
    if tech in ("xrd", "pdf_iq") and q and q_hint is None and named != "pdf_iq":  # only an iq/sq name settles Q against 2θ
        warnings.append(f"x ends at {_n(x[-1])}: read as Q in Å⁻¹, not 2θ")
        conf = "medium" if conf == "high" else conf
    if len(x) < MIN_POINTS:
        warnings.append(f"only {len(x)} points")
    edge, guessed = _edge(tech, x, y, out["header"], _elements(composition, warnings), warnings)
    x_label, y_label = ("Q (Å⁻¹)", "Intensity") if tech == "xrd" and q else LABELS.get(tech, (None, None))
    return {**out, "technique": tech, "confidence": "low" if guessed else conf, "reason": reason, "x_label": x_label,
            "y_label": y_label, "x_range": [round(float(x[0]), 4), round(float(x[-1]), 4)], "n_points": int(len(x)),
            "preview": _preview(x, y), "edge": edge}
