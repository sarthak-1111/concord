# Concord report — s0052 (PtO2)

**No candidate phase simultaneously satisfies XRD, PDF, and XAFS constraints, with PtNi scoring highest in joint simulation.**

Phase: **None**

Quantitative analyses reveal that none of the candidate structures (Pt, Pt3Co, PtNi, PtO2) simultaneously satisfy XRD, PDF, and XAFS data. Phase consistency fails, bond lengths, coordination numbers, oxidation state, and disorder show significant discrepancies. Joint simulation scores favor PtNi over PtO2. Visual inspection rejects XRD and EXAFS data but accepts PDF despite a high Rw value.

## Key numbers (from the tools)

- **XRD**: best match Pt (profile correlation 0.378, 25 % of the peak area explained); sphere diameter 3.3 nm from 2 indexed reflections
- **PDF**: PtO2 refines to Rw 0.974; a 4.4394 Å, b 4.6747 Å, c 3.1677 Å; U_iso O 0.0005 Å², Pt 0.0075 Å²; particle diameter 3.8 nm
- **EXAFS** (Pt L3): Pt–O N 6.8 ± 9.1 at 2.060 Å, σ² 0.0118 Å²; R-factor 0.4307
- **XANES**: Pt valence 2.79 from a linear combination of standards, 4.74 from the edge position
- **Bond valence** (PDF model): 3.79

## Evidence by technique

