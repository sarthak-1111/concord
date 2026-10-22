# Progress

**Deadline: 2026-10-23 13:48 JST (2026-10-23T04:48Z)**, 32 h after the prompt was received at 2026-10-22 05:48 JST.
Times below are JST on 2026-10-22.

## Goals

| # | Goal | Status |
|---|---|---|
| 1 | Fork runs, references cloned, `EYE_MODULE_PATH` set, docs, health and tests pass | Fork, docs, health and tests done (47 tests). References and eye module **blocked**, see "Blocked" |
| 2 | Dataset v1 valid | Done: 60 samples (31 train, 10 val, 10 test, 9 faults), validator 1149/1149 checks |
| 3 | `make eval` end to end with C1–C6 | Done, passes every threshold (C7 added) |
| 4 | UI shows cross-check panel, critic log and virtual XAFS for every test sample; `make eval` still passes | Done: all 19 test and fault samples show C1–C7, a current critic log and a virtual XAFS (checked through the API at 16:34); `make eval` passes |

## Blocks

- [x] **06:29 Fork.** CrystaLenz forked with full history (`upstream`, commit `dc08f09`); gpt-oss client with per-role
  thinking, ADK `BaseLlm` adapter, XRD tools refactored into tested functions (three upstream bugs fixed, see
  `PRIOR_WORK.md`). Endpoint reachable (gpt-oss:120b).
- [x] **07:01 Dataset.** Builder from open structures (all COD, CC0, in `data/manifest.csv`), XRD/PDF/XAFS simulation,
  seven planted fault types, validator. v1: 60 samples; `dataset_big`: 320 samples for development.
- [x] **07:59 Analysis + `make eval`.** PDF refinement (diffpy.srfit), EXAFS/XANES, bond-valence sums, C1–C6.
- [x] **08:26 Agents and vision loop.** ADK pipeline analysis → visual inspection → generator ⇄ critic ⇄ resolver
  (≤ 3 rounds) → reporter; evidence ids, number guard, re-runs that settle objections; CLI.
- [x] **08:44 Virtual XAFS and C7.** Ensemble prediction labelled PREDICTED, NOT MEASURED, recommendation, scored
  on hidden spectra; joint score C7.
- [x] **08:55 Web UI.** Sample picker, cross-check panel, technique tabs, virtual XAFS band, critic log, export.
- [x] **09:21 Paper miner, C4.** OpenAlex/Crossref/arXiv priors with DOIs; C4 mixed-valence and metal rules.
- [x] **10:17 Visual loop.** Fix menu with keep-or-revert, zoom, physicality, calibrated residual rules;
  PDF-uncertainty and C7 fixes.
- [x] **10:20 Priors** for all nine test materials.
- [x] **10:28 Upload.** *Analyse your own data* in the UI: composition, XRD/PDF/XAFS files and optional instrument
  values, checked at the API (element symbols, edge element in the composition, 20 MiB, three files), then the tools
  run at once. The report lists assumed values and what could not be analysed.
- [x] **14:38 Agent-run fixes** (see "Agent runs").
- [x] **16:27 Agent runs** for all 19 test and fault samples (`make eval-agents`); `docs/DEMO.md` with the
  three-minute storyboard around s0031.
- [x] **16:31 Mislabelled edge.** On s0045 (labelled TiO2, Ce L3 edge measured) C4 explained the missing Ce as a
  metal with an oxidised component, and the virtual XAFS raised. C4 now says the label or the edge is wrong, and the
  virtual XAFS predicts the model's own Ti K edge without scoring it against the Ce spectrum (3cc029b).
- [x] **16:36 μ(E) uploads.** The virtual XAFS was compared only with a χ(k) file, so an upload with μ(E) alone got no
  comparison, no EXAFS term in C7 and a recommendation to measure the edge it had measured. It now uses the same χ(k)
  as the EXAFS fit (921ae7e; s0004 with μ(E) only: R 0.057, against 0.006 from the supplied χ(k)).

## Agent runs (`make eval-agents`, test + faults)

First batch (4.2 h, ended 14:12): 14 of 19 samples complete, 0 unsupported numbers in the reports, 1.6 critic
rounds and 37k tokens per sample, mean 23 min per sample (the endpoint answered a health probe in up to 130 s). The
critic's objections were settled by re-runs on s0017, s0019, s0034, s0038 and s0044. Five fault samples failed:

- **4 × `KeyError: 'phase'`** (s0003, s0024, s0045, s0052): when no candidate fits, the generator's `phase` is null
  and ADK 1.12 drops null fields from saved agent output. Fields are now read with `.get` (bd942be).
- **1 × endpoint gave up** (s0031) after four attempts: Cloudflare returns 524 when a request has waited 100 s at the origin.
  A busy endpoint now gets five attempts with a 15 s × 2ⁿ back-off, and a run that loses the endpoint midway keeps
  what the finished agents produced, marked incomplete in the report and the UI (bd942be).
- A re-run the critic asked for failed when the LLM passed an argument the action does not take (`optional`); the
  resolver now drops such arguments (26cb34d).

The five were re-run with `--reuse-agents`, which keeps a complete run whose check statuses match the recomputed
analysis (14:37–15:53). s0024, s0031, s0045 and s0052 completed; s0024 got through five Cloudflare 524s on the new
back-off. s0003 failed again with `ChunkedEncodingError: Response ended prematurely`: the tunnel cut a streamed reply,
and that exception escaped the retry loop. The client now retries it (4ad1557) and s0003 was run once more.

