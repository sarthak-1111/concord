# Demo

Five steps that show Concord on one sample, then a three-minute video plan. Everything runs locally; only a new
critic run needs the LLM endpoint in `.env`. The saved critic runs in `results/runs/` are shown without it.

## Five steps

1. **Install, build the data and score it** (once):

   ```bash
   make setup && make data   # dataset v1: 60 samples from open structures, validated (about 30 s to build)
   make eval                 # tools and checks on the 19 test and fault samples (about 2 min), results/eval.md
   ```

2. **Open the workbench** in two terminals: `make api`, then `make ui`, and go to
   http://127.0.0.1:3000/console#s0031.

3. **Read the cross-check panel.** s0031 is labelled Pt and every technique alone gives a plausible answer, yet
   three checks are red, each with its numbers:
   - **C1:** no candidate structure fits the PDF (best Rw 0.51, for Pt).
   - **C3:** EXAFS counts 13.1 ± 2.2 Pt neighbours where the refined model has 8.8.
   - **C6:** XRD sees 2.66 nm crystallites where the PDF sees 1.61 nm particles.

   *Show numbers* opens the values and the tolerances from `config.yaml`.

4. **Look at the fits.** The XRD tab shows the data against simulated Pt with its reflection ticks. The zoom below
   it lands on 36.5–48.5° 2θ: the measured 111 peak sits at a lower angle than its tick, a hump at 43.5° matches no
   reflection, and at the 200 position (46°) there is almost nothing. The visual inspection rejects the fit, tries
   a second phase and reverts it: adding PtO2 takes the residual RMS only from 562 to 561, far from the 20 % a kept
   fix needs. The virtual EXAFS of the refined model misses the measured spectrum (R-factor 0.60; clean samples are
   near 0.02).

5. **Read the critic log and export.** The saved run of *Run full · with critic* is shown below the tabs. On s0031
   the analyst declines to name a phase, each claim cites its evidence ids, and the critic raises no objection. On
   s0052 the critic caught the analyst saying the visual inspection had rejected the PDF fit, which it had accepted,
   and the claim was corrected in the next round. On s0038 the critic's objections were settled by re-runs: it
   doubted that PtO2 was absent, and a two-phase XRD refinement gave PtO2 0 % of the intensity. *Report .md*
   downloads the report.

The planted fault was an icosahedral particle: 20 twinned tetrahedral domains, which no single fcc model
reproduces. Concord does not name the twinning. It refuses to report one structural model, and every check that
disagrees says by how much.

To try your own files, open *Analyse your own data* in the sidebar, give the composition and the XRD, PDF and/or
XAFS files, and press *Upload and analyse*.

## Three-minute storyboard

Record s0031 with the saved critic log (`results/runs/s0031/agents.json`): a live critic run takes 20 to 60 minutes
on the shared endpoint. The fast run in shot 2 is live.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:15 | The console and its sample list | "XRD, PDF and XAFS each answer a different question about a nanoparticle. Concord asks whether the answers describe one structure." |
| 0:15–0:40 | Pick s0031, labelled Pt, and press *Run fast · tools only*; cut the 46 s wait | "This sample is labelled platinum. The fast run needs no LLM: phase search, PDF refinement and EXAFS fit in under a minute." |
| 0:40–1:15 | The cross-check panel; *Show numbers* on C1, C3 and C6 | "Alone, each fit looks reasonable. Together, three checks fail. No candidate fits the PDF: the best Rw is 0.51. EXAFS counts 13 platinum neighbours where the model has 9. XRD sees 2.7 nm crystallites, the PDF 1.6 nm particles. Every check shows its numbers and its tolerance." |
| 1:15–1:45 | The XRD tab: the fit with its ticks, the zoom on 36.5–48.5°, the *Fixes tried* line | "The visual inspection zooms in where the fit fails: the main peak is shifted, and where platinum's 200 peak should be there is almost nothing. It tries the obvious fix, a second phase, PtO2. The residual moves from 562 to 561, so the fix is reverted." |
| 1:45–2:05 | The virtual XAFS panel | "From the refined model Concord predicts the XAFS, labelled predicted, not measured. The measured spectrum lies outside the whole band: R-factor 0.60, where clean samples sit near 0.02." |
| 2:05–2:40 | The critic log: the analyst's model, *none: no candidate fits*, with evidence chips under each claim; then ten seconds of s0052's log | "The analyst, gpt-oss, writes the model from this evidence only; each claim cites evidence ids, and a number guard rejects any number not in the evidence. Here it declines to name a phase, and a separate critic finds nothing to object to. On another sample the analyst said the PDF fit had been rejected; the critic pointed to the inspection, which had accepted it, and the analyst corrected itself." |
| 2:40–3:00 | *Report .md* downloads; `results/eval.md` | "The planted fault was an icosahedral particle: twenty twinned domains that no single fcc model reproduces. Concord does not name it. It refuses to report one model and says by how much the techniques disagree. On the 19 test and fault samples it identified every clean phase, caught 6 of 9 planted faults and raised no false alarm." |
