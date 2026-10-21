"""FEFF6L (bundled with xraylarch) for EXAFS paths of arbitrary clusters, with an on-disk cache.

Used both to simulate spectra (data builder, virtual XAFS) and to get scattering paths for shell fits.
"""
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from larch.xafs import feffpath
from larch.xafs.feffrunner import find_exe
from pymatgen.core import Element

from concord.config import ROOT

CACHE = ROOT / ".cache" / "feff"
HOLE = {"K": 1, "L1": 2, "L2": 3, "L3": 4}
HBAR2_KB_AMU = 48.508  # ħ²/(k_B·amu) in Å²·K


def feff_input(symbols: list[str], positions: np.ndarray, absorber: int, edge: str, rmax_path: float = 5.5,
               nleg: int = 3, title: str = "concord") -> str:
    """feff.inp for a cluster; positions in Å, absorber index into the lists. One potential per element."""
    pos = np.asarray(positions, float) - np.asarray(positions[absorber], float)
    ipot = {el: i + 1 for i, el in enumerate(sorted({s for j, s in enumerate(symbols) if j != absorber}))}
    lines = [f"TITLE {title}", f"HOLE {HOLE[edge]} 1.0", "CONTROL 1 1 1 1", "PRINT 0 0 0 0",
             f"RMAX {rmax_path:.2f}", f"NLEG {nleg}", "POTENTIALS", f"  0 {Element(symbols[absorber]).Z} {symbols[absorber]}"]
    lines += [f"  {i} {Element(el).Z} {el}" for el, i in ipot.items()]
    lines.append("ATOMS")
    order = np.argsort(np.linalg.norm(pos, axis=1))
    for i in order:
        lines.append(f"  {pos[i, 0]:10.5f} {pos[i, 1]:10.5f} {pos[i, 2]:10.5f} {0 if i == absorber else ipot[symbols[i]]}")
    lines.append("END")
    return "\n".join(lines) + "\n"


def run_feff(inp: str) -> list[Path]:
    """Run FEFF6L once per distinct input (cached by content hash); returns the feffNNNN.dat path files."""
    key = hashlib.sha256(inp.encode()).hexdigest()[:20]
    folder = CACHE / key
    if not (folder / "done").exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix="run_", dir=CACHE))
        (tmp / "feff.inp").write_text(inp)
        proc = subprocess.run([str(find_exe("feff6l"))], cwd=tmp, capture_output=True, text=True, timeout=600)
        if not list(tmp.glob("feff0001.dat")):
            raise RuntimeError(f"FEFF6L produced no paths (exit {proc.returncode}): {proc.stdout[-300:]}")
        shutil.rmtree(folder, ignore_errors=True)
        tmp.rename(folder)
        (folder / "done").write_text("ok")
    return sorted(folder.glob("feff0*.dat"))


def cluster_around(symbols: list[str], positions: np.ndarray, center: int, radius: float = 6.5) -> tuple[list[str], np.ndarray, int]:
    pos = np.asarray(positions, float)
    d = np.linalg.norm(pos - pos[center], axis=1)
    keep = np.where(d <= radius)[0]
    return [symbols[i] for i in keep], pos[keep], int(np.where(keep == center)[0][0])


def debye_uiso(mass_amu: float, theta_d: float, temperature: float = 300.0) -> float:
    """Uncorrelated mean-square displacement (Å²) from the Debye model (Willis & Pryor, Thermal Vibrations in Crystallography)."""
    x = theta_d / temperature
    t = np.linspace(1e-6, x, 400)
    phi = np.trapezoid(t / np.expm1(t), t) / x
    return float(3 * HBAR2_KB_AMU / (mass_amu * theta_d) * (phi / x + 0.25))


def load_paths(files: list[Path], reff_max: float | None = None) -> list:
    paths = [feffpath(str(f)) for f in files]
    return [p for p in paths if reff_max is None or p.reff <= reff_max]


def sigma2_correlated_debye(r: float, mass1: float, mass2: float, theta_d: float, temperature: float, density: float) -> float:
    """MSRD σ² (Å²) of a pair at distance r in the correlated Debye model (Sevillano, Meuth & Rehr,
    Phys. Rev. B 20, 4908 (1979), doi:10.1103/PhysRevB.20.4908), with M = 2μ for unlike atoms.
    Larch's own implementation is a Fortran dylib that only exists for x86_64 on macOS.
    """
    m_eff = 2 * mass1 * mass2 / (mass1 + mass2)
    k_d = (6 * np.pi ** 2 * density) ** (1 / 3)
    u = np.linspace(1e-6, 1.0, 2000)
    x = u * k_d * r
    integrand = u / np.tanh(u * theta_d / (2 * temperature)) * (1 - np.sin(x) / x)
    return float(3 * HBAR2_KB_AMU / (m_eff * theta_d) * np.trapezoid(integrand, u))


def path_sigma2(path, theta_d: float, temperature: float, density: float) -> float:
    """Correlated-Debye σ² for a FEFF path: the absorber–scatterer pair at reff (multiple scattering approximated by reff)."""
    absorber, scatterer = path.geom[0][0], path.geom[1][0]
    return sigma2_correlated_debye(float(path.reff), Element(absorber).atomic_mass, Element(scatterer).atomic_mass,
                                   theta_d, temperature, density)
