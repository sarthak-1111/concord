# Concord report — s0019 (Pt3Co)

**Concord analysis confirms Pt₃Co intermetallic phase with consistent structural parameters across XRD, PDF, and XAFS.**

Phase: **Pt3Co**

Concord analysis of the Pt3Co sample integrates XRD, PDF and XAFS data to produce a consistent structural model.

## Key numbers (from the tools)

- **XRD**: best match Pt3Co (profile correlation 0.956, 93 % of the peak area explained); sphere diameter 3.4 nm from 7 indexed reflections
- **PDF**: Pt3Co refines to Rw 0.074; a 3.8315 Å; U_iso Co 0.0051 Å², Pt 0.0033 Å²; particle diameter 2.9 nm
- **EXAFS** (Pt L3): Pt–Co N 3.2 ± 0.5 at 2.702 Å, σ² 0.0073 Å²; Pt–Pt N 7.8 ± 0.8 at 2.710 Å, σ² 0.0048 Å²; R-factor 0.0019
- **XANES**: Pt valence 0.07 from a linear combination of standards, -0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: X‑ray diffraction ranks Pt₃Co highest (score 0.9469) and yields a sphere‑diameter of 3.384 nm, matching the PDF‑derived size of 2.933 nm (relative difference 0.154).
- **PDF**: Pair distribution function refinement gives lattice parameters a = b = c = 3.832 Å (reference 3.831 Å) and a particle size of 2.933 nm, with the best‑fit phase identified as Pt₃Co (rw = 0.07356).
- **EXAFS**: EXAFS fits provide coordination numbers N(Pt‑Co) = 3.21 ± 0.49 and N(Pt‑Pt) = 7.79 ± 0.80, Debye‑Waller factors σ² = 0.00731 Å² (Pt‑Co) and 0.00484 Å² (Pt‑Pt) corresponding to ratios of 0.87 and 0.73 to the PDF‑derived pair widths, and no significant Pt‑O shell (N = 4.305e‑10).
- **XANES**: XANES linear‑combination fitting shows Pt is primarily metallic (Pt⁰ = 0.9832, Pt⁴⁺ = 0.01676) giving a valence of ~0.07, consistent with the bond‑valence sum of 0.0.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt3Co. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.73–0.87 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt3Co has the best joint score (margin 0.037). |

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

0. The sample consists of the intermetallic Pt3Co phase. _(evidence: check.C1, pdf.best, xrd.ranking)_
1. The refined lattice parameter is a = b = c = 3.832 Å. _(evidence: pdf.fit.Pt3Co)_
2. Average particle size is ~3.38 nm (XRD sphere diameter) and ~2.93 nm (PDF), with a relative difference of 0.154. _(evidence: xrd.size, pdf.fit.Pt3Co, check.C6)_
3. EXAFS coordination numbers are N(Pt‑Co) = 3.21 ± 0.49 and N(Pt‑Pt) = 7.79 ± 0.80, which differ from the surface‑truncated model values (3.45 and 6.89) by 0.24 and 0.89 respectively; both differences are below the warning threshold of 1.0 defined in check.C3, so the coordination numbers are considered consistent. _(evidence: exafs.fit, check.C3, rerun.R2.1.exafs_window_scan)_
4. XANES linear combination fit indicates the Pt is primarily metallic (Pt⁰ fraction 0.9832, minor Pt⁴⁺ fraction 0.0168), giving a valence of ~0.07, in agreement with the bond‑valence sum of 0.0. _(evidence: xanes, bvs, check.C4)_
5. EXAFS Debye‑Waller factors are σ² = 0.00731 Å² for Pt‑Co and σ² = 0.00484 Å² for Pt‑Pt; these correspond to ratios of 0.87 and 0.73 relative to the PDF uncorrelated pair widths, indicating consistent disorder. _(evidence: exafs.fit, check.C5)_
6. No significant Pt‑O coordination shell is detected (N = 4.305e-10, not significant). _(evidence: exafs.extra_shell)_
7. Joint simulation of XRD, PDF and EXAFS ranks Pt3Co as the best candidate (score 0.041) with a margin of 0.0366 over PtNi, confirming the phase assignment. _(evidence: check.C7)_
8. The measured XAFS edge is consistent with the predicted spectrum for Pt3Co (rfactor ≈ 0.0055). _(evidence: virtual_xafs)_
9. The particle size is comparable to previously reported Pt3Co nanoparticle sizes of approximately 3.9–5.0 nm. _(evidence: prior.1, prior.4, prior.6)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.guard | numbers not in the evidence: 4.3 | – | – | copy numbers from the evidence or remove them | number_guard |
| R2.1 | The Pt‑Pt coordination number from EXAFS (7.79 ± 0.80) differs from the surface‑truncated model value (6.89) by 0.89, which is close to the warning threshold of 1.0 defined in check.C3. This near‑threshold discrepancy suggests the coordination number may be sensitive to fitting parameters and should be verified. | check.C3 | exafs_window_scan | N over kmax 10-12: Pt 7.31-8.23, Co 2.77-3.62 | not confirmed |

## Limitations

- The Pt‑Pt coordination discrepancy of 0.89 approaches the warning threshold of 1.0 defined in check.C3, indicating sensitivity to fitting parameters despite the re‑run window scan (Pt N ranging 7.31–8.23).
- XANES analysis has low fidelity (simple edge model) and relies on a modest valence shift, limiting confidence in oxidation‑state quantification.
- The Pt‑O extra shell is not statistically significant (N ≈ 4.3e‑10, significance = false).
- Particle‑size comparison relies on conversion of Scherrer breadth to a sphere diameter; the relative size difference, though within the 0.25 warning, remains non‑negligible.
- The virtual XAFS spectrum is a predicted consistency check (rfactor ≈ 0.0055) and not a direct measurement.
