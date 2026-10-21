"""Adapter for the external visual-inspection ("eye") module.

The module is loaded at runtime from EYE_MODULE_PATH (a .py file or a package folder) and never copied into this
repository. The first callable found among ENTRY_POINTS is called with (image_path, context) and its answer is
normalised to {verdict: accept|reject, issues: [{region, pattern, likely_cause, suggested_action}]}.
shortcut: the eye module's real interface could not be read (reference repos not cloned); ENTRY_POINTS and
normalise() follow the contract in the brief and must be checked once the module is available.
"""
import importlib
import importlib.util
import sys
from pathlib import Path

from concord.config import env

ENTRY_POINTS = ("inspect", "inspect_plot", "inspect_image", "analyze_image", "evaluate", "judge")


class EyeUnavailable(RuntimeError):
    pass


def load(path: str | None = None):
    """The eye module's inspection callable, or None when EYE_MODULE_PATH is not set."""
    path = path or env().get("EYE_MODULE_PATH")
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.exists():
        raise EyeUnavailable(f"EYE_MODULE_PATH points to {p}, which does not exist")
    if p.is_dir():
        sys.path.insert(0, str(p.parent))
        mod = importlib.import_module(p.name)
    else:
        spec = importlib.util.spec_from_file_location("concord_external_eye", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    for name in ENTRY_POINTS:
        if callable(fn := getattr(mod, name, None)):
            return fn
    raise EyeUnavailable(f"{p} defines none of {ENTRY_POINTS}")


def normalise(raw) -> dict:
    if isinstance(raw, str):
        raw = {"verdict": raw}
    verdict = str(raw.get("verdict", raw.get("decision", "reject"))).lower()
    issues = []
    for it in raw.get("issues", []) or []:
        it = it if isinstance(it, dict) else {"pattern": str(it)}
        issues.append({k: str(it.get(k, "")) for k in ("region", "pattern", "likely_cause", "suggested_action")})
    return {"verdict": "accept" if verdict in ("accept", "ok", "pass", "good") else "reject", "issues": issues}


def inspect(fn, image: str | Path, context: dict) -> dict:
    try:
        raw = fn(str(image), context)
    except TypeError:  # single-argument interface
        raw = fn(str(image))
    return {**normalise(raw), "inspector": "eye"}
