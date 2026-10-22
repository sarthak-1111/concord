# Concord report — s0039 (PtO2)

**PtO2 identified as the sole structural phase in the sample.**

Phase: **PtO2**

All techniques converge on PtO2 as the single structural model for the sample.

## Key numbers (from the tools)

- **XRD**: best match PtO2 (profile correlation 0.979, 100 % of the peak area explained); sphere diameter 7.2 nm from 10 indexed reflections
- **PDF**: PtO2 refines to Rw 0.189; a 4.4849 Å, b 4.5390 Å, c 3.1344 Å; U_iso O 0.0078 Å², Pt 0.0011 Å²; particle diameter 7.9 nm
- **EXAFS** (Pt L3): Pt–O N 6.1 ± 0.5 at 2.004 Å, σ² 0.0091 Å²; R-factor 0.0063
- **XANES**: Pt valence 3.65 from a linear combination of standards, 4.29 from the edge position
- **Bond valence** (PDF model): 4.00

## Evidence by technique

- **XRD**: XRD ranks PtO2 with a score of 0.9873, full observed area fraction explained (1.0), and yields a sphere diameter of 7.199 nm (≈7.2 nm).
- **PDF**: PDF fit for PtO2 gives an Rw of 0.1892, particle size 7.929 nm, and lattice parameters a = 4.485 Å, b = 4.539 Å, c = 3.134 Å (close to reference values).
- **EXAFS**: EXAFS on the Pt L₃ edge reports a Pt–O distance of 2.004 Å (σ² = 0.0091 Å²) with a coordination number of 6.05 and an R‑factor of 0.006301.
- **XANES**: XANES analysis gives a Pt valence of ~3.65 (edge valence 4.29), consistent with the bond‑valence‑sum value of 4.00.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on PtO2. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 1.02–1.02 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | PtO2 has the best joint score (margin 0.924). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (PtO2; 24 ensemble members, Debye temperature 451–461 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.1023 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Pt–Pt bond length 2.8 Å, [doi:10.31635/ccschem.022.202101628](https://doi.org/10.31635/ccschem.022.202101628) (2022): «No Pt–Pt characteristic peak (at ∼2.8 Å) was detected for both Pt-B-MoS2 and Pt-S-MoS2 samples, confirming the atomic dispersion of Pt on the supports.»
- Pt oxidation state 4, [doi:10.31635/ccschem.022.202101628](https://doi.org/10.31635/ccschem.022.202101628) (2022): «However, for the Pt loading of S-MoS2 samples (donated as Pt-S-MoS2), the Pt exhibited an additional peak at ∼74.0 eV, suggesting the existing higher oxidation state of the Pt4+ species.»
- particle size 1.3 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 6.5 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 12.7 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 8.54 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 3 nm, [doi:10.1039/c5nr03585f](https://doi.org/10.1039/c5nr03585f) (2015): «The SnO2 nanoparticle cluster matrix consists of tens of thousands of SnO2 nanoparticles with an ultra-small grain size estimated to be 3.0 nm.»
- particle size 1.1–2.1 nm, [doi:10.1021/acsami.8b06815](https://doi.org/10.1021/acsami.8b06815) (2018): «The high crystallinity and uniform crystal structure of the ZnO matrix conduct the in situ deposition of PtO 2 nanoparticles with 1.1–2.1 nm, which are evenly and densely anchored on the surface.»

## Claims

0. Phase consistency: XRD and PDF identify PtO2 as the dominant phase with high scores and full area fraction explained. _(evidence: check.C1, xrd.ranking, pdf.best)_
1. Bond lengths: The Pt‑O distance from EXAFS (2.004 Å) matches the PDF‑refined model (≈1.998 Å) within 0.006 Å. _(evidence: check.C2, exafs.fit, pdf.fit.PtO2)_
2. Coordination numbers: EXAFS gives a Pt‑O coordination of 6.05, consistent with the bulk model (6.0) after surface truncation (model N≈5.77), differing by only 0.28. _(evidence: check.C3, exafs.fit, pdf.fit.PtO2)_
3. Oxidation state: XANES valence (~3.65) and edge valence (4.29) agree with the bond‑valence‑sum value (4.00) within 0.35, confirming Pt⁴⁺. _(evidence: check.C4, xanes, bvs)_
4. Disorder: EXAFS σ² (0.0091 Å²) matches the PDF uncorrelated σ² (0.00896 Å²) with a ratio of 1.016, well within the expected range. _(evidence: check.C5, exafs.fit, pdf.fit.PtO2)_
5. Particle size: XRD yields a sphere diameter of ~7.2 nm (7.199 nm) and PDF gives a diameter of ~7.93 nm (7.929 nm), a relative difference of ~9 %. _(evidence: check.C6, xrd.size, pdf.fit.PtO2)_
6. Joint simulation score: Combining XRD, PDF and EXAFS, PtO2 attains the lowest total score (0.1041) with a margin of 0.924 over alternatives, making it the best model. _(evidence: check.C7, xrd.ranking, pdf.fit.PtO2, exafs.fit)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- XANES fidelity is low (simple edge model) and the valence deviation (‑0.35) approaches the tolerance limit of 0.5.
- Particle size estimates differ by ~9 % between XRD (7.199 nm) and PDF (7.929 nm), though both are within the 25 % tolerance.
- All checks pass their respective tolerances, but the analysis relies on a single‑phase model; any minor secondary phases below detection limits would not be captured.
