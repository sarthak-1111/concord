# Concord report — s0031 (Pt)

**Phase consistency fails; overall phase set to null.**

Phase: **null**

Phase consistency fails; XRD indicates missing peaks at 10.06° and 38.35° and adding Pt3Co contributes 0 % intensity (RMS unchanged), while PDF fit for Pt is poor (Rw = 0.509 > 0.25) and lattice change (0.03) exceeds tolerance (0.003). No candidate matches both techniques, so overall phase set to null.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.880, 93 % of the peak area explained); sphere diameter 2.6 nm from 2 indexed reflections
- **PDF**: Pt refines to Rw 0.509; a 4.0395 Å; U_iso Pt 0.0196 Å²; particle diameter 1.3 nm
- **EXAFS** (Pt L3): Pt–Pt N 11.2 ± 1.5 at 2.851 Å, σ² 0.0112 Å²; Pt–O N 0.1 ± 0.3 at 2.060 Å, σ² 0.0010 Å² (shell not in the model); R-factor 0.0071
- **XANES**: Pt valence 0.00 from a linear combination of standards, 0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: The diffraction pattern lacks the expected peaks at 10.06° and 38.35°; adding a second phase of Pt3Co contributed 0 % of the simulated intensity and left the RMS unchanged at 540, while adding PtO2 (23 % intensity) reduced the RMS to 519.6 but the fit was still rejected.
- **PDF**: The PDF fit for Pt yields Rw = 0.509 (above the 0.25 tolerance) and a lattice parameter change of 0.03, exceeding the 0.003 warning limit; the particle size from PDF is 1.312 nm.
- **EXAFS**: The Pt–Pt bond length is 2.85 Å, differing from the PDF model by –0.0058 Å (within tolerance), but the coordination number is 11.25 ± 1.5 versus the model 8.14, a deviation of 3.1; the disorder ratio σ²_EXAFS/σ²_PDF is 0.287 (below the lower bound 0.3), and the size discrepancy between XRD (2.63 nm) and PDF (1.31 nm) gives a relative difference of 1.007 (> 0.5 fail threshold). The joint simulation score for Pt is 0.3894 with a margin of 0.1716.
- **XANES**: Linear combination fitting shows 100 % Pt⁰ with a bond‑valence sum valence of 0.0, confirming a metallic Pt state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.51 for Pt). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | **FAIL** | EXAFS coordination differs from the model by up to 3.1: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 0.29–0.29 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
| C6 Size (XRD vs PDF) | **FAIL** | XRD sees larger crystallites than the PDF particle diameter: XRD is volume-weighted (large particles dominate) while the PDF envelope is closer to a number average, or a disordered surface shell shortens the PDF range. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.172). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt; 24 ensemble members, Debye temperature 107–108 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.5381 in R 1.0–3.5 Å.

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

0. Phase consistency fails; set overall phase to null. _(evidence: check.C1, rerun.R2.1.xrd_add_phase, vision.xrd)_
1. EXAFS Pt–Pt bond length (2.85 Å) matches PDF model (2.856 Å) within 0.0058 Å. _(evidence: check.C2)_
2. EXAFS Pt–Pt coordination number (11.25 ± 1.5) deviates from model expectation (8.14) by 3.1, indicating surface under‑coordination or vacancies. _(evidence: check.C3)_
3. XANES LCF shows 100 % Pt⁰ and bond‑valence sum gives valence 0.0, confirming a metallic Pt state. _(evidence: check.C4)_
4. Disorder ratio (EXAFS/PDF σ²) is 0.287, below the lower bound 0.3, implying static disorder or a distorted first shell. _(evidence: check.C5)_
5. Size discrepancy: XRD sphere diameter 2.63 nm vs PDF particle diameter 1.31 nm yields relative difference 1.007, exceeding the fail threshold 0.5. _(evidence: check.C6)_
6. Joint simulation: Pt has the lowest joint score (0.3894) with margin 0.1716, making it the best candidate among those tested. _(evidence: check.C7)_
7. Visual inspection summary: XRD rejected, PDF rejected, EXAFS accepted. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | Phase consistency fails; set overall phase to null. | check.C1 | exafs_window_scan | N over kmax 10-12: Pt 11.58-13.13 | confirmed |
| R2.1 | The claim that the overall phase should be set to null ignores the XRD inspector's identification of missing diffraction peaks (10.06° and 38.35°) and the suggested addition of a second phase; a rerun adding a second candidate phase is required to test whether phase consistency can be restored. | vision.xrd, check.C1 | xrd_add_phase | adding Pt3Co (0 % of the simulated intensity) takes the XRD residual RMS from 540 to 540 | not confirmed |
| R3.1 | The claim that the overall phase should be set to null is not fully justified; while the phase‑consistency check fails for the single‑phase models, the possibility that a different second phase (e.g., PtO2) could resolve the missing XRD peaks and improve PDF agreement has not been tested. | check.C1, vision.xrd, rerun.R2.1.xrd_add_phase | xrd_add_phase | adding PtO2 (23 % of the simulated intensity) takes the XRD residual RMS from 540 to 519.6 | not confirmed |

## Limitations

- XRD rejects the single‑phase model due to missing peaks and negligible intensity contribution from the tested second phase Pt3Co.
- PDF rejects the model because the Rw value (0.509) exceeds the acceptable limit and the lattice parameter shift (0.03) is too large.
- EXAFS coordination number mismatch (diff = 3.1) indicates surface under‑coordination or vacancies, and the disorder ratio (0.287) flags static disorder.
- Size estimates differ markedly between XRD (2.63 nm) and PDF (1.31 nm), exceeding the fail threshold for relative difference.
- The candidate phase list may be incomplete, as adding PtO2 improves the XRD RMS but does not resolve overall consistency.
