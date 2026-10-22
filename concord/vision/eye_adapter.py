"""Adapter for the external fit reviewer ("eye") module.

The module is loaded at runtime from EYE_MODULE_PATH (a .py file or a package folder) and never copied into this
repository. Two interfaces are understood:
- the PDF agent's residual reader (pdf_backend app/modules/agent/residual.py): analyse(r, gobs, gcalc) measures the
  difference curve and interpret() names causes with their evidence. It judges PDF fits from the curves; other
  techniques get the open fallback judge.
- an image judge: the first callable among ENTRY_POINTS, called with (image_path, context).
Answers are normalised to {verdict: accept|reject, issues: [{region, pattern, likely_cause, suggested_action}]}.
"""
import importlib
import importlib.util
import logging
import sys
import types
from pathlib import Path

from concord.config import env

ENTRY_POINTS = ("inspect", "inspect_plot", "inspect_image", "analyze_image", "evaluate", "judge")
_PLATFORM_LOGGING = ("app", "app.core", "app.core.logging_config")
# The reviewer's causes that Concord's fix menu can act on; the others (lattice, scale, ADPs, delta2) it refines already.
_ACTIONS = {"instrument resolution (qdamp)": "pdf_toggle_envelope"}


class EyeUnavailable(RuntimeError):
    pass


def _exec_file(p: Path):
    spec = importlib.util.spec_from_file_location("concord_external_eye", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ModuleNotFoundError as exc:
        if exc.name not in _PLATFORM_LOGGING:
            raise
        # the PDF platform's modules log through app.core.logging_config: lend them the standard logger rather than
        # importing the platform (its settings, database and log files)
        shim = {n: types.ModuleType(n) for n in _PLATFORM_LOGGING}
        shim["app.core.logging_config"].get_logger = logging.getLogger
        sys.modules.update(shim)
        try:
            spec.loader.exec_module(mod)
        finally:
            for n in _PLATFORM_LOGGING:
                sys.modules.pop(n, None)
    return mod


def _residual_reader(mod):
    def read(image, context: dict):
        if context.get("technique") != "pdf":
            return None
        c = context["curves"]
        diag = mod.analyse([float(v) for v in c["x"]], [float(v) for v in c["obs"]], [float(v) for v in c["calc"]])
        causes = mod.interpret(diag)
        region = "–".join(f"{v:g}" for v in diag.get("r_range", [])) + " Å"
        # strong evidence (the reviewer's "high") or no parameter that could fix it (wrong phase) rejects the fit
        bad = [k for k in causes if k.get("confidence") == "high" or not k.get("parameters")]
        return {"verdict": "reject" if bad else "accept",
                "issues": [{"region": region, "pattern": k.get("evidence", ""), "likely_cause": k.get("cause", ""),
                            "suggested_action": _ACTIONS.get(k.get("cause"), "")} for k in causes]}
    return read


def load(path: str | None = None):
    """The eye module's inspection callable, or None when EYE_MODULE_PATH is not set."""
    path = path or env().get("EYE_MODULE_PATH")
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.exists():
        raise EyeUnavailable(f"EYE_MODULE_PATH points to {p}, which does not exist")
    cache, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # the module's folder is read-only to us: no __pycache__
    try:
        if p.is_dir():
            sys.path.insert(0, str(p.parent))
            mod = importlib.import_module(p.name)
        else:
            mod = _exec_file(p)
    except Exception as exc:  # a broken external module never stops the analysis: the fallback judge runs
        raise EyeUnavailable(f"{p} could not be loaded ({type(exc).__name__}: {exc})") from exc
    finally:
        sys.dont_write_bytecode = cache
    if callable(getattr(mod, "analyse", None)) and callable(getattr(mod, "interpret", None)):
        return _residual_reader(mod)
    for name in ENTRY_POINTS:
        if callable(fn := getattr(mod, name, None)):
            return fn
    raise EyeUnavailable(f"{p} defines none of {ENTRY_POINTS}, nor analyse/interpret")


def normalise(raw) -> dict:
    if isinstance(raw, str):
        raw = {"verdict": raw}
    verdict = str(raw.get("verdict", raw.get("decision", "reject"))).lower()
    issues = []
    for it in raw.get("issues", []) or []:
        it = it if isinstance(it, dict) else {"pattern": str(it)}
        issues.append({k: str(it.get(k, "")) for k in ("region", "pattern", "likely_cause", "suggested_action")})
    return {"verdict": "accept" if verdict in ("accept", "ok", "pass", "good") else "reject", "issues": issues}


def inspect(fn, image: str | Path, context: dict) -> dict | None:
    """The eye's verdict, or None when it does not judge this technique (the fallback judge runs instead)."""
    try:
        raw = fn(str(image), context)
    except TypeError:  # single-argument interface
        raw = fn(str(image))
    return None if raw is None else {**normalise(raw), "inspector": "eye"}
