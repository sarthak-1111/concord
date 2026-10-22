"use client";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { ArrowCounterClockwise, CheckCircle, Funnel, Robot, Sliders, XCircle, Wrench } from "@phosphor-icons/react";
import { API, curvesKey, fetcher, type Curves, type View } from "@/lib/api";
import Value, { fmt } from "@/components/Value";
import Plot from "@/components/Plot";

const TABS: { key: string; label: string; ids: (ev: Record<string, unknown>) => string[]; error: string[] }[] = [
  { key: "xrd", label: "XRD", ids: () => ["xrd.ranking", "xrd.size"], error: ["xrd"] },
  { key: "pdf", label: "PDF", ids: (ev) => ["pdf.best", ...Object.keys(ev).filter((k) => k.startsWith("pdf.fit."))], error: ["pdf"] },
  { key: "exafs", label: "EXAFS", ids: () => ["exafs.fit", "exafs.extra_shell"], error: ["exafs"] },
  { key: "xanes", label: "XANES", ids: () => ["xanes", "bvs"], error: ["xanes", "bvs"] },
];

export const Figure = ({ src, alt, caption, lazy }: { src: string; alt: string; caption?: string; lazy?: boolean }) => (
  <figure className="m-0">
    <div className="overflow-hidden rounded-md bg-figure p-2 shadow-ring">
      <img src={API + src} alt={alt} loading={lazy ? "lazy" : undefined} className="block h-auto w-full" />
    </div>
    {caption ? <figcaption className="mt-1.5 text-xs text-meta">{caption}</figcaption> : null}
  </figure>
);

export type Studio = { kind: "preprocess" | "analysis"; technique: string };

