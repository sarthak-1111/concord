# Concord report — s0009 (Pt)

**Metallic Pt nanoparticles ~3 nm, Pt‑Pt bond 2.77 Å, zero‑valent Pt.**

Phase: **Pt**

All quantitative cross‑technique checks agree that the sample consists of metallic Pt nanoparticles of ~3 nm size, with Pt–Pt bond length ~2.77 Å, reduced coordination due to finite size, and no oxidation.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.958, 95 % of the peak area explained); sphere diameter 3.2 nm from 4 indexed reflections
- **PDF**: Pt refines to Rw 0.074; a 3.9229 Å; U_iso Pt 0.0041 Å²; particle diameter 2.6 nm
- **EXAFS** (Pt L3): Pt–Pt N 9.4 ± 0.7 at 2.772 Å, σ² 0.0043 Å²; R-factor 0.0069
- **XANES**: Pt valence 0.00 from a linear combination of standards, -0.03 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD identifies the phase as Pt with a ranking score of 0.9552, profile correlation 0.9576 and explains 0.952 of the observed area; the sphere diameter from the size analysis is 3.18 nm (Scherrer median 2.38 nm) and the relative size difference to PDF is 0.223.
- **PDF**: PDF fitting selects Pt as the best candidate (rw = 0.07404) with a refined particle size of 2.6 nm and lattice parameter a = 3.923 Å (reference 3.922 Å).
- **EXAFS**: EXAFS yields a Pt‑Pt bond length of 2.772 Å (σ² = 0.00425 Å²) matching the PDF model distance of 2.774 Å (Δ = ‑0.0019 Å); the average coordination number is 9.37 ± 0.65, and the disorder ratio σ²_exafs/σ²_PDF is 0.514. Visual inspection flags a low Durbin‑Watson statistic of 0.8257.
- **XANES**: XANES L₃‑edge linear combination fitting gives 100 % Pt⁰ (valence 0.0) with a bond‑valence sum of 0.0, confirming the metallic zero‑valent state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Pt. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.51–0.51 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Pt has the best joint score (margin 0.108). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co; 24 ensemble members, Debye temperature 213–236 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0572 in R 1.0–3.5 Å.

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

0. The crystalline phase present in the sample is metallic Pt. _(evidence: check.C1, xrd.ranking, pdf.best, check.C7)_
1. The Pt–Pt bond length is 2.772 Å (EXAFS) and matches the PDF refined distance of 2.774 Å (Δ=−0.0019 Å). _(evidence: check.C2)_
2. The average Pt–Pt coordination number from EXAFS is 9.37 ± 0.65, consistent with a size‑reduced particle (model N≈10.09 after surface truncation). _(evidence: check.C3)_
3. The Pt atoms are in the metallic zero‑valent state (Pt⁰), as indicated by XANES L₃ edge linear combination fitting (100 % Pt⁰) and bond‑valence sum (0.0). _(evidence: check.C4)_
4. The disorder parameter σ² from EXAFS (0.00425 Å²) is ~0.51 of the uncorrelated PDF pair width (0.00827 Å²), as expected for bonded neighbors. _(evidence: check.C5)_
5. The particle size is ~3 nm: XRD sphere diameter 3.18 nm, PDF diameter 2.6 nm, relative difference 0.223 (<0.25). _(evidence: check.C6, xrd.size)_
6. Joint simulation of XRD, PDF and EXAFS yields the lowest combined score for Pt (0.0417) with a margin of 0.108 over the next candidate, satisfying the minimum margin requirement. _(evidence: check.C7)_
7. Visual inspection of the EXAFS data flagged a low Durbin‑Watson statistic (0.8257), indicating possible correlated residuals, but all quantitative checks passed. _(evidence: vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- The EXAFS visual check reports a low Durbin‑Watson statistic (0.8257), indicating possible correlated residuals despite passing quantitative checks.
- XANES fidelity is noted as low (simple edge model) which may limit sensitivity to minor oxidation states.
- Size agreement between XRD and PDF shows a relative difference of 0.223, close to the warning threshold of 0.25.
