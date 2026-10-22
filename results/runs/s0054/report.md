# Concord report — s0054 (Pt)

**Metallic Pt identified as the sole phase present in the sample.**

Phase: **Pt**

The combined XRD, PDF, and XAFS analyses converge on metallic Pt as the sole phase present, with consistent structural parameters across techniques.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.977, 99 % of the peak area explained); sphere diameter 5.2 nm from 5 indexed reflections
- **PDF**: Pt refines to Rw 0.071; a 3.9216 Å; U_iso Pt 0.0041 Å²; particle diameter 4.9 nm
- **EXAFS** (Pt L3): Pt–Pt N 10.8 ± 0.5 at 2.777 Å, σ² 0.0047 Å²; R-factor 0.0035
- **XANES**: Pt valence 0.00 from a linear combination of standards, -0.03 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking assigns Pt a score of 0.9829, profile correlation 0.9771, and observed area fraction explained 0.9916, and the refined sphere diameter is 5.16 nm.
- **PDF**: PDF fitting for Pt yields Rw = 0.0709 (well below the good‑fit tolerance of 0.25) with a particle size (psize) of 4.87 nm, and the lattice parameters match the reference (a = b = c = 3.922 Å).
- **EXAFS**: EXAFS analysis gives a Pt–Pt bond length of 2.776 Å (Δ = 0.0035 Å vs. PDF model), coordination number 10.78 (model 10.98, Δ = ‑0.2), and σ² = 0.00467 Å², which is 0.575 of the PDF uncorrelated pair width, within the expected 0.3–1.3 range.
- **XANES**: XANES linear combination fitting shows a weight of 1.0 for Pt⁰ and 0.0 for Pt²⁺/Pt⁴⁺, with a bond‑valence sum valence of 0.0, confirming a metallic oxidation state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.57–0.57 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.172). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co; 24 ensemble members, Debye temperature 217–238 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0501 in R 1.0–3.5 Å.

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

0. Both XRD and PDF analyses identify the sample as the metallic Pt phase. _(evidence: check.C1, xrd.ranking, pdf.best, pdf.fit.Pt)_
1. XRD ranking shows Pt with a score of 0.9829, profile correlation 0.9771, and observed area fraction explained 0.9916. _(evidence: xrd.ranking)_
2. PDF fit for Pt yields Rw = 0.0709, which is below the good‑fit tolerance of 0.25. _(evidence: pdf.fit.Pt, check.C1)_
3. EXAFS Pt–Pt bond length 2.776 Å matches the PDF model distance 2.773 Å, difference 0.0035 Å. _(evidence: check.C2)_
4. EXAFS coordination number for Pt–Pt is 10.78, model value after surface truncation is 10.98, difference -0.2. _(evidence: check.C3)_
5. XANES linear combination fitting shows weight 1.0 for Pt⁰ and 0.0 for Pt⁺² and Pt⁺⁴, and bond‑valence sum gives valence 0.0, confirming metallic Pt. _(evidence: check.C4)_
6. EXAFS σ² is 0.00467 Å², which is 0.575 of the PDF uncorrelated pair width 0.00812 Å²; the ratio lies within the expected range 0.3–1.3. _(evidence: check.C5)_
7. XRD sphere diameter is 5.16 nm, PDF diameter is 4.87 nm, relative difference 0.06, within the tolerance of 0.25. _(evidence: check.C6)_
8. Joint simulation score for Pt is 0.0327, with a margin of 0.1722 over the next best candidate, indicating Pt as the best model. _(evidence: check.C7)_
9. Visual inspection confirms XRD, PDF, and EXAFS data are accepted. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- XANES fidelity is noted as low (simple edge model) despite agreement with the bond‑valence sum.
- Size estimates differ between XRD (5.16 nm) and PDF (4.87 nm), though the relative difference of 0.06 is within the 0.25 tolerance.
- No objections were raised in the objection log.
