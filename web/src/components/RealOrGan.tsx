"use client";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { ArrowRight, Detective, X } from "@phosphor-icons/react";
import { fetcher } from "@/lib/api";
import { fmt } from "@/components/Value";
import Plot from "@/components/Plot";

type Curve = { x: number[]; y: number[] };
type Show = {
  technique: string; x_label: string; y_label: string; real: Curve; simulated: Curve; gan: Curve; seed: number;
  source: { id?: string; title?: string; licence?: string; url?: string; attribution?: string };
  c2st: { gan: number | null; classical: number | null; note: string } | null;
};
type Who = "real" | "simulated" | "gan";

const WHO: Record<Who, { label: string; color: string; line: string }> = {
  real: { label: "Measured", color: "var(--series-1)", line: "on a real instrument" },
  gan: { label: "GAN", color: "var(--series-2)", line: "the simulation after the GAN added instrument effects" },
  simulated: { label: "Simulation", color: "var(--series-3)", line: "a clean simulation of the same material" },
};
const ORDERS: Who[][] = [["gan", "real", "simulated"], ["real", "simulated", "gan"], ["simulated", "gan", "real"], ["gan", "simulated", "real"], ["real", "gan", "simulated"], ["simulated", "real", "gan"]];
const TECHS = [["xrd", "XRD"], ["pdf", "PDF"], ["exafs", "EXAFS"]] as const;