export default function TechniqueTabs({ view, focus, onStudio }: { view: View; focus?: { id: string; n: number }; onStudio?: (s: Studio) => void }) {
  const ev = view.evidence;
  const { data: curves } = useSWR<Curves>(curvesKey(view), fetcher, { revalidateOnFocus: false });
  const tabs = TABS.filter((t) => view.plots[t.key] || t.ids(ev).some((id) => id in ev) || t.error.some((e) => e in view.errors));
  const [active, setActive] = useState(tabs[0]?.key);
  useEffect(() => { if (focus && tabs.some((t) => t.key === focus.id)) setActive(focus.id); }, [focus?.n]); // eslint-disable-line react-hooks/exhaustive-deps
  const tab = tabs.find((t) => t.key === active) ?? tabs[0];
  if (!tab) return <p className="text-sm text-meta">No technique produced a result.</p>;
  const vision = view.vision?.[tab.key];
  const fit = view.fitting?.[tab.key];
  const c = curves?.[tab.key as "xrd" | "pdf" | "exafs"];
  const pngs = [view.plots[tab.key], view.plots[`${tab.key}_zoom`]].filter(Boolean);
  return (
    <section aria-label="Fits by technique" className="grid gap-4">
      <div role="tablist" aria-label="Technique" className="inline-flex w-fit flex-wrap gap-1 rounded-md bg-surface-warm p-1">
        {tabs.map((t) => (
          <button key={t.key} role="tab" aria-selected={t.key === tab.key} onClick={() => setActive(t.key)}
            className={`rounded-sm px-3 py-1 text-sm font-medium transition-colors duration-150 ${t.key === tab.key ? "bg-surface text-fg shadow-ring" : "text-muted hover:text-fg"}`}>
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" className="grid gap-5 @4xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="grid min-w-0 content-start gap-4">
          {c ? (
            <div className="min-w-0 rounded-md bg-surface p-3 shadow-ring">
              <div className="mb-2 text-sm font-medium text-fg">{c.title}</div>
              <Plot key={tab.key} x={c.x} xLabel={c.x_label} yLabel={c.y_label} ticks={c.ticks} window={c.window} ariaLabel={`${c.title}: data, model and difference`}
                series={[{ key: "obs", label: "data", y: c.obs, color: "var(--series-1)", width: 1.25 }, { key: "calc", label: "model", y: c.calc, color: "var(--series-2)", width: 1.5 }]}
                diff={{ y: c.diff, label: "difference (data minus model)" }} />
              {onStudio ? (
                <div className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3">
                  {tab.key === "pdf" && view.raw_pdf ? (
                    <button onClick={() => onStudio({ kind: "preprocess", technique: "pdf" })} className="btn btn-quiet"><Funnel size={16} weight="bold" aria-hidden />Open in preprocessing</button>
                  ) : null}
                  <button onClick={() => onStudio({ kind: "analysis", technique: tab.key })} className="btn btn-quiet"><Sliders size={16} weight="bold" aria-hidden />Open in analysis</button>
                </div>
              ) : null}
            </div>
          ) : pngs[0] ? <Figure src={pngs[0]} alt={`${tab.label} fit: data, model and difference`} />
            : <p className="text-sm text-meta">No fit plot for this technique.</p>}
          {fit ? (
            <div className="rounded-md bg-surface p-3 text-sm shadow-ring">
              <div className="eyebrow flex items-center gap-1"><Robot size={12} weight="bold" aria-hidden />Fitted by the {tab.label} agent</div>
              <p className="mt-1 tabular-nums text-fg">{fit.metric} {fmt(fit.start)} → {fmt(fit.end)}{Object.keys(fit.values).length ? "" : ", kept the defaults"}</p>
              {fit.steps.length ? (
                <ol className="mt-2 grid gap-1.5">
                  {fit.steps.map((s) => (
                    <li key={s.step} className="grid gap-0.5">
                      <div className="flex flex-wrap items-center gap-x-2">
                        <span className="font-mono text-xs">{Object.entries(s.changes).map(([k, v]) => `${k} ${fmt(v)}`).join(", ") || "defaults"}</span>
                        <span className="tabular-nums text-muted">{fmt(s.metric)}</span>
                        {s.kept ? <span className="flex items-center gap-1 text-xs text-ok"><CheckCircle size={12} weight="fill" aria-hidden />kept</span>
                          : <span className="flex items-center gap-1 text-xs text-meta"><ArrowCounterClockwise size={12} weight="bold" aria-hidden />reverted</span>}
                      </div>
                      <p className="text-fg-2">{s.reason}{s.error ? ` (${s.error})` : ""}</p>
                    </li>
                  ))}
                </ol>
              ) : null}
              <p className="mt-2 text-muted">{fit.verdict}</p>
            </div>
          ) : null}
          {vision ? (
            <div className={`rounded-md p-3 text-sm ${vision.accepted ? "bg-ok-bg" : "bg-bad-bg"}`}>
              <div className={`flex items-center gap-1.5 font-medium ${vision.accepted ? "text-ok" : "text-bad"}`}>
                {vision.accepted ? <CheckCircle size={16} weight="fill" aria-hidden /> : <XCircle size={16} weight="fill" aria-hidden />}
                Fit {vision.accepted ? "accepted" : "rejected"}
              </div>
              <p className="mt-1 text-fg-2">Visual inspection ({vision.inspector}): {vision.verdict}. Numerical: {vision.numerical.reason}.</p>
              {vision.issues?.length ? (
                <ul className="mt-1 list-disc pl-5 text-fg-2">{vision.issues.map((i, k) => <li key={k}>{Object.values(i).join(", ")}</li>)}</ul>
              ) : null}
              {vision.steps?.length ? (
                <div className="mt-2">
                  <div className="eyebrow flex items-center gap-1"><Wrench size={12} weight="bold" aria-hidden />Fixes tried</div>
                  <ul className="mt-1 grid gap-1 text-fg-2">
                    {vision.steps.map((s, k) => <li key={k}><span className="font-mono text-xs">{s.action}</span> ({s.kept ? "kept" : "reverted"}): {s.finding}</li>)}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
          {c && pngs.length ? (
            <details className="text-sm">
              <summary className="cursor-pointer text-muted hover:text-fg">Figures the visual inspection judged</summary>
              <div className="mt-2 grid gap-3">
                {pngs.map((p, i) => <Figure key={p} src={p} lazy alt={`${tab.label} fit${i ? ", zoomed on the largest misfit" : ""}`}
                  caption={i ? "Zoom on the window where the difference is largest relative to the noise." : undefined} />)}
              </div>
            </details>
          ) : null}
        </div>
        <div className="grid min-w-0 content-start gap-4">
          {tab.error.filter((e) => e in view.errors).map((e) => (
            <p key={e} role="alert" className="rounded-md bg-bad-bg p-3 text-sm text-bad">{e}: {view.errors[e]}</p>
          ))}
          {tab.ids(ev).filter((id) => id in ev).map((id) => (
            <div key={id} className="min-w-0">
              <div className="mb-1 font-mono text-xs text-meta">{id}</div>
              <Value v={ev[id]} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
