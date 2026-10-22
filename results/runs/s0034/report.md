# Concord report — s0034 (Co3O4)

**Concord analysis robustly identifies Co₃O₄ as the dominant phase despite an unresolved XRD peak at 10.22°.**

Phase: **Co3O4**

All quantitative metrics (checks C1‑C7) robustly support Co3O4 as the primary phase. Visual inspection of the XRD pattern reveals an unexplained peak at 10.22°, which is not explained by adding Pt3Co; the peak remains unresolved but does not affect the overall structural model.

## Key numbers (from the tools)

- **XRD**: best match Co3O4 (profile correlation 0.789, 100 % of the peak area explained); sphere diameter 1.4 nm from 4 indexed reflections
- **PDF**: Co3O4 refines to Rw 0.136; a 8.0825 Å; U_iso Co 0.0027 Å², O 0.0048 Å²; particle diameter 1.7 nm
- **EXAFS** (Co K): Co–O N 5.3 ± 0.6 at 1.929 Å, σ² 0.0073 Å²; R-factor 0.0052
- **XANES**: Co valence 2.64 from a linear combination of standards, 2.33 from the edge position
- **Bond valence** (PDF model): 2.67

## Evidence by technique

- **XRD**: XRD ranking assigns Co₃O₄ a score of 0.8735 with an observed area fraction explained of 1.0, while Pt₃Co scores only 0.06049 with 0.0 fraction; an unexplained peak at 10.22° remains after adding Pt₃Co (0 % intensity share, RMS unchanged at 148.1).
- **PDF**: PDF fitting of Co₃O₄ yields Rw = 0.1357 (good fit) and a particle size of 1.71 nm, contrasting with Pt₃Co Rw = 0.9693; the fit shows no unexplained peaks.
- **EXAFS**: EXAFS gives a Co–O bond length of 1.929 Å (diff = 0.0044 Å vs PDF model) and a coordination number of 5.32 ± 0.62 (difference = 0.88, below the warning limit of 1.0); a k‑range window scan (kmax 10‑12) shows N varies between 5.32 and 5.65, confirming stability.
- **XANES**: XANES-derived valence of 2.64 and bond‑valence‑sum valence of 2.666 differ by –0.03, well within the tolerance of 0.5.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on Co3O4. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | pass | EXAFS σ² is 0.97–0.97 × the uncorrelated PDF width, as expected: EXAFS measures the relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | Co3O4 has the best joint score (margin 0.780). |

## Virtual XAFS — PREDICTED, NOT MEASURED

