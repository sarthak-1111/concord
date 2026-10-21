"""Structure models for the dataset: ordered bulk supercells and nanoparticles.

fcc metals and alloys use ASE cluster tools (cuboctahedra, regular truncated octahedra, icosahedra; L1_2 order
via `alloy=True`); every system also supports spherical cuts. Oxide cuts keep complete cation coordination.
"""
import numpy as np
from ase import Atoms
from ase.cluster import Icosahedron, Octahedron
from pymatgen.core import Structure
from scipy.spatial import cKDTree

from concord.tools.pdfcalc import site_label

FCC_SHAPES = {"cuboctahedron", "truncated_octahedron", "icosahedron"}


def ordered_supercell(structure: Structure, reps, rng: np.random.Generator) -> Atoms:
    """Supercell as ASE Atoms; partially occupied sites get one species drawn by occupancy."""
    sc = structure * reps
    symbols = []
    for site in sc:
        species = list(site.species.items())
        if len(species) == 1 and species[0][1] >= 0.999:
            symbols.append(species[0][0].symbol)
        else:
            p = np.array([occ for _, occ in species], float)
            symbols.append(species[rng.choice(len(species), p=p / p.sum())][0].symbol)
    return Atoms(symbols=symbols, positions=sc.cart_coords, cell=sc.lattice.matrix, pbc=True)


def volume_per_atom(structure: Structure) -> float:
    return structure.volume / sum(sum(s.species.values()) for s in structure)


def equivalent_diameter_nm(atoms: Atoms, structure: Structure) -> float:
    """Diameter of the sphere with the particle's volume (atoms × bulk volume per atom)."""
    return float((6 * len(atoms) * volume_per_atom(structure) / np.pi) ** (1 / 3) / 10)


def _fcc_cluster(shape: str, symbol, n: int, a: float, alloy: bool) -> Atoms:
    if shape == "cuboctahedron":
        return Octahedron(symbol, length=2 * n + 1, cutoff=n, latticeconstant=a, alloy=alloy)
    if shape == "truncated_octahedron":
        return Octahedron(symbol, length=3 * n + 1, cutoff=n, latticeconstant=a, alloy=alloy)
    if shape == "icosahedron":
        return Icosahedron(symbol, noshells=n + 1, latticeconstant=a)
    raise ValueError(shape)


def fcc_cluster(shape: str, symbol, a: float, target_nm: float, structure: Structure, alloy: bool = False) -> Atoms:
    """ASE cluster whose equivalent diameter is closest to target_nm."""
    best = None
    for n in range(1, 40):
        atoms = _fcc_cluster(shape, symbol, n, a, alloy)
        d = equivalent_diameter_nm(atoms, structure)
        if best is None or abs(d - target_nm) < abs(best[0] - target_nm):
            best = (d, atoms)
        if d > target_nm:
            break
    atoms = best[1]
    atoms.center()
    return atoms


def sphere_cut(structure: Structure, d_nm: float, rng: np.random.Generator, anions=("O",)) -> Atoms:
    """Spherical particle cut from the bulk. Cations inside the sphere are kept with all their anion neighbours."""
    radius = d_nm * 5.0
    reps = [int(np.ceil((2 * radius + 12) / x)) for x in structure.lattice.abc]
    bulk = ordered_supercell(structure, reps, rng)
    pos = bulk.get_positions()
    center = bulk.cell.cartesian_positions([0.5, 0.5, 0.5]) + rng.uniform(-0.5, 0.5, 3)  # vary the surface termination
    dist = np.linalg.norm(pos - center, axis=1)
    sym = np.array(bulk.get_chemical_symbols())
    is_anion = np.isin(sym, anions)
    keep = (~is_anion) & (dist <= radius)
    if is_anion.any() and keep.any():
        cat = pos[keep]
        bond = 1.25 * min(d for d in _nn_cation_anion(structure, anions))
        cand = np.where(is_anion & (dist <= radius + bond))[0]
        near = [i for i in cand if np.min(np.linalg.norm(cat - pos[i], axis=1)) <= bond]
        keep[near] = True
    elif not keep.any():
        keep = dist <= radius
    atoms = Atoms(symbols=sym[keep].tolist(), positions=pos[keep] - center)
    atoms.center(vacuum=5.0)
    return atoms


def _nn_cation_anion(structure: Structure, anions) -> list[float]:
    out = []
    for site in structure:
        if site_label(site) not in anions:
            out += [nb.nn_distance for nb in structure.get_neighbors(site, 3.2) if site_label(nb) in anions]
    return out or [2.0]


