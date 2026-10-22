# Concord report — s0010 (Pt)

**All cross‑technique consistency checks (C1‑C7) pass, confirming Pt as the sole phase, but EXAFS visual inspection fails due to significant autocorrelation (Durbin‑Watson = 0.6193).**

Phase: **Pt**

All cross‑technique consistency checks (C1–C7) pass, indicating Pt as the single phase across XRD, PDF, and EXAFS. However, the visual inspection of the EXAFS data was rejected because the Durbin‑Watson statistic is 0.6193, showing significant autocorrelation in the residuals.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.979, 99 % of the peak area explained); sphere diameter 6.7 nm from 5 indexed reflections
- **PDF**: Pt refines to Rw 0.141; a 3.9208 Å; U_iso Pt 0.0043 Å²; particle diameter 7.8 nm
- **EXAFS** (Pt L3): Pt–Pt N 11.5 ± 0.7 at 2.775 Å, σ² 0.0049 Å²; R-factor 0.0054
- **XANES**: Pt valence 0.00 from a linear combination of standards, 0.07 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: The XRD ranking gives Pt a score of 0.9853, profile correlation 0.9789 and explains 0.9949 of the observed area, with a sphere diameter of 6.736 nm (Scherrer median 5.521 nm).
- **PDF**: PDF fitting for Pt yields Rw = 0.1412, lattice parameters a = b = c = 3.921 Å (reference 3.922 Å), isotropic U = 0.004322, delta2 = 0.8191, and particle size 7.794 nm over r‑range 1.5–25.0 Å.
- **EXAFS**: EXAFS fit (Pt L₃ edge) reports an R‑factor of 0.00544, e₀ shift of 0.3655 eV, coordination number N = 11.55 ± 0.708, bond length R = 2.775 ± 0.002838 Å, and σ² = 0.004917; however, visual inspection is rejected because the Durbin‑Watson statistic is 0.6193, indicating significant autocorrelation in the residuals.
- **XANES**: XANES gives a valence of 0.0 (edge‑valence 0.06555) with linear combination fitting weights Pt⁰ = 1.0, Pt²⁺ = 0.0, Pt⁴⁺ = 0.0; fidelity is noted as low (simple edge model).

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.57–0.57 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.221). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co; 24 ensemble members, Debye temperature 211–230 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0676 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Pt–Pt bond length 2.876 ± 0.028 Å, [doi:10.2533/chimia.2008.287](https://doi.org/10.2533/chimia.2008.287) (2008): «A Pt–Pt distance of 2.876(28) Å and a Pt–P bond length of 2.32(4) Å are obtained.»
- Pt oxidation state 4, [doi:10.1039/c2mt20053h](https://doi.org/10.1039/c2mt20053h) (2012): «Reduction of Pt(IV) complexes over time in cell growth media and A2780 cells was observed by XANES, and shown to correspond with their reduction potentials and cytotoxicities.»
- particle size 5 nm, [doi:10.1103/physrevb.85.075439](https://doi.org/10.1103/physrevb.85.075439) (2012): «The estimation of metal nanoparticle diameter by analysis of extended x-ray absorption fine structure (EXAFS) data from coordination numbers is nontrivial, particularly for particles 5 nm in diameter, for which the under»
- particle size 3 nm, [doi:10.48550/arXiv.2406.01004](https://doi.org/10.48550/arXiv.2406.01004) (2024): «We successfully synthesized Pt@ZIF-8 in two steps, the average particle size of Pt nanoparticles is about 3 nm.»
- particle size 1.5 nm, [doi:10.1103/physrevb.84.245438](https://doi.org/10.1103/physrevb.84.245438) (2011): «For large NP sizes (diameter $d$ >1.5 nm) \ensuremath{\Theta}${}_{D}$ was found to decrease toward \ensuremath{\Theta}${}_{D}$ of bulk Pt with increasing NP size.»
- particle size 4 nm, [doi:10.1039/b303911k](https://doi.org/10.1039/b303911k) (2003): «Significant size effects are observed in the particle size interval from ca. 1 to 4 nm, including the positive shift of the CO stripping peak with decreasing particle size and a pronounced asymmetry of the current transi»
- particle size 2 nm, [doi:10.1039/b821622n](https://doi.org/10.1039/b821622n) (2009): «Our model demonstrates that, due to rapid changes in the Gibbs–Thomson energy, particle size effects dominate degradation for ∼2 nm particles but play almost no role for ∼5 nm particles.»
- particle size 5 nm, [doi:10.1039/b821622n](https://doi.org/10.1039/b821622n) (2009): «Our model demonstrates that, due to rapid changes in the Gibbs–Thomson energy, particle size effects dominate degradation for ∼2 nm particles but play almost no role for ∼5 nm particles.»

## Claims

0. Cross‑technique consistency checks C1 through C7 all pass, supporting Pt as the single phase for this sample. _(evidence: check.C1, check.C2, check.C3, check.C4, check.C5, check.C6, check.C7)_
1. Visual inspection of the EXAFS data was rejected because the Durbin‑Watson statistic is 0.6193, indicating significant autocorrelation in the residuals. _(evidence: vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- The EXAFS visual inspection fails (Durbin‑Watson = 0.6193 < 1.0), so the residuals exhibit significant autocorrelation despite the quantitative fit being good.
- XANES fidelity is low due to the simple edge model, limiting confidence in subtle oxidation‑state nuances.
