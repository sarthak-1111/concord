# Concord report — s0044 (IrO2)

**IrO₂ identified as the sole crystalline phase with ~7 nm particles and near‑IV oxidation state, but a low EXAFS/PDF disorder ratio flags static disorder.**

Phase: **IrO2**

All cross‑technique checks are satisfied except a disorder warning (C5), which persists after testing EXAFS fits with varied kmax values. The EXAFS/PDF disorder ratio remains low at 0.273, and the EXAFS coordination numbers (5.785–5.89) and σ² values (0.007273–0.007485 Å²) are stable across kmax = 10–12, indicating static disorder or a split first shell rather than fitting instability. The combined XRD, PDF and EXAFS data support IrO₂ as the sole crystalline phase with particle size from XRD sphere diameter 7.8 nm and PDF diameter 7.11 nm, and Ir oxidation state ≈4.

## Key numbers (from the tools)

- **XRD**: best match IrO2 (profile correlation 0.979, 100 % of the peak area explained); sphere diameter 7.8 nm from 10 indexed reflections
- **PDF**: IrO2 refines to Rw 0.234; a 4.5038 Å, c 3.1593 Å; U_iso Ir 0.0009 Å², O 0.0265 Å²; particle diameter 7.1 nm
- **EXAFS** (Ir L3): Ir–O N 5.9 ± 0.6 at 1.983 Å, σ² 0.0075 Å²; R-factor 0.0100
- **XANES**: Ir valence 3.91 from a linear combination of standards, 4.19 from the edge position
- **Bond valence** (PDF model): 4.00

## Evidence by technique

- **XRD**: XRD yields a high phase score of 0.986 and a sphere diameter of 7.8 nm (Scherrer median 6.34 nm), matching the PDF size of 7.11 nm within a relative difference of 0.097.
- **PDF**: PDF fit for IrO₂ gives rw = 0.234 and a particle size of 7.11 nm, confirming the XRD‑derived phase and size.
- **EXAFS**: EXAFS shows an Ir–O bond length of 1.983 Å (σ² = 0.007485 Å²) and coordination numbers ranging 5.785–5.89 across kmax = 10–12, stable against window variation.
- **XANES**: XANES determines an Ir valence of 3.91, consistent with the bond‑valence sum of 4.002 and the formal Ir⁴⁺ state.

## Cross-technique checks

| check | status | explanation |
|---|---|---|
| C1 Phase consistency (XRD vs PDF) | pass | XRD and PDF agree on IrO2. |
| C2 Bond lengths (EXAFS R vs PDF model) | pass | EXAFS bond lengths match the PDF-refined model. |
| C3 Coordination numbers (EXAFS N vs model) | pass | EXAFS coordination matches the PDF model after surface truncation. |
| C4 Oxidation state (XANES vs bond-valence sum) | pass | XANES and the bond-valence sum agree. |
| C5 Disorder (EXAFS σ² vs PDF pair width) | **warn** | EXAFS/PDF disorder ratio 0.27–0.27 is outside 0.3–1.3: static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes. |
| C6 Size (XRD vs PDF) | pass | XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter. |
| C7 Joint simulation score (XRD + PDF + EXAFS) | pass | IrO2 has the best joint score. |

## Virtual XAFS — PREDICTED, NOT MEASURED

Ir L3 EXAFS computed with FEFF from the PDF-refined model (IrO2; 24 ensemble members, Debye temperature 513–528 K). This edge was measured, so the prediction serves as a consistency check against the measurement.

Against the measured spectrum: R-factor 0.1014 in R 1.0–3.5 Å.

## Literature priors (other samples: context, not constraints)

