# Concord report — s0019 (Pt3Co)

**Pt3Co phase confirmed with metallic character and consistent structural parameters.**

Phase: **Pt3Co**

All cross‑technique checks passed, confirming Pt3Co as the consistent phase with metallic character, appropriate lattice, size, bond lengths, coordination numbers, and disorder.

## Key numbers (from the tools)

- **XRD**: best match Pt3Co (profile correlation 0.962, 99 % of the peak area explained); sphere diameter 3.4 nm from 6 indexed reflections
- **PDF**: Pt3Co refines to Rw 0.074; a 3.8315 Å; U_iso Co 0.0051 Å², Pt 0.0033 Å²; particle diameter 2.9 nm
- **EXAFS** (Pt L3): Pt–Co N 3.2 ± 0.5 at 2.702 Å, σ² 0.0073 Å²; Pt–Pt N 7.8 ± 0.8 at 2.710 Å, σ² 0.0048 Å²; R-factor 0.0019
- **XANES**: Pt valence 0.07 from a linear combination of standards, -0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: Joint score 0.972 (profile_corr 0.9622, area explained 0.9863) confirms Pt3Co; lattice parameters a = b = c = 3.832 Å match the reference 3.831 Å; sphere diameter 3.41 nm (Scherrer median 2.49 nm); one peak remains unindexed but further threshold lowering risks over‑fitting.
- **PDF**: Rw 0.07356 (well below 0.25) with lattice a = b = c = 3.832 Å matching reference; particle size from PDF envelope 2.93 nm; Δ2 0.5168 and u_iso values Co 0.005079, Pt 0.003309.
- **EXAFS**: R‑factor 0.001883 (well below 0.05) gives Pt‑Co bond length 2.702 Å (Δ 0.007 Å vs PDF model 2.709 Å) and Pt‑Pt bond length 2.71 Å (Δ 0.0003 Å); coordination numbers Pt‑Co 3.211 and Pt‑Pt 7.786; σ² values 0.007307 and 0.00484 respectively; no significant extra Pt‑O shell (N ≈ 4.3e‑10).
- **XANES**: Valence 0.06703 (edge shift –0.03727) and BVS valence 0.0 indicate metallic Pt3Co; linear combination fit shows Pt⁰ weight 0.9832 and Pt⁴⁺ weight 0.01676.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt3Co. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.73–0.87 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt3Co has the best joint score (margin 0.055). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt3Co; 24 ensemble members, Debye temperature 261–265 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0054 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- particle size 3.9 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 9.1 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 15 nm, [doi:10.1080/15533174.2013.831452](https://doi.org/10.1080/15533174.2013.831452) (2014): «XRD analysis confirmed the average size of Pt3Co@Pt nanocomposites around 15 nm, which allowed the assumption of the role of PBE surfactant.»
- particle size 5 nm, [doi:10.1149/2.0531514jes](https://doi.org/10.1149/2.0531514jes) (2015): «The ASAXS data, as well as data from aqueous dissolution, X-ray absorption spectroscopy, individual particle energy-dispersive spectroscopy, X-ray fluorescence spectrometry, and kinetic Monte Carlo calculations support a»
- particle size 5 nm, [doi:10.1149/1945-7111/abfcd9](https://doi.org/10.1149/1945-7111/abfcd9) (2021): «Comparison of Pt3Co/C and Pt/C with similar mean particle sizes (4.9 vs 5.0 nm) and particle size distributions reveals that the Pt3Co/C has a higher potentiostatic dissolution rate (4–5 times), a higher steady state con»
- particle size 4.5 nm, [doi:10.26434/chemrxiv.15007168/v1](https://doi.org/10.26434/chemrxiv.15007168/v1) (2026): «Particles with 66% ordered Pt 3 Co and 4.5 nm size could be synthesized by annealing for 2h at 1000°C followed by 50 h at 600°C, under 80% CO in N 2 atmosphere.»

## Claims

0. Phase identified as Pt3Co, consistent across XRD, PDF, and EXAFS. _(evidence: check.C1, xrd.ranking, pdf.best, exafs.fit)_
1. Lattice parameters a = b = c = 3.832 Å, matching reference value 3.831 Å. _(evidence: pdf.fit.Pt3Co)_
2. Particle diameter ≈ 3.41 nm from XRD and ≈ 2.93 nm from PDF, agreement within tolerance. _(evidence: xrd.size, pdf.fit.Pt3Co, check.C6)_
3. EXAFS Pt–Co bond length 2.702 Å, PDF model 2.709 Å; EXAFS Pt–Pt bond length 2.71 Å, PDF model 2.709 Å; differences within tolerance. _(evidence: check.C2, exafs.fit)_
4. EXAFS Pt–Co coordination number 3.211, model truncated value 3.45; EXAFS Pt–Pt coordination number 7.786, model truncated value 6.89; differences within tolerance. _(evidence: check.C3, exafs.fit)_
5. XANES valence 0.06703 and BVS valence 0.0 indicate metallic Pt3Co; LCF shows Pt+0 weight 0.9832 and Pt+4 weight 0.01676. _(evidence: check.C4, xanes, bvs)_
6. EXAFS σ2 values (Pt–Co 0.007307, Pt–Pt 0.00484) are 0.871 and 0.731 times the PDF uncorrelated σ2, as expected for correlated motion. _(evidence: check.C5, exafs.fit)_
7. Joint simulation score best for Pt3Co (score 0.039) with margin 0.0549 over the next candidate. _(evidence: check.C7)_
8. No significant extra Pt–O shell detected (N ≈ 4.305e-10, not significant). _(evidence: exafs.extra_shell)_
9. XRD joint score 0.972; one peak remains unindexed but further lowering thresholds may over–fit. _(evidence: fitting.xrd)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The Pt‑Pt coordination number from EXAFS (7.786) differs from the surface‑truncated PDF model value (6.89) by 0.90, which is close to the warning threshold (1.0) for coordination‑number differences. This borderline discrepancy may indicate an inconsistency between the EXAFS fit and the PDF‑derived structural model. | check.C3, exafs.fit | exafs_window_scan | N over kmax 10-12: Pt 7.31-8.23, Co 2.77-3.62 | not confirmed |

## Limitations

- One XRD peak remains unindexed; improving the score to ~0.991 would require threshold changes that may over‑fit.
- The Pt‑Pt coordination number from EXAFS (7.786) differs from the surface‑truncated PDF model (6.89) by 0.90, close to the warning threshold of 1.0 (borderline discrepancy, not confirmed).
- XANES analysis has low fidelity due to a simple edge model, limiting confidence in the precise valence determination.
- Size estimates differ between XRD (3.41 nm) and PDF (2.93 nm) with a relative difference of 0.162, still within the warning limit of 0.25.
