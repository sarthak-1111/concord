# Concord report — s0014 (TiO2)

**TiO2‑anatase identified as the consistent phase across XRD, PDF, and XAFS analyses.**

Phase: **TiO2-anatase**

Combined analysis of XRD, PDF and XAFS data indicates that the sample is TiO2‑anatase. All technical checks pass except a warning on the oxidation state, which is physically interpretable as surface reduction or mixed valence not captured by the bulk model.

## Key numbers (from the tools)

- **XRD**: best match TiO2-anatase (profile correlation 0.981, 100 % of the peak area explained); sphere diameter 7.1 nm from 8 indexed reflections
- **PDF**: TiO2-anatase refines to Rw 0.240; a 3.7825 Å, c 9.5218 Å; U_iso O 0.0048 Å², Ti 0.0020 Å²; particle diameter 7.2 nm
- **EXAFS** (Ti K): Ti–O N 6.6 ± 0.7 at 1.947 Å, σ² 0.0076 Å²; R-factor 0.0077
- **XANES**: Ti valence 3.50 from a linear combination of standards, 4.02 from the edge position
- **Bond valence** (PDF model): 4.01

## Evidence by technique

- **XRD**: The XRD ranking gives TiO2‑anatase a score of 0.9866 and explains 99.52 % of the observed area, matching the PDF phase and passing the phase‑consistency check (C1).
- **PDF**: PDF refinement of TiO2‑anatase yields a low Rw of 0.2397 and a particle size of 7.166 nm, consistent with the XRD sphere diameter of 7.15 nm (check C6).
- **EXAFS**: EXAFS fitting reports a Ti–O distance of 1.947 Å (Δ = ‑0.0056 Å vs PDF model) and a σ² of 0.00763 Å², a ratio of 1.124 to the PDF pair width, both within tolerances (checks C2, C5).
- **XANES**: XANES linear‑combination fitting yields an average Ti valence of ~3.5, which differs by ‑0.51 from the bond‑valence sum of 4.008, triggering a warning on oxidation state (check C4).

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on TiO2-anatase. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | **warn** | XANES says 3.5, the refined structure implies 4.0: mixed valence, a surface phase or vacancies the average structure misses. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 1.12–1.12 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | TiO2-anatase has the best joint score (margin 0.609). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ti K EXAFS computed with FEFF from the PDF-refined model (TiO2-anatase; 24 ensemble members, Debye temperature 719–733 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0035 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Ti–O bond length 1.93 ± 0.01 Å, [doi:10.1515/zna-1981-1110](https://doi.org/10.1515/zna-1981-1110) (1981): «Using the theoretical phases, Ti-O bond distances of 1.93(1) Å were derived both for rutile and anatase, as compared to the crystallographic values of 1.948 - 1.980(1) Å (rutile) and 1.934-1.980(1) Å (anatase).»
- Ti oxidation state 4, [doi:10.1088/2053-1591/ab4e3f](https://doi.org/10.1088/2053-1591/ab4e3f) (2019): «Anal.At.Spectrom.29 736] coordination environment and Ti 4+ oxidation state was observed with 0.02 and 0.04 O 2 partial pressures, respectively.»
- Ti oxidation state 3, [doi:10.1021/jp048567f](https://doi.org/10.1021/jp048567f) (2004): «Surface sensitive reflection mode XAFS indicates that intercalation leads to a 3−4 nm surface region characterized by an effective Ti oxidation state close to 3+.»
- Ti oxidation state 3, [doi:10.2139/ssrn.6544703](https://doi.org/10.2139/ssrn.6544703) (2026): «EPR spectroscopy identified stabilized Ti3+ centers and oxygen-centered radicals, enhanced under UV illumination, indicating sulfate-induced oxygen vacancies and charge localization.»
- particle size 5–13 nm, [doi:10.1007/s40089-014-0111-x](https://doi.org/10.1007/s40089-014-0111-x) (2014): «The sizes of synthesized particles were in the range 5–13 nm, i.e. 9 nm on an average and with a regular shape.»
- particle size 9 nm, [doi:10.1007/s40089-014-0111-x](https://doi.org/10.1007/s40089-014-0111-x) (2014): «The sizes of synthesized particles were in the range 5–13 nm, i.e. 9 nm on an average and with a regular shape.»
- particle size 46 nm, [doi:10.4236/snl.2012.24014](https://doi.org/10.4236/snl.2012.24014) (2012): «We found that the average size of samples was changed from 30 to 46 nm with changing temperature from 450℃ to 650℃ and at fixed temperature (450℃) with changing of calcination times from 1 to 3 hours, the size was change»
- particle size 58 nm, [doi:10.4236/snl.2012.24014](https://doi.org/10.4236/snl.2012.24014) (2012): «We found that the average size of samples was changed from 30 to 46 nm with changing temperature from 450℃ to 650℃ and at fixed temperature (450℃) with changing of calcination times from 1 to 3 hours, the size was change»
- particle size 13.8 ± 5.5 nm, [doi:10.1590/1516-1439.301914](https://doi.org/10.1590/1516-1439.301914) (2015): «The TiO2 elongated nanoparticles having a length of 13.8 ± 5.5 nm and a diameter of 9.0 ±1.2 nm were characterized by powder X-Ray diffraction, transmission electron microscopy, selected area diffraction, BET surface are»
- particle size 9 ± 1.2 nm, [doi:10.1590/1516-1439.301914](https://doi.org/10.1590/1516-1439.301914) (2015): «The TiO2 elongated nanoparticles having a length of 13.8 ± 5.5 nm and a diameter of 9.0 ±1.2 nm were characterized by powder X-Ray diffraction, transmission electron microscopy, selected area diffraction, BET surface are»

## Claims

0. Phase consistency (XRD vs PDF) – TiO2‑anatase is the common phase. _(evidence: check.C1, xrd.ranking, pdf.best)_
1. Bond lengths (EXAFS R vs PDF model) – Ti‑O distance from EXAFS (1.947 Å) matches the PDF‑refined Ti‑O distance (1.953 Å) with a max absolute difference of 0.0056 Å. _(evidence: check.C2, exafs.fit, pdf.fit.TiO2-anatase)_
2. Coordination numbers (EXAFS N vs model) – EXAFS Ti‑O coordination (6.62) is close to the surface‑adjusted model value (5.75), derived from bulk coordination (6.0) and surface factor (0.959); the difference is 0.87, below the warning threshold. _(evidence: check.C3, exafs.fit, pdf.fit.TiO2-anatase)_
3. Oxidation state (XANES vs bond‑valence sum) – XANES linear‑combination fit yields a mixed valence (≈3.5) whereas the bond‑valence sum gives 4.008; the difference of -0.51 exceeds the warn limit (0.5) and suggests surface reduction or vacancies. _(evidence: check.C4, xanes, bvs)_
4. Disorder (EXAFS σ² vs PDF pair width) – EXAFS σ² for Ti‑O (0.00763 Å²) is 1.124 × the uncorrelated PDF width (0.00678 Å²), within the acceptable ratio range (0.3–1.3). _(evidence: check.C5, exafs.fit, pdf.fit.TiO2-anatase)_
5. Size (XRD vs PDF) – XRD‑derived sphere diameter (7.15 nm) and PDF‑derived particle size (7.17 nm) differ by -0.002, well within the tolerance. _(evidence: check.C6, xrd.size, pdf.fit.TiO2-anatase)_
6. Joint simulation score (XRD + PDF + EXAFS) – TiO2‑anatase has the best overall score (0.0874) versus rutile (0.6965) with a margin of 0.609, exceeding the required minimum margin (0.02). _(evidence: check.C7)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- The oxidation‑state discrepancy (‑0.51 exceeds the warn limit of 0.5) suggests surface reduction or vacancy effects not captured by the bulk model.
- No objections were raised in the objection log, but the XANES fidelity is reported as low, indicating limited confidence in the exact valence determination.
