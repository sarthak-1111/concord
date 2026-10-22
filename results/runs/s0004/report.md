# Concord report — s0004 (CeO2)

**All techniques confirm a single‑phase CeO₂ material.**

Phase: **CeO2**

All three techniques (XRD, PDF, EXAFS) are mutually consistent and support a single‑phase CeO₂ model.

## Key numbers (from the tools)

- **XRD**: best match CeO2 (profile correlation 0.985, 100 % of the peak area explained); sphere diameter 87.2 nm from 9 indexed reflections
- **PDF**: CeO2 refines to Rw 0.063; a 5.4096 Å; U_iso Ce 0.0014 Å², O 0.0119 Å²; no finite-size envelope (bulk)
- **EXAFS** (Ce L3): Ce–O N 8.6 ± 0.5 at 2.342 Å, σ² 0.0091 Å²; R-factor 0.0029
- **XANES**: Ce valence 4.00 from a linear combination of standards, 4.15 from the edge position
- **Bond valence** (PDF model): 4.00

## Evidence by technique

- **XRD**: XRD identifies CeO₂ with a ranking score of 0.991, profile correlation of 0.9851, and explains 1.0 (100 %) of the observed area; size analysis gives a sphere diameter of 87.16 nm, a Scherrer median of 74.89 nm and a strain of -0.0002194.
- **PDF**: PDF refinement yields an Rw of 0.06327 and lattice parameters a = b = c = 5.41 Å, matching the reference values.
- **EXAFS**: EXAFS provides a Ce–O bond length of 2.342 Å ± 0.0049 Å, a coordination number of 8.65 ± 0.54 (consistent with bulk CeO₂ coordination of 8), and a disorder parameter σ² of 0.00915 Å² (0.687 × the PDF uncorrelated σ² of 0.01331 Å²).
- **XANES**: XANES linear‑combination fitting shows 100 % Ce⁴⁺ (0 % Ce³⁺) with a valence of 4.0, and the bond‑valence sum gives 4.001, agreeing with the formal valence of 4.0.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on CeO2. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.69–0.69 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | skip | needs an XRD size and a nanoparticle PDF fit |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | CeO2 has the best joint score. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ce L3 EXAFS computed with FEFF from the PDF-refined model (CeO2; 24 ensemble members, Debye temperature 483–491 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0058 in R 1.0–3.5 Å.

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

0. The sample is a single‑phase CeO₂, identified by XRD with a ranking score of 0.991 and profile correlation of 0.9851, explaining 1.0 (100 %) of the observed area. _(evidence: xrd.ranking, check.C1)_
1. PDF refinement confirms CeO₂ with an Rw of 0.06327 and lattice parameters a = b = c = 5.41 Å, identical to the reference values. _(evidence: pdf.fit.CeO2, check.C1)_
2. XRD and PDF phase assignments are consistent; the lattice relative change is 0.0. _(evidence: check.C1)_
3. EXAFS yields a Ce‑O bond length of 2.342 Å (±0.0049 Å), matching the PDF model distance (difference –0.0005 Å). _(evidence: exafs.fit, check.C2)_
4. The EXAFS coordination number for Ce‑O is 8.65 (±0.54), consistent with the bulk CeO₂ coordination of 8 after applying the surface factor. _(evidence: exafs.fit, check.C3)_
5. XANES linear‑combination fitting shows 100 % Ce⁴⁺ (0 % Ce³⁺) with a valence of 4.0; the bond‑valence sum gives 4.001, agreeing with the formal valence of 4.0. _(evidence: xanes, bvs, check.C4)_
6. EXAFS disorder parameter σ² = 0.00915 Å² is 0.687 of the PDF uncorrelated σ² = 0.01331 Å², within the expected 0.3–1.3 range. _(evidence: check.C5)_
7. XRD size analysis gives a sphere diameter of 87.16 nm, a Scherrer median of 74.89 nm, and a strain of –0.0002194; PDF size fit was not performed, so the size cross‑check is skipped. _(evidence: xrd.size, check.C6)_
8. Joint simulation of XRD, PDF and EXAFS yields the best overall score for CeO₂ (combined score = 0.028, with contributions XRD = 0.0149, PDF = 0.0633, EXAFS = 0.0058). _(evidence: check.C7)_
9. Virtual XAFS prediction for the Ce L₃ edge matches the measured data (rfactor_R = 0.00577, band coverage = 0.01987), confirming consistency. _(evidence: virtual_xafs)_
10. Visual inspection by the gpt‑oss judge accepted the XRD, PDF and EXAFS data. _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- PDF size fitting was not performed, so the size cross‑check with XRD is skipped (check C6).
- XANES analysis has low fidelity (simple edge model) and no metallic model component, limiting the precision of oxidation‑state determination (check C4).
