# Concord report — s0045 (TiO2)

**TiO₂ sample exhibits conflicting phase signals and a distinct Ce⁴⁺ component absent from the refined TiO₂ model.**

Phase: **None**

The TiO2 sample shows contradictory phase identification: XRD favours rutile while PDF favours anatase, and the XANES data reveal a Ce4+ component that is not represented in the refined TiO2 model, indicating a separate Ce-containing phase (impurity or surface oxide). Size estimates differ between XRD (2.42 nm sphere diameter) and PDF (1.83 nm), reflecting technique‑dependent weighting. Joint XRD + PDF scoring favours anatase over rutile.

Not analysed: exafs (ValueError: absorber Ce is not in the refined model TiO2); virtual_xafs (ValueError: Ce is not in the refined model).

## Key numbers (from the tools)

- **XRD**: best match TiO2-rutile (profile correlation 0.615, 14 % of the peak area explained); sphere diameter 2.4 nm from 2 indexed reflections
- **PDF**: TiO2-anatase refines to Rw 0.915; a 3.7942 Å, c 9.5563 Å; U_iso O 0.0005 Å², Ti 0.0005 Å²; particle diameter 1.8 nm
- **XANES**: Ce valence 4.00 from a linear combination of standards, 4.09 from the edge position
- **Bond valence** (PDF model): 0.00

## Evidence by technique

- **XRD**: XRD ranking favours rutile (score 0.4263, observed area fraction explained 0.1436) over anatase (score 0.3334, area explained 0.2101).
- **PDF**: PDF fit best‑matches anatase (Rw 0.9154) while the rutile fit is poorer (Rw 0.9746); both exceed the acceptable Rw limit of 0.25.
- **EXAFS**: EXAFS probing failed (ValueError: absorber Ce is not in the refined model TiO₂), so no bond‑length comparison is available.
- **XANES**: XANES at the Ce L₃ edge shows Ce fully as Ce⁴⁺ (valence 4.0, LCF weight Ce⁴⁺ = 1.0) whereas the bond‑valence‑sum for the TiO₂ model gives a valence of 0.0, indicating Ce is not represented in the TiO₂ structural model.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.92 for TiO2-anatase). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | skip | needs EXAFS and PDF |
| C3 Coordination numbers (EXAFS N vs model) | skip | needs EXAFS and PDF |
| C4 Oxidation state (XANES vs bond-valence sum) | **FAIL** | XANES shows an oxidised component (valence 4.00) that the metallic model lacks: a surface oxide or oxidised species. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | skip | needs EXAFS and PDF |
| C6 Size (XRD vs PDF) | **warn** | XRD sees larger crystallites than the PDF particle diameter: XRD is volume-weighted (large particles dominate) while the PDF envelope is closer to a number average, or a disordered surface shell shortens the PDF range. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | **FAIL** | Scored on all techniques together, TiO2-rutile beats the reported TiO2-anatase. |

## Literature priors (other samples: context, not constraints)

