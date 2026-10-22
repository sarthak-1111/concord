# Concord report — s0003 (TiO2)

**TiO₂ nanoparticles (~4 nm) show no consistent crystalline phase and exhibit mixed structural and oxidation-state indicators.**

Phase: **None**

The TiO2 sample lacks a consistent crystalline phase: XRD ranking favours TiO2-anatase (score 0.759, area fraction 0.728) while the PDF fit for anatase has Rw 0.8321 (and 0.8456 without the particle envelope), far above the good-fit tolerance of 0.25, and check.C1 reports phase-consistency failure (lattice_rel_change 0.0205). Consequently the phase is set to null. Nanoparticle size is ~4 nm (XRD sphere diameter 3.885 nm, PDF particle size 4.011 nm). PDF anatase lattice parameters are a = 3.708 Å, b = 3.708 Å, c = 9.331 Å (relative change 0.0205 vs reference). EXAFS shows a Ti–O bond length of 1.958 Å, 0.0441 Å longer than the PDF model distance 1.914 Å (check.C2), and a coordination number of 9.23 ± 4.122, 3.66 higher than the bulk model value 5.57 (check.C3). XANES linear-combination fit gives a Ti valence of 3.883, while the edge position suggests 4.24 and bond-valence-sum gives 4.45, indicating mixed valence or non-stoichiometry (check.C4). Disorder analysis yields an EXAFS/PDF σ² ratio of 0.237, below the lower bound of 0.3 (check.C5). Joint simulation favours anatase with total score 0.4966 (margin 0.0566) over rutile (score 0.5532) (check.C7). Visual inspections reject each technique (XRD peaks at 25.52°, 30.82°, 64.58°; PDF Rw 0.832; EXAFS Durbin‑Watson 0.8809).

## Key numbers (from the tools)

- **XRD**: best match TiO2-anatase (profile correlation 0.780, 73 % of the peak area explained); sphere diameter 3.9 nm from 6 indexed reflections
- **PDF**: TiO2-anatase refines to Rw 0.832; a 3.7075 Å, c 9.3313 Å; U_iso O 0.0500 Å², Ti 0.0123 Å²; particle diameter 4.0 nm
- **EXAFS** (Ti K): Ti–O N 9.2 ± 4.1 at 1.958 Å, σ² 0.0148 Å²; R-factor 0.0732
- **XANES**: Ti valence 3.88 from a linear combination of standards, 4.24 from the edge position
- **Bond valence** (PDF model): 4.45

## Evidence by technique

