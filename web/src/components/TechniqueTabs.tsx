"use client";
import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Wrench } from "@phosphor-icons/react";
import { API, type View } from "@/lib/api";
import Value from "@/components/Value";

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

export default function TechniqueTabs({ view, focus }: { view: View; focus?: { id: string; n: number } }) {
  const ev = view.evidence;
  const tabs = TABS.filter((t) => view.plots[t.key] || t.ids(ev).some((id) => id in ev) || t.error.some((e) => e in view.errors));
  const [active, setActive] = useState(tabs[0]?.key);
  useEffect(() => { if (focus && tabs.some((t) => t.key === focus.id)) setActive(focus.id); }, [focus?.n]); // eslint-disable-line react-hooks/exhaustive-deps
  const tab = tabs.find((t) => t.key === active) ?? tabs[0];
  if (!tab) return <p className="text-sm text-meta">No technique produced a result.</p>;
  const vision = view.vision?.[tab.key];
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
      <div role="tabpanel" className="grid gap-5 @3xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className="grid content-start gap-4">
          {view.plots[tab.key] ? <Figure src={view.plots[tab.key]} alt={`${tab.label} fit: data, model and difference`} />
            : <p className="text-sm text-meta">No fit plot for this technique.</p>}
          {view.plots[`${tab.key}_zoom`] ? (
            <Figure src={view.plots[`${tab.key}_zoom`]} alt={`${tab.label} fit zoomed on the largest misfit`} lazy
              caption="Zoom on the window where the difference is largest relative to the noise." />
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
        </div>
        <div className="grid content-start gap-4">
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
