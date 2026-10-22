"""The techniques a user did not measure, generated from the model fitted to what they did. GENERATED, NOT MEASURED.

The structure and size come from the saved analysis: the PDF-refined model when the PDF identified the phase, else
the library structure of the XRD phase with the XRD sphere diameter. Each missing technique is simulated with the
planner's simulators, and the locally trained realism GAN adds instrument effects when it is loaded. The curves are
shown to the user, never analysed: checks C1-C7 compare measurements only, and a curve generated from the model
would only agree with itself.
"""
import numpy as np
from pymatgen.core import Element, Structure

from concord import analysis as an
from concord.data_builder.build import instruments
from concord.planner import AXES, GRIDS, QDAMP, QMAX, simulate

LABEL = "GENERATED, NOT MEASURED"
INPUT = {"xrd": "xrd", "pdf": "pdf", "exafs": "xafs"}  # planner technique → analysis input name


def missing(res: dict) -> list[str]:
    return [t for t in GRIDS if INPUT[t] not in res["inputs"]["techniques"]]


def _model(res: dict) -> tuple[Structure, float, str, str]:
    """(structure, size in nm, phase, where they come from) of the analysis."""
    phase, comp = res.get("phase"), res["inputs"]["composition"]
    if not phase:
        raise ValueError("no phase was identified from the measured data, so there is no model to generate from")
    fit = (res.get("pdf") or {}).get("fits", [None])[0]
    if fit and fit["candidate"] == phase and fit.get("psize_nm"):
        return Structure.from_str(fit["structure"], fmt="cif"), float(fit["psize_nm"]), phase, "the PDF-refined model"
    size = (res.get("xrd") or {}).get("sphere_diameter_nm")
    if not size:
        raise ValueError("the analysis has no particle size, so there is no model to generate from")
    return an.candidates(comp)[phase], float(size), phase, "the XRD phase and its sphere diameter"


def generate(res: dict, realism=None, seed: int = 0) -> dict:
    todo = missing(res)
    if not todo:
        raise ValueError("every technique was measured; there is nothing to generate")
    st, size, phase, source = _model(res)
    cations = an._cations(st.composition.reduced_formula)
    absorber = max(cations, key=lambda e: Element(e).Z)
    edge = an.default_edge(absorber)
    theta = instruments()["debye_temperature_K"].get(phase)
    notes = [] if theta else [f"No Debye temperature is tabulated for {phase}; 300 K is assumed for the thermal motion."]
    conditions = {"xrd": {}, "pdf": {"qmax": QMAX, "qdamp": QDAMP}, "exafs": {"edge": f"{absorber} {edge}"}}
    out = {}
    for tech in todo:
        x = GRIDS[tech]
        clean = np.asarray(simulate(tech, st, theta or 300.0, size, absorber, edge), float)
        real = None
        if realism:
            try:
                real = np.asarray(realism(tech, x, clean, composition=res["inputs"]["composition"], seed=seed, **conditions[tech]), float)
            except (ValueError, TypeError) as exc:  # e.g. an edge the GAN was not trained on: shown clean, never faked
                notes.append(f"No instrument realism for {tech.upper()}: {exc}")
        out[tech] = {"x_label": AXES[tech][0], "y_label": AXES[tech][1], "x": x.round(4).tolist(), "clean": clean.round(6).tolist(),
                     "realistic": None if real is None else real.round(6).tolist()}
    return {"label": LABEL, "from": {"measured": res["inputs"]["techniques"], "phase": phase, "size_nm": round(size, 3), "source": source,
                                     "absorber": absorber, "edge": edge},
            "techniques": out, "notes": notes}
