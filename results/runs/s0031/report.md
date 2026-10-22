# Concord report — s0031 (Pt)

**Metallic Pt is the only candidate matching any measurements, but cross‑technique consistency checks fail, indicating missing phases or structural disorder.**

Phase: **None**

Metallic Pt is the only candidate that matches any of the measurements, but several cross‑technique consistency checks fail, indicating missing phases or structural disorder.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.864, 55 % of the peak area explained); sphere diameter 2.7 nm from 1 indexed reflections
- **PDF**: Pt refines to Rw 0.505; a 4.0371 Å; U_iso Pt 0.0237 Å²; particle diameter 1.6 nm
- **EXAFS** (Pt L3): Pt–Pt N 13.1 ± 2.2 at 2.847 Å, σ² 0.0131 Å²; R-factor 0.0610
- **XANES**: Pt valence 0.00 from a linear combination of standards, 0.04 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking shows Pt as the dominant phase (score = 0.7377, profile_corr = 0.8644) but accounts for only 54.8 % of the observed diffraction area, and two peaks at 10.06° and 38.1° remain unexplained.
- **PDF**: PDF fit to Pt yields a high Rw of 0.5054, a lattice parameter a = 4.037 Å (reference = 3.922 Å, 2.94 % larger), and a particle size of 1.61 nm, all indicating a poor fit.
- **EXAFS**: EXAFS fit has an R‑factor of 0.06095 and a Pt–Pt coordination number N = 13.13 ± 2.18, which exceeds the surface‑adjusted model value of 8.84 by 4.29.
- **XANES**: XANES linear‑combination fitting gives 100 % Pt⁰ (valence = 0.0) with no contribution from oxidized Pt species.

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

0. The sample is metallic Pt, as indicated by the composition label, XANES linear combination fitting (100 % Pt⁰) and bond‑valence sum (valence = 0). _(evidence: sample, xanes, bvs)_
1. XRD ranking shows Pt as the dominant crystalline phase (score = 0.7377, profile correlation = 0.8644) but only explains 54.8 % of the observed diffraction area; two peaks at 10.06° and 38.1° remain unexplained, suggesting additional unmodelled phase(s). _(evidence: xrd.ranking, check.C1, vision.xrd)_
2. Phase‑consistency check C1 fails: the PDF best fit to Pt has a high Rw of 0.5054 (above the 0.25 limit) and the lattice parameter differs by 2.94 % from the reference, indicating that the true phase may be missing from the candidate list. _(evidence: pdf.fit.Pt, pdf.best, check.C1)_
3. PDF fit to Pt yields a lattice parameter a = 4.037 Å (reference = 3.922 Å) and a particle size psize = 1.61 nm, but the fit quality (Rw = 0.5054) is poor. _(evidence: pdf.fit.Pt, pdf.best)_
4. EXAFS bond length for the Pt–Pt pair (R = 2.847 Å) matches the PDF‑model distance (2.855 Å) within 0.007 Å, satisfying the bond‑length consistency check (C2). _(evidence: exafs.fit, check.C2)_
5. EXAFS coordination number for Pt–Pt (N = 13.13 ± 2.18) exceeds the surface‑adjusted model value (8.84) by 4.29, failing the coordination‑number check (C3) and suggesting surface segregation, vacancies or disorder. _(evidence: exafs.fit, check.C3)_
6. The disorder ratio (EXAFS σ² = 0.01309 Å² vs PDF σ² ≈ 0.01409 Å²) is 0.276, below the acceptable 0.3–1.3 range, triggering a warning (C5) that points to static disorder or a distinct surface layer. _(evidence: check.C5)_
7. Particle‑size estimates differ: XRD sphere diameter = 2.66 nm (Scherrer = 2.16 nm) versus PDF particle diameter = 1.61 nm, a relative difference of 0.65, which fails the size‑consistency check (C6). _(evidence: xrd.size, pdf.fit.Pt, check.C6)_
8. Joint simulation scores rank Pt as the best overall candidate (score = 0.4147) with a margin of 0.1665 over the next best, supporting Pt as the most plausible phase among the tested list. _(evidence: check.C7)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- Phase‑consistency check C1 fails (PDF Rw = 0.505 > 0.25, lattice deviation = 0.0294).
- Coordination‑number check C3 fails (difference = 4.29 > 2.0).
- Disorder ratio check C5 warns (ratio = 0.276 < 0.3).
- Size‑consistency check C6 fails (relative difference = 0.65 > 0.5).
- EXAFS R‑factor exceeds the acceptable limit (0.06095 > 0.05).
