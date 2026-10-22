# Progress

**Deadline: 2026-10-23 13:48 JST (2026-10-23T04:48Z)**, 32 h after the prompt was received at 2026-10-22 05:48 JST.
Times below are JST on 2026-10-22.

## Goals

| # | Goal | Status |
|---|---|---|
| 1 | Fork runs, references cloned, `EYE_MODULE_PATH` set, docs, health and tests pass | Fork, docs, health and tests done (42 tests). References and eye module **blocked**, see "Blocked" |
| 2 | Dataset v1 valid | Done: 60 samples (31 train, 10 val, 10 test, 9 faults), validator 1149/1149 checks |
| 3 | `make eval` end to end with C1–C6 | Done, passes every threshold (C7 added) |
| 4 | UI shows cross-check panel, critic log and virtual XAFS for every test sample; `make eval` still passes | UI done; agent runs for the 19 test and fault samples in progress |

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
- [ ] **Agent runs** for all test and fault samples (`make eval-agents`), `docs/DEMO.md`.

## `make eval` history (v1, test + faults)

| commit | time | phase ID | EXAFS R MAE (Å) | CN MAE | oxidation | size XRD | size PDF | faults detected | false alarms | s/sample | virtual EXAFS R | hidden | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f5d485d | 07:59 | 0.9 | 0.0036 | 0.35 | 1 | 2.0 | 0.037 | 0.56 | 0.2 | 31 | – | – | no |
| 548fe39 | 08:26 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.56 | 0 | 25 | – | – | no |
| edc9f04 | 08:44 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.56 | 0 | 25 | 0.041 | 0.010 | no |
| 7e9c900 | 09:21 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.67 | 0 | 24 | 0.041 | 0.010 | yes |
| 713a87c | 10:17 | 1 | 0.0033 | 0.40 | 1 | 0.099 | 0.039 | 0.67 | 0 | 25 | 0.022 | 0.011 | yes |

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
