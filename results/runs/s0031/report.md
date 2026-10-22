# Concord report — s0031 (Pt)

**Phase assignment is ambiguous; no candidate structure fits both XRD and PDF data within the defined tolerances.**

Phase: **None**

No candidate phase fits both XRD and PDF data within tolerances; Pt is the most likely candidate from XRD alone but PDF fit is poor. Several checks indicate mismatches in coordination, disorder, and particle size. Vision inspection also rejects XRD, PDF, and EXAFS fits.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.864, 55 % of the peak area explained); sphere diameter 2.7 nm from 1 indexed reflections
- **PDF**: Pt refines to Rw 0.505; a 4.0371 Å; U_iso Pt 0.0237 Å²; particle diameter 1.6 nm
- **EXAFS** (Pt L3): Pt–Pt N 13.1 ± 2.2 at 2.847 Å, σ² 0.0131 Å²; R-factor 0.0610
- **XANES**: Pt valence 0.00 from a linear combination of standards, 0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking identifies Pt as the best matching phase with a score of 0.738, profile correlation of 0.864, and explains ~55 % of the observed area fraction.
- **PDF**: PDF fitting yields Pt as the best candidate (Rw = 0.505) but the fit quality exceeds the acceptable limit (Rw > 0.25) and the refined lattice parameter a = 4.037 Å shows a relative change of 0.0294 versus the reference, far above the warn threshold of 0.003.
- **EXAFS**: EXAFS bond length for the Pt–Pt pair (R = 2.847 ± 0.012 Å) matches the PDF‑refined distance (2.855 Å) within 0.007 Å, satisfying the bond‑length tolerance; however, the coordination number (N = 13.13 ± 2.18) exceeds the model expectation (bulk N = 12, surface‑adjusted N ≈ 8.84) by 4.29, indicating over‑coordination, and an additional Pt–O shell (N = 0.118 ± 0.531) is not statistically significant.
- **XANES**: XANES linear‑combination fitting shows Pt in the metallic state (Pt⁰ = 1.0, Pt²⁺ = 0, Pt⁴⁺ = 0) and the bond‑valence sum also yields a valence of 0, confirming a zero oxidation state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.51 for Pt). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | **FAIL** | EXAFS coordination differs from the model by up to 4.3: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 0.28–0.28 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
| C6 Size (XRD vs PDF) | **FAIL** | XRD sees larger crystallites than the PDF particle diameter: XRD is volume-weighted (large particles dominate) while the PDF envelope is closer to a number average, or a disordered surface shell shortens the PDF range. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.167). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt; 24 ensemble members, Debye temperature 97–98 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.6027 in R 1.0–3.5 Å.

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

0. Phase assignment is ambiguous; no candidate structure fits both XRD and PDF data within the defined tolerances. _(evidence: check.C1)_
1. XRD ranking identifies Pt as the best matching phase with a score of 0.738, profile correlation of 0.864, and explains ~55 % of the observed area fraction. _(evidence: xrd.ranking)_
2. PDF fitting yields Pt as the best candidate (Rw = 0.505) but the fit quality exceeds the acceptable limit (Rw > 0.25) and the refined lattice parameter (a = 4.037 Å) shows a relative change of 0.0294 versus the reference, far above the warn threshold of 0.003. _(evidence: pdf.fit.Pt, check.C1)_
3. EXAFS bond length for the Pt–Pt pair (R = 2.847 ± 0.012 Å) matches the PDF‑refined distance (2.855 Å) within 0.007 Å, satisfying the bond‑length tolerance. _(evidence: exafs.fit, check.C2)_
4. EXAFS coordination number for Pt–Pt (N = 13.13 ± 2.18) exceeds the model expectation (bulk N = 12, surface‑adjusted N ≈ 8.84) by 4.29, indicating over‑coordination or a model mismatch. _(evidence: exafs.fit, check.C3)_
5. An additional Pt–O shell is present at low occupancy (N = 0.118 ± 0.531) but does not improve the fit (rfactor change negligible), so it is not statistically significant. _(evidence: exafs.extra_shell, check.C3)_
6. XANES linear‑combination fitting shows Pt in the metallic state (Pt⁰ = 1.0, Pt²⁺ = 0, Pt⁴⁺ = 0) and the bond‑valence sum also yields a valence of 0, confirming a zero oxidation state. _(evidence: xanes, bvs, check.C4)_
7. The disorder ratio (EXAFS σ² = 0.01309 Å² vs. PDF σ² ≈ 0.01409 Å²) equals 0.276, which is below the acceptable range (0.3–1.3), suggesting static disorder or a surface‑layer effect. _(evidence: check.C5)_
8. Particle size from XRD (sphere diameter = 2.66 nm, Scherrer = 2.16 nm) is substantially larger than the PDF‑derived particle diameter (1.61 nm), giving a relative difference of 0.65 (> 0.5), indicating a size discrepancy between volume‑weighted XRD and number‑weighted PDF. _(evidence: xrd.size, pdf.fit.Pt, check.C6)_
9. Joint simulation scores across XRD, PDF, and EXAFS rank Pt as the best overall candidate (combined score = 0.415) with a margin of 0.167 over the next best model, though individual checks reveal significant mismatches. _(evidence: check.C7)_
10. Vision inspection rejects all three techniques: XRD due to unexplained peaks at 10.06° and 38.1°; PDF due to high Rw (0.505) and envelope decay issues; EXAFS due to an R‑factor of 0.061 (> 0.05). These rejections corroborate the need for additional phases or model refinement. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- Check C1 (phase consistency) fails: XRD phase Pt (score 0.738, area explained 0.548) vs PDF phase Pt (Rw 0.505) with lattice rel. change 0.0294, exceeding tolerances.
- Check C3 (coordination numbers) fails: EXAFS N exceeds model by 4.29, beyond the fail threshold of 2.0.
- Check C5 (disorder) warns: EXAFS σ²/ PDF σ² ratio = 0.276, below the acceptable range 0.3–1.3.
- Check C6 (size) fails: XRD sphere diameter 2.66 nm (Scherrer 2.16 nm) vs PDF particle diameter 1.61 nm, relative difference 0.65 (> 0.5).
- Vision inspection rejects XRD due to unexplained peaks at 10.06° and 38.1°; rejects PDF because Rw 0.505 (> 0.25) and envelope decay issues; rejects EXAFS because R‑factor 0.0610 (> 0.05).