- **XRD**: XRD ranking selects Pt as the best phase (score 0.3273, area explained 0.2514) but visual inspection rejects the data and the best phase explains only 0.25 of the peak area, below the 0.5 threshold.
- **PDF**: PDF fitting identifies PtO₂ as the best match (Rw 0.9741) despite a high Rw; visual inspection accepts the PDF, but the fit quality exceeds the acceptable Rw 0.25 limit.
- **EXAFS**: EXAFS fit to PtO₂ yields a Pt–O bond length of 2.06 Å ± 0.1097 (diff 0.0418 Å vs PDF model) and coordination number 6.822 ± 9.063 (diff 1.3 from bulk 5.52), both exceeding warn thresholds; disorder ratio σ²_EXAFS/σ²_PDF = 1.481 is above the warn limit of 1.3.
- **XANES**: XANES valence of 2.789 is lower than the bond‑valence sum (3.791) and formal valence (4.0), a discrepancy of –1.0 exceeding the fail tolerance.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.97 for PtO2). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | **warn** | EXAFS and the PDF model disagree by up to 0.042 Å: local distortion, a second phase, or strain the average structure does not capture. |
| C3 Coordination numbers (EXAFS N vs model) | **warn** | EXAFS coordination differs from the model by up to 1.3: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | **FAIL** | XANES says 2.8, the refined structure implies 3.8: mixed valence, a surface phase or vacancies the average structure misses. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 1.48–1.48 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | **FAIL** | Scored on all techniques together, Pt beats the reported PtO2. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Pt L3 EXAFS computed with FEFF from the PDF-refined model (Pt, Pt3Co, PtNi, PtO2; 24 ensemble members, Debye temperature 117–176 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.7568 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Pt–Pt bond length 2.8 Å, [doi:10.31635/ccschem.022.202101628](https://doi.org/10.31635/ccschem.022.202101628) (2022): «No Pt–Pt characteristic peak (at ∼2.8 Å) was detected for both Pt-B-MoS2 and Pt-S-MoS2 samples, confirming the atomic dispersion of Pt on the supports.»
- Pt oxidation state 4, [doi:10.31635/ccschem.022.202101628](https://doi.org/10.31635/ccschem.022.202101628) (2022): «However, for the Pt loading of S-MoS2 samples (donated as Pt-S-MoS2), the Pt exhibited an additional peak at ∼74.0 eV, suggesting the existing higher oxidation state of the Pt4+ species.»
- particle size 1.3 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 6.5 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 12.7 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 8.54 nm, [doi:10.1055/s-0042-1755335](https://doi.org/10.1055/s-0042-1755335) (2023): «Results Platina 30c to CM: Nanoparticles were identified under DLS (mean particle size varying from 1.3 nm in 30c to 6.5 nm in CM) and HRTEM (particle size varying from 3.31 to 12.7 nm in 30c to 1.94 to 8.54 nm in CM).»
- particle size 3 nm, [doi:10.1039/c5nr03585f](https://doi.org/10.1039/c5nr03585f) (2015): «The SnO2 nanoparticle cluster matrix consists of tens of thousands of SnO2 nanoparticles with an ultra-small grain size estimated to be 3.0 nm.»
- particle size 1.1–2.1 nm, [doi:10.1021/acsami.8b06815](https://doi.org/10.1021/acsami.8b06815) (2018): «The high crystallinity and uniform crystal structure of the ZnO matrix conduct the in situ deposition of PtO 2 nanoparticles with 1.1–2.1 nm, which are evenly and densely anchored on the surface.»

## Claims

0. Phase consistency between XRD and PDF fails: XRD ranking suggests Pt as the best phase (score 0.327, area explained 0.251) while PDF best fit is PtO2 (Rw 0.974); no candidate provides a good match to both techniques. _(evidence: check.C1, xrd.ranking, pdf.best, pdf.fit.PtO2)_
1. Bond length Pt‑O from EXAFS (2.06 Å ± 0.1097) differs from the PDF model (2.018 Å) by 0.0418 Å, exceeding the warn threshold, indicating possible local distortion or a secondary phase. _(evidence: check.C2, exafs.fit, pdf.fit.PtO2)_
2. Coordination number for Pt‑O from EXAFS (N = 6.822 ± 9.063) deviates from the bulk model value (5.52) by 1.3, above the warn limit, suggesting surface vacancies or disorder. _(evidence: check.C3, exafs.fit, pdf.fit.PtO2)_
3. Oxidation state from XANES (2.789) is lower than the bond‑valence sum (3.791) and the formal valence (4.0), a discrepancy of –1.0 exceeding the fail tolerance, indicating mixed valence or a missing phase. _(evidence: check.C4, xanes, bvs)_
4. Disorder ratio σ²(EXAFS)/σ²(PDF) for Pt‑O is 1.481, above the upper warn limit of 1.3, implying static disorder or a distinct surface layer not captured by the average PDF structure. _(evidence: check.C5, exafs.fit, pdf.fit.PtO2)_
5. Particle size from XRD (sphere diameter 3.33 nm, Scherrer 2.55 nm) and PDF (3.76 nm) differ by a relative difference of –0.113, within the warn limit, indicating consistent size estimates. _(evidence: check.C6, xrd.size, pdf.fit.PtO2)_
6. Joint simulation score across XRD, PDF, and EXAFS fails: Pt scores 0.7619, PtO2 0.8315, and PtNi 0.8442; the margin of 0.0696 exceeds the minimum required 0.02, leading to a failure of the joint model. _(evidence: check.C7, xrd.ranking, pdf.best, exafs.fit, virtual_xafs)_
7. Visual inspection by the gpt‑oss judge rejected XRD and EXAFS data, while PDF received an ‘accept’ verdict (despite a high Rw of 0.974). _(evidence: vision.xrd, vision.pdf, vision.exafs)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The claim that visual inspection rejected PDF is not supported: vision.pdf reports a verdict of "accept", while the claim states that PDF was rejected. | vision.xrd, vision.pdf, vision.exafs | – | no re-run requested; the analyst must answer it | open |

## Limitations

- Phase consistency fails (XRD vs PDF).
- Bond‑length and coordination‑number discrepancies indicate local distortion or secondary phases.
- Oxidation‑state mismatch suggests mixed valence.
- Disorder ratio points to static disorder.
- Joint simulation scores (Pt 0.7619, PtO₂ 0.8315, PtNi 0.8442) exceed the required margin of 0.02, leading to overall model failure.
