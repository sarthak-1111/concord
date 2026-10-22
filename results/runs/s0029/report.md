# Concord report — s0029 (PtNi)

**PtNi phase identified with excellent XRD (score 0.9693, profile correlation 0.9712) and PDF (Rw 0.08845) agreement.**

Phase: **PtNi**

Concord analysis of the PtNi sample combining XRD and PDF data.

## Key numbers (from the tools)

- **XRD**: best match PtNi (profile correlation 0.971, 97 % of the peak area explained); sphere diameter 4.5 nm from 5 indexed reflections
- **PDF**: PtNi refines to Rw 0.088; a 3.7852 Å; U_iso Pt 0.0029 Å²; particle diameter 4.4 nm

## Evidence by technique

- **XRD**: XRD fitting yields a high score of 0.9693 and profile correlation of 0.9712, indicating an excellent fit; the sphere diameter from XRD is 4.542 nm.
- **PDF**: PDF fitting yields a low Rw of 0.08845, well below the good‑fit threshold of 0.25, with refined lattice parameters a = b = c = 3.785 Å and a particle size of 4.37 nm.
- **EXAFS**: Virtual XAFS predicts that measuring the Pt L₃ edge to k ≥ 12 Å⁻¹ would discriminate PtNi from the PDF‑equivalent Pt₃Co phase.
- **XANES**: No XANES data were acquired; oxidation‑state assessment is therefore unavailable.

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

0. The sample is identified as the PtNi phase. _(evidence: sample, check.C1, xrd.ranking, pdf.best)_
1. XRD fitting yields a high score of 0.9693 and profile correlation of 0.9712, indicating an excellent fit. _(evidence: xrd.ranking, fitting.xrd, check.C1)_
2. PDF fitting yields a low Rw of 0.08845, well below the good‑fit threshold of 0.25. _(evidence: pdf.fit.PtNi, fitting.pdf, check.C1)_
3. The refined lattice parameters are a = b = c = 3.785 Å, matching the reference values. _(evidence: pdf.fit.PtNi)_
4. Particle size from XRD (sphere diameter 4.542 nm) and PDF (particle size 4.37 nm) agree, with a relative difference of 0.039. _(evidence: xrd.size, pdf.fit.PtNi, check.C6)_
5. Joint simulation score selects PtNi as the best candidate (score 0.0586) with a margin of 0.0485 over the next best candidate. _(evidence: check.C7)_
6. Virtual XAFS predicts that measuring the Pt L3 edge to k ≥ 12 Å⁻¹ would discriminate PtNi from the PDF‑equivalent Pt3Co phase. _(evidence: virtual_xafs)_
7. The measured particle size values (4.542 nm from XRD and 4.37 nm from PDF) lie within the literature range (2–8.3 nm) for PtNi nanoparticles. _(evidence: xrd.size, pdf.fit.PtNi, prior.2, prior.4)_
8. Visual inspection of the XRD data was accepted (gpt-oss judge) and the PDF data was accepted (eye). _(evidence: vision.xrd, vision.pdf)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- EXAFS and XANES measurements are missing, so bond‑length, coordination‑number, oxidation‑state, and disorder checks could not be performed.
- The joint simulation score (0.0586) selects PtNi as best candidate with a margin of 0.0485, but this relies on simulated rather than measured XAFS data.