def segregate(atoms: Atoms, minor: str, major: str, rng: np.random.Generator, strength: float = 0.8) -> Atoms:
    """Move the minor element to the core: same composition, radial ordering (planted 'alloy segregation')."""
    out = atoms.copy()
    sym = np.array(out.get_chemical_symbols())
    n_minor = int((sym == minor).sum())
    r = np.linalg.norm(out.get_positions() - out.get_positions().mean(axis=0), axis=1)
    score = r * strength + rng.uniform(0, r.max() * (1 - strength) + 1e-9, len(r))
    sym[:] = major
    sym[np.argsort(score)[:n_minor]] = minor
    out.set_chemical_symbols(sym.tolist())
    return out


def _hemisphere(n: np.ndarray, count: int = 60) -> np.ndarray:
    """Fibonacci directions on the unit sphere with d·n > 0.15 (the outward hemisphere of a surface atom)."""
    i = np.arange(2 * count) + 0.5
    phi, z = np.pi * (1 + 5 ** 0.5) * i, 1 - 2 * i / (2 * count)
    d = np.c_[np.sqrt(1 - z ** 2) * np.cos(phi), np.sqrt(1 - z ** 2) * np.sin(phi), z]
    return d[d @ n > 0.15]


def add_oxide_shell(atoms: Atoms, metal: str, rng: np.random.Generator, coverage: float, bond: float = 2.0,
                    per_metal: int = 4) -> tuple[Atoms, int]:
    """Planted 'oxide shell': a PtO-like surface layer. Each chosen under-coordinated surface metal atom ends up with
    up to `per_metal` O at `bond` Å (four for Pt2+ as in PtO, bond valence ≈ 0.5 each), placed in its outward
    hemisphere at least 1.8 Å from other metal atoms (bridging O) and 2.5 Å from other O; O already bonded to a
    neighbour count."""
    pos = atoms.get_positions()
    center = pos.mean(axis=0)
    tree = cKDTree(pos)
    cn = np.array([len(nb) - 1 for nb in tree.query_ball_point(pos, r=3.1)])
    surface = np.where((cn < 10) & (np.array(atoms.get_chemical_symbols()) == metal))[0]
    chosen = surface[rng.random(len(surface)) < coverage]
    new: list[np.ndarray] = []
    for i in chosen:
        n = (pos[i] - center) / np.linalg.norm(pos[i] - center)
        have = sum(1 for o in new if abs(np.linalg.norm(o - pos[i]) - bond) < 0.15)
        for d in rng.permutation(_hemisphere(n)):
            if have >= per_metal:
                break
            o = pos[i] + bond * d
            near = tree.query(o, k=2)[0]  # the host must be the nearest metal atom (at `bond`), the next one ≥ 1.8 Å away
            if near[0] < bond - 1e-6 or near[1] < 1.8 or (new and np.min(np.linalg.norm(np.asarray(new) - o, axis=1)) < 2.5):
                continue
            new.append(o)
            have += 1
    out = atoms + Atoms("O" * len(new), positions=new) if new else atoms.copy()
    return out, len(chosen)


def substitute(atoms: Atoms, host: str, dopant: str, fraction: float, rng: np.random.Generator) -> Atoms:
    out = atoms.copy()
    sym = np.array(out.get_chemical_symbols())
    hosts = np.where(sym == host)[0]
    sym[rng.choice(hosts, size=max(1, int(round(fraction * len(hosts)))), replace=False)] = dopant
    out.set_chemical_symbols(sym.tolist())
    return out


def remove_fraction(atoms: Atoms, element: str, fraction: float, rng: np.random.Generator) -> tuple[Atoms, int]:
    sym = np.array(atoms.get_chemical_symbols())
    idx = np.where(sym == element)[0]
    gone = rng.choice(idx, size=int(round(fraction * len(idx))), replace=False)
    keep = np.setdiff1d(np.arange(len(atoms)), gone)
    return atoms[keep], len(gone)


def cluster_shells(atoms: Atoms, absorber: str, rmax: float = 4.0, tol: float = 0.25) -> list[dict]:
    """First coordination shell per neighbour element, averaged over every absorber atom of a finite cluster
    (so surface truncation is included)."""
    pos = atoms.get_positions()
    sym = np.array(atoms.get_chemical_symbols())
    abs_idx = np.where(sym == absorber)[0]
    tree = cKDTree(pos)
    dist, nb_el = [], []
    for i, nbs in zip(abs_idx, tree.query_ball_point(pos[abs_idx], r=rmax)):
        nbs = [j for j in nbs if j != i]
        dist.append(np.linalg.norm(pos[nbs] - pos[i], axis=1))
        nb_el.append(sym[nbs])
    dist, nb_el = np.concatenate(dist), np.concatenate(nb_el)
    shells = []
    for el in np.unique(nb_el):
        d = dist[nb_el == el]
        first = d[d < d.min() + tol]
        shells.append({"absorber": absorber, "neighbor": str(el), "N": float(len(first) / len(abs_idx)), "R_A": float(first.mean())})
    return sorted(shells, key=lambda s: s["R_A"])