- Ti oxidation state 4, [doi:10.1088/2053-1591/ab4e3f](https://doi.org/10.1088/2053-1591/ab4e3f) (2019): «Anal.At.Spectrom.29 736] coordination environment and Ti 4+ oxidation state was observed with 0.02 and 0.04 O 2 partial pressures, respectively.»
- particle size 8 nm, [doi:10.4028/www.scientific.net/kem.833.147](https://doi.org/10.4028/www.scientific.net/kem.833.147) (2020): «The average sizes of nanoparticles estimated respectively are ~ 8 nm and ~ 22 nm.»
- particle size 22 nm, [doi:10.4028/www.scientific.net/kem.833.147](https://doi.org/10.4028/www.scientific.net/kem.833.147) (2020): «The average sizes of nanoparticles estimated respectively are ~ 8 nm and ~ 22 nm.»
- particle size 1 nm, [doi:10.1002/cctc.200900104](https://doi.org/10.1002/cctc.200900104) (2009): «The metal particles contained on an average about 20 atoms, which is consistent with a particle size of 1 nm.»
- particle size 32 nm, [doi:10.1021/la7039916](https://doi.org/10.1021/la7039916) (2008): «The relative reactivity of 5 and 32 nm particles as determined from Langmuir adsorption parameters did not appear to vary greatly despite differences that occur in nanoparticle aggregation for these two different size na»
- particle size 9 nm, [doi:10.51415/10321/3804](https://doi.org/10.51415/10321/3804) (None): «The Image J analysis showed that the average particle distribution of nTiO2 was 9 nm.»
- particle size 7 nm, [doi:10.1115/1.859841.paper69](https://doi.org/10.1115/1.859841.paper69) (2011): «We present a detailed comparison of two samples of identical atomic composition but different texture, with narrow TiO2 particle-size distributions centered at 4 and 7 nm.»

## Claims

0. No candidate TiO2 phase simultaneously fits the XRD and PDF data; the XRD ranking favours rutile (score 0.426, area explained 0.144) while the PDF best fit is anatase (Rw 0.915), indicating the true phase may be missing from the candidate list. _(evidence: check.C1, xrd.ranking, pdf.best, pdf.fit.TiO2-anatase, pdf.fit.TiO2-rutile, vision.xrd)_
1. XANES at the Ce L3 edge shows Ce is fully Ce4+ (valence 4.0). The bond‑valence‑sum for the refined TiO2 model yields no Ce (valence 0.0). The error that Ce is not in the refined model confirms Ce is not represented in the TiO2 structural model, indicating a separate Ce‑containing component (impurity or surface oxide), but the evidence does not differentiate between these possibilities. _(evidence: check.C4, xanes, bvs, error.exafs)_
2. Particle size from XRD (sphere diameter 2.42 nm, Scherrer median 2.11 nm) exceeds the PDF‑derived diameter (1.83 nm) with a relative difference of 0.321, reflecting the volume‑weighted nature of XRD versus the number‑average PDF (or a disordered surface shell that shortens the PDF range). _(evidence: check.C6, xrd.size)_
3. Joint simulation scoring across XRD and PDF gives TiO2‑anatase a higher overall score (0.7499) than TiO2‑rutile (0.6799), indicating that when both techniques are considered together, anatase is favoured. _(evidence: check.C7)_
4. Visual inspection rejected the XRD pattern because the best phase explains only 0.14 of the observed peak area (below the 0.5 threshold) and unexplained peaks remain at 29.4° and 47.39°. _(evidence: vision.xrd, check.C1)_
5. The PDF fit is rejected as its refined Rw of 0.915 exceeds the acceptable limit of 0.25. _(evidence: vision.pdf, pdf.best)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | XANES analysis shows Ce is fully Ce4+ (valence 4.00) whereas the bond‑valence‑sum model predicts a metallic valence of 0.0, a discrepancy of 4.0, suggesting an oxidised surface species not captured by the structural model. | check.C4, xanes, bvs, error.exafs | exafs_probe_shell | re-run exafs_probe_shell failed: ValueError | failed |
| R2.1 | The claim that Ce is an impurity or dopant rather than a surface oxide is not supported by the evidence; XANES and the bond‑valence‑sum only indicate Ce is present as Ce4+ and absent from the TiO2 model, but they do not differentiate impurity from a surface oxide. | check.C4, xanes, bvs, error.exafs | – | no re-run requested; the analyst must answer it | open |
| R2.2 | The joint simulation scoring is misrepresented: the evidence shows TiO2‑anatase has the higher joint score (0.7499) compared to TiO2‑rutile (0.6799), contrary to the claim that rutile is favoured. | check.C7 | – | no re-run requested; the analyst must answer it | open |
| R3.1 | The claim that Ce is a separate Ce‑containing component (impurity or surface oxide) is not directly supported by the evidence; the evidence only shows Ce4+ is present and not included in the TiO2 model, but does not establish that Ce forms a distinct phase or surface oxide. | check.C4, xanes, bvs, error.exafs | – | no re-run requested; the analyst must answer it | open |

## Limitations

- PDF fit is rejected because Rw = 0.9154 > 0.25.
- XRD visual inspection rejects the pattern (only 0.14 of peak area explained, below the 0.5 threshold) and leaves unexplained peaks at 29.4° and 47.39°.
- Size estimates differ (XRD sphere diameter 2.422 nm vs PDF particle diameter 1.834 nm, relative difference 0.321) reflecting technique‑dependent weighting.
- Joint simulation scoring (anatase = 0.7499, rutile = 0.6799) favours anatase, contradicting the earlier claim that rutile is favoured.
- XANES and BVS confirm Ce⁴⁺ presence but cannot distinguish whether Ce resides in a separate impurity phase or as a surface oxide; current data only show Ce is absent from the refined TiO₂ model.
