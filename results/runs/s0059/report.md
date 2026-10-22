# Concord report — s0059 (Pt3Co)

**All three techniques (XRD, PDF, EXAFS) agree that the sample is Pt₃Co.**

Phase: **Pt3Co**

All three techniques (XRD, PDF, EXAFS) agree that the sample is Pt3Co.

## Key numbers (from the tools)

- **XRD**: best match Pt3Co (profile correlation 0.958, 91 % of the peak area explained); sphere diameter 3.4 nm from 7 indexed reflections
- **PDF**: Pt3Co refines to Rw 0.054; a 3.8315 Å; U_iso Co 0.0054 Å², Pt 0.0032 Å²; particle diameter 2.9 nm
- **EXAFS** (Pt L3): Pt–Co N 4.0 ± 0.8 at 2.712 Å, σ² 0.0084 Å²; Pt–Pt N 8.5 ± 1.1 at 2.708 Å, σ² 0.0051 Å²; R-factor 0.0034
- **XANES**: Pt valence 0.07 from a linear combination of standards, 0.16 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD identifies Pt₃Co as the dominant phase with a score of 0.9393, profile correlation 0.9579 and explains 91.15% of the observed area; the particle‑size analysis yields a sphere diameter of 3.388 nm (Scherrer median 2.755 nm).
- **PDF**: PDF fitting selects Pt₃Co as the best candidate (rw = 0.05376) with lattice parameters a = b = c = 3.832 Å and a refined particle size of 2.887 nm, consistent with the XRD size (relative difference 0.173).
- **EXAFS**: EXAFS fit to a CoPt₃ model gives Pt‑Co bond length 2.712 Å (Δ = 0.0023 Å) and Pt‑Pt bond length 2.708 Å (Δ = ‑0.0016 Å), coordination numbers 4.0 (Pt‑Co) and 8.45 (Pt‑Pt) with warnings for deviations up to 1.57, and σ² values 0.977 and 0.795 times the uncorrelated PDF widths, as expected for correlated motion.
- **XANES**: XANES analysis yields a Pt valence of 0.0735, matching the bond‑valence‑sum and formal valence of 0.0, indicating a metallic Pt₃Co phase.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt3Co. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | **warn** | EXAFS coordination differs from the model by up to 1.6: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.80–0.98 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt3Co has the best joint score (margin 0.047). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt3Co; 24 ensemble members, Debye temperature 267–269 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0081 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- particle size 3.9 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 9.1 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 15 nm, [doi:10.1080/15533174.2013.831452](https://doi.org/10.1080/15533174.2013.831452) (2014): «XRD analysis confirmed the average size of Pt3Co@Pt nanocomposites around 15 nm, which allowed the assumption of the role of PBE surfactant.»
- particle size 5 nm, [doi:10.1149/2.0531514jes](https://doi.org/10.1149/2.0531514jes) (2015): «The ASAXS data, as well as data from aqueous dissolution, X-ray absorption spectroscopy, individual particle energy-dispersive spectroscopy, X-ray fluorescence spectrometry, and kinetic Monte Carlo calculations support a»
- particle size 5 nm, [doi:10.1149/1945-7111/abfcd9](https://doi.org/10.1149/1945-7111/abfcd9) (2021): «Comparison of Pt3Co/C and Pt/C with similar mean particle sizes (4.9 vs 5.0 nm) and particle size distributions reveals that the Pt3Co/C has a higher potentiostatic dissolution rate (4–5 times), a higher steady state con»
- particle size 4.5 nm, [doi:10.26434/chemrxiv.15007168/v1](https://doi.org/10.26434/chemrxiv.15007168/v1) (2026): «Particles with 66% ordered Pt 3 Co and 4.5 nm size could be synthesized by annealing for 2h at 1000°C followed by 50 h at 600°C, under 80% CO in N 2 atmosphere.»

## Claims

0. Phase consistency (XRD vs PDF) – both identify Pt3Co as the dominant phase. _(evidence: check.C1, xrd.ranking, pdf.best, pdf.fit.Pt3Co)_
1. Lattice parameters of the Pt3Co phase are a = b = c = 3.832 Å. _(evidence: pdf.fit.Pt3Co)_
2. Particle size from XRD (sphere diameter 3.39 nm, Scherrer 2.76 nm) agrees with PDF size (2.89 nm) within 0.173 relative difference. _(evidence: check.C6)_
3. Bond lengths from EXAFS match the PDF‑refined model: Pt‑Co = 2.712 Å (PDF 2.709 Å, Δ = 0.0023 Å); Pt‑Pt = 2.708 Å (PDF 2.709 Å, Δ = –0.0016 Å). _(evidence: check.C2)_
4. EXAFS coordination numbers differ from bulk model values (Pt‑Co diff = 0.56, Pt‑Pt diff = 1.57; max absolute diff = 1.57). This suggests surface segregation, vacancies, or a disordered surface. _(evidence: check.C3)_
5. Oxidation state: XANES valence 0.07, bond‑valence sum 0.0, formal valence 0.0 – consistent with a metallic Pt3Co phase. _(evidence: check.C4)_
6. Disorder: EXAFS σ² values are 0.977 (Pt‑Co) and 0.795 (Pt‑Pt) times the uncorrelated PDF widths, as expected for correlated atomic motion. _(evidence: check.C5)_
7. Joint simulation score: Pt3Co has the lowest combined score (0.0347) with a margin of 0.0474 over the next candidate. _(evidence: check.C7)_
8. Visual inspection: XRD, PDF, and EXAFS data all accepted by the gpt‑oss judge. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- Coordination numbers from EXAFS differ from bulk model values (max absolute diff = 1.57), suggesting possible surface segregation, vacancies, or disorder.
- The XANES fit has low fidelity (simple edge model) and the oxidation‑state tolerance is tight (metal_warn_abs = 0.2).
- No objections were logged, but the analysis relies on model assumptions (e.g., spherical particles, correlated motion) that could affect size and disorder estimates.