- Ir oxidation state 3, [doi:10.1021/acscatal.5c05765](https://doi.org/10.1021/acscatal.5c05765) (2025): «Our findings reveal two distinct electrochemical regimes, a low potential plateau associated with a nonconductive Ir 3+ state and a linear region where small potential variations induce reversible oxidation state and str»
- particle size 2.5 nm, [doi:10.1088/2053-1591/ad30ab](https://doi.org/10.1088/2053-1591/ad30ab) (2024): «The average particle size of the IrO2 particles on poly(BIAN-thiophene)/TNT was 2.5 nm.»
- particle size 10 nm, [doi:10.1149/ma2023-01362023mtgabs](https://doi.org/10.1149/ma2023-01362023mtgabs) (2023): «Here, we demonstrate how nanoparticles below 10 nm can be obtained at high preparation temperatures up to 800 °C with unprecedented control over particle size and morphology.»
- particle size 1.7 ± 0.4 nm, [doi:10.1149/ma2016-02/38/2425](https://doi.org/10.1149/ma2016-02/38/2425) (2016): «Chlorine−free iridium oxide nanoparticles are synthesized using the modified Adams fusion method(5), which is capable of producing spherical 1.7 ± 0.4 nm particles with a specific surface area of 150 m2/g using a low tem»
- particle size 6.5–19 nm, [doi:10.1166/jnn.2007.750](https://doi.org/10.1166/jnn.2007.750) (2007): «Nanoparticles of transition metal oxides with metallic properties, RuO2, IrO2, and ReO3 in the ranges 6.5-19 nm, 6-14 nm, and 8.5-32.5 nm, respectively have been prepared by soft chemical routes.»
- particle size 6–14 nm, [doi:10.1166/jnn.2007.750](https://doi.org/10.1166/jnn.2007.750) (2007): «Nanoparticles of transition metal oxides with metallic properties, RuO2, IrO2, and ReO3 in the ranges 6.5-19 nm, 6-14 nm, and 8.5-32.5 nm, respectively have been prepared by soft chemical routes.»
- particle size 8.5–32.5 nm, [doi:10.1166/jnn.2007.750](https://doi.org/10.1166/jnn.2007.750) (2007): «Nanoparticles of transition metal oxides with metallic properties, RuO2, IrO2, and ReO3 in the ranges 6.5-19 nm, 6-14 nm, and 8.5-32.5 nm, respectively have been prepared by soft chemical routes.»

## Claims

0. Phase consistency between XRD and PDF is confirmed: both identify IrO₂ as the sole phase, with high XRD score (0.986) and PDF fit (rw 0.234). _(evidence: check.C1)_
1. Ir–O bond length from EXAFS (1.982 Å) matches the PDF model (1.986 Å) within 0.0034 Å. _(evidence: check.C2)_
2. Ir–O coordination number from EXAFS (5.89) agrees with the PDF model after surface truncation (5.75) within 0.14. _(evidence: check.C3)_
3. Ir oxidation state determined by XANES (≈3.91) aligns with the bond‑valence sum (4.002) and the formal valence (4). _(evidence: check.C4)_
4. The EXAFS disorder (σ² = 0.00748 Å²) is lower than the PDF pair width (σ² ≈ 0.02744 Å²), giving a ratio of 0.273, below the acceptable range (0.3–1.3). This suggests static disorder, a distorted or split first shell, or surface‑layer effects that affect the two probes differently. EXAFS fits with kmax 10–12 yield coordination numbers 5.785–5.89 and σ² values 0.007273–0.007485 Å², confirming the low ratio is not due to fitting instability. _(evidence: check.C5, rerun.R2.1.exafs_window_scan)_
5. Particle size from XRD (sphere diameter 7.8 nm, Scherrer median 6.34 nm) agrees with PDF size (7.11 nm) within a relative difference of 0.097. _(evidence: check.C6)_
6. Joint simulation score for the evaluated candidate IrO₂ is 0.1187 (XRD:0.0213, PDF:0.2339, EXAFS:0.101). No alternative candidates were evaluated, so comparative favorability cannot be assessed. _(evidence: check.C7)_
7. The measured particle size (XRD sphere diameter 7.8 nm, PDF 7.11 nm) falls within literature ranges for IrO₂ nanoparticles (1.7–10 nm) reported in prior studies. _(evidence: prior.2, prior.3, prior.4, prior.5, prior.6, prior.7)_
8. The oxidation state ≈4 matches expectations for IrO₂, contrasting with literature reports of lower Ir oxidation states (e.g., Ir³⁺) under different conditions. _(evidence: prior.1)_

## Objections and resolutions

| id | objection | cited | re-run | finding | status |
|---|---|---|---|---|---|
| R1.1 | The claim that IrO₂ is favored over alternative phases in the joint simulation lacks supporting evidence because no alternative candidate phases were evaluated; the evidence only reports the score for IrO₂. | check.C7 | xrd_add_phase | re-run xrd_add_phase failed: TypeError | failed |
| R2.1 | The disorder warning (C5) suggests static disorder or a split first shell that the current model does not capture. To assess whether the EXAFS coordination number and sigma² are stable, a re-fit of the EXAFS data with varied k‑max values is required. | check.C5 | exafs_window_scan | N over kmax 10-12: O 5.79-5.89 | not confirmed |

## Limitations

- Disorder warning C5: the EXAFS/PDF σ² ratio is 0.273, below the acceptable 0.3–1.3 range, indicating static disorder, a split first shell, or surface‑layer effects not captured by the current model.
- Joint simulation limitation: claim C7 lacks comparative evidence because no alternative candidate phases were evaluated; the re‑run of xrd_add_phase failed.
