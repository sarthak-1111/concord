# Concord report — s0049 (CeO2)

**All techniques confirm a single bulk‑like CeO₂ phase with the expected structure, oxidation state, and coordination.**

Phase: **CeO2**

All three techniques (XRD, PDF, EXAFS) are mutually consistent and support a single CeO2 phase with bulk-like structure, oxidation state, and coordination.

## Key numbers (from the tools)

- **XRD**: best match CeO2 (profile correlation 0.984, 100 % of the peak area explained); sphere diameter 91.4 nm from 9 indexed reflections
- **PDF**: CeO2 refines to Rw 0.064; a 5.4094 Å; U_iso Ce 0.0015 Å², O 0.0126 Å²; no finite-size envelope (bulk)
- **EXAFS** (Ce L3): Ce–O N 7.9 ± 0.3 at 2.342 Å, σ² 0.0078 Å²; R-factor 0.0014
- **XANES**: Ce valence 4.00 from a linear combination of standards, 4.07 from the edge position
- **Bond valence** (PDF model): 4.00

## Evidence by technique

- **XRD**: The XRD ranking score is 0.9906 with a profile correlation of 0.9844, observed area fraction explained 1.0 and peak relative intensity 0.693, indicating an excellent fit; size analysis yields a sphere diameter of 91.44 nm, a Scherrer median of 78.92 nm, a strain of -0.0002022, and 9 indexed peaks.
- **PDF**: The PDF fit gives a goodness‑of‑fit rw = 0.06439 and lattice parameters a = b = c = 5.409 Å (reference 5.41 Å), confirming the CeO₂ crystal structure.
- **EXAFS**: EXAFS analysis shows a Ce–O bond length of 2.342 Å (±0.0033 Å) matching the PDF model, a coordination number of 7.936 (±0.3279) close to the bulk value 8.0, and a Debye‑Waller factor σ² = 0.007819 Å².
- **XANES**: XANES linear combination fitting gives Ce⁴⁺ weight = 1.0, Ce³⁺ weight = 0.0, yielding a valence of 4.0; the bond‑valence sum calculation gives 4.001, matching the formal valence.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on CeO2. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.55–0.55 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | skip | needs an XRD size and a nanoparticle PDF fit |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | CeO2 has the best joint score. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ce L3 EXAFS computed with FEFF from the PDF-refined model (CeO2; 24 ensemble members, Debye temperature 465–475 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0019 in R 1.0–3.5 Å.

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

0. Phase consistency between XRD and PDF: both identify CeO2 with high agreement. _(evidence: check.C1, xrd.ranking, pdf.fit.CeO2)_
1. XRD ranking score 0.9906, profile correlation 0.9844, area explained 1.0, peak relative intensity 0.693 indicate excellent fit. _(evidence: xrd.ranking, check.C1)_
2. PDF fit goodness rw=0.06439 and lattice parameters a=b=c=5.409 Å (reference 5.41 Å) show good agreement with expected CeO2 structure. _(evidence: pdf.fit.CeO2)_
3. EXAFS bond length Ce-O = 2.342 Å (±0.0033 Å) matches PDF model value 2.342 Å within 0.0001 Å. _(evidence: exafs.fit, pdf.fit.CeO2, check.C2)_
4. EXAFS coordination number Ce-O = 7.936 (±0.3279) is consistent with bulk coordination 8.0 (diff -0.06). _(evidence: exafs.fit, check.C3)_
5. XANES LCF weights Ce+4=1.0, Ce+3=0.0 give Ce valence 4.0; bond-valence sum valence 4.001 matches formal valence 4.0. _(evidence: xanes, bvs, check.C4)_
6. Disorder: EXAFS σ²=0.007819 Å², PDF uncorrelated σ²=0.01416 Å², ratio 0.552, as expected for correlated motion. _(evidence: exafs.fit, pdf.fit.CeO2, check.C5)_
7. Joint simulation score: CeO2 best with xrd=0.0156, pdf=0.0644, exafs=0.002, total score=0.0273. _(evidence: check.C7)_
8. XRD size analysis yields sphere diameter 91.44 nm, Scherrer median 78.92 nm, strain -0.0002022, indexed peaks 9. _(evidence: xrd.size)_
9. Virtual XAFS prediction matches measured EXAFS with rfactor_R=0.001878, band coverage k=0.05298, per‑candidate rfactor for CeO2=0.002015. _(evidence: virtual_xafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- No nanoparticle PDF size refinement was performed, so XRD and PDF size consistency could not be directly compared.
- The XANES model is low‑fidelity (simple edge) and does not capture subtle pre‑edge features.
- Uncertainties are limited to the reported statistical errors; systematic errors (e.g., instrument calibration) are not quantified.
