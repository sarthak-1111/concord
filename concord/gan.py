"""Adapter for the Concord Forge realism GANs (one generator each for XRD, PDF and EXAFS).

The generator weights ship in models/gan/ (from https://github.com/sarthak-1111/GAN-Hackathon, which trains them); the
model code is loaded at run time from a clone of that repo at GAN_REPO_PATH (the clone's weights are used when
models/gan/ lacks them): forge.gan
defines the generator, forge.data / forge.realism / forge.realdata the model grids, views and condition vectors, and
Git LFS pointers are resolved to the clone's .git/lfs object store. A generator takes a clean simulated spectrum on its
model grid and returns it with a smooth gain (0.9-1.1), background and coloured noise (EXAFS: also up to 2 glitches);
peak positions are left unchanged by construction. CPU only; nothing is written to the clone.
"""
import importlib
import json
import os
import sys
import types
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
import yaml
from dotenv import dotenv_values

from concord.config import ROOT

TECHNIQUES = ("xrd", "pdf", "exafs")
CLEAR_LICENCES = ("CC-BY-4.0", "CC0-1.0")
MAX_POINTS = 600
LABELS = {"xrd": ("2θ (degrees, Cu Kα)", "Intensity (normalized)"), "pdf": ("r (Å)", "G(r) (normalized)"),
          "exafs": ("k (Å⁻¹)", "k²χ(k) (normalized)")}
CONDITIONS = {"xrd": set(), "pdf": {"qmax", "qdamp"}, "exafs": {"edge"}}


def repo_path() -> str | None:
    # not a secret, so unlike config.env() the process environment may set it (tests, CI); .env otherwise
    return (os.environ.get("GAN_REPO_PATH") or dotenv_values(ROOT / ".env").get("GAN_REPO_PATH") or "").strip() or None


def _lfs(p: Path, repo: Path) -> Path:
    """The working-tree file, or the LFS object when it is a Git LFS pointer."""
    with p.open("rb") as fh:
        head = fh.read(200)
    if not head.startswith(b"version https://git-lfs"):
        return p
    oid = head.split(b"oid sha256:")[1].split()[0].decode()
    obj = repo / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    if not obj.exists():
        raise FileNotFoundError(f"{p.relative_to(repo)} is a Git LFS pointer whose object was not fetched (git lfs pull)")
    return obj


def _unavailable(*_, **__):
    raise RuntimeError("forge.paths helpers are not loaded by Concord")


def _import_forge(repo: Path) -> types.SimpleNamespace:
    art = repo / "artifacts"
    # forge/paths.py creates artifact directories on import: its importers get the paths from a stub instead
    paths = types.ModuleType("forge.paths")
    paths.__dict__.update(ROOT=repo, DATA=art / "data", MODELS=art / "models", CONFIGS=repo / "configs",
                          STRUCT_DIR=art / "data" / "work" / "structures", FEFF_DIR=art / "data" / "work" / "feff",
                          **dict.fromkeys(("load_yaml", "seed_everything", "sha256_file", "sha256_json"), _unavailable))
    cache, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # the clone stays untouched: no __pycache__
    sys.path.insert(0, str(repo))
    sys.modules["forge.paths"] = paths
    try:
        mods = {n: importlib.import_module(f"forge.{n}") for n in ("gan", "data", "realism", "realdata")}
    finally:
        sys.path.remove(str(repo))
        sys.dont_write_bytecode = cache
    if not mods["gan"].__file__.startswith(str(repo)):
        raise ImportError(f"another 'forge' package was imported ({mods['gan'].__file__})")
    g = yaml.safe_load((repo / "configs" / "instruments.yaml").read_text())["grids"]["pdf"]
    grids = {"xrd": mods["data"].TTH_MODEL, "pdf": g["r_min"] + g["r_step"] * np.arange(mods["data"].PDF_N),
             "exafs": mods["realdata"].K_STORE[mods["data"].K_SLICE]}
    return types.SimpleNamespace(repo=repo, grids=grids, **mods)


