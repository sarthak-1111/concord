# Prior work

Judges score only the new work, so this file lists exactly what came from where. It is updated with every commit that changes the boundary.

## 1. CrystaLenz (forked, MIT)

- Upstream: https://github.com/MJRaei/CrystaLenz, remote `upstream`, forked at commit
  **`dc08f09ac09b3e23a0ff0a13f82a926bc16a242d`** (2026-02-15, "updated the readme"). Full history kept.
- Licence and copyright notice kept in `LICENSE` (MIT, "Copyright (c) 2025 CrystaLens Contributors"); credit in `NOTICE`.

### Taken from CrystaLenz unchanged

| Path | What it is |
|---|---|
| `src/agent.py`, `src/agents/**` (agent graph, prompts) | Google ADK agent graph: root → sequential(parallel(research, XRD), final analyzer); XRD sub-agents (data loader, preprocessor, peak finder, Scherrer/WH, reference check, reporter, hyperparameter optimizer); research sub-agents (paper miner, retriever) |
| `src/schemas/schemas.py` | Pydantic output schemas of the ADK agents |
| `src/data_store/data_store.py` | In-memory store shared by the XRD tools |
| `backend/app/main.py` | Starlette API: `POST /api/runs`, WebSocket event stream |
| `web/` | Next.js console UI that streams run events |
| `sample_data/*.csv`, `docs/media/workflow.png`, `examples/chunker_test.py` | Sample patterns, figure, chunker demo |

### Changed in the fork

| Change | Where |
|---|---|
| Model `gemini-2.5-flash` → gpt-oss through an ADK `BaseLlm` adapter (`model_for(role)`) | every `src/**/agent.py` |
| XRD tool logic moved into pure functions in `concord/tools/xrd.py`; the ADK tools are thin wrappers around them | `src/agents/xrd_agent/sub_agents/{data_preprocessor,peak_finder,scherrer_and_wh}/tools.py` |
| **Bug fix:** the Voigt model called `voigt(x - center, sigma, gamma)`, i.e. passed sigma/gamma into lmfit's amplitude/center slots, so peak widths were never fitted (fixed at σ=γ=1°) and FWHM/Scherrer sizes were wrong | `concord/tools/xrd.py::_voigt` |
| **Bug fix:** Williamson–Hall regressed β cosθ on 4 sinθ/λ with λ in metres, so the "strain" was ε·λ (~1e-13); now regresses on 4 sinθ and reports dimensionless strain and the intercept size | `concord/tools/xrd.py::scherrer_wh`, `src/schemas/schemas.py` (WH field descriptions) |
| **Bug fix:** Voigt widths capped at 0.2°, which cannot fit nanoparticle peaks (2 nm Pt has FWHM ≈ 4°); fit window now adapts to the peak width | `concord/tools/xrd.py::find_and_fit_peaks` |
| `np.trapz` (removed in numpy 2) → fitted Voigt area | `concord/tools/xrd.py` |
| Reference matching no longer needs Materials Project: reference lines come from any pymatgen structure | `concord/tools/xrd.py::reference_lines`, `match_reference` |
| Upstream tests imported a module path that no longer existed (`src.sub_agents...`) and could not run; ported to the refactored functions with the same assertions | `tests/conftest.py`, `tests/test_xrd_tools.py` (first four tests) |
| `requirements.txt` → `pyproject.toml` + `uv.lock` (pinned) | repo root |

## 2. New in Concord

Everything not listed in section 1, in particular:

- `concord/llm/client.py` — LLM client: per-role thinking, timeouts, retries, capability probe, JSON-in-text fallback with one repair, concurrency limit, token/latency trace.
- `concord/llm/adk_model.py` — ADK model adapter for the bearer-token Ollama endpoint.
- `concord/tools/__init__.py` — common tool interface (registration + trace).
- `concord/tools/xrd.py` — new parts: header-aware loader with column/unit detection, Caglioti instrument correction, TCH pseudo-Voigt pattern simulation, whole-profile phase ranking, sphere-equivalent diameter.
- `scripts/secret_scan.py`, `.githooks/pre-commit` — pre-commit secret scan.
- `config.yaml`, `concord/config.py`, `concord/trace.py`.
- New tests: `tests/test_llm_client.py`, `tests/test_secret_scan.py`, physics tests in `tests/test_xrd_tools.py`.

## 3. Reference repositories (read only, never copied)

`pdf_frontend` and `pdf_backend` (bitbucket.org/fccubic) are meant to be cloned to `../concord-ref/` and read for workflow steps, parameter defaults and user flow only. **Status: not cloned yet** (cloning was blocked by this session's permission policy; see `docs/PROGRESS.md`). No ideas referenced from them so far.

## 4. Libraries and data used (not ours)

Google ADK, pymatgen, ASE, diffpy.structure, diffpy.srfit, DebyeCalculator, xraylarch (bundled FEFF6L), xraydb, lmfit, scipy, numpy. Structures from open databases are listed with source and licence in `data/manifest.csv`.
