# Concord report — s0029 (PtNi)

**PtNi phase identified as the best candidate for the PtNi sample**

Phase: **PtNi**

The structural model for the PtNi sample is best described by the PtNi phase, with consistent and high‑quality fits from XRD and PDF, size agreement, and the strongest joint simulation score. Visual inspection of both datasets was accepted, while EXAFS data are pending.

## Key numbers (from the tools)

- **XRD**: best match PtNi (profile correlation 0.971, 97 % of the peak area explained); sphere diameter 4.5 nm from 5 indexed reflections
- **PDF**: PtNi refines to Rw 0.089; a 3.7854 Å; U_iso Pt 0.0029 Å²; particle diameter 4.4 nm

## Evidence by technique

- **XRD**: The XRD fit score is 0.9693, with 5 of 7 peaks indexed and 96.6% of the observed area explained, indicating a high‑quality fit.
- **PDF**: The PDF fit Rw is 0.08912, well below the good‑fit threshold of 0.25, and the particle size estimates from XRD (sphere diameter 4.542 nm) and PDF (psize 4.364 nm) agree with a relative difference of 0.041.
- **EXAFS**: No EXAFS data are currently available; virtual XAFS predicts that measuring the Pt L₃ edge to k ≥ 12 Å⁻¹ would discriminate PtNi from Pt₃Co.
- **XANES**: XANES data were not collected, so oxidation‑state validation is pending.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on PtNi. |
| C2 Bond lengths (EXAFS R vs PDF model) | skip | needs EXAFS and PDF |
| C3 Coordination numbers (EXAFS N vs model) | skip | needs EXAFS and PDF |
| C4 Oxidation state (XANES vs bond-valence sum) | skip | needs XANES and a PDF-refined structure |
| C5 Disorder (EXAFS σ² vs PDF pair width) | skip | needs EXAFS and PDF |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | PtNi has the best joint score (margin 0.048). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt3Co, PtNi; 24 ensemble members, Debye temperature 258–281 K). Measure the Pt L3 edge to k ≥ 12 Å⁻¹. The prediction is least certain near R ≈ 1.2 Å (band ±79 % of the median |χ(R)|); the measurement would discriminate the PDF-equivalent phases Pt3Co, PtNi.

## Literature priors (other samples: context, not constraints)

- particle size 3 nm, [doi:10.1557/proc-1217-y08-03](https://doi.org/10.1557/proc-1217-y08-03) (2009): «The average grain sizes observed with a TEM were around 3 nm in diameter.»
- particle size 2–5 nm, [doi:10.3390/catal6120201](https://doi.org/10.3390/catal6120201) (2016): «The size of PtNi alloy nanoparticles is approximately 2–5 nm.»
- particle size 2–16 nm, [doi:10.1080/17458080.2013.838703](https://doi.org/10.1080/17458080.2013.838703) (2013): «It was observed that the deposited Pt and PtNi bimetallic nanoparticles on the surface of CNTs had average particle sizes of 2–16 nm, when they were prepared from the polyol method.»
- particle size 8.3 nm, [doi:10.1149/1.1802135](https://doi.org/10.1149/1.1802135) (2004): «The carbon-supported PtNi nanoparticles had a mean diameter of 8.3 nm and were obtained by a two-stage process involving the ballmilling of carbon and the precursor and the thermal degradation of the homogenized mixture »
- particle size 3.7 nm, [doi:10.1039/c9nr08352a](https://doi.org/10.1039/c9nr08352a) (2019): «The resulting PtNi alloy nanoparticles have a narrow size distribution with an average diameter of 3.7 nm, which are smaller than those obtained via classical solution growth.»
- particle size 2.9–5.8 nm, [doi:10.1039/b307040a](https://doi.org/10.1039/b307040a) (2003): «The average particle size of PtNi prepared by microwave irradiation was the lowest, in the range of 2.9–5.8 nm.»

## Claims

0. The PtNi phase has the highest XRD score (0.969) and the lowest PDF Rw (0.089), indicating it is the best candidate. _(evidence: sample, xrd.ranking, pdf.best, check.C1)_
1. XRD fit score is 0.969, with 5 of 7 peaks indexed and 96.6% of observed area explained, showing a high‑quality fit. _(evidence: fitting.xrd, xrd.ranking, xrd.size)_
2. PDF fit Rw is 0.089, well below the good‑fit threshold of 0.25, confirming a strong agreement between model and data. _(evidence: fitting.pdf, pdf.fit.PtNi, check.C1)_
3. XRD and PDF size estimates agree: XRD sphere diameter 4.54 nm, PDF particle size 4.36 nm, with a relative difference of 0.041. _(evidence: xrd.size, pdf.fit.PtNi, check.C6)_
4. Joint simulation score favors PtNi (score 0.059) over Pt3Co (score 0.1073) and PtO2 (score 0.9893), with a margin of 0.0483, making PtNi the best overall candidate. _(evidence: check.C7)_
5. Visual inspection of both XRD and PDF data was accepted. _(evidence: vision.xrd, vision.pdf)_
6. No EXAFS data are currently available; virtual XAFS predicts that measuring the Pt L₃ edge to k ≥ 12 Å⁻¹ would discriminate PtNi from Pt₃Co. _(evidence: virtual_xafs)_
7. The derived particle size (~4.4–4.5 nm) lies within literature ranges for PtNi nanoparticles (2–8.3 nm). _(evidence: xrd.size, pdf.fit.PtNi, prior.2, prior.4, prior.5, prior.6)_

## Objections and resolutions

The critic raised no objections.

## Limitations

- EXAFS and XANES measurements are missing, limiting validation of local bonding and oxidation state.
- Further improvement of the XRD fit (>2% score increase) or PDF Rw reduction is unlikely given the current high quality of the fits.