@lru_cache(maxsize=1)
def _state():
    """(forge namespace or None, {technique: generator}, {technique: why it did not load})."""
    path = repo_path()
    if not path:
        return None, {}, dict.fromkeys(TECHNIQUES, "GAN_REPO_PATH is not set")
    repo = Path(path).expanduser().resolve()
    if not (repo / "forge" / "gan.py").exists():
        return None, {}, dict.fromkeys(TECHNIQUES, f"GAN_REPO_PATH={repo} has no forge/gan.py")
    try:
        fg = _import_forge(repo)
    except Exception as exc:
        return None, {}, dict.fromkeys(TECHNIQUES, f"forge could not be imported ({type(exc).__name__}: {exc})")
    models, errors = {}, {}
    for t in TECHNIQUES:
        try:
            bundled = ROOT / "models" / "gan" / f"realism_{t}" / "generator_ema.pt"  # shipped with this repo
            ck = torch.load(bundled if bundled.exists() else _lfs(repo / "artifacts" / "models" / f"realism_{t}" / "generator_ema.pt", repo),
                            map_location="cpu", weights_only=True)
            G = fg.gan.Generator(fg.realism.LENGTH[t], fg.realism.COND_DIM[t], glitches=t == "exafs")
            G.load_state_dict(ck["state_dict"])
            models[t] = G.eval()
        except Exception as exc:
            errors[t] = f"{type(exc).__name__}: {exc}"
    return fg, models, errors


def available() -> dict:
    """{"repo": GAN_REPO_PATH or None, "loaded": [techniques], "errors": {technique: why it did not load}}."""
    _, models, errors = _state()
    return {"repo": repo_path(), "loaded": [t for t in TECHNIQUES if t in models], "errors": errors}


def _model(technique: str):
    if technique not in TECHNIQUES:
        raise ValueError(f"technique must be one of {TECHNIQUES}, not {technique!r}")
    fg, models, errors = _state()
    if technique not in models:
        raise RuntimeError(f"realism GAN for {technique} not loaded: {errors[technique]}")
    return fg, models[technique]


@torch.inference_mode()
def _generate(G, view: np.ndarray, cond: np.ndarray, seed: int) -> np.ndarray:
    g = torch.Generator().manual_seed(int(seed))
    z = torch.randn(1, G.z_dim, generator=g)  # z first, then the noise: the draw order of realism_infer.apply
    out = G(torch.as_tensor(view, dtype=torch.float32)[None], torch.as_tensor(cond, dtype=torch.float32)[None], z=z, gen=g)
    return out[0].double().numpy()


def realism(technique: str, x, y, *, composition: str, seed: int = 0, **conditions) -> np.ndarray:
    """A clean simulated curve with the GAN's instrument effects, on the input x grid (same shape as y).

    composition is a formula ("Pt", "Pt3Co", "PtNi"), turned into [Pt, Co, Ni, Fe, Cu, other] fractions as forge.realdata
    does for the training data. The input is resampled onto the model grid, passed through the generator and resampled
    back; points outside the model grid are returned unchanged.
    - xrd:   x = 2θ in degrees for Cu Kα, y = intensity (any scale). Model grid 20-80° (1536 points).
    - pdf:   x = r in Å, y = G(r) (any scale). Model grid 0.50-30.08 Å (0.02 Å steps). Conditions qmax (Å⁻¹, default 25)
             and qdamp (Å⁻¹, default 0.04).
    - exafs: x = k in Å⁻¹, y = χ(k) unweighted. Model grid 2.00-14.75 Å⁻¹ (0.05 steps, works on k²χ). Condition edge
             ("Pt" for Pt L3, or "Co", "Ni", "Fe", "Cu" K; "Pt L3" or "Co K" also accepted, default "Pt"); the oxide flag
             is set when the formula contains O.
    The same seed gives the same curve.
    """
    fg, G = _model(technique)
    if extra := set(conditions) - CONDITIONS[technique]:
        raise TypeError(f"unknown {technique} conditions {sorted(extra)}; expected {sorted(CONDITIONS[technique]) or 'none'}")
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.ndim != 1 or x.shape != y.shape or len(x) < 2:
        raise ValueError("x and y must be 1-D arrays of the same length")
    comp6, oxide = fg.realdata.comp6_from_formula(composition)
    if comp6 is None:
        raise ValueError(f"composition {composition!r} is not a chemical formula")
    order = np.argsort(x)
    xs, ys, grid = x[order], y[order], fg.grids[technique]
    if technique == "xrd":
        v = np.interp(grid, xs, ys)
        scale = max(v.max(), 1e-12)
        out = _generate(G, fg.data.view("xrd", v[None])[0], fg.realism.cond_xrd(comp6[None])[0], seed) * scale
    elif technique == "pdf":
        v = np.interp(grid, xs, ys, left=0, right=0)
        scale = max(np.abs(v).max(), 1e-12)
        cond = fg.realism.cond_pdf(comp6[None], [conditions.get("qmax", 25.0)], [conditions.get("qdamp", 0.04)])[0]
        out = _generate(G, fg.data.view("pdf", v[None])[0], cond, seed) * scale
    else:
        edge = str(conditions.get("edge", "Pt")).split()[0].capitalize()
        if edge not in fg.data.EDGES:
            raise ValueError(f"edge must be one of {fg.data.EDGES}, not {edge!r}")
        chi = np.interp(fg.realdata.K_STORE, xs, ys, left=0, right=0)
        cond = fg.realism.cond_exafs([fg.data.EDGES.index(edge)], comp6[None], [oxide])[0]
        out = _generate(G, fg.data.view("exafs_pt", chi[None])[0], cond, seed) / grid ** 2
    res = y.copy()
    inside = (x >= grid[0]) & (x <= grid[-1])
    res[inside] = np.interp(x[inside], grid, out)
    return res


