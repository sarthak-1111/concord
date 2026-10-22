# Concord report — s0017 (CeO2)

**Concord analysis identifies CeO2 as the best candidate but highlights PDF fit deficiencies and mixed Ce valence.**

Phase: **CeO2**

Concord analysis of a CeO2 sample shows XRD and EXAFS data consistent with CeO2, while the PDF fit quality is insufficient (Rw = 0.3099 > 0.25), indicating possible heterogeneity or missing phases. The PDF-derived lattice constant deviates by a relative change of 0.0055, exceeding the warning tolerance of 0.003, suggesting possible dopants, vacancies, or a reduced/oxidised phase. XANES reveals mixed Ce valence (effective ~3.86) deviating from the formal Ce4+ state. Overall, CeO2 remains the best candidate among those considered.

## Key numbers (from the tools)

- **XRD**: best match CeO2 (profile correlation 0.949, 100 % of the peak area explained); sphere diameter 7.0 nm from 9 indexed reflections
- **PDF**: CeO2 refines to Rw 0.310; a 5.4397 Å; U_iso Ce 0.0014 Å², O 0.0078 Å²; particle diameter 6.2 nm
- **EXAFS** (Ce L3): Ce–O N 7.4 ± 0.5 at 2.357 Å, σ² 0.0075 Å²; R-factor 0.0044
- **XANES**: Ce valence 3.86 from a linear combination of standards, 3.69 from the edge position
- **Bond valence** (PDF model): 3.86

## Evidence by technique

