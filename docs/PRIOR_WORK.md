# Prior work

Judges score only the new work, so this file lists exactly what came from where. It is updated with every commit that
changes the boundary.

## 1. CrystaLenz (forked, MIT)

- Upstream: https://github.com/MJRaei/CrystaLenz, remote `upstream`, forked at commit
  **`dc08f09ac09b3e23a0ff0a13f82a926bc16a242d`** (2026-02-15, "updated the readme"). Full history kept.
- Licence and copyright notice kept in `LICENSE` (MIT, "Copyright (c) 2025 CrystaLens Contributors"); credit in `NOTICE`.

### Taken from CrystaLenz unchanged

| Path | What it is |
|---|---|
| `src/agent.py`, `src/agents/**` (agent graph, prompts), except the files listed below | Google ADK agent graph: root → sequential(parallel(research, XRD), final analyzer) with its XRD and research sub-agents |
| `src/schemas/schemas.py`, `src/data_store/data_store.py` | Output schemas and the in-memory store of the XRD agents |
| `sample_data/*.csv`, `docs/media/workflow.png`, `examples/chunker_test.py` | Sample patterns, figure, chunker demo |

### Changed in the fork

| Change | Where |
|---|---|
| Model `gemini-2.5-flash` → gpt-oss through an ADK `BaseLlm` adapter (`model_for(role)`) | every `src/**/agent.py` |
| Web search: Google Programmable Search → open-access PDFs from OpenAlex and arXiv (no key) | `src/agents/research_agent/sub_agents/paper_miner/tools/search_papers.py` |
| Embeddings: OpenAI `text-embedding-3-large` → local CPU model `BAAI/bge-small-en-v1.5`; FAISS index kept | `src/agents/research_agent/sub_agents/retriever/tools/{create_vector_store,retrieve_data}.py` |
| PDF text: PyMuPDF (AGPL) → pypdf (BSD) | `src/agents/research_agent/sub_agents/paper_miner/tools/extract_texts_from_pdfs.py` |
| XRD tool logic moved into pure functions in `concord/tools/xrd.py`; the ADK tools are thin wrappers around them | `src/agents/xrd_agent/sub_agents/{data_preprocessor,peak_finder,scherrer_and_wh}/tools.py` |
| **Bug fix:** the Voigt model called `voigt(x - center, sigma, gamma)`, i.e. passed sigma/gamma into lmfit's amplitude/center slots, so peak widths were never fitted (fixed at σ=γ=1°) and FWHM/Scherrer sizes were wrong | `concord/tools/xrd.py::_voigt` |
| **Bug fix:** Williamson–Hall regressed β cosθ on 4 sinθ/λ with λ in metres, so the "strain" was ε·λ (~1e-13); now regresses on 4 sinθ and reports dimensionless strain and the intercept size | `concord/tools/xrd.py::scherrer_wh`, `src/schemas/schemas.py` |
| **Bug fix:** Voigt widths capped at 0.2°, which cannot fit nanoparticle peaks (2 nm Pt has FWHM ≈ 4°); fit window now adapts to the peak width | `concord/tools/xrd.py::find_and_fit_peaks` |
| `np.trapz` (removed in numpy 2) → fitted Voigt area | `concord/tools/xrd.py` |
| Reference matching no longer needs Materials Project: reference lines come from any pymatgen structure | `concord/tools/xrd.py::reference_lines`, `match_reference` |
| Upstream tests imported a module path that no longer existed (`src.sub_agents...`) and could not run; ported to the refactored functions with the same assertions | `tests/conftest.py`, `tests/test_xrd_tools.py` (first four tests) |
| API server rewritten for Concord; the run-and-stream protocol (`POST /api/runs`, WebSocket `/api/runs/{id}/stream`) is kept | `backend/app/main.py` |
| Console rewritten as the Concord workbench (`console/page.tsx`), then redesigned as a conversation beside a results workbench; `PlotsView`, `PromptForm`, `EventCard`, the logo and the unused Tailwind v3 config removed; `useRunStream` (CrystaLenz's WebSocket hook) keeps events per run id and reports a closed connection; `layout.tsx` and `globals.css` rewritten; Next.js 14.2.7 → 16.4.0, React 18 → 19.3.0 (14.x has unpatched advisories) | `web/` |
| `requirements.txt` → `pyproject.toml` + `uv.lock` (pinned; uv only resolves releases at least two weeks old) | repo root |

## 2. New in Concord

| Path | What it does |
|---|---|
| `concord/llm/client.py` | LLM client for the bearer-token Ollama endpoint: thinking level per role, timeouts per level, retries with backoff, capability probe (`tools`, `format`) with JSON-in-text fallback and one repair, at most 2 requests in flight, streamed replies (Cloudflare tunnels cut idle requests), tokens and latency in the trace, endpoint address never logged |
| `concord/llm/adk_model.py` | ADK `BaseLlm` adapter, so ADK agents run on gpt-oss |
| `concord/tools/xrd.py` (new parts) | header-aware loader, Caglioti instrument correction, Voigt deconvolution, exact sphere Scherrer constant, width-aware indexing, whole-profile phase ranking, pattern simulation with the size-broadening shape measured on the pattern's own peaks, phase scales refined with a Chebyshev + 1/2θ background |
| `concord/tools/pdfcalc.py`, `concord/tools/pdf.py` | PDF calculator (Debye sum with Q-damping, spherical envelope) and diffpy.srfit refinement of lattice, U_iso, δ2 and particle size |
| `concord/tools/feff.py`, `concord/tools/xafs.py` | FEFF6 paths from structures, correlated-Debye σ², normalisation and background, first-shell EXAFS fit with a structural background for outer shells, probe shells, XANES edge position and linear-combination fitting |
| `concord/tools/virtual_xafs.py` | virtual EXAFS from the PDF model: ensemble band, PREDICTED, NOT MEASURED label, measurement recommendation, scoring against hidden or measured spectra |
| `concord/analysis.py` | deterministic runner: input autodetection, all techniques, bond-valence sums with self-calibrated R0, virtual XAFS, checks |
| `concord/checks.py` | cross-technique checks C1–C7 with tolerances from `config.yaml` |
| `concord/agents/` | evidence bundle with citable ids and number guard; re-run actions that settle objections; ADK pipeline (analysis → fitting agents → visual inspection → generator–critic–resolver loop → reporter) |
| `concord/vision/` | deterministic fit plots (XRD with reflection ticks, PDF, EXAFS in k and R, zoom on the largest misfit), residual features calibrated on the dev split (Durbin–Watson on independent points, structured and concentrated misfit, grouped unexplained diffraction peaks), physicality checks, eye-module adapter, open fallback judge, acceptance rule, fix loop (a menu of deterministic re-fits, kept only when confirmed and not worse, otherwise reverted) |
| `concord/literature.py` | paper miner: OpenAlex, Crossref and arXiv; abstracts split into sentences, local embeddings, FAISS; fixed-pattern extraction of bond lengths, coordination numbers, oxidation states and sizes, each with DOI and sentence; cached |
| `concord/evaluate.py`, `eval/config.yaml` | `make eval`: metrics, registered thresholds, `results/eval.{json,md}` |
| `concord/cli.py` | `concord analyze <folder> [--fast]`, `concord priors`, `concord eval`, `concord health` |
| `concord/data_builder/`, `scripts/validate_dataset.py`, `data/` | dataset builder from open structures (COD; Materials Project, JARVIS, OQMD as fallbacks), nanoparticle models, XRD/PDF/XAFS simulation with planted faults, validator, structure manifest |
| `concord/agents/fitter.py` | fitting agents: one gpt-oss agent per technique (XRD, PDF, EXAFS) chooses the next settings or accepts; `concord.tweak.refit` computes every number; guardrails in code (ranges, at most 3 refits, window at least 70 % of its default span, keep only on a 2 % metric gain, PDF lattice drift at most 3 %, Qdamp never fitted); kept settings re-run the analysis |
| `concord/agents/chat.py` | questions about one sample answered from its evidence bundle: cited evidence ids, number guard with one rewrite, a suggested follow-up run |
| `concord/upload_inspect.py` | technique detection from file content (with the file name as a hint), previews, absorption edge from a μ(E) energy range; used to rewrite CSV and text-header uploads as plain columns |
| `concord/planner.py` | measurement planner: candidate phases simulated with Concord's XRD, PDF and FEFF code, pairwise separation per technique, separation over instrument noise when a realism model is given |
| `concord/gan.py` | run-time adapter for the realism GANs of Concord Forge (below) |
| `concord/tools/sq_to_gr.py`, `scripts/make_raw_pdf.py` | raw I(Q) to G(r): background subtraction, normalisation with Compton (xraydb form factors), F(Q), a polynomial correction constrained at low r, sine transform with optional Lorch window; written without the reference repositories' preprocessing. The script writes each sample's raw I(Q) and empty-container files from the builder's own simulation |
| `concord/tweak.py` | the fit settings per technique, a refit of one technique with the checks it changes, and a re-analysis with the user's settings |
| `concord/generate.py` | the techniques a user did not measure, simulated from the fitted model (plus GAN realism), GENERATED, NOT MEASURED |
| `backend/app/main.py`, `web/src/components/*.tsx`, `web/src/lib/{api,thread,insight}.ts` | sample workbench API and UI: conversation (`Chat`), results workbench (`Workbench`, `CheckPanel` with Settle this, `TechniqueTabs`, `VirtualXafs`, `CriticLog`, `Priors`), interactive SVG plots (`Plot`), measurement planner (`Planner`), Real or GAN? (`RealOrGan`), sample rail, upload dialog |
| `config.yaml`, `concord/config.py`, `concord/trace.py`, `scripts/secret_scan.py`, `.githooks/pre-commit`, `Makefile` | configuration, JSONL trace, pre-commit secret scan, make targets |
| `tests/` except the four ported XRD tests | 40+ tests: physics of every tool, checks, evidence, literature extraction, LLM client, vision, secret scan |

## 3. Reference repositories (read only; copied only as §3a lists)

Cloned read-only over SSH on 2026-10-22 at 21:04 into `../concord-ref/`, outside this repository; `git remote -v`
shows no credentials and nothing in the clones was changed:

- `pdf_frontend` (d0746ef) and `pdf_backend` (3bf4be1), bitbucket.org/fccubic, branch `main`: the PDF analysis
  platform and its agent.
- `xafs_backend` (4e9568a) and `xafs_frontend` (add424a), bitbucket.org/fccubicsaxs: upload and preprocessing only,
  no analysis code; nothing referenced.

**Idea referenced, code written fresh: the composition periodic table.** At the user's request the composition picker
follows `pdf_frontend`'s idea of choosing a sample's elements from a periodic table (block tints, a search box, an
amount per picked element). `web/src/components/PeriodicTable.tsx` and `web/src/lib/elements.ts` are new code: the
grid positions are computed from the atomic number, names come from pymatgen, and a dot marks elements with library
candidates (`GET /api/elements`), which the reference does not do.

**Idea referenced, code written fresh: the fitting agents.** `concord/agents/fitter.py` follows the idea of
`pdf_backend/app/modules/agent/refinement.py`: the order of steps and the guardrails live in code, and the model makes
the judgment calls (which region or candidate to try next, whether a stage's result is physically acceptable, when
nothing is left worth trying). Its 3 % lattice drift limit is reused as a guardrail. No code was copied: Concord's
agent covers XRD and EXAFS as well as PDF, and every refit is done by Concord's own `concord.tweak.refit`. Since
2026-10-23 the PDF agent's prompt and keep-or-revert gate, and the PDF refinement ladder, are copied code: see §3a.

They were cloned after Concord's pipeline was built (up to d2441bb), so its design does not come from them. Their
preprocessing (raw data to S(Q) and G(r), PARA files, XAFS normalisation) was deliberately not used for ideas.

**Used at run time, not copied: the eye.** The reviewer the PDF agent runs after each fit,
`pdf_backend/app/modules/agent/residual.py`, is `EYE_MODULE_PATH`. `concord/vision/eye_adapter.py` loads it (with the
standard logger in place of the platform's, so the platform itself is not imported) and judges PDF fits with its
`analyse`/`interpret`: a fit is rejected when a cause has high confidence or no parameter can fix it (wrong phase).
This rule was set before measuring. On the development split it rejected 2 of 44 clean PDF fits and 20 of 37 faulty
ones (5/5 wrong phase, 5/5 multi-domain, 5/5 mislabelled, 0/5 oxide shell). XRD and EXAFS fits keep the open judge.

Ideas found there that Concord had already built independently (nothing changed):
- a fix is kept only when it improves the fit (their stage acceptance and fit check; Concord's keep-or-revert loop);
- prose may state only numbers from saved results (their reporter's number check; Concord's number guard);
- uncertainties scaled to the number of independent points (their PDF uncertainties; Concord's EXAFS windows).

## 3a. Copied from fccubic/pdf_backend (commit 3bf4be1) by the author's decision, 2026-10-23

Until 2026-10-23 the reference repositories were used for ideas only. On 2026-10-23 the author (Sarthak Verma) decided
to copy the PDF platform's fitting agent, the Refinement specialist, into Concord; its preprocessing and data
reduction code was not copied. Copied, from `bitbucket.org/fccubic/pdf_backend` at commit `3bf4be1`:

- `app/modules/agent/refinement.py` into `concord/agents/pdf_specialist/refinement.py`: the module docstring,
  `NEVER_REFINE`, `BOUNDS`, `MAX_LATTICE_DRIFT`, the `STAGES` ladder (scale and lattice, thermal factors, particle size,
  correlated motion, instrument, consolidate), `stage_by_key`, `check_physical` and `should_accept` (1 % minimum Rw
  gain), verbatim except that the unused `app.*` logger and `AgentContext` imports were dropped. Not copied: the
  pdffit2 request builder, the symmetry helpers, `particle_size_estimate`, `sanitize_decision` and the free-text
  instruction parser. New in Concord: `as_result`, which puts Concord's srfit values in the result schema
  `should_accept` reads.
- `app/modules/agent/science/prompts.py` (`SPECIALIST`, `REFINEMENT_NOTES`) and the guidance of `_ask_next_action` in
  `app/modules/agent/agents.py` into `concord/agents/pdf_specialist/prompts.py`: the specialist's role, the ladder's
  rules and the refinement guidance, adapted so it calls no platform tools and answers with Concord's JSON decision.
- How Concord uses them (new code): `concord/tools/pdf.py` `fit_pdf` runs the copied ladder on Concord's diffpy.srfit
  engine in place of the platform's pdffit2 job service (`_await_fit` in `_analysis_body`), keeps or reverts each stage
  with the copied `should_accept`, skips the instrument stage (Qdamp is never fitted in Concord), asks no 1 % gain
  of the particle-size stage (Concord's envelope is in the model whenever it is on, and a diameter held at its XRD
  start would make C6 compare XRD with itself) and returns the stages; `concord/agents/fitter.py` gives the PDF fitting agent the copied prompt and judges each of its refits with
  the copied `should_accept`. The XRD and EXAFS agents are unchanged by this.
- EXAFS specialist: structure copied/adapted from fccubic/pdf_backend `refinement.py` at `3bf4be1`, by the author's
  decision on 2026-10-23; the reference has no EXAFS agent, so the stages and bounds are new. Adapted, not copied
  line for line: the shape of `STAGES` (a fixed list of `key`/`label`/`free`/`why` dicts ending in a `with_kept`
  consolidate stage), a `BOUNDS` table, `check_physical` returning a list of problem strings, and `should_accept`
  with the reference's contract and 1 % minimum gain (on the EXAFS R-factor instead of Rw), in
  `concord/agents/exafs_specialist.py`; its `SYSTEM` prompt follows the style of `SPECIALIST`/`REFINEMENT_NOTES`. New
  in Concord: the EXAFS stages (ΔE0; ΔE0 + ΔR; σ²; N with σ²; consolidate), the EXAFS bounds and the staged mode of
  `concord/tools/xafs.py` `shell_fit(staged=True)`. `run_exafs` does not use it (on s0019 it ends at R 0.0030
  against 0.0019 for the one-shot fit).

## 3a-x. Copied from fccubicsaxs/xafs_backend (branch `ai-agent`, commit f637212) by the author's decision, 2026-10-23

From `app/modules/agent/fitflow.py` (the EXAFS platform's fitting agent), in `concord/tools/xafs_fitflow.py`:
`SIGNIFICANT` (2.0), `F_TEST_P` (0.05), `LIGHT_SIGMA2` (0.004 Å²), the light-shell starting points of `select_model`
(N0 1, 0.5, 2, 4), `_f_test` (verbatim) and `_minor_verdict` (adapted to `shell_fit`'s result). `light_shell` follows
`select_model` for one light shell: fitted from each start with σ² held, lowest reduced χ² wins, kept only when N is
above 2σ, within 0.15 Å and better by an F-test at p < 0.05, then its own σ² freed when the data fixes it. This rule
now decides the probe shell in `run_exafs` and the critic's `exafs_probe_shell` re-run, replacing Concord's earlier
rule (N above 3σ and the R-factor down 30 %). On s0009, s0010, s0019 and s0024 it reaches the same decision as the
earlier rule (no probe shell kept). Not copied: the platform plumbing (tool runs, workspace, database), the foil S0²
fit, fitting k-weights 1, 2 and 3 together, `robustness`, multi-shell fits and report saving.

## 3b. Concord Forge (the user's own repository, used at run time)

[github.com/sarthak-1111/GAN-Hackathon](https://github.com/sarthak-1111/GAN-Hackathon), by the same author, cloned
read-only on 2026-10-22 into `../concord-ref/GAN-Hackathon`; the three realism generators (`generator_ema.pt`) were
fetched with Git LFS into the clone's LFS store, each checked against its LFS hash, and the clone's working tree is
unchanged. `concord/gan.py` imports the repository's model code at run time (with its directory-creating `paths`
module stubbed and no bytecode written) and loads the weights with `torch.load(weights_only=True)`; nothing is copied
into Concord. Used for: instrument realism in the planner and the Real or GAN? demonstration, including the real
spectra and simulated twins of `artifacts/data/real/` with their per-item licences shown. Not used for any analysis,
check or metric. Its predictor model is not used.

## 4. Libraries, services and data used (not ours)

Google ADK, pymatgen, ASE, diffpy.structure, diffpy.srfit, DebyeCalculator, xraylarch (bundled FEFF6L), xraydb, lmfit,
scipy, numpy, matplotlib, Starlette, uvicorn, sentence-transformers with `BAAI/bge-small-en-v1.5` (MIT), faiss-cpu, pypdf,
Next.js, React, SWR, Tailwind CSS, Phosphor Icons (MIT), the Newsreader font (SIL OFL, via `next/font`). The UI's colour,
radius and motion values come from the OpenDesign `claude` style package (visual language only: no names, marks or fonts
of that brand). Literature metadata and abstracts from OpenAlex, Crossref and arXiv (each prior cites its
DOI). Structures from open databases are listed with source and licence in `data/manifest.csv`.