Three saved objections whose re-run could not run were labelled "not confirmed", which the UI showed as refuted:
s0038 R1.1 and s0044 R1.1 (the `optional` argument) and s0045 R1.1 (Ce is not in the TiO2 model of the mislabelled
sample). Since 1e6fd90 such an objection is `failed`, shown as not settled, and the three were relabelled. No metric
counts them.

s0003 completed at 16:27 (3 rounds). All 19 runs: 0 numbers in the prose that are not in the evidence, 1.8 critic
rounds, 26 min and 42k tokens per sample. With the critic, 6 of 9 faults are flagged and 0 of 10 clean samples, the
same as the checks alone: every objection a re-run settled was refuted, none upheld, so the critic added no
detection. What it did catch were false statements in the analyst's claims: s0003 (the XANES valence 3.883 called
above 4, corrected), s0052 (the PDF fit called visually rejected, corrected) and s0024 (C7 called failing; the next
round still reads "a fail status for the combined assessment").

## `make eval` history (v1, test + faults)

| commit | time | phase ID | EXAFS R MAE (Å) | CN MAE | oxidation | size XRD | size PDF | faults detected | false alarms | s/sample | virtual EXAFS R | hidden | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f5d485d | 07:59 | 0.9 | 0.0036 | 0.35 | 1 | 2.0 | 0.037 | 0.56 | 0.2 | 31 | – | – | no |
| 548fe39 | 08:26 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.56 | 0 | 25 | – | – | no |
| edc9f04 | 08:44 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.56 | 0 | 25 | 0.041 | 0.010 | no |
| 7e9c900 | 09:21 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.67 | 0 | 24 | 0.041 | 0.010 | yes |
| 713a87c | 10:17 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.67 | 0 | 25 | 0.022 | 0.011 | yes |
| 3cc029b | 16:34 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.67 | 0 | 24 | 0.022 | 0.011 | yes |

Until 7e9c900 the run failed one threshold, planted-fault detection (0.56 < 0.6). It passed after new C4 rules, not
after a threshold change; the rules were calibrated on the development split, never on test samples (below).

## How methods were changed without tuning on the test set

Method changes are tried on `dataset_big` samples s0060 and up (val + faults, 44 clean, 37 faulty); the v1 test and
fault samples are only scored. No threshold in `eval/config.yaml` was changed; one was added (virtual EXAFS
R ≤ 0.10, at 08:40, before its first eval; the file notes that test samples s0029 and s0054 had been looked at while
the prediction was developed).

- **XRD size.** A stiff baseline (λ = 1e8) instead of the CrystaLenz default: sphere-size MAE 10× lower on 168
  train/val nanoparticles. Peaks broader than a 1 nm crystallite are amorphous humps and are not indexed.
- **C4 oxidation (dev split).** Clean metals and alloys: LCF valence 0.05 ± 0.055, maximum 0.16, so a metal warns at
  0.2 and fails at 0.25. Mixed-valence CeO2 moves the bond-valence sum (−0.07 to −0.14) and the XANES edge in the same
  direction, which clean oxides do not (|BVS − formal| ≤ 0.009).
- **Visual rules (dev split).** Diffraction is judged by residual peaks above 15 % of the maximum after a
  Rietveld-style background: 1/44 clean patterns flagged, 5/5 wrong phases, 5/5 multi-domain, 4/5 mislabeled. The
  concentration and Durbin–Watson rules flagged 14/44 and 7/44 clean patterns and are not used for diffraction.
  EXAFS is judged inside the fit window with the region count scaled to its 11–16 independent points (25/39 clean
  fits rejected before, 0/39 after).
- **PDF uncertainties.** A parameter on its bound (δ2 = 0) made the covariance singular (U_iso ± 0.7 Å²,
  size ± 192 nm on s0298) and broke the virtual EXAFS ensemble; such parameters are now fixed before the
  uncertainties are computed.
- **C7.** Every candidate is scored on the same techniques (a candidate without the absorber has no EXAFS term);
  this removed the only dev false alarm.

Dev split before and after the visual-loop block (no agents): phase ID 1.00 → 1.00, fault detection 0.73 → 0.73,
false alarms 0.023 → 0, sizes and bond lengths unchanged.

## Data notes

- The oxide-shell fault was rebuilt once (548fe39): Pt–O σ² from the oxide's Debye temperature and the Pt valence
  from its Pt–O bonds (it was Pt²⁺ with one atop O). Only oxide-shell samples changed; v1 still passes 1149/1149.
- `dataset_big` has one known validator failure, s0302 (anatase, EXAFS Ti–O N 7.45 against the model's 6.00,
  R 1.952 against 1.954 Å). It is a development sample and is kept as built.

## Not detected

Oxide shell (s0010, s0059; C3 warns on s0059) and the low-concentration dopant (s0038) stay below the detection
limits of these checks; the README lists them under limitations.

## Blocked

- **Reference repositories** `xafs_backend` and `xafs_frontend` (bitbucket.org/fccubicsaxs): private. SSH has no
  bitbucket.org host key or key on this machine, and `.env` has no `REF_GIT_USERNAME`/`REF_GIT_TOKEN` (a Bitbucket
  API token with repository read scope, username `x-bitbucket-api-token-auth`). Nothing was taken from them.
- **Eye module:** `EYE_MODULE_PATH` is not set. The open fallback (residual features + gpt-oss judge) runs instead;
  the adapter loads the module at run time once the path is given.
