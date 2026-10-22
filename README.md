# Concord

**One command turns XRD, PDF and XAFS data of the same sample into one structural model, with every
cross-technique disagreement checked, explained or flagged.**

Each technique sees a different part of the structure: XRD the long-range order, the PDF the local and
intermediate order, EXAFS the neighbours of one element, XANES its oxidation state. Concord fits all of them with
deterministic, tested code and then checks them against each other (C1–C7). A generator–critic pair of LLM
agents argues over the result, but **numbers decide and the LLM explains**: every number comes from a tool or a
cited source, and disagreements are settled by re-running tools, never by the model.

Concord is a fork of [CrystaLenz](https://github.com/MJRaei/CrystaLenz) (MIT). What is new is listed exactly in
[`docs/PRIOR_WORK.md`](docs/PRIOR_WORK.md).

## Quick start

```bash
make setup                     # uv sync + git hooks (Python 3.12, uv)
cp .env.example .env           # LLM_BASE_URL, LLM_API_KEY (only needed for the agents)
make data                      # build dataset v1 (60 samples) from open structures, then validate it

uv run concord analyze dataset/samples/s0031 --fast   # tools + checks, no LLM, about 30 s
uv run concord analyze dataset/samples/s0031          # + visual inspection + critic loop (gpt-oss)
```

A sample folder holds any of `xrd.xy`, `pdf.gr`, `xafs_mu.dat` / `xafs_chi.k`, and either a `sample.json` or
`--composition Pt3Co`. Techniques are detected from the files present, instrument values from the file headers;
anything assumed is printed. Output: `results/runs/<sample>/report.md`, fit plots, `analysis.json`.

Web UI (sample picker, cross-check panel, fit plots, virtual XAFS, critic log, literature priors, export):

```bash
make api    # http://127.0.0.1:8000
make ui     # http://127.0.0.1:3000/console#s0031
```

Other commands: `uv run concord priors Pt3Co` (literature values with DOIs), `make eval`, `make test`,
`uv run concord health` (LLM endpoint).

## Results

<!-- results:start -->
`make eval` on dataset v1 (test, faults: 10 clean samples, 9 with planted faults), thresholds from `eval/config.yaml`. Overall: **pass**.

| metric | value | threshold | |
|---|---|---|---|
| Phase identification accuracy | 1 | ≥ 0.9 | pass |
| EXAFS bond length, mean abs. error (Å) | 0.00326 | ≤ 0.02 | pass |
| PDF bond length, mean abs. error (Å) | 0.000359 | ≤ 0.02 | pass |
| EXAFS coordination number, mean abs. error | 0.401 | ≤ 1.0 | pass |
| Oxidation state within 0.5 | 1 | ≥ 0.8 | pass |
| Size from XRD, mean rel. error | 0.0989 | ≤ 0.3 | pass |
| Size from PDF, mean rel. error | 0.0385 | ≤ 0.2 | pass |
| Planted faults detected (a check fails) | 0.667 | ≥ 0.6 | pass |
| False alarms on clean samples | 0 | ≤ 0.2 | pass |
| C1–C6 reported for every sample | 1 | ≥ 1.0 | pass |
| Runtime per sample, mean (s) | 24.1 | ≤ 120 | pass |
| Virtual EXAFS vs spectrum, median R-factor | 0.0406 | ≤ 0.1 | pass |

Virtual EXAFS against the hidden spectrum (XAFS withheld): median R-factor 0.010  
Faults that only raise a warning: 11% of fault samples.  

Per-sample details: [`results/eval.md`](results/eval.md).
<!-- results:end -->

## What it does

```
sample folder ─► XRD   peaks, phase ranking, Scherrer/WH size (Voigt, instrument-corrected)
               ► PDF   srfit refinement of every candidate: lattice, U_iso, size
               ► EXAFS first-shell fit on FEFF paths of the PDF model (+ probe shells)
               ► XANES valence (standards), bond-valence sum of the refined structure
               ► virtual EXAFS from the PDF model (PREDICTED, NOT MEASURED)
               ► checks C1–C7 ─► visual inspection of each fit ─► generator ⇄ critic (≤ 3 rounds) ─► report
```

| Check | Compares |
|---|---|
| C1 | XRD phase ranking vs PDF refinement; lattice drift from the database value |
| C2 | EXAFS bond lengths vs the PDF-refined model |
| C3 | EXAFS coordination numbers vs the model (with surface truncation); shells the model lacks |
| C4 | XANES valence vs the bond-valence sum; mixed valence when both move away from the formal value |
| C5 | EXAFS σ² vs PDF pair widths (correlated vs uncorrelated motion, explained rather than flagged) |
| C6 | XRD vs PDF size (volume- vs number-weighted, multi-domain particles) |
| C7 | Joint score of each candidate: simulated XRD, PDF and EXAFS together |

- **Virtual XAFS.** When XAFS is missing, an ensemble of PDF-equivalent models (lattice, displacement, size and
  equally good candidates) is run through FEFF; the spread is shown as a band, labelled PREDICTED, NOT MEASURED,
  with a measurement recommendation. When XAFS was measured, the prediction is a consistency check.
- **Generator–critic loop.** The critic has its own prompt, high thinking and only the evidence. Every objection
  must cite evidence ids; it can ask for one of five re-runs (another candidate, envelope on/off, a probe shell, a
  k-range scan, size from the strongest peak), and the re-run decides. A number guard rejects any number in the
  prose that is not in the evidence.
- **Visual inspection.** Fit plots are rendered deterministically and judged by the eye module when
  `EYE_MODULE_PATH` is set, otherwise by an open fallback (residual features + gpt-oss judge). A fit is accepted only
  if the visual and numerical criteria both pass.
- **Literature priors.** OpenAlex, Crossref and arXiv abstracts, local embeddings and FAISS; values are read with
  fixed patterns and kept with their DOI and sentence. They are context for the critic and the report, never fit
  constraints for this sample.

## With or without the eye module

Set `EYE_MODULE_PATH` in `.env` to the eye module (a file or package). It is loaded at run time through
`concord/vision/eye_adapter.py` and never copied into this repository. Without it, the open fallback judges the
plots from residual statistics; everything else is the same.

## Limitations

- The dataset is simulated (open structures, FEFF, Debye-scattering and XRD simulation); real data will expose
  effects it lacks (preferred orientation, multiple scattering beyond FEFF's paths, beam damage).
- XANES uses a simple edge model with valence standards; oxide valences carry systematic offsets up to about 0.5.
- Sub-monolayer oxide shells and dopants of a few percent sit at the detection limit of these techniques; the
  planted low-concentration dopant is not detected.
- Pt3Co and Pt are hard to tell apart by PDF alone for small particles; C7 and EXAFS help, not always.
- The eye module interface could not be inspected (the reference repositories were not available), so the adapter
  tries a list of common entry points.
- The reference repositories `pdf_frontend` and `pdf_backend` were not cloned; nothing was taken from them.

## Licence

MIT (see `LICENSE`, `NOTICE`). Structures come from open databases with their licences in `data/manifest.csv`;
literature priors cite their DOI.