/** "Real or GAN?": three unlabelled curves of one material; the viewer picks the measured one, then all are revealed. */
export default function RealOrGan({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [tech, setTech] = useState<"xrd" | "pdf" | "exafs">("xrd");
  const [seed, setSeed] = useState(0);
  const [pick, setPick] = useState<Who>();
  const [score, setScore] = useState({ right: 0, fooled: 0, rounds: 0 });
  const { data, error, isLoading } = useSWR<Show>(open ? `/api/gan/showcase?technique=${tech}&seed=${seed}` : null, fetcher, { revalidateOnFocus: false });

  useEffect(() => {
    const d = ref.current;
    if (open && d && !d.open) d.showModal();
    if (!open && d?.open) d.close();
  }, [open]);

  const order = ORDERS[seed % ORDERS.length];
  const choose = (w: Who) => {
    if (pick) return;
    setPick(w);
    setScore((s) => ({ right: s.right + +(w === "real"), fooled: s.fooled + +(w === "gan"), rounds: s.rounds + 1 }));
  };
  const next = () => { setPick(undefined); setSeed((s) => s + 1); };
  const headline = !pick ? null : pick === "real" ? "Right, that one was measured." : pick === "gan"
    ? "Fooled. That curve never touched an instrument." : "That is the clean simulation, too smooth to be real.";

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="rog-h"
      className="m-auto max-h-[calc(100dvh-32px)] w-[min(1080px,calc(100vw-32px))] overscroll-contain rounded-lg bg-surface p-0 text-fg shadow-raised backdrop:bg-black/40">
      <div className="grid gap-5 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <span className="eyebrow inline-flex items-center gap-1"><Detective size={13} weight="bold" aria-hidden />Real or GAN?</span>
            <h2 id="rog-h" className="mt-1 font-display text-3xl font-medium leading-tight">One of these was measured. Which one?</h2>
            <p className="mt-1 max-w-[70ch] text-sm text-muted">
              The other two start from the same clean simulation. One stays clean; the GAN, trained on measured spectra, turns the other into what an instrument would record.
            </p>
          </div>
          <button onClick={onClose} className="btn btn-ghost -mr-2 -mt-1 px-2" aria-label="Close"><X size={18} weight="bold" /></button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div role="tablist" aria-label="Technique" className="inline-flex rounded-md bg-surface-warm p-1">
            {TECHS.map(([k, l]) => (
              <button key={k} role="tab" aria-selected={tech === k} onClick={() => { setTech(k); setPick(undefined); }}
                className={`rounded-sm px-3 py-1 text-sm font-medium transition-colors duration-150 ${tech === k ? "bg-surface text-fg shadow-ring" : "text-muted hover:text-fg"}`}>{l}</button>
            ))}
          </div>
          {score.rounds ? (
            <span className="text-sm text-muted tabular-nums">Found the measured one {score.right} of {score.rounds}; fooled by the GAN {score.fooled} {score.fooled === 1 ? "time" : "times"}.</span>
          ) : null}
        </div>

        {error ? <p role="alert" className="rounded-md bg-bad-bg p-3 text-sm text-bad">{error.message}</p> : null}
        <div className="grid gap-3 md:grid-cols-3">
          {order.map((w, i) => {
            const c = data?.[w], shown = !!pick, me = pick === w;
            return (
              <button key={`${seed}-${w}`} onClick={() => choose(w)} disabled={!data || shown} aria-label={`Curve ${"ABC"[i]}${shown ? `: ${WHO[w].label}` : ""}`}
                className={`rise grid min-w-0 gap-2 rounded-md p-3 text-left transition-[box-shadow,background-color] duration-200 ${shown ? (w === "real" ? "bg-ok-bg ring-2 ring-[var(--success)]" : me ? "bg-bad-bg ring-2 ring-[var(--danger)]" : "bg-bg") : "bg-bg shadow-ring hover:bg-surface-warm"} disabled:cursor-default`}>
                <span className="flex items-center justify-between">
                  <span className="font-display text-lg font-medium">{"ABC"[i]}</span>
                  {shown ? <span className="rounded-full px-2 py-0.5 text-[11px] font-semibold text-accent-on" style={{ background: WHO[w].color }}>{WHO[w].label}</span>
                    : <span className="text-xs text-meta">Pick this one</span>}
                </span>
                {c ? (
                  <span className="pointer-events-none block min-w-0">
                    <Plot x={c.x} xLabel={data!.x_label} yLabel={data!.y_label} height={170} ariaLabel={`Curve ${"ABC"[i]}`}
                      series={[{ key: w, label: shown ? WHO[w].label : `curve ${"ABC"[i]}`, y: c.y, color: shown ? WHO[w].color : "var(--fg-2)", width: 1.25 }]} />
                  </span>
                ) : <span className="block h-[210px] animate-pulse rounded-sm bg-surface-warm" aria-busy={isLoading} />}
              </button>
            );
          })}
        </div>

        {pick && data ? (
          <div className="rise grid gap-2 rounded-md bg-bg p-4" role="status">
            <p className="font-display text-2xl font-medium">{headline}</p>
            <p className="text-sm text-fg-2">
              {order.map((w, i) => `${"ABC"[i]} is ${WHO[w].line}`).join("; ")}.
            </p>
            {data.c2st?.gan != null ? (
              <p className="text-sm text-muted">
                Honest scorecard for {tech.toUpperCase()}: a classifier trained to spot fakes catches the GAN&apos;s curves {fmt(Math.round(data.c2st.gan * 100))} % of the time
                {data.c2st.classical != null ? `, and classical added noise ${fmt(Math.round(data.c2st.classical * 100))} %` : ""}. 50 % would mean it cannot tell them from measured data.
              </p>
            ) : null}
            <p className="text-xs text-meta">
              Measured spectrum: {data.source.attribution ?? [data.source.title ?? data.source.id, data.source.licence].filter(Boolean).join(", ")}
              {data.source.url ? <> (<a href={data.source.url.startsWith("http") ? data.source.url : `https://doi.org/${data.source.url}`} target="_blank" rel="noreferrer" className="text-accent hover:underline">source</a>)</> : null}.
            </p>
            <div className="mt-1"><button onClick={next} className="btn btn-primary">Next round<ArrowRight size={16} weight="bold" aria-hidden /></button></div>
          </div>
        ) : null}
      </div>
    </dialog>
  );
}
