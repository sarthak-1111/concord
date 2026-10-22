# Concord evaluation — dataset (test, faults)

10 clean test samples, 9 fault samples. Thresholds from `eval/config.yaml`.

| metric | value | threshold | result |
|---|---|---|---|
| phase_id_accuracy | 1.000 | ≥ 0.9 | pass |
| exafs_bond_length_mae_A | 0.003 | ≤ 0.02 | pass |
| pdf_bond_length_mae_A | 0.000 | ≤ 0.02 | pass |
| exafs_cn_mae | 0.401 | ≤ 1.0 | pass |
| oxidation_accuracy | 1.000 | ≥ 0.8 | pass |
| size_rel_mae_xrd | 0.099 | ≤ 0.3 | pass |
| size_rel_mae_pdf | 0.038 | ≤ 0.2 | pass |
| fault_detection_rate | 0.667 | ≥ 0.6 | pass |
| false_alarm_rate | 0.000 | ≤ 0.2 | pass |
| checks_reported | 1.000 | ≥ 1.0 | pass |
| runtime_s_mean | 24.038 | ≤ 120 | pass |
| virtual_xafs_rfactor_median | 0.022 | ≤ 0.1 | pass |

Other numbers: virtual_xafs_n 10, virtual_xafs_hidden_rfactor_median 0.011, size_rel_mae_exafs 0.362, fault_warn_or_fail_rate 0.778, warn_rate_clean 0.200, runtime_s_max 50.930, llm_tokens_per_sample 41656.789, agent_wall_s_mean 1556.405, agent_rounds_mean 1.789, fault_detection_rate_agents 0.667, false_alarm_rate_agents 0.000, unsupported_numbers_total 0, agent_errors 0

## Fault detection by type

| fault | detected |
|---|---|
| alloy_segregation | 1.000 |
| low_concentration_dopant | 0.000 |
| mislabeled_metadata | 1.000 |
| mixed_oxidation_states | 1.000 |
| multi_domain | 1.000 |
| oxide_shell | 0.000 |
| wrong_phase_candidate | 1.000 |

## Per sample

| sample | split | fault | phase (true) | C1 | C2 | C3 | C4 | C5 | C6 | C7 | virtual XAFS R | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0004 | test | – | CeO2 (CeO2) | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | 0.006 (measured) | 5 |
| s0009 | test | – | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.057 (measured) | 28 |
| s0014 | test | – | TiO2-anatase (TiO2-anatase) | ✓ | ✓ | ✓ | ! | ✓ | ✓ | ✓ | 0.003 (measured) | 15 |
| s0019 | test | – | Pt3Co (Pt3Co) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.005 (measured) | 35 |
| s0029 | test | – | PtNi (PtNi) | ✓ | – | – | – | – | ✓ | ✓ | 0.011 (hidden) | 39 |
| s0034 | test | – | Co3O4 (Co3O4) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.033 (measured) | 24 |
| s0039 | test | – | PtO2 (PtO2) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.102 (measured) | 20 |
| s0044 | test | – | IrO2 (IrO2) | ✓ | ✓ | ✓ | ✓ | ! | ✓ | ✓ | 0.101 (measured) | 11 |
| s0049 | test | – | CeO2 (CeO2) | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | 0.002 (measured) | 6 |
| s0054 | test | – | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.050 (measured) | 19 |
| s0003 | faults | wrong_phase_candidate | None (TiO2-brookite) | ✗ | ! | ✗ | ✗ | ! | ✓ | ✓ | 0.154 (measured) | 36 |
| s0010 | faults | oxide_shell | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.068 (measured) | 20 |
| s0017 | faults | mixed_oxidation_states | CeO2 (CeO2) | ! | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | 0.005 (measured) | 4 |
| s0024 | faults | alloy_segregation | Pt (Pt3Co) | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 0.044 (measured) | 51 |
| s0031 | faults | multi_domain | None (Pt) | ✗ | ✓ | ✗ | ✓ | ! | ✗ | ✓ | 0.603 (measured) | 40 |
| s0038 | faults | low_concentration_dopant | Pt (Pt) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.030 (measured) | 17 |
| s0045 | faults | mislabeled_metadata | None (CeO2) | ✗ | – | – | ✗ | – | ! | ✗ | – | 17 |
| s0052 | faults | wrong_phase_candidate | None (PtO2-alpha) | ✗ | ! | ! | ✗ | ! | ✓ | ✗ | 0.757 (measured) | 42 |
| s0059 | faults | oxide_shell | Pt3Co (Pt3Co) | ✓ | ✓ | ! | ✓ | ✓ | ✓ | ✓ | 0.008 (measured) | 28 |

✓ pass  ! warn  ✗ fail  – skipped (technique missing)