- **XRD**: XRD ranks CeO2 highest with a profile correlation of 0.9492 and explains 0.996 of the diffraction intensity, though weak peaks at 27.84° and 46.69° remain unassigned.
- **PDF**: PDF refinement to CeO2 yields a weighted‑R factor of 0.3099 (exceeding the recommended 0.25 threshold) and a lattice constant a = 5.44 Å, a relative change of 0.0055 versus the reference 5.41 Å.
- **EXAFS**: EXAFS fitting gives a Ce‑O bond length of 2.357 ± 0.0057 Å (matching the PDF model distance of 2.356 Å within 0.0016 Å) and a coordination number of 7.44 ± 0.54, consistent with the surface‑truncated model value of 7.54.
- **XANES**: XANES linear‑combination fitting yields Ce³⁺ weight 0.1448 and Ce⁴⁺ weight 0.8552, giving an effective valence of ~3.86, below the formal Ce⁴⁺ state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **warn** | XRD and PDF agree on CeO2, but the refined lattice differs from the database value by 0.55 %: a dopant, vacancies or a reduced/oxidised phase can change it. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | **FAIL** | The refined bond lengths (bond-valence sum 3.86) and the XANES edge (3.69) both put the valence below the formal 4: mixed valence or non-stoichiometry (for example reduced cations with oxygen vacancies) that the stoichiometric model lacks. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.82–0.82 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | CeO2 has the best joint score. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ce L3 EXAFS computed with FEFF from the PDF-refined model (CeO2; 24 ensemble members, Debye temperature 489–495 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0053 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Ce oxidation state 4, [doi:10.1002/cctc.202001829](https://doi.org/10.1002/cctc.202001829) (2021): «The Cu K‐edge and Ce L3‐edge XANES and EXAFS analyses revealed the dynamic and crucial role of Cu2+/Cu+ and Ce4+/Ce3+ ionic pairs during the catalytic reaction.»
- Ce oxidation state 3, [doi:10.1002/cctc.202001829](https://doi.org/10.1002/cctc.202001829) (2021): «The Cu K‐edge and Ce L3‐edge XANES and EXAFS analyses revealed the dynamic and crucial role of Cu2+/Cu+ and Ce4+/Ce3+ ionic pairs during the catalytic reaction.»
- Ce oxidation state 3, [doi:10.1039/c1jm14251h](https://doi.org/10.1039/c1jm14251h) (2011): «The specific Ce3+/Ce4+ ratio was also qualitatively determined by fitting the Ce LIII-edge XANES spectra.»
- Ce oxidation state 4, [doi:10.1039/c1jm14251h](https://doi.org/10.1039/c1jm14251h) (2011): «The specific Ce3+/Ce4+ ratio was also qualitatively determined by fitting the Ce LIII-edge XANES spectra.»
- Ce oxidation state 4, [doi:10.1021/acs.jpcc.8b03596](https://doi.org/10.1021/acs.jpcc.8b03596) (2018): «In situ TR-XRD and AP-XPS characterization showed significant changes in the chemical state of the catalysts under reaction conditions, with the copper being fully reduced and a partial Ce 4+ → Ce 3+ transformation occur»
- Ce oxidation state 3, [doi:10.1021/acs.jpcc.8b03596](https://doi.org/10.1021/acs.jpcc.8b03596) (2018): «In situ TR-XRD and AP-XPS characterization showed significant changes in the chemical state of the catalysts under reaction conditions, with the copper being fully reduced and a partial Ce 4+ → Ce 3+ transformation occur»
- particle size 14.46 nm, [doi:10.1063/1.4946479](https://doi.org/10.1063/1.4946479) (2016): «The average crystallite size was found to be 14.46 nm to 21.57 nm.»
- particle size 21.57 nm, [doi:10.1063/1.4946479](https://doi.org/10.1063/1.4946479) (2016): «The average crystallite size was found to be 14.46 nm to 21.57 nm.»
- particle size 10 nm, [doi:10.17780/ksujes.1369994](https://doi.org/10.17780/ksujes.1369994) (2024): «The calculated crystallite particle size utilizing the Scherrer equation was 10 nm.»
- particle size 5.2 nm, [doi:10.1371/journal.pone.0122989](https://doi.org/10.1371/journal.pone.0122989) (2015): «The average crystalline domain diameter was found to be 5.2 nm, with a very narrow size distribution.»
- particle size 19 nm, [doi:10.21203/rs.3.rs-8722013/v1](https://doi.org/10.21203/rs.3.rs-8722013/v1) (2026): «A high-resolution transmission electron microscope (HTEM) was used to analyze the morphology of the particles, which have a size range of 8 to 19 nm at different temperatures such as 300, 400, and 500 0 C.»
- particle size 15–40 nm, [doi:10.1134/s0020168524701097](https://doi.org/10.1134/s0020168524701097) (2024): «The material prepared from PC/Ce(NO3)3/NaCl consisted of two types of CeO2 particles: particles 15–40 nm in diameter (forming irregularly shaped structures) and particles 1.5–2.2 nm in diameter.»

## Claims

0. XRD data are best described by the CeO2 phase with a profile correlation of 0.9492, explaining 0.996 of the diffraction intensity; the refined lattice shows a relative change of 0.0055, and weak peaks at 27.84° and 46.69° remain unassigned. _(evidence: xrd.ranking, xrd.size, check.C1, vision.xrd)_
1. PDF refinement to CeO2 yields a weighted‑R factor of 0.3099, which exceeds the recommended threshold of 0.25, indicating a poor fit. _(evidence: pdf.fit.CeO2, vision.pdf, check.C1)_
2. A re‑run of the PDF refinement without the particle‑size envelope gives an even higher Rw of 0.3589, confirming the inadequate PDF fit. _(evidence: rerun.R1.1.pdf_toggle_envelope)_
3. The PDF‑derived lattice constant a = 5.44 Å differs from the reference value 5.41 Å by a relative change of 0.0055, which exceeds the warning tolerance of 0.003, indicating a lattice shift beyond acceptable limits. _(evidence: pdf.fit.CeO2, check.C1)_
4. The PDF‑derived particle size of 6.163 nm agrees with the XRD sphere diameter of 6.98 nm within a relative difference of 0.132. _(evidence: pdf.fit.CeO2, xrd.size, check.C6)_
5. EXAFS fitting gives a Ce‑O bond length of 2.357 Å (±0.0057 Å), matching the PDF model distance of 2.356 Å within a difference of 0.0016 Å. _(evidence: exafs.fit, check.C2)_
6. The EXAFS coordination number for Ce‑O is 7.44 ± 0.54, matching the surface‑truncated model value of 7.54 (difference −0.1). _(evidence: exafs.fit, check.C3)_
7. The EXAFS Debye‑Waller factor σ² for the Ce‑O pair is 0.00752 Å², which is 0.817 times the uncorrelated PDF width (0.0092 Å²), within the expected ratio range. _(evidence: exafs.fit, check.C5)_
8. XANES linear‑combination fitting yields Ce³⁺ weight 0.1448 and Ce⁴⁺ weight 0.8552, giving an effective valence of 3.855; the bond‑valence sum gives 3.862, both below the formal Ce⁴⁺ valence of 4.0, causing check.C4 to fail and indicating mixed valence or oxygen vacancies. _(evidence: xanes, bvs, check.C4)_
9. Joint simulation across XRD, PDF, and EXAFS assigns the highest combined score to CeO2 (score = 0.122), confirming it as the best candidate. _(evidence: check.C7)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The claim states that the overall structural model is reasonable despite the elevated PDF weighted‑R factor (Rw = 0.3099), yet the evidence shows a PDF quality failure (Rw above the recommended 0.25 threshold) and the visual PDF inspector flags this as a problem. No supporting evidence is provided for the model’s overall reasonableness. | pdf.fit.CeO2, vision.pdf | pdf_toggle_envelope | CeO2 without the particle envelope: Rw 0.359 (was 0.310) | not confirmed |
| R2.1 | The claim that the lattice constant shift (relative change 0.0055) is "within the warning tolerance" is incorrect: check.C1 sets the warning tolerance for lattice shifts at 0.003, and the observed relative change of 0.0055 exceeds this, triggering a warning status. | pdf.fit.CeO2, check.C1 | – | no re-run requested; the analyst must answer it | open |

## Limitations

- PDF fit quality is poor (Rw = 0.3099 > 0.25) and worsens without the particle‑size envelope (Rw = 0.3589), indicating possible heterogeneity or missing phases.
- The lattice‑constant shift (relative change 0.0055) exceeds the warning tolerance of 0.003, triggering a caution about dopants, vacancies, or a reduced/oxidised phase.
- XANES oxidation‑state assessment fails the check (effective valence 3.86 vs formal 4.0), suggesting mixed valence or oxygen vacancies not captured by the stoichiometric CeO2 model.
