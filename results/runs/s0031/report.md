# Concord report — s0031 (Pt)

**Phase cannot be assigned confidently as no single candidate fits both XRD and PDF data.**

Phase: **None**

No single candidate structure fits both XRD and PDF data, so the phase cannot be assigned confidently.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.864, 55 % of the peak area explained); sphere diameter 2.7 nm from 1 indexed reflections
- **PDF**: Pt refines to Rw 0.505; a 4.0371 Å; U_iso Pt 0.0237 Å²; particle diameter 1.6 nm
- **EXAFS** (Pt L3): Pt–Pt N 11.5 ± 0.6 at 2.852 Å, σ² 0.0114 Å²; R-factor 0.0035
- **XANES**: Pt valence 0.00 from a linear combination of standards, 0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: The XRD ranking gives Pt a fit score of 0.7377, a profile correlation of 0.8644, and it explains 54.8% of the observed area.
- **PDF**: PDF fitting identifies Pt as the best model with Rw = 0.5054, lattice parameters a = b = c = 4.037 Å, particle size = 1.61 nm, delta2 = 5.729 and isotropic displacement U_iso(Pt) = 0.02371.
- **EXAFS**: EXAFS analysis for Pt yields an Rfactor of 0.003549, edge‑energy shift of –0.03232 eV, Pt–Pt distance of 2.852 Å, coordination number 11.54 ± 0.55 and σ² = 0.0114 Å².
- **XANES**: XANES L₃‑edge linear combination fitting gives 100 % Pt⁰, 0 % Pt²⁺, 0 % Pt⁴⁺, with a valence of 0.0, matching the bond‑valence‑sum valence of 0.0.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.51 for Pt). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | **FAIL** | EXAFS coordination differs from the model by up to 2.7: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 0.24–0.24 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
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

0. Phase consistency between XRD and PDF fails; no candidate among Pt, Pt3Co, PtNi, PtO2 fits both datasets, so the phase cannot be assigned. _(evidence: check.C1)_
1. XRD ranking shows Pt has the highest fit score of 0.7377, profile correlation 0.8644, and explains 54.8% of observed area. _(evidence: xrd.ranking)_
2. PDF fitting identifies Pt as the best model with Rw 0.5054, lattice parameter a = b = c = 4.037 Å, particle size 1.61 nm, delta2 5.729, and isotropic displacement parameter U_iso(Pt) = 0.02371. _(evidence: pdf.best, pdf.fit.Pt)_
3. EXAFS analysis for Pt yields Rfactor 0.003549, edge energy shift -0.03232 eV, Pt–Pt distance 2.852 Å, coordination number 11.54 ± 0.55, and Debye‑Waller factor σ² = 0.0114 Å². _(evidence: exafs.fit)_
4. XANES L₃ edge linear combination fitting gives 100 % Pt⁰, 0 % Pt²⁺, 0 % Pt⁴⁺, with valence 0.0, matching the bond‑valence sum valence of 0.0. _(evidence: xanes, bvs)_
5. Bond lengths from EXAFS (2.852 Å) match the PDF model (2.855 Å) within 0.003 Å, well inside the tolerance of 0.02 Å. _(evidence: check.C2)_
6. EXAFS coordination number (11.54) exceeds the surface‑adjusted model expectation (8.84) by 2.69, surpassing the fail threshold of 2.0, indicating possible surface segregation, vacancies, or disorder. _(evidence: check.C3)_
7. Oxidation state assessment shows metallic Pt (valence 0.0) with zero discrepancy between XANES and bond‑valence sum, satisfying metallic model criteria. _(evidence: check.C4)_
8. Disorder ratio σ²_EXAFS / σ²_PDF is 0.24, below the acceptable range 0.3–1.3, suggesting static disorder or a distinct surface layer not captured equally by the two probes. _(evidence: check.C5)_
9. Size comparison reveals XRD sphere diameter 2.657 nm and Scherrer median 2.16 nm are larger than PDF particle size 1.61 nm, with relative difference 0.65 exceeding the fail limit of 0.5, indicating a size distribution or surface‑related shrinkage in the PDF. _(evidence: check.C6)_
10. Joint simulation scores are: Pt = 0.4147, Pt₃Co = 0.5812, PtO₂ = 0.9147; Pt has the lowest score, making it the most consistent candidate across XRD, PDF, and EXAFS. _(evidence: check.C7)_
11. Virtual XAFS predicts an Rfactor of 0.603 for Pt, higher than the measured 0.003549, confirming the measured EXAFS quality; predictions for Pt₃Co (0.7813) and PtO₂ (0.9108) are even larger. _(evidence: virtual_xafs)_
12. Vision inspection rejects the XRD fit (extra peaks, unresolved phase) and the PDF fit (lattice drift, high Rw), while the EXAFS fit is accepted. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- Phase consistency check (C1) fails: XRD and PDF cannot be reconciled for any candidate (best PDF Rw = 0.505, XRD score = 0.738).
- Coordination number check (C3) fails: EXAFS N = 11.54 exceeds the surface‑adjusted model expectation of 8.84 by 2.69 (threshold 2.0), indicating possible surface segregation or disorder.
- Disorder ratio check (C5) warns: σ²_EXAFS / σ²_PDF = 0.24, below the acceptable 0.3–1.3 range, suggesting static disorder or a distinct surface layer.
- Size comparison (C6) fails: XRD sphere diameter = 2.66 nm (Scherrer = 2.16 nm) vs PDF particle size = 1.61 nm, relative difference = 0.65 (> 0.5 limit), implying a size distribution or surface‑related shrinkage.
- Vision inspection rejects the XRD fit (extra/unexplained peaks) and the PDF fit (lattice drift, high Rw), while accepting the EXAFS fit.
