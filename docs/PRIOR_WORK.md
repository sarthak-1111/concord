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
| `web/src/components/EventCard.tsx`, `web/src/lib/useRunStream.ts`, `web/src/app/{layout,globals}` | Event card and WebSocket hook of the console (small fixes below) |
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
| Console rewritten as the Concord workbench (`console/page.tsx`); `PlotsView`, `PromptForm`, the logo and the unused Tailwind v3 config removed; `EventCard` hooks moved above its early return (React rules of hooks); `useRunStream` clears events between runs; Next.js 14.2.7 → 16.4.0, React 18 → 19.3.0 (14.x has unpatched advisories) | `web/` |
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
| `concord/agents/` | evidence bundle with citable ids and number guard; re-run actions that settle objections; ADK pipeline (analysis → visual inspection → generator–critic–resolver loop → reporter) |
| `concord/vision/` | deterministic fit plots (XRD with reflection ticks, PDF, EXAFS in k and R, zoom on the largest misfit), residual features calibrated on the dev split (Durbin–Watson on independent points, structured and concentrated misfit, grouped unexplained diffraction peaks), physicality checks, eye-module adapter, open fallback judge, acceptance rule, fix loop (a menu of deterministic re-fits, kept only when confirmed and not worse, otherwise reverted) |
| `concord/literature.py` | paper miner: OpenAlex, Crossref and arXiv; abstracts split into sentences, local embeddings, FAISS; fixed-pattern extraction of bond lengths, coordination numbers, oxidation states and sizes, each with DOI and sentence; cached |
| `concord/evaluate.py`, `eval/config.yaml` | `make eval`: metrics, registered thresholds, `results/eval.{json,md}` |
| `concord/cli.py` | `concord analyze <folder> [--fast]`, `concord priors`, `concord eval`, `concord health` |
| `concord/data_builder/`, `scripts/validate_dataset.py`, `data/` | dataset builder from open structures (COD; Materials Project, JARVIS, OQMD as fallbacks), nanoparticle models, XRD/PDF/XAFS simulation with planted faults, validator, structure manifest |
| `backend/app/main.py`, `web/src/components/{CheckPanel,TechniqueTabs,VirtualXafs,CriticLog,Priors,SampleList,Value}.tsx`, `web/src/lib/api.ts` | sample workbench API and UI |
| `config.yaml`, `concord/config.py`, `concord/trace.py`, `scripts/secret_scan.py`, `.githooks/pre-commit`, `Makefile` | configuration, JSONL trace, pre-commit secret scan, make targets |
| `tests/` except the four ported XRD tests | 40+ tests: physics of every tool, checks, evidence, literature extraction, LLM client, vision, secret scan |

## 3. Reference repositories (read only, never copied)

Cloned read-only over SSH on 2026-10-22 at 21:04 into `../concord-ref/`, outside this repository; `git remote -v`
shows no credentials and nothing in the clones was changed:

- `pdf_frontend` (d0746ef) and `pdf_backend` (3bf4be1), bitbucket.org/fccubic, branch `main`: the PDF analysis
  platform and its agent.
- `xafs_backend` (4e9568a) and `xafs_frontend` (add424a), bitbucket.org/fccubicsaxs: upload and preprocessing only,
  no analysis code; nothing referenced.

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

## 4. Libraries, services and data used (not ours)

Google ADK, pymatgen, ASE, diffpy.structure, diffpy.srfit, DebyeCalculator, xraylarch (bundled FEFF6L), xraydb, lmfit,
scipy, numpy, matplotlib, Starlette, uvicorn, sentence-transformers with `BAAI/bge-small-en-v1.5` (MIT), faiss-cpu, pypdf,
Next.js, React, SWR, Tailwind CSS. Literature metadata and abstracts from OpenAlex, Crossref and arXiv (each prior cites its
DOI). Structures from open databases are listed with source and licence in `data/manifest.csv`.
