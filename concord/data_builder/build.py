"""Build the dataset in the shared data contract: `make data` (v1, 60 samples), `make data-big` (grow to 320).

The sample plan is prefix-stable (sample i depends only on i and the seed), so growing the dataset never
changes existing samples or their split. Every sample is one structural model simulated three ways.
"""
import argparse
import csv
import hashlib
import json
import logging
import multiprocessing as mp
import time
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from concord.config import ROOT
from concord.data_builder import models as M
from concord.data_builder import simulate as S
from concord.data_builder.fetch import load_structures, systems
from concord.tools.feff import debye_uiso, sigma2_correlated_debye
from concord.tools.pdfcalc import first_shells, site_label

log = logging.getLogger("concord.build")
HERE = Path(__file__).parent
OUT = ROOT / "dataset"
SEED = 20261022
FAULTS = ["wrong_phase_candidate", "oxide_shell", "mixed_oxidation_states", "alloy_segregation",
          "multi_domain", "low_concentration_dopant", "mislabeled_metadata"]
FAULT_SYSTEMS = {"wrong_phase_candidate": ["TiO2-brookite", "PtO2-alpha"], "oxide_shell": ["Pt", "Pt3Co", "PtNi"],
                 "mixed_oxidation_states": ["CeO2"], "alloy_segregation": ["Pt3Co", "PtNi"], "multi_domain": ["Pt"],
                 "low_concentration_dopant": ["Pt"], "mislabeled_metadata": ["CeO2", "TiO2-anatase", "Pt", "IrO2"]}
VALENCE_STANDARDS = {"Pt": [0, 2, 4], "Ce": [3, 4], "Ti": [3, 4], "Co": [2, 3], "Ir": [0, 4]}
THETA_ALIAS = {"TiO2-brookite": "TiO2-anatase", "PtO2-alpha": "PtO2"}


def instruments() -> dict:
    return yaml.safe_load((HERE / "instruments.yaml").read_text())


