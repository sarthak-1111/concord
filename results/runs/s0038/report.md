# Concord report — s0038 (Pt)

**Metallic Pt dominates the sample with negligible PtO₂ contribution.**

Phase: **Pt**

All techniques indicate that the sample is primarily metallic Pt. PtO₂ contribution is negligible, as demonstrated by a very low XRD profile correlation (0.03083), zero intensity share in a dedicated multi‑phase XRD refinement, and a poor PDF fit (Rw 0.9842) compared to Pt (Rw 0.1123). The PDF lattice parameter deviates only slightly from the reference (relative change 0.0025) and improves with a nanoparticle envelope. EXAFS bond lengths, coordination numbers, oxidation state, disorder, and particle size all agree with the Pt model, and the joint simulation score strongly favors Pt over Pt₃Co and PtO₂.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.976, 99 % of the peak area explained); sphere diameter 6.0 nm from 5 indexed reflections
- **PDF**: Pt refines to Rw 0.112; a 3.9119 Å; U_iso Pt 0.0041 Å²; particle diameter 6.0 nm
- **EXAFS** (Pt L3): Pt–Pt N 11.4 ± 0.4 at 2.768 Å, σ² 0.0052 Å²; R-factor 0.0014
- **XANES**: Pt valence 0.00 from a linear combination of standards, -0.07 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking shows a large observed‑area fraction explained for PtO₂ (0.6374) but its profile correlation is very low (0.03083); a dedicated multi‑phase refinement yields zero intensity share for PtO₂ (intensity_share 0.0) and no RMS improvement (850.5 → 850.5), indicating negligible PtO₂.
- **PDF**: PDF fitting gives a good fit for Pt (Rw 0.1123) versus a poor fit for PtO₂ (Rw 0.9842); the Pt lattice parameter deviates only slightly from reference (relative change 0.0025) and improves with a nanoparticle envelope (Rw 0.1123 vs 0.2076).
- **EXAFS**: EXAFS Pt‑Pt bond length (2.768 Å) matches the PDF‑refined distance (2.766 Å, diff 0.0019 Å) and coordination number (11.35) matches the surface‑truncated PDF model (11.17, diff 0.18); σ² (0.00518 Å²) is 0.631 of the uncorrelated PDF pair width (0.00821 Å²).
- **XANES**: XANES linear combination fit gives Pt in oxidation state 0, identical to the bond‑valence‑sum result (0).

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.63–0.63 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.163). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co; 24 ensemble members, Debye temperature 218–237 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0303 in R 1.0–3.5 Å.

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

0. XRD ranking shows a large observed‑area fraction explained for PtO₂ (0.6374) but its profile correlation is very low (0.03083); a dedicated multi‑phase XRD refinement yields zero intensity share for PtO₂ (intensity_share 0.0) and no improvement in RMS (850.5 → 850.5), indicating negligible PtO₂ contribution. PDF fitting for PtO₂ has a high Rw (0.9842) versus Pt (0.1123), further confirming the absence of PtO₂. Together with the XRD and PDF agreement on Pt, the dominant phase is metallic Pt. _(evidence: xrd.ranking, rerun.R2.1.xrd_add_phase, pdf.best, pdf.fit.PtO2, pdf.fit.Pt, check.C1, check.C7)_
1. The PDF refined lattice parameter for Pt differs from the reference by a relative change of 0.0025, which is within the warning tolerance of 0.003, and the fit improves when a nanoparticle envelope is included (Rw 0.1123 vs 0.2076). _(evidence: check.C1, pdf.fit.Pt, rerun.R1.2.pdf_toggle_envelope)_
2. EXAFS Pt‑Pt bond length (2.768 Å) matches the PDF‑refined Pt‑Pt distance (2.766 Å) with a difference of 0.0019 Å. _(evidence: check.C2)_
3. EXAFS Pt‑Pt coordination number (11.35) matches the surface‑truncated PDF model (11.17) with a difference of 0.18. _(evidence: check.C3)_
4. XANES linear combination fit shows Pt in oxidation state 0, which equals the bond‑valence‑sum result (0). _(evidence: check.C4)_
5. EXAFS σ² (0.00518 Å²) is 0.631 times the uncorrelated PDF pair width (0.00821 Å²), as expected. _(evidence: check.C5)_
6. Particle size from XRD (sphere diameter 5.99 nm) and PDF (diameter 6.02 nm) have a relative difference of -0.006, indicating agreement. _(evidence: check.C6, xrd.size, pdf.fit.Pt)_
7. Joint simulation score favors Pt (score 0.0457) over Pt₃Co and PtO₂, with a margin of 0.1631. _(evidence: check.C7)_
8. No significant Pt‑O coordination was detected; the extra shell contribution is negligible. _(evidence: exafs.extra_shell)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The statement that the sample is "pure Pt" is not fully supported: the XRD ranking lists a non‑zero area fraction explained for PtO₂ (0.6374) even though its profile correlation is low, and the analysis does not explicitly rule out a minor PtO₂ phase. | xrd.ranking, check.C1 | xrd_add_phase | re-run xrd_add_phase failed: TypeError | failed |
| R1.2 | The PDF refined lattice parameter differs from the reference by a relative change of 0.0025, which is close to the warning tolerance of 0.003. A re‑fit with the nanoparticle envelope toggled on/off would test whether this deviation is model‑dependent. | check.C1, pdf.fit.Pt | pdf_toggle_envelope | Pt without the particle envelope: Rw 0.208 (was 0.112) | not confirmed |
| R2.1 | The claim that PtO₂ contribution is negligible is not fully supported: the XRD ranking shows a large observed‑area fraction explained for PtO₂ (0.6374) despite its low profile correlation, which contradicts the statement of negligible PtO₂. A dedicated multi‑phase XRD refinement is needed to assess the PtO₂ fraction. | xrd.ranking, pdf.fit.PtO2, check.C1 | xrd_add_phase | adding PtO2 (0 % of the simulated intensity) takes the XRD residual RMS from 850.5 to 850.5 | not confirmed |

## Limitations

- The XRD ranking reports a non‑zero area fraction for PtO₂ (0.6374) despite its low profile correlation, and the multi‑phase refinement could not reduce the residual RMS, leaving a minor uncertainty about trace PtO₂.
- The PDF lattice parameter change (0.0025) is close to the warning tolerance (0.003), and the fit quality degrades without the nanoparticle envelope (Rw 0.208), indicating sensitivity to model choice.
