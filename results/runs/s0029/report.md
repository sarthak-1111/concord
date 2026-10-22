# Concord report — s0029 (PtNi)

**PtNi phase confirmed with concordant XRD and PDF data.**

Phase: **PtNi**

Concord analysis of the PtNi sample combining XRD and PDF data.

## Key numbers (from the tools)

- **XRD**: best match PtNi (profile correlation 0.971, 97 % of the peak area explained); sphere diameter 4.5 nm from 5 indexed reflections
- **PDF**: PtNi refines to Rw 0.088; a 3.7852 Å; U_iso Pt 0.0029 Å²; particle diameter 4.4 nm

## Evidence by technique

- **XRD**: The XRD ranking identifies PtNi as the top candidate with a score of 0.9693, profile correlation of 0.9712 and observed area fraction explained of 0.9665.
- **PDF**: PDF refinement selects PtNi as the best fit (rw = 0.08845) with lattice parameters a = b = c = 3.785 Å matching the reference.
- **EXAFS**: EXAFS analysis is unavailable; checks C2‑C5 are skipped due to missing EXAFS data.
- **XANES**: XANES analysis is unavailable; check C4 is skipped due to missing XANES data.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on PtNi. |
| C2 Bond lengths (EXAFS R vs PDF model) | skip | needs EXAFS and PDF |
| C3 Coordination numbers (EXAFS N vs model) | skip | needs EXAFS and PDF |
| C4 Oxidation state (XANES vs bond-valence sum) | skip | needs XANES and a PDF-refined structure |
| C5 Disorder (EXAFS σ² vs PDF pair width) | skip | needs EXAFS and PDF |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | PtNi has the best joint score (margin 0.049). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt3Co, PtNi; 24 ensemble members, Debye temperature 259–283 K). Measure the Pt L3 edge to k ≥ 12 Å⁻¹. The prediction is least certain near R ≈ 3.3 Å (band ±66 % of the median |χ(R)|); the measurement would discriminate the PDF-equivalent phases Pt3Co, PtNi.

## Literature priors (other samples: context, not constraints)

- particle size 3 nm, [doi:10.1557/proc-1217-y08-03](https://doi.org/10.1557/proc-1217-y08-03) (2009): «The average grain sizes observed with a TEM were around 3 nm in diameter.»
- particle size 2–5 nm, [doi:10.3390/catal6120201](https://doi.org/10.3390/catal6120201) (2016): «The size of PtNi alloy nanoparticles is approximately 2–5 nm.»
- particle size 2–16 nm, [doi:10.1080/17458080.2013.838703](https://doi.org/10.1080/17458080.2013.838703) (2013): «It was observed that the deposited Pt and PtNi bimetallic nanoparticles on the surface of CNTs had average particle sizes of 2–16 nm, when they were prepared from the polyol method.»
- particle size 8.3 nm, [doi:10.1149/1.1802135](https://doi.org/10.1149/1.1802135) (2004): «The carbon-supported PtNi nanoparticles had a mean diameter of 8.3 nm and were obtained by a two-stage process involving the ballmilling of carbon and the precursor and the thermal degradation of the homogenized mixture »
- particle size 3.7 nm, [doi:10.1039/c9nr08352a](https://doi.org/10.1039/c9nr08352a) (2019): «The resulting PtNi alloy nanoparticles have a narrow size distribution with an average diameter of 3.7 nm, which are smaller than those obtained via classical solution growth.»
- particle size 2.9–5.8 nm, [doi:10.1039/b307040a](https://doi.org/10.1039/b307040a) (2003): «The average particle size of PtNi prepared by microwave irradiation was the lowest, in the range of 2.9–5.8 nm.»

## Claims

0. The sample phase is PtNi, as identified by XRD ranking and PDF best fit. _(evidence: xrd.ranking, pdf.best, check.C1)_
1. Lattice parameters a = b = c = 3.785 Å, matching the PDF refinement for PtNi. _(evidence: pdf.fit.PtNi)_
2. Particle size from XRD sphere diameter is 4.542 nm; PDF particle size is 4.37 nm; relative difference is 0.039, indicating agreement between techniques. _(evidence: xrd.size, pdf.fit.PtNi, check.C6)_
3. Joint simulation score favors PtNi with combined score 0.0586 and margin 0.0485, better than Pt3Co and PtO2. _(evidence: check.C7)_
4. Checks C1, C6, and C7 pass, confirming phase consistency, size agreement, and joint score ranking. _(evidence: check.C1, check.C6, check.C7)_
5. Checks C2, C3, C4, and C5 are skipped due to missing EXAFS/XANES data. _(evidence: check.C2, check.C3, check.C4, check.C5)_
6. Virtual XAFS predicts that measurement of the Pt L3 edge to k ≥ 12 Å⁻¹ would discriminate PtNi from Pt3Co, especially near R ≈ 3.3 Å. _(evidence: virtual_xafs)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- The absence of measured EXAFS and XANES data prevents evaluation of bond lengths, coordination numbers, oxidation state, and disorder (checks C2‑C5).
- Virtual XAFS predictions are unmeasured and only indicate that measuring the Pt L₃ edge to k ≥ 12 Å⁻¹, especially near R ≈ 3.3 Å, would be needed to discriminate PtNi from Pt₃Co.