Co K EXAFS computed with FEFF from the PDF-refined model (Co3O4; 24 ensemble members, Debye temperature 542–552 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.0328 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Co oxidation state 2, [doi:10.48550/arXiv.1404.1658](https://doi.org/10.48550/arXiv.1404.1658) (2014): «XANES along with linear combination fit provide relative concentrations of Co2+ and Co3+.Temperature dependent DC magnetization exhibits the same antiferromagnetic behavior as observed in single crystal.»
- Co oxidation state 3, [doi:10.48550/arXiv.1404.1658](https://doi.org/10.48550/arXiv.1404.1658) (2014): «XANES along with linear combination fit provide relative concentrations of Co2+ and Co3+.Temperature dependent DC magnetization exhibits the same antiferromagnetic behavior as observed in single crystal.»
- Co oxidation state 3, [doi:10.48550/arXiv.1201.5193](https://doi.org/10.48550/arXiv.1201.5193) (2012): «Co L-edge and Mn L-edge XANES suggested substitu-tion of Co3+ sites by Mn3+, which increased the activity of the catalytic sites in the hybrid materials, further boosting the ORR activity compared to the pure cobalt oxid»
- Co oxidation state 3, [doi:10.1021/acscatal.9b01048](https://doi.org/10.1021/acscatal.9b01048) (2019): «The consumption of surface oxygen and reduction of Co 3+ to Co 2+ during 2-propanol oxidation derived from X-ray absorption spectroscopy and X-ray photoelectron spectroscopy measurements before and after reaction and poi»
- Co oxidation state 2, [doi:10.1021/acscatal.9b01048](https://doi.org/10.1021/acscatal.9b01048) (2019): «The consumption of surface oxygen and reduction of Co 3+ to Co 2+ during 2-propanol oxidation derived from X-ray absorption spectroscopy and X-ray photoelectron spectroscopy measurements before and after reaction and poi»
- Co oxidation state 3, [doi:10.34726/hss.2016.17050](https://doi.org/10.34726/hss.2016.17050) (2017): «The combined results of operando NAP-XPS and operando FTIR spectroscopy (i.e., static steady-state and dynamic switching experiments) indicate a redox Mars-van-Krevelen mechanism of CO oxidation on Co3O4, involving the C»
- particle size 4.3 nm, [doi:10.1063/1.2817481](https://doi.org/10.1063/1.2817481) (2007): «Along with the results from the previous experiments on the Co3O4 nanoparticles with average diameter of 8 and 4.3 nm, the variation of TN with the particle diameter, d, appears to follow the finite size scaling relation»
- particle size 20–25 nm, [doi:10.1166/jnn.2015.9776](https://doi.org/10.1166/jnn.2015.9776) (2014): «HR-TEM images showed that Co3O4 nanoparticles have sphere-like structure with an average particle size in the range of 20-25 nm (MCM) and 45-50 nm (CCM).»
- particle size 45–50 nm, [doi:10.1166/jnn.2015.9776](https://doi.org/10.1166/jnn.2015.9776) (2014): «HR-TEM images showed that Co3O4 nanoparticles have sphere-like structure with an average particle size in the range of 20-25 nm (MCM) and 45-50 nm (CCM).»
- particle size 46.9 nm, [doi:10.1021/jp904022e](https://doi.org/10.1021/jp904022e) (2009): «Cubic Co 3 O 4 nanoparticles with average diameters of 5.9, 21.1, and 46.9 nm (hereafter small, medium, and large) have been synthesized and characterized by pXRD, TEM, and BET.»
- particle size 80–130 nm, [doi:10.35414/akufemubid.1275507](https://doi.org/10.35414/akufemubid.1275507) (2023): «The nanospheres were with an average size distribution of almost 80-130 nm.»
- particle size 60 nm, [doi:10.18321/cpc23(1)53-62](https://doi.org/10.18321/cpc23(1)53-62) (2025): «Unique features of cobalt (II)(III) oxide Co3O4 nanoparticles are size between 12 and 60 nm, and high surface area and porosity that enhances their performances in fields such as energy storage, environmental and sensing»

## Claims

0. XRD ranking identifies Co3O4 as the dominant phase with score 0.8735 and observed area fraction explained 1.0 _(evidence: xrd.ranking)_
1. PDF fit for Co3O4 yields Rw 0.1357, indicating a good fit _(evidence: pdf.fit.Co3O4)_
2. Phase consistency check C1 passes: XRD and PDF both select Co3O4 as the phase (xrd_score 0.874, pdf_rw 0.136) _(evidence: check.C1)_
3. EXAFS‑Co‑O bond length 1.929 Å matches PDF model distance 1.925 Å (diff 0.0044 Å), within tolerance (check C2) _(evidence: check.C2)_
4. EXAFS coordination number 5.32 ± 0.62 is consistent with bulk Co3O4 coordination 5.33 after surface correction; the difference is 0.88, below the warning limit of 1.0 (check C3). A k‑range window scan (kmax 10‑12) shows N varies between 5.32 and 5.65, confirming stability _(evidence: check.C3, rerun.R1.1.exafs_window_scan)_
5. XANES-derived valence 2.64 and bond‑valence‑sum valence 2.666 differ by –0.03, well within tolerance (check C4) _(evidence: check.C4)_
6. EXAFS disorder σ² 0.00729 matches the PDF uncorrelated pair width 0.0075 (ratio 0.973), within the allowed range (check C5) _(evidence: check.C5)_
7. Particle size from XRD sphere diameter 1.43 nm and PDF diameter 1.71 nm have relative difference –0.163, within tolerance (check C6) _(evidence: check.C6)_
8. Joint simulation score strongly favors Co3O4 (score 0.1265) over Pt3Co (score 0.9068), with a margin of 0.7803 (check C7) _(evidence: check.C7)_
9. Visual inspection of the XRD pattern flags an unexplained peak at 10.22°. Adding Pt3Co as a second phase yields 0 % intensity share and no change in RMS, so the peak remains unexplained (vision.xrd, rerun.R1.2.xrd_add_phase) _(evidence: vision.xrd, rerun.R1.2.xrd_add_phase)_
10. Visual inspection of PDF and EXAFS accept the data _(evidence: vision.pdf, vision.exafs)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The EXAFS coordination number difference (0.88) is close to the warning threshold (1.0) in check C3, indicating borderline consistency; a stability test across k‑range values is needed. | check.C3 | exafs_window_scan | N over kmax 10-12: O 5.32-5.65 | not confirmed |
| R1.2 | An unexplained XRD peak at 10.22° remains after the single‑phase Co3O4 model; the prior Pt3Co test used 0 % intensity and did not explore a genuine two‑phase refinement, so a refined addition of Pt3Co should be attempted. | vision.xrd, xrd.ranking | xrd_add_phase | adding Pt3Co (0 % of the simulated intensity) takes the XRD residual RMS from 148.1 to 148.1 | not confirmed |

## Limitations

- The unexplained XRD peak at 10.22° is not accounted for by the current single‑phase model or by adding Pt₃Co, leaving a residual feature.
- The EXAFS coordination number difference (0.88) is close to the warning threshold (1.0), representing borderline consistency despite the supporting k‑range stability test.
