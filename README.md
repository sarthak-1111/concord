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

Web UI: a conversation with the analyst beside a results workbench. The conversation opens with what the tools found
(from the data, no LLM), streams every run (tools, critic, literature search) as it happens, and answers questions
about the sample from its evidence only: each answer cites evidence ids that open the matching check, fit or panel,
and passes the number guard (a number the evidence lacks is flagged, never hidden). The workbench holds the
cross-check strip under a one-line verdict, interactive fit plots (drag to zoom, a readout of every curve) with the
visual verdicts, the virtual XAFS, the critic review, literature priors and the report, with Markdown and JSON export.
Every failing or warning check offers **Settle this**: one of the critic's deterministic re-runs (another PDF
candidate, a second XRD phase, an EXAFS k-range scan, a probe shell, envelope on or off, size from the strongest
peak), and the re-run's numbers decide. Numbers in the analyst's answers are linked to the evidence value they came
from. Light and dark themes; phone layouts switch between the two panes.

Under every fit plot, **Open in analysis** changes that fit's settings (XRD range, baseline and peak finding; PDF
candidate, r range, Qdamp, envelope; EXAFS k and R windows, k-weight, probe shell) and shows the refit and every
cross-check that would change, in about a second; **Keep and re-analyse** records the settings in the report, and
**Original** restores the analysis before them. For PDF, **Open in preprocessing** reduces the raw total scattering
step by step (raw and container, S(Q), F(Q), G(r)) with Concord's own code (`concord/tools/sq_to_gr.py`) and can
analyse the new G(r) as a new sample; raw I(Q) files can be uploaded directly. When a sample lacks a technique, the
conversation offers to generate it from the fitted model with the GAN's instrument realism, labelled GENERATED, NOT
MEASURED and never used by the checks. Compositions can be picked from a periodic table that marks the elements with
library structures.

```bash
make api    # http://127.0.0.1:8000
make ui     # http://127.0.0.1:3000/console#s0031
```

Your own data in the UI: press **Analyse your own data** in the sidebar (or the upload button in the composer), give
the composition and drop up to four files. Concord reads each one and works out from its content whether it is an XRD
pattern, a PDF, raw I(Q), μ(E) or χ(k), shows a preview and the reading it chose (changeable), and finds the absorption edge
from the energy range of a μ(E) scan. CSV files and files with a text header row are rewritten as plain columns. The
tools run at once and the critic is one click away. Without data: **Try an example** opens an analysed sample, and
**Plan a measurement** (below) tells you what to measure. Values missing from the file headers are assumed and listed. For the XANES valence, put μ(E) of at least
two standards of known valence as `<El>_v<valence>.dat` in a `references/` folder beside the sample folders.

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
| Runtime per sample, mean (s) | 24 | ≤ 120 | pass |
| Virtual EXAFS vs spectrum, median R-factor | 0.0219 | ≤ 0.1 | pass |

Virtual EXAFS against the hidden spectrum (XAFS withheld): median R-factor 0.011  
Faults that only raise a warning: 11% of fault samples.  
With the critic (`make eval-agents`, 19 of 19 runs complete): faults flagged by a check or a re-run-confirmed objection 67%, clean samples flagged 0%, numbers in the agents' prose not found in the evidence: 0, 26 min and 42k tokens per sample.  

Per-sample details: [`results/eval.md`](results/eval.md).
<!-- results:end -->

## What it does