def plan(n: int) -> list[dict]:
    lib = [s["name"] for s in systems() if s.get("library", True)]
    specs = []
    for i in range(n):
        rng = np.random.default_rng([SEED, i])
        fault = FAULTS[(i // 7) % len(FAULTS)] if i % 7 == 3 else None
        system = FAULT_SYSTEMS[fault][(i // 49) % len(FAULT_SYSTEMS[fault])] if fault else lib[i % len(lib)]
        sysdef = next(s for s in systems() if s["name"] == system)
        bulk = fault is None and (i // len(lib)) % 5 == 0
        shape = "icosahedron" if fault == "multi_domain" else sysdef["shapes"][(i // len(lib)) % len(sysdef["shapes"])]
        if fault in ("oxide_shell", "alloy_segregation", "low_concentration_dopant") and shape == "icosahedron":
            shape = "cuboctahedron"
        techniques = ["xrd", "pdf"] if (fault is None and i % 8 == 5) else ["xrd", "pdf", "xafs"]
        specs.append({"index": i, "sample_id": f"s{i:04d}", "system": system, "form": "bulk" if bulk else "nanoparticle",
                      "shape": None if bulk else shape, "size_nm": None if bulk else float(np.exp(rng.uniform(np.log(1.5), np.log(8.0)))),
                      "techniques": techniques, "fault": fault, "seed": [SEED, i]})
    return specs


def split_of(spec: dict) -> str:
    if spec["fault"]:
        return "faults"
    return {0: "train", 1: "train", 2: "train", 3: "val", 4: "test"}[spec["index"] % 5]


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _env_classes(atoms, absorber: str, r1: float, center_only: float | None, rng) -> list[tuple[int, float]]:
    """Group absorber atoms by first-shell environment (neighbour element and distance in 0.05 Å bins);
    one random representative per class, weighted by class population."""
    from scipy.spatial import cKDTree
    pos = atoms.get_positions()
    sym = np.array(atoms.get_chemical_symbols())
    idx = np.where(sym == absorber)[0]
    mid = pos.mean(axis=0)
    if center_only is not None:  # bulk supercell: only atoms far from the cell faces
        idx = idx[np.linalg.norm(pos[idx] - mid, axis=1) < center_only]
    groups: dict = {}
    for i, nbs in zip(idx, cKDTree(pos).query_ball_point(pos[idx], r=r1 + 0.3)):
        key = tuple(sorted(Counter((sym[j], round(float(np.linalg.norm(pos[j] - pos[i])) / 0.05)) for j in nbs if j != i).items()))
        groups.setdefault(key, []).append(i)
    classes = sorted(groups.values(), key=len, reverse=True)[:40]
    total = sum(len(m) for m in classes)
    return [(int(rng.choice(m)), len(m) / total) for m in classes]


def build_sample(spec: dict) -> dict:
    t0 = time.time()
    OUT = Path(spec["out"])
    cfg = instruments()
    rng = np.random.default_rng(spec["seed"])
    sysdefs = {s["name"]: s for s in systems()}
    sd = sysdefs[spec["system"]]
    cif, structure = load_structures()[spec["system"]][0]
    absorber, edge = sd["absorber"], sd["edge"]
    theta_d = cfg["debye_temperature_K"][THETA_ALIAS.get(sd["name"], sd["name"])]
    temp = cfg["xafs"]["temperature_K"]
    fault, detail = spec["fault"], ""
    oxidation = {k: float(v) for k, v in sd["oxidation_state"].items()}
    valences = {oxidation[absorber]: 1.0} if sd["name"] != "Co3O4" else {2.0: 1 / 3, 3.0: 2 / 3}
    phases = [{"name": sd["name"], "space_group": None, "fraction": 1.0, "source": cif}]

    # -- model -----------------------------------------------------------------------------------------
    structure = structure.copy()
    if fault == "low_concentration_dopant":
        structure.scale_lattice(structure.volume * (1 - 0.071 * 0.04) ** 3)  # Vegard toward PtNi for 4 % Ni
    if fault == "mixed_oxidation_states":
        x = float(rng.uniform(0.06, 0.12))  # CeO2-x
        structure.scale_lattice(structure.volume * (1 + 0.05 * x) ** 3)
    a = structure.lattice.a
    if spec["form"] == "bulk":
        reps = [int(np.ceil(26.0 / x)) for x in structure.lattice.abc]
        atoms = M.ordered_supercell(structure, reps, rng)
        center_only = min(atoms.cell.lengths()) / 2 - cfg["xafs"]["cluster_radius_A"] - 0.5
    else:
        center_only = None
        if spec["shape"] in M.FCC_SHAPES and sd["kind"] in ("metal", "alloy"):
            minor = [el for el in sd["oxidation_state"] if el != "Pt"]
            if sd["name"] == "Pt3Co":
                atoms = M.fcc_cluster(spec["shape"], ["Co", "Pt"], a, spec["size_nm"], structure, alloy=True)
            else:
                atoms = M.fcc_cluster(spec["shape"], "Pt", a, spec["size_nm"], structure)
                if minor:  # disordered A1 alloy (PtNi)
                    atoms = M.substitute(atoms, "Pt", minor[0], 0.5, rng)
        else:
            atoms = M.sphere_cut(structure, spec["size_nm"], rng)
    if fault == "alloy_segregation":
        minor = next(el for el in sd["oxidation_state"] if el != "Pt")
        atoms = M.segregate(atoms, minor, "Pt", rng)
        detail = f"{minor} enriched in the core, Pt-rich shell (same overall composition)"
    if fault == "low_concentration_dopant":
        atoms = M.substitute(atoms, "Pt", "Ni", 0.04, rng)
        detail = "4 % Ni substituted at random on Pt sites (lattice contracted by Vegard's law)"
        oxidation["Ni"] = 0.0
    if fault == "oxide_shell":
        coverage = float(rng.uniform(0.5, 0.9))
        atoms, n_ox = M.add_oxide_shell(atoms, "Pt", rng, coverage)
        # per-Pt valence from its Pt-O bonds: 0.5 v.u. each at 2.0 Å (four bonds of 2.02 Å make Pt2+ in PtO), at most 2
        from scipy.spatial import cKDTree
        sym = np.array(atoms.get_chemical_symbols())
        pos = atoms.get_positions()
        n_o = np.array([len(nb) for nb in cKDTree(pos[sym == "O"]).query_ball_point(pos[sym == "Pt"], r=2.15)]) if (sym == "O").any() else np.zeros((sym == "Pt").sum())
        val = np.minimum(2.0, 0.5 * n_o)
        valences = {float(v): float(np.mean(val == v)) for v in np.unique(val)}
        f = float(np.mean(n_o > 0))
        oxidation["Pt"] = float(val.mean())
        oxidation["O"] = -2.0
        phases = [{"name": sd["name"], "space_group": None, "fraction": 1 - f, "source": cif},
                  {"name": "PtO surface oxide (disordered)", "space_group": None, "fraction": f, "source": "planted"}]
        detail = (f"{int((n_o > 0).sum())} surface Pt atoms ({100 * f:.0f} % of Pt) bonded to O at 2.0 Å (PtO-like layer, "
                  f"{n_o[n_o > 0].mean():.1f} O per oxidised Pt, mean Pt valence {val.mean():.2f})")
    if fault == "mixed_oxidation_states":
        n_o = sum(1 for s in atoms.get_chemical_symbols() if s == "O")
        atoms, removed = M.remove_fraction(atoms, "O", x / 2, rng)
        n_ce = sum(1 for s in atoms.get_chemical_symbols() if s == "Ce")
        f3 = min(1.0, 2 * removed / n_ce)
        valences = {3.0: f3, 4.0: 1 - f3}
        oxidation["Ce"] = 4 - f3
        detail = f"{removed} of {n_o} O removed (CeO2-x, x={x:.3f}); {100 * f3:.0f} % Ce3+, lattice expanded"
    if fault == "multi_domain":
        detail = "icosahedral particle: 20 twinned tetrahedral domains, coherent domains smaller than the particle"
    if fault == "wrong_phase_candidate":
        detail = f"sample is {sd['name']}, a polymorph that is not in the analysis candidate library"
    label = sd["formula"]
    if fault == "mislabeled_metadata":
        others = [s for s in sysdefs.values() if s.get("library", True) and s["formula"] != sd["formula"]]
        label = others[spec["index"] % len(others)]["formula"]
        detail = f"metadata says {label}; the sample is {sd['formula']}"

    symbols = atoms.get_chemical_symbols()
    elements = sorted(set(symbols))
    uiso = {el: debye_uiso(S.mass(el), theta_d, temp) for el in elements}
    heavy = max(elements, key=lambda el: S.mass(el))
    density = 1 / M.volume_per_atom(structure)  # atoms per Å³ of the bulk phase

    # -- ground truth shells --------------------------------------------------------------------------------
    if spec["form"] == "bulk":
        shells = first_shells(structure, absorber)
    else:
        shells = M.cluster_shells(atoms, absorber)
    r1 = min(s["R_A"] for s in shells)
    for s in shells:
        theta = cfg.get("pair_debye_temperature_K", {}).get(f"{absorber}-{s['neighbor']}", theta_d)
        s["sigma2"] = sigma2_correlated_debye(s["R_A"], S.mass(absorber), S.mass(s["neighbor"]), theta, temp, density)
        s.setdefault("absorber", absorber)

    sample_dir = OUT / "samples" / spec["sample_id"]
    sample_dir.mkdir(parents=True, exist_ok=True)
    params: dict = {}

    # -- XRD -------------------------------------------------------------------------------------------
    x = cfg["xrd"]
    tt = np.arange(x["two_theta"]["min"], x["two_theta"]["max"] + 1e-9, x["two_theta"]["step"])
    cag = {k: S._u(rng, v) for k, v in x["caglioti"].items()}
    if spec["form"] == "bulk":
        cryst = S._u(rng, x["bulk_crystallite_nm"])
        clean = S.xrd_bulk(structure, tt, x["wavelength_A"], cag, cryst, {el: S.biso_of(u) for el, u in uiso.items()})
        params["crystallite_nm"] = cryst
    else:
        clean = S.xrd_cluster(atoms, tt, x["wavelength_A"], cag, S.biso_of(uiso[heavy]))
    counts_max = float(np.exp(rng.uniform(*np.log(x["counts_max"]))))
    inten, sig = S.xrd_measure(tt, clean, rng, x["background"], counts_max)
    np.savetxt(sample_dir / "xrd.xy", np.c_[tt, inten, sig], fmt="%.4f %.2f %.3f",
               header=f"x=2theta_deg wavelength_A={x['wavelength_A']}\ncolumns: 2theta_deg intensity sigma")
    params.update({"caglioti": cag, "counts_max": counts_max})

    # -- PDF -------------------------------------------------------------------------------------------
    p = cfg["pdf"]
    r = np.arange(p["r"]["min"], p["r"]["max"] + 1e-9, p["r"]["step"])
    qmax, qdamp = S._u(rng, p["qmax"]), S._u(rng, p["qdamp"])
    if spec["form"] == "bulk":
        qbroad, delta2 = S._u(rng, p["qbroad"]), S._u(rng, p["delta2"])
        g = S.pdf_bulk(structure, r, qmax, qdamp, qbroad, uiso, delta2)
    else:
        qbroad, delta2 = 0.0, 0.0
        g = S.pdf_cluster(atoms, r, p["qmin"], qmax, qdamp, S.biso_of(uiso[heavy]))
    g_obs, g_sig = S.pdf_measure(r, g, rng, p["qmin"], qmax, S._u(rng, p["noise_rel"]))
    np.savetxt(sample_dir / "pdf.gr", np.c_[r, g_obs, g_sig], fmt="%.3f %.6f %.6f",
               header=f"qmax={qmax:.3f} qdamp={qdamp:.4f} qbroad={qbroad:.4f} qmin={p['qmin']}\ncolumns: r_A G sigma")
    params.update({"qmax": qmax, "qdamp": qdamp, "qbroad": qbroad, "delta2": delta2, "uiso": uiso})

    # -- XAFS ------------------------------------------------------------------------------------------
    xa = cfg["xafs"]
    kmax = S.kmax_for(absorber, edge, xa["k"]["max"])
    k = np.arange(0, kmax + 1e-9, xa["k"]["step"])
    s02_true = xa["s02"][absorber]
    s02_meta = float(s02_true + rng.uniform(-xa["s02_calibration_error"], xa["s02_calibration_error"]))
    e0_shift = S._u(rng, xa["e0_shift_eV"])
    sites = _env_classes(atoms, absorber, r1, center_only, rng)
    chi = np.zeros_like(k)
    pos = atoms.get_positions()
    for i, w in sites:
        chi += w * S.exafs_chi(symbols, pos, absorber, edge, [i], s02_true, theta_d, temp, density, k,
                               xa["cluster_radius_A"], xa["rmax_path_A"], cfg.get("pair_debye_temperature_K"))
    noise = S._u(rng, xa["noise_chi"])
    energy, mu, e_edge = S.mu_spectrum(k, chi, absorber, edge, valences, xa["xanes"], e0_shift, kmax, rng, noise)
    files = ["xrd.xy", "pdf.gr"]
    if "xafs" in spec["techniques"]:
        np.savetxt(sample_dir / "xafs_mu.dat", np.c_[energy, mu], fmt="%.3f %.6f", header=f"edge={absorber}_{edge}\ncolumns: energy_eV mu")
        np.savetxt(sample_dir / "xafs_chi.k", np.c_[k, chi + rng.normal(0, noise, len(k))], fmt="%.3f %.6f",
                   header=f"edge={absorber}_{edge}\ncolumns: k_inv_A chi")
        files += ["xafs_mu.dat", "xafs_chi.k"]
    else:  # kept out of the sample folder; used only to score virtual XAFS
        hidden = OUT / "hidden" / spec["sample_id"]
        hidden.mkdir(parents=True, exist_ok=True)
        np.savetxt(hidden / "xafs_chi.k", np.c_[k, chi], fmt="%.3f %.6f", header=f"edge={absorber}_{edge} (noise-free, hidden)")
    params.update({"s02_true": s02_true, "e0_shift": e0_shift, "edge_eV": e_edge, "chi_noise": noise,
                   "absorber_classes": len(sites), "valences": {str(k_): v for k_, v in valences.items()}})

    lat = dict(zip(("a", "b", "c", "alpha", "beta", "gamma"), (round(v, 5) for v in structure.lattice.parameters)))
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    phases[0]["space_group"] = SpacegroupAnalyzer(structure, symprec=0.1).get_space_group_symbol()
    sample = {
        "sample_id": spec["sample_id"],
        "composition": label,
        "techniques": spec["techniques"],
        "instrument": {
            "xrd": {"wavelength_A": x["wavelength_A"], "two_theta_range": [float(tt[0]), float(tt[-1])], "caglioti_deg2": cag},
            "pdf": {"qmax": round(qmax, 3), "qdamp": round(qdamp, 4), "qbroad": round(qbroad, 4), "qmin": p["qmin"]},
            "xafs": {"edge": f"{absorber} {edge}", "s02": round(s02_meta, 3), "temperature_K": temp, "kmax": round(kmax, 2)},
        },
        "origin": "simulated",
        "ground_truth": {
            "phases": phases, "lattice": lat, "size_nm": round(M.equivalent_diameter_nm(atoms, structure), 3) if spec["form"] != "bulk" else None,
            "shells": [{k_: (round(v, 5) if isinstance(v, float) else v) for k_, v in s.items()} for s in shells],
            "oxidation_state": {k_: round(v, 3) for k_, v in oxidation.items()},
            "notes": f"{spec['form']}{' ' + spec['shape'] if spec['shape'] else ''}, {len(atoms)} atoms, system {sd['name']}",
        },
        "faults": [{"type": fault, "detail": detail}] if fault else [],
    }
    (sample_dir / "sample.json").write_text(json.dumps(sample, indent=2))
    files.append("sample.json")
    params_hash = hashlib.sha256(json.dumps({**{k: v for k, v in spec.items() if k != "out"}, **params}, sort_keys=True, default=str).encode()).hexdigest()[:16]
    log.info("%s %-14s %-12s %-20s %5d atoms %4.1fs", spec["sample_id"], sd["name"], spec["form"], fault or "-", len(atoms), time.time() - t0)
    src = next(r for r in csv.DictReader((ROOT / "data" / "manifest.csv").open()) if r.get("cif_file") == cif)
    return {"sample_id": spec["sample_id"], "source": f"{src['source']}:{src['source_id']}", "licence": src["licence"],
            "generator": "concord.data_builder v1", "params_hash": params_hash, "split": split_of(spec),
            **{f"sha256_{f}": _hash(sample_dir / f) for f in files}}


def write_references():
    """Simulated XANES valence standards (same edge model as the samples, lower fidelity)."""
    xanes = instruments()["xafs"]["xanes"]
    ref = OUT / "references"
    ref.mkdir(parents=True, exist_ok=True)
    edges = {s["absorber"]: s["edge"] for s in systems()}
    for el, vals in VALENCE_STANDARDS.items():
        for v, (e, n) in S.standards(el, edges[el], vals, xanes).items():
            np.savetxt(ref / f"{el}_v{v:g}.dat", np.c_[e, n], fmt="%.3f %.6f", header=f"simulated {el} {edges[el]} standard, valence {v:g}")


def _init_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S", force=True)


def main(n: int, workers: int, out: Path = OUT):
    global OUT
    OUT = out
    specs = [{**s, "out": str(out)} for s in plan(n)]
    OUT.mkdir(parents=True, exist_ok=True)
    old = {}
    if (OUT / "manifest.csv").exists():
        old = {r["sample_id"]: r for r in csv.DictReader((OUT / "manifest.csv").open())}
    todo = [s for s in specs if not (s["sample_id"] in old and (OUT / "samples" / s["sample_id"] / "sample.json").exists())]
    log.info("%d samples planned, %d to build", len(specs), len(todo))
    write_references()
    with mp.get_context("spawn").Pool(workers, initializer=_init_logging) as pool:
        rows = list(pool.imap_unordered(build_sample, todo))
    allrows = sorted([*[r for sid, r in old.items() if sid in {s["sample_id"] for s in specs} and sid not in {r["sample_id"] for r in rows}], *rows],
                     key=lambda r: r["sample_id"])
    with (OUT / "manifest.csv").open("w", newline="") as fh:
        fields = sorted({k for r in allrows for k in r}, key=lambda k: (not k.startswith("sample_id"), k.startswith("sha256"), k))
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(allrows)
    splits = {"train": [], "val": [], "test": [], "faults": []}
    for s in specs:
        splits[split_of(s)].append(s["sample_id"])
    (OUT / "splits.json").write_text(json.dumps(splits, indent=1))
    log.info("done: %s", {k: len(v) for k, v in splits.items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    _init_logging()
    main(args.n, args.workers, Path(args.out))
