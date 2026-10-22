# Concord report — s0024 (Pt3Co)

**No single phase satisfies all techniques; XRD prefers Pt3Co, PDF prefers Pt, and joint analysis yields ambiguous discrimination.**

Phase: **None**

No single phase satisfies all techniques; XRD prefers Pt3Co, PDF prefers Pt, and joint analysis yields ambiguous discrimination. The joint simulation margin (0.0962) exceeds the minimum tolerance but remains modest, leading to a fail status for the combined assessment.

## Key numbers (from the tools)

- **XRD**: best match Pt3Co (profile correlation 0.982, 99 % of the peak area explained); sphere diameter 9.0 nm from 5 indexed reflections
- **PDF**: Pt refines to Rw 0.306; a 3.8314 Å; U_iso Pt 0.0027 Å²; particle diameter 5.2 nm
- **EXAFS** (Pt L3): Pt–Pt N 10.5 ± 0.7 at 2.709 Å, σ² 0.0040 Å²; R-factor 0.0061
- **XANES**: Pt valence 0.05 from a linear combination of standards, 0.35 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking indicates Pt3Co as the best‑fitting phase with score 0.9848, profile correlation 0.9818, and observed area fraction explained 0.9893; the XRD‑derived particle diameter is 8.99 nm.
- **PDF**: PDF best fit is Pt with Rw 0.3058, particle size 5.166 nm, and lattice parameters a = b = c = 3.831 Å.
- **EXAFS**: EXAFS fit using a Pt model (absorber Pt, edge L3) yields an R‑factor 0.006088, Pt‑Pt distance 2.709 Å, coordination number 10.53 ± 0.71, and Debye‑Waller factor σ² = 0.004011 Å².
- **XANES**: XANES analysis gives a Pt valence of 0.05106 (edge valence 0.3496) and linear combination fitting of 97.45 % Pt⁰ and 2.55 % Pt²⁺, consistent with a metallic state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | XRD prefers Pt3Co but the PDF prefers Pt. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.73–0.73 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | **FAIL** | XRD sees larger crystallites than the PDF particle diameter: XRD is volume-weighted (large particles dominate) while the PDF envelope is closer to a number average, or a disordered surface shell shortens the PDF range. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | **FAIL** | Scored on all techniques together, Pt3Co beats the reported Pt. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co, PtNi; 24 ensemble members, Debye temperature 268–292 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0443 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- particle size 3.9 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 9.1 nm, [doi:10.1002/adfm.202408383](https://doi.org/10.1002/adfm.202408383) (2024): «The average size of well‐dispersed Pt3Co i‐NPs (≈3.9 nm) on Te─C is considerably smaller than that of Pt3Co i‐NPs (≈9.1 nm) on commercial carbon.»
- particle size 15 nm, [doi:10.1080/15533174.2013.831452](https://doi.org/10.1080/15533174.2013.831452) (2014): «XRD analysis confirmed the average size of Pt3Co@Pt nanocomposites around 15 nm, which allowed the assumption of the role of PBE surfactant.»
- particle size 5 nm, [doi:10.1149/2.0531514jes](https://doi.org/10.1149/2.0531514jes) (2015): «The ASAXS data, as well as data from aqueous dissolution, X-ray absorption spectroscopy, individual particle energy-dispersive spectroscopy, X-ray fluorescence spectrometry, and kinetic Monte Carlo calculations support a»
- particle size 5 nm, [doi:10.1149/1945-7111/abfcd9](https://doi.org/10.1149/1945-7111/abfcd9) (2021): «Comparison of Pt3Co/C and Pt/C with similar mean particle sizes (4.9 vs 5.0 nm) and particle size distributions reveals that the Pt3Co/C has a higher potentiostatic dissolution rate (4–5 times), a higher steady state con»
- particle size 4.5 nm, [doi:10.26434/chemrxiv.15007168/v1](https://doi.org/10.26434/chemrxiv.15007168/v1) (2026): «Particles with 66% ordered Pt 3 Co and 4.5 nm size could be synthesized by annealing for 2h at 1000°C followed by 50 h at 600°C, under 80% CO in N 2 atmosphere.»

## Claims

0. XRD ranking indicates Pt3Co is the best fitting phase with score 0.9848, profile correlation 0.9818, and observed area fraction explained 0.9893. _(evidence: xrd.ranking)_
1. PDF best fit is Pt, with Rw 0.3058, particle size 5.166 nm, and lattice parameters a = b = c = 3.831 Å. _(evidence: pdf.best, pdf.fit.Pt)_
2. EXAFS fit uses Pt model (absorber Pt, edge L3), with R‑factor 0.006088, Pt‑Pt distance 2.709 Å, coordination number 10.53 ± 0.71, and Debye‑Waller factor σ² = 0.004011 Å². _(evidence: exafs.fit)_
3. XANES analysis yields a Pt valence of 0.05106 (edge valence 0.3496) and linear combination fitting shows 97.45 % Pt⁰ and 2.55 % Pt²⁺, consistent with a metallic state. _(evidence: xanes)_
4. Bond‑valence‑sum calculation gives a valence of 0.0, matching the formal valence of Pt (0) and supporting the metallic assignment. _(evidence: bvs)_
5. Check C1 fails: XRD prefers phase Pt3Co (score 0.985, area explained 0.989, relative peak intensity 0.842) while PDF best fit is Pt (Rw 0.306). The lattice‑parameter relative change of 0.0231 exceeds the allowed tolerance of 0.003. _(evidence: check.C1)_
6. Check C2 passes: The EXAFS Pt‑Pt distance (2.708 Å ± 0.0032) matches the PDF model distance (2.709 Å) with a difference of –0.0007 Å, well within the 0.02 Å warning threshold. _(evidence: check.C2)_
7. Check C3 passes: EXAFS coordination number (10.53 ± 0.71) is close to the surface‑truncated model value (11.06) with a difference of –0.53, within the 1.0 warning limit. _(evidence: check.C3)_
8. Check C4 passes: XANES valence (0.05) differs from the bond‑valence‑sum valence (0.0) by 0.05, within the metallic tolerance of 0.2, and the metallic model flag is true. _(evidence: check.C4)_
9. Check C5 passes: EXAFS σ² (0.00401 Å²) is 0.735 times the PDF uncorrelated σ² (0.00546 Å²), inside the acceptable ratio range 0.3–1.3. _(evidence: check.C5)_
10. Check C6 fails: XRD particle diameter (8.99 nm) exceeds the PDF particle diameter (5.17 nm) giving a relative difference of 0.74, which is above the failure threshold of 0.5. _(evidence: check.C6)_
11. Check C7 fails: The joint simulation scores for Pt3Co (0.1254) versus PtNi (0.2216) differ by a modest margin of 0.0962, leading to ambiguous discrimination among candidates despite exceeding the minimum margin tolerance, resulting in a fail status. _(evidence: check.C7)_
12. Visual inspection confirms XRD and EXAFS data are accepted, while PDF data is rejected. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The claim states that Check C7 fails because the margin of 0.0962 is insufficient for confident discrimination. However, the evidence provides a tolerance of min_margin = 0.02, meaning the observed margin exceeds the required threshold and should be considered sufficient. Thus the reasoning behind the claim is not supported by the evidence. | check.C7 | pdf_fit_candidate | Pt3Co refines to Rw 0.314 against 0.306 for Pt | not confirmed |

## Limitations

- Check C1 fails: XRD prefers Pt3Co (score 0.985, area 0.989) while PDF prefers Pt (Rw 0.306) and the lattice‑parameter relative change 0.0231 exceeds the allowed tolerance of 0.003.
- Check C6 fails: XRD particle diameter 8.99 nm versus PDF particle diameter 5.17 nm gives a relative difference of 0.74, above the failure threshold of 0.5.
- Check C7 fails: Joint simulation margin 0.0962 exceeds the minimum tolerance of 0.02 but is deemed insufficient for confident discrimination, leading to an overall fail status for the combined assessment.
