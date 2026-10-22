"use client";
import { useEffect, useState } from "react";
import { Compass, Detective, Waves } from "@phosphor-icons/react";
import { post } from "@/lib/api";
import { fmt } from "@/components/Value";
import Plot from "@/components/Plot";
import CompositionField from "@/components/PeriodicTable";

type Tech = { x_label: string; y_label: string; x: number[]; curves: Record<string, number[]>; realistic: Record<string, number[]> | null;
  pairs: { a: string; b: string; separation: number; over_noise: number | null }[]; score: number };
export type PlanResult = { label: string; composition: string; size_nm: number; candidates: string[]; absorber: string; edge: string;
  techniques: Record<string, Tech>; ranking: string[]; recommendation: string; notes: string[]; timings_s: Record<string, number> };

const COLORS = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];
const NAME: Record<string, string> = { xrd: "XRD", pdf: "PDF", exafs: "EXAFS" };

/** 0 → 1 over the duration once `on` turns true; jumps straight to 1 when motion is reduced. */
function useMorph(on: boolean, ms = 1100) {
  const [t, setT] = useState(on ? 1 : 0);
  useEffect(() => {
    if (!on) return setT(0);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return setT(1);
    let raf = 0;
    const t0 = performance.now();
    const step = (now: number) => {
      const p = Math.min(1, (now - t0) / ms);
      setT(1 - (1 - p) ** 3);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [on, ms]);
  return t;
}

export default function Planner({ initial, ganReady, onShowcase }: { initial?: string; ganReady: boolean; onShowcase: () => void }) {
  const [composition, setComposition] = useState(initial || "Pt3Co");
  const [size, setSize] = useState(3);
  const [excluded, setExcluded] = useState<string[]>([]);
  const [realistic, setRealistic] = useState(false);
  const [plan, setPlan] = useState<PlanResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const t = useMorph(realistic && !!plan?.techniques[plan.ranking[0]]?.realistic);

  const run = (opts: { realistic?: boolean; candidates?: string[] } = {}) => runFor(composition, opts);
  const runFor = async (comp: string, opts: { realistic?: boolean; candidates?: string[] } = {}) => {
    setBusy(true);
    setError(undefined);
    try {
      const p = await post<PlanResult>("/api/plans", { composition: comp.trim(), size_nm: size, realistic: opts.realistic ?? realistic,
        candidates: opts.candidates?.length ? opts.candidates : undefined });
      setPlan(p);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => { run(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleRealism = () => { const r = !realistic; setRealistic(r); run({ realistic: r, candidates: plan?.candidates.filter((c) => !excluded.includes(c)) }); };
  const best = plan ? plan.techniques[plan.ranking[0]] : undefined;
  const maxScore = plan ? Math.max(...plan.ranking.map((k) => plan.techniques[k].score)) : 1;

  return (
    <div className="h-full overflow-y-auto overscroll-contain">
      <div className="mx-auto grid max-w-[1040px] grid-cols-[minmax(0,1fr)] gap-6 px-4 py-6 sm:px-8">
        <header className="grid gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="eyebrow inline-flex items-center gap-1"><Compass size={13} weight="bold" aria-hidden />Plan a measurement</span>
            <span className="rounded-sm bg-bad px-2 py-0.5 text-[11px] font-bold tracking-wide text-accent-on">SIMULATED, NOT MEASURED</span>
          </div>
          <h1 className="font-display text-3xl font-medium leading-tight">Which technique tells the candidates apart?</h1>
          <p className="max-w-[70ch] text-sm text-muted">
            Concord simulates XRD, PDF and EXAFS for every candidate structure of the composition and measures how different they look.
            Nothing here is analysed as data; it tells you what to measure.
          </p>
        </header>

        <form onSubmit={(e) => { e.preventDefault(); setExcluded([]); run(); }} className="grid gap-4 rounded-lg bg-surface p-4 shadow-ring sm:grid-cols-[1fr_1.3fr_auto] sm:items-end">
          <label className="grid gap-1 text-sm font-medium text-fg-2">Composition
            <CompositionField value={composition} onChange={setComposition} />
          </label>
          <label className="grid gap-1 text-sm font-medium text-fg-2">
            <span className="flex justify-between">Particle size <span className="font-normal tabular-nums text-muted">{size} nm</span></span>
            <input type="range" min={1} max={10} step={0.5} value={size} onChange={(e) => setSize(+e.target.value)} className="accent-[var(--accent)]" />
          </label>
          <button disabled={busy} className="btn btn-primary justify-center"><Compass size={16} weight="bold" aria-hidden />{busy ? "Simulating…" : "Simulate"}</button>
        </form>

        {error ? (
          <div role="alert" className="flex flex-wrap items-center gap-2 rounded-md bg-bad-bg p-3 text-sm text-bad">
            <span className="min-w-0 flex-1">{error}. Try a composition with several candidate phases:</span>
            {["Pt3Co", "TiO2", "PtNi"].map((c) => (
              <button key={c} type="button" onClick={() => { setComposition(c); setExcluded([]); runFor(c); }} className="btn btn-quiet py-1 text-[13px]">{c}</button>
            ))}
          </div>
        ) : null}

        {plan ? (
          <>
            <section className="grid gap-4 rounded-lg bg-surface p-5 shadow-ring">
              <div className="flex flex-wrap items-center gap-2">
                <span className="eyebrow">Candidates</span>
                {plan.candidates.concat(excluded.filter((c) => !plan.candidates.includes(c))).map((c, i) => {
                  const off = excluded.includes(c);
                  return (
                    <button key={c} disabled={busy} aria-pressed={!off} title={off ? "Add back" : "Leave out"}
                      onClick={() => { const ex = off ? excluded.filter((x) => x !== c) : [...excluded, c]; setExcluded(ex); run({ candidates: [...plan.candidates, ...excluded].filter((x) => !ex.includes(x)) }); }}
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm transition-colors duration-150 ${off ? "text-meta line-through shadow-ring" : "bg-surface-warm text-fg"}`}>
                      <span className="size-2 rounded-full" style={{ background: off ? "var(--meta)" : COLORS[i % 4] }} aria-hidden />{c}
                    </button>
                  );
                })}
              </div>
              <p className="font-display text-xl leading-snug text-fg">{plan.recommendation}</p>
              <ol className="grid gap-2" aria-label="Techniques ranked by how well they separate the candidates">
                {plan.ranking.map((k, i) => (
                  <li key={k} className="grid grid-cols-[64px_1fr_56px] items-center gap-3 text-sm">
                    <span className="font-medium">{NAME[k] ?? k}</span>
                    <span className="h-2 overflow-hidden rounded-full bg-surface-warm">
                      <span className={`block h-full rounded-full ${i === 0 ? "bg-accent" : "bg-meta"}`} style={{ width: `${(plan.techniques[k].score / maxScore) * 100}%` }} />
                    </span>
                    <span className="text-right tabular-nums text-muted">{fmt(plan.techniques[k].score)}</span>
                  </li>
                ))}
              </ol>
              <p className="text-xs text-meta">Score: how different the closest pair of candidates looks (RMS difference of curves scaled to unit RMS; 0 is identical).</p>
            </section>

            <section className={`flex flex-wrap items-center gap-3 rounded-lg p-4 transition-colors duration-200 ${realistic ? "bg-accent/10 ring-1 ring-accent/40" : "bg-surface shadow-ring"}`}>
              <Waves size={24} weight="duotone" className="shrink-0 text-accent" aria-hidden />
              <div className="min-w-0 flex-1">
                <div className="font-medium">Instrument realism</div>
                <p className="text-sm text-muted">
                  {realistic && best?.realistic
                    ? "Every curve below now carries the background, gain and noise a real instrument adds, generated by a GAN trained on measured spectra."
                    : ganReady ? "Let a GAN trained on measured spectra add what a real instrument adds, and see whether the difference survives."
                      : "The realism GANs are not loaded (set GAN_REPO_PATH)."}
                </p>
              </div>
              <button type="button" role="switch" aria-checked={realistic} disabled={!ganReady || busy} onClick={toggleRealism}
                className={`relative h-7 w-12 shrink-0 rounded-full transition-colors duration-200 disabled:opacity-50 ${realistic ? "bg-accent" : "bg-surface-warm shadow-ring"}`}>
                <span className="sr-only">Instrument realism</span>
                <span className={`absolute left-0 top-1 size-5 rounded-full bg-surface shadow-raised transition-transform duration-200 ${realistic ? "translate-x-6" : "translate-x-1"}`} />
              </button>
              <button type="button" onClick={onShowcase} className="btn btn-quiet"><Detective size={16} weight="bold" aria-hidden />Real or GAN?</button>
            </section>

            {plan.ranking.map((k) => {
              const tc = plan.techniques[k];
              const noisy = tc.pairs.filter((q) => q.over_noise != null);  // with realism, the pair the noise hides most is the honest headline
              const closest = noisy.length ? [...noisy].sort((a, b) => a.over_noise! - b.over_noise!)[0] : [...tc.pairs].sort((a, b) => a.separation - b.separation)[0];
              const series = plan.candidates.filter((c) => tc.curves[c]).map((c, i) => {
                const clean = tc.curves[c], real = tc.realistic?.[c];
                return { key: c, label: c, color: COLORS[plan.candidates.indexOf(c) % 4], width: 1.5,
                  y: real && t > 0 ? clean.map((v, j) => v + (real[j] - v) * t) : clean };
              });
              return (
                <section key={k} className="grid gap-3 rounded-lg bg-surface p-4 shadow-ring">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="font-display text-xl font-medium">{NAME[k] ?? k}</h2>
                    {closest ? (
                      <span className="text-sm text-muted">
                        {closest.over_noise != null ? "Hardest pair under instrument noise" : "Closest pair"}: {closest.a} and {closest.b},{" "}
                        <span className="tabular-nums text-fg">{fmt(closest.separation)}</span>
                        {closest.over_noise != null ? <>, <span className={`tabular-nums font-medium ${closest.over_noise >= 3 ? "text-ok" : "text-warn"}`}>{fmt(closest.over_noise)}×</span> the noise{closest.over_noise < 3 ? ", hard to resolve" : ""}</> : null}
                      </span>
                    ) : null}
                  </div>
                  <Plot x={tc.x} xLabel={tc.x_label} yLabel={tc.y_label} series={series} height={220} ariaLabel={`Simulated ${NAME[k] ?? k} of each candidate`} />
                </section>
              );
            })}
            {plan.notes.length ? <ul className="grid gap-1 text-xs text-meta">{plan.notes.map((n) => <li key={n}>{n}</li>)}</ul> : null}
          </>
        ) : busy ? <div className="h-64 animate-pulse rounded-lg bg-surface-warm" aria-busy="true" /> : null}
      </div>
    </div>
  );
}
