"""Add the raw total-scattering files (pdf_iq.dat, pdf_bkg.dat) to an existing dataset.

Each sample is replayed through the builder's own deterministic simulation (its seeded plan entry) up to the PDF;
only the two raw files are written. The replayed G(r) must match the stored pdf.gr to its printed precision,
which proves the raw data are the ones the stored G(r) came from. Not in manifest.csv: the analysis never reads them.

    uv run python -W ignore scripts/make_raw_pdf.py [--root dataset] [--workers 6]
"""
import argparse
import csv
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from concord.data_builder.build import build_sample, plan  # noqa: E402


def replay(spec: dict) -> tuple[str, float, float]:
    t0 = time.time()
    g = build_sample(spec)["g"]
    stored = np.loadtxt(Path(spec["out"]) / "samples" / spec["sample_id"] / "pdf.gr")[:, 1]
    return spec["sample_id"], float(np.abs(np.round(g, 6) - stored).max()), time.time() - t0


def main(root: Path, workers: int) -> int:
    ids = [r["sample_id"] for r in csv.DictReader((root / "manifest.csv").open())]
    specs = plan(max(int(s[1:]) for s in ids) + 1)
    todo = [{**specs[int(s[1:])], "out": str(root), "raw_pdf_only": True} for s in ids]
    t0, bad = time.time(), []
    with mp.get_context("spawn").Pool(workers) as pool:
        for sid, dev, dt in sorted(pool.imap_unordered(replay, todo)):
            print(f"{sid}  replayed G(r) vs pdf.gr max |dG| {dev:.1e}  {dt:.1f}s")
            if dev > 1.5e-6:  # stored with 6 decimals: an exact replay differs by rounding only
                bad.append(sid)
    print(f"{len(todo)} samples in {time.time() - t0:.0f}s; replay mismatch: {bad or 'none'}")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "dataset"))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    sys.exit(main(Path(a.root), a.workers))