- **XRD**: Ranking favours TiO₂‑anatase (score 0.759, area fraction 0.728) but visual inspection rejects the fit due to unexplained peaks at 25.52°, 30.82° and 64.58°.
- **PDF**: Fit to anatase yields Rw 0.832 (far above the 0.25 tolerance) with lattice parameters a = 3.708 Å, b = 3.708 Å, c = 9.331 Å (relative change 0.0205) and a particle size of 4.011 nm.
- **EXAFS**: Ti–O bond length is 1.958 Å (0.0441 Å longer than the PDF model distance 1.914 Å) and the coordination number is 9.23 ± 4.122 (3.66 higher than the bulk value 5.57), both exceeding tolerances.
- **XANES**: Linear‑combination fitting gives a Ti valence of 3.883 (below the formal 4.0), while the edge position suggests 4.24 and bond‑valence‑sum gives 4.45, indicating possible mixed valence or non‑stoichiometry.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | **FAIL** | No candidate structure fits the PDF (best Rw 0.83 for TiO2-anatase). The true phase may be missing from the candidate list, or the sample label is wrong. |
| C2 Bond lengths (EXAFS R vs PDF model) | **warn** | EXAFS and the PDF model disagree by up to 0.044 Å: local distortion, a second phase, or strain the average structure does not capture. |
| C3 Coordination numbers (EXAFS N vs model) | **FAIL** | EXAFS coordination differs from the model by up to 3.7: segregation, vacancies or a disordered surface. |
| C4 Oxidation state (XANES vs bond-valence sum) | **FAIL** | The refined bond lengths (bond-valence sum 4.45) and the XANES edge (4.24) both put the valence above the formal 4: mixed valence or non-stoichiometry (for example reduced cations with oxygen vacancies) that the stoichiometric model lacks. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 0.24–0.24 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | TiO2-anatase has the best joint score (margin 0.057). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ti K EXAFS computed with FEFF from the PDF-refined model (TiO2-anatase, TiO2-rutile; 24 ensemble members, Debye temperature 275–557 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.1544 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Ti oxidation state 4, [doi:10.1088/2053-1591/ab4e3f](https://doi.org/10.1088/2053-1591/ab4e3f) (2019): «Anal.At.Spectrom.29 736] coordination environment and Ti 4+ oxidation state was observed with 0.02 and 0.04 O 2 partial pressures, respectively.»
- particle size 8 nm, [doi:10.4028/www.scientific.net/kem.833.147](https://doi.org/10.4028/www.scientific.net/kem.833.147) (2020): «The average sizes of nanoparticles estimated respectively are ~ 8 nm and ~ 22 nm.»
- particle size 22 nm, [doi:10.4028/www.scientific.net/kem.833.147](https://doi.org/10.4028/www.scientific.net/kem.833.147) (2020): «The average sizes of nanoparticles estimated respectively are ~ 8 nm and ~ 22 nm.»
- particle size 1 nm, [doi:10.1002/cctc.200900104](https://doi.org/10.1002/cctc.200900104) (2009): «The metal particles contained on an average about 20 atoms, which is consistent with a particle size of 1 nm.»
- particle size 32 nm, [doi:10.1021/la7039916](https://doi.org/10.1021/la7039916) (2008): «The relative reactivity of 5 and 32 nm particles as determined from Langmuir adsorption parameters did not appear to vary greatly despite differences that occur in nanoparticle aggregation for these two different size na»
- particle size 9 nm, [doi:10.51415/10321/3804](https://doi.org/10.51415/10321/3804) (None): «The Image J analysis showed that the average particle distribution of nTiO2 was 9 nm.»
- particle size 7 nm, [doi:10.1115/1.859841.paper69](https://doi.org/10.1115/1.859841.paper69) (2011): «We present a detailed comparison of two samples of identical atomic composition but different texture, with narrow TiO2 particle-size distributions centered at 4 and 7 nm.»

## Claims

0. No consistent crystalline phase could be assigned; phase set to null _(evidence: check.C1)_
1. Particle size from XRD sphere diameter is 3.885 nm and from PDF psize is 4.011 nm, indicating ~4 nm nanoparticles _(evidence: xrd.size, pdf.fit.TiO2-anatase, check.C6)_
2. Lattice parameters from PDF anatase fit are a=3.708 Å, b=3.708 Å, c=9.331 Å, a relative change of 0.0205 compared to reference values _(evidence: pdf.fit.TiO2-anatase, check.C1)_
3. EXAFS Ti–O bond length is 1.958 Å, 0.0441 Å longer than the PDF model distance of 1.914 Å, exceeding the warning tolerance _(evidence: exafs.fit, check.C2)_
4. EXAFS Ti–O coordination number is 9.23 ± 4.122, 3.66 higher than the bulk model value of 5.57, failing the coordination number check _(evidence: exafs.fit, check.C3)_
5. XANES-derived valence from linear‑combination fitting is 3.883 (below the formal Ti valence of 4.0), while the XANES edge position suggests a valence of 4.24 (above formal). The bond‑valence‑sum estimate is 4.45, also above formal. This discrepancy indicates possible mixed valence or non‑stoichiometry _(evidence: xanes, bvs, check.C4)_
6. Disorder analysis shows EXAFS σ²=0.01476, PDF σ² (with Δ²) =0.00913, giving a ratio of 0.237, below the lower bound of 0.3, suggesting static disorder _(evidence: check.C5)_
7. Joint simulation score: anatase total score 0.4966, rutile total score 0.5532, margin 0.0566; anatase has the best joint score among candidates _(evidence: check.C7)_
8. XRD visual inspection flagged unexplained peaks at 25.52°, 30.82°, and 64.58°, leading to rejection of the XRD fit _(evidence: vision.xrd)_
9. PDF visual inspection rejected due to high Rw of 0.832, exceeding the 0.25 threshold _(evidence: vision.pdf)_
10. EXAFS visual inspection rejected because the Durbin‑Watson statistic is 0.8809, below the acceptable limit of 1.0 _(evidence: vision.exafs)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The claim that both XANES-derived valence (3.883) and BVS-derived valence (4.45) are above the formal Ti valence of 4.0 is incorrect: the XANES-derived valence is below 4.0. Therefore the statement that both indicate mixed valence or non‑stoichiometry is unsupported by the evidence. | xanes, bvs, check.C4 | – | no re-run requested; the analyst must answer it | open |
| R2.1 | No consistent crystalline phase could be assigned; phase set to null | check.C1, check.C7, xrd.ranking | pdf_toggle_envelope | TiO2-anatase without the particle envelope: Rw 0.846 (was 0.832) | not confirmed |
| R3.1 | No consistent crystalline phase could be assigned; phase set to null | check.C1, check.C7, xrd.ranking | xrd_add_phase | adding TiO2-rutile (0 % of the simulated intensity) takes the XRD residual RMS from 2338 to 2338 | not confirmed |

## Limitations

- Phase assignment fails (check.C1) and the joint simulation margin (0.0566) is small.
- XRD, PDF and EXAFS visual inspections all reject their fits.
- Disorder analysis shows an EXAFS/PDF σ² ratio of 0.237 (< 0.3), pointing to static disorder.
- The XANES valence discrepancy is one‑sided (XANES below 4, BVS above 4), so the claim that both exceed the formal valence is inaccurate.