@lru_cache(maxsize=64)
def _source_url(manifest: Path, item_id: str) -> str | None:
    with manifest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith(f"real_spectrum,{item_id},"):
                return line.split(",")[3]
    return None


def _c2st(repo: Path, technique: str) -> dict:
    # held-out real spectra vs twin + GAN and vs twin + classical augmentation, from the repo's own report
    # artifacts/reports/gan_diagnostics.json (the same numbers as gan_diagnostics.md and the model cards)
    out = {"gan": None, "classical": None, "note": "50 % means a classifier cannot tell them from real data"}
    try:
        c = next(r["c2st"] for r in json.loads((repo / "artifacts" / "reports" / "gan_diagnostics.json").read_text())
                 if r["technique"] == technique)
        out.update(gan=round(float(c["gan"]["acc"]), 3), classical=round(float(c["classical"]["acc"]), 3))
    except (OSError, ValueError, KeyError, StopIteration):
        pass
    return out


def showcase(technique: str, seed: int = 0) -> dict:
    """One real open spectrum, its simulated twin and the twin through the GAN, for a "Real or GAN?" demo.

    The item is chosen by seed among those with a twin, preferring a CC-BY-4.0 / CC0-1.0 licence and the held-out split
    (never used in GAN training). The GAN curve is the twin through the same generator call as realism(), with the item's
    stored condition vector. All three share the model grid (thinned to at most MAX_POINTS) and are scaled to max |y| = 1.
    """
    fg, G = _model(technique)
    real = fg.repo / "artifacts" / "data" / "real"
    z = np.load(real / f"{technique}.npz", allow_pickle=False)
    ok = z["has_twin"] & (z["twin_ok"] if "twin_ok" in z.files else True)
    clear = ok & np.isin(z["licence"], CLEAR_LICENCES)
    pool = next((np.flatnonzero(m) for m in (clear & (z["split"] == "eval"), clear, ok) if m.any()), None)
    if pool is None:
        raise RuntimeError(f"{real / f'{technique}.npz'} has no item with a simulated twin")
    i = int(pool[int(seed) % len(pool)])
    step = -(-len(fg.grids[technique]) // MAX_POINTS)
    xs = fg.grids[technique][::step].round(4).tolist()

    def curve(v):
        v = np.asarray(v, float)[::step]
        return {"x": xs, "y": (v / max(np.abs(v).max(), 1e-12)).round(5).tolist()}

    item, title, lic = str(z["item_id"][i]), " ".join(str(z["material"][i]).split()), str(z["licence"][i])
    url = _source_url(fg.repo / "artifacts" / "data" / "manifest.csv", item)
    return {"technique": technique, "x_label": LABELS[technique][0], "y_label": LABELS[technique][1],
            "real": curve(z["x"][i]), "simulated": curve(z["twin"][i]),
            "gan": curve(_generate(G, z["twin"][i], z["cond"][i], seed)),
            "source": {"id": item, "title": title, "licence": lic, "url": url,
                       "attribution": ", ".join(filter(None, (f"{title} ({item})", url, f"licence {lic}")))},
            "c2st": _c2st(fg.repo, technique), "seed": int(seed)}
