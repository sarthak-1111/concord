# Concord evaluation — dataset (test, faults)

10 clean test samples, 9 fault samples. Thresholds from `eval/config.yaml`.

| metric | value | threshold | result |
|---|---|---|---|
| phase_id_accuracy | 0.900 | ≥ 0.9 | pass |
| exafs_bond_length_mae_A | 0.004 | ≤ 0.02 | pass |
| pdf_bond_length_mae_A | 0.000 | ≤ 0.02 | pass |
| exafs_cn_mae | 0.347 | ≤ 1.0 | pass |
| oxidation_accuracy | 1.000 | ≥ 0.8 | pass |
| size_rel_mae_xrd | 2.003 | ≤ 0.3 | **FAIL** |
| size_rel_mae_pdf | 0.037 | ≤ 0.2 | pass |
| fault_detection_rate | 0.556 | ≥ 0.6 | **FAIL** |
| false_alarm_rate | 0.200 | ≤ 0.2 | pass |
| checks_reported | 1.000 | ≥ 1.0 | pass |
| runtime_s_mean | 31.072 | ≤ 120 | pass |

Other numbers: size_rel_mae_exafs 0.303, fault_warn_or_fail_rate 0.778, warn_rate_clean 0.500, runtime_s_max 66.760, llm_tokens_per_sample 0

## Fault detection by type

| fault | detected |
|---|---|
| alloy_segregation | 1.000 |
| low_concentration_dopant | 0.000 |
| mislabeled_metadata | 1.000 |
| mixed_oxidation_states | 0.000 |
| multi_domain | 1.000 |
| oxide_shell | 0.000 |
| wrong_phase_candidate | 1.000 |

## Per sample

| sample | split | fault | phase (true) | C1 | C2 | C3 | C4 | C5 | C6 | s |
|---|---|---|---|---|---|---|---|---|---|---|
| s0004 | test | – | CeO2 (CeO2) | ✓ | ✓ | ✓ | ✓ | ✓ | – | 5 |
| s0009 | test | – | PtNi (Pt) | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | 35 |
| s0014 | test | – | TiO2-anatase (TiO2-anatase) | ✓ | ✓ | ✓ | ! | ✓ | ✓ | 24 |
| s0019 | test | – | Pt3Co (Pt3Co) | ✓ | ✓ | ✓ | ✓ | ✓ | ! | 38 |
| s0029 | test | – | PtNi (PtNi) | ✓ | – | – | – | – | ✓ | 67 |
| s0034 | test | – | Co3O4 (Co3O4) | ! | ✓ | ✓ | ✓ | ✓ | ✗ | 26 |
| s0039 | test | – | PtO2 (PtO2) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 18 |
| s0044 | test | – | IrO2 (IrO2) | ✓ | ✓ | ✓ | ✓ | ! | ✓ | 16 |
| s0049 | test | – | CeO2 (CeO2) | ✓ | ✓ | ✓ | ✓ | ✓ | – | 6 |
| s0054 | test | – | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 34 |
| s0003 | faults | wrong_phase_candidate | None (TiO2-brookite) | ✗ | ! | ✗ | ! | ! | ✓ | 33 |
| s0010 | faults | oxide_shell | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 39 |
| s0017 | faults | mixed_oxidation_states | CeO2 (CeO2) | ! | ✓ | ✓ | ✓ | ✓ | ✓ | 4 |
| s0024 | faults | alloy_segregation | Pt (Pt3Co) | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | 48 |
| s0031 | faults | multi_domain | Pt3Co (Pt) | ✗ | ✗ | ✗ | ✓ | ! | – | 63 |
| s0038 | faults | low_concentration_dopant | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 35 |
| s0045 | faults | mislabeled_metadata | None (CeO2) | ✗ | – | – | ✗ | – | ! | 17 |
| s0052 | faults | wrong_phase_candidate | None (PtO2-alpha) | ✗ | ! | ! | ! | ! | ! | 51 |
| s0059 | faults | oxide_shell | Pt3Co (Pt3Co) | ✓ | ✓ | ! | ! | ✓ | ✓ | 33 |

✓ pass  ! warn  ✗ fail  – skipped (technique missing)