```
sample folder ─► XRD   peaks, phase ranking, Scherrer/WH size (Voigt, instrument-corrected)
               ► PDF   srfit refinement of every candidate: lattice, U_iso, size
               ► EXAFS first-shell fit on FEFF paths of the PDF model (+ probe shells)
               ► XANES valence (standards), bond-valence sum of the refined structure
               ► virtual EXAFS from the PDF model (PREDICTED, NOT MEASURED)
               ► checks C1–C7
               ─► fitting agents: XRD, PDF, EXAFS (refit, keep or revert, re-run the analysis)
               ─► visual inspection of each fit ─► generator ⇄ critic (≤ 3 rounds) ─► report
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
- **Fitting agents.** One gpt-oss agent per technique drives its fit (`concord/agents/fitter.py`). Each turn it tries
  at most two new settings (XRD 2θ window, baseline stiffness, peak thresholds; PDF candidate phase, r window,
  nanoparticle envelope; EXAFS k window, R max, k-weight, light-neighbour probe shell) or accepts. A tested,
  deterministic refit computes every number. Guardrails in code: values clipped to their ranges, at most 3 refits per
  technique, no data window below 70 % of its default span, a refit kept only if its metric (PDF Rw, EXAFS R-factor,
  XRD score) improves by at least 2 %, PDF lattice drift at most 3 %, Qdamp never fitted. The kept settings re-run the
  whole analysis before visual inspection; the steps are shown under each fit plot.
- **Generator–critic loop.** The critic has its own prompt, high thinking and only the evidence. Every objection
  must cite evidence ids; it can ask for one of seven re-runs (another PDF candidate, envelope on/off, a probe shell,
  a k-range scan, size from the strongest peak, a second XRD phase, a zoomed visual inspection), and the re-run
  decides. A re-run that cannot run leaves the objection unsettled. A number guard rejects any number in the prose
  that is not in the evidence.
- **Visual inspection.** Fit plots are rendered deterministically (XRD with reflection ticks, PDF, EXAFS in k and R,
  and a zoom on the largest misfit). PDF fits are judged by the eye module when `EYE_MODULE_PATH` is set (the PDF
  agent's residual reviewer, below); XRD and EXAFS fits, and PDF without it, by an open fallback (residual features
  calibrated on the development split + gpt-oss judge). A fit is accepted only if the
  visual and the numerical and physicality criteria all pass. A rejected fit gets one fix from a fixed menu (second
  XRD phase, PDF envelope on/off, EXAFS O shell); the fix is kept only if its re-run confirms it and the verdict does
  not get worse, otherwise it is reverted (at most 3 iterations).
- **Literature priors.** OpenAlex, Crossref and arXiv abstracts, local embeddings and FAISS; values are read with
  fixed patterns and kept with their DOI and sentence. They are context for the critic and the report, never fit
  constraints for this sample.

## Plan a measurement, and the realism GANs

**Plan a measurement** takes a composition and a particle size, simulates XRD, PDF and EXAFS for every candidate
phase with Concord's own simulators, and ranks the techniques by how different the closest pair of candidates looks
(RMS difference of curves scaled to unit RMS). Everything is labelled SIMULATED, NOT MEASURED and is never analysed
as data. With **Instrument realism**, the realism GANs of the companion repository
[Concord Forge](https://github.com/sarthak-1111/GAN-Hackathon) add the background, gain and noise a real instrument
records, and each pair is reported as a multiple of that noise: for Pt3Co at 3 nm, PDF keeps its closest pair 39 times
above the noise while XRD separates Pt from Pt3Co by less than twice the noise. **Real or GAN?** shows a measured
spectrum next to its simulation and the GAN's version of it, and asks which one was measured.

Set `GAN_REPO_PATH` to a clone of that repository (its `generator_ema.pt` weights fetched with Git LFS). The models are
loaded at run time with `torch.load(weights_only=True)` and never copied here. Their limits, from the repository's
own test: a classifier tells GAN output from measured data 66 % of the time for XRD (classical added noise: 81 %), but
95 % for PDF and 91 % for EXAFS, no better than classical noise. EXAFS realism covers the Pt, Co, Ni, Fe and Cu edges
only. Without the GANs the planner works with clean simulations.

## With or without the eye module

Set `EYE_MODULE_PATH` in `.env` to the eye module. It is loaded at run time through `concord/vision/eye_adapter.py`
and never copied into this repository. The eye is the reviewer of the PDF agent (`pdf_backend`,
`app/modules/agent/residual.py`, private): it reads a PDF difference curve zone by zone and names the cause (lattice
drift, scale, envelope, correlated motion, wrong phase). On the development split it rejected 2 of 44 clean PDF fits
and 20 of 37 faulty ones. An image-judging module with an `inspect(image, context)` entry point also works. Without
the eye, the open fallback judges every fit; everything else is the same.

## Limitations

- The dataset is simulated (open structures, FEFF, Debye-scattering and XRD simulation); real data will expose
  effects it lacks (preferred orientation, multiple scattering beyond FEFF's paths, beam damage).
- XANES uses a simple edge model with valence standards; oxide valences carry systematic offsets up to about 0.5.
- Sub-monolayer oxide shells and dopants of a few percent sit at the detection limit of these techniques; the
  planted low-concentration dopant is not detected.
- Pt3Co and Pt are hard to tell apart by PDF alone for small particles; C7 and EXAFS help, not always.
- The number guard checks that every number in the prose is in the evidence, not that it is attached to the right
  quantity. On s0031 the analyst quoted the C5 ratio 0.276 next to the wrong PDF σ², and the critic let it pass.
- The critic picks the re-run itself. On s0024 it rightly objected that C7 passes, then asked for a PDF re-fit that
  does not test that, so the log marks the objection refuted.
- The eye judges PDF fits only; XRD and EXAFS use the open judge. Of the 19 saved critic runs in `results/runs/`,
  s0031 was re-run with the eye; the other 18 were made before it was connected, so their PDF verdicts come from the
  open judge.

## Licence

MIT (see `LICENSE`, `NOTICE`). Structures come from open databases with their licences in `data/manifest.csv`;
literature priors cite their DOI.
