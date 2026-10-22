"use client";
import { useState } from "react";
import { API, type View } from "@/lib/api";
import Value from "@/components/Value";

const TABS: { key: string; label: string; ids: (ev: Record<string, unknown>) => string[]; error: string[] }[] = [
  { key: "xrd", label: "XRD", ids: () => ["xrd.ranking", "xrd.size"], error: ["xrd"] },
  { key: "pdf", label: "PDF", ids: (ev) => ["pdf.best", ...Object.keys(ev).filter((k) => k.startsWith("pdf.fit."))], error: ["pdf"] },
  { key: "exafs", label: "EXAFS", ids: () => ["exafs.fit", "exafs.extra_shell"], error: ["exafs"] },
  { key: "xanes", label: "XANES · bond valence", ids: () => ["xanes", "bvs"], error: ["xanes", "bvs"] },
];

export default function TechniqueTabs({ view }: { view: View }) {
  const ev = view.evidence;
  const tabs = TABS.filter((t) => view.plots[t.key] || t.ids(ev).some((id) => id in ev) || t.error.some((e) => e in view.errors));
  const [active, setActive] = useState(tabs[0]?.key);
  const tab = tabs.find((t) => t.key === active) ?? tabs[0];
  if (!tab) return <section className="text-sm text-slate-500">No technique produced a result.</section>;
  const vision = view.vision?.[tab.key];
  return (
    <section aria-label="Results by technique" className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div role="tablist" className="mb-3 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button key={t.key} role="tab" aria-selected={t.key === tab.key} onClick={() => setActive(t.key)}
            className={`rounded-lg px-3 py-1.5 text-sm transition ${t.key === tab.key ? "bg-[#d68e2f] text-white" : "border border-slate-200 bg-white/70 text-slate-700 hover:bg-slate-50"}`}>
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" className="grid gap-4 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div>
          {view.plots[tab.key] ? (
            <img src={API + view.plots[tab.key]} alt={`${tab.label} fit: data, model and difference`} className="w-full rounded border border-slate-100" />
          ) : <p className="text-sm text-slate-500">No fit plot for this technique.</p>}
          {view.plots[`${tab.key}_zoom`] ? (
            <figure className="mt-3">
              <img src={API + view.plots[`${tab.key}_zoom`]} alt={`${tab.label} fit zoomed on the largest misfit`} className="w-full rounded border border-slate-100" />
              <figcaption className="mt-1 text-xs text-slate-500">Zoom on the window where the difference is largest relative to the noise.</figcaption>
            </figure>
          ) : null}
          {vision ? (
            <p className={`mt-2 text-sm ${vision.accepted ? "text-emerald-700" : "text-red-700"}`}>
              Visual inspection ({vision.inspector}): {vision.verdict}; numerical: {vision.numerical.reason}. Fit {vision.accepted ? "accepted" : "rejected"}.
              {vision.issues?.length ? <span className="block text-slate-600">{vision.issues.map((i) => Object.values(i).join(" · ")).join(" | ")}</span> : null}
              {vision.steps?.length ? (
                <span className="block text-slate-600">
                  Fixes tried: {vision.steps.map((s) => `${s.action} (${s.kept ? "kept" : "reverted"}): ${s.finding}`).join(" | ")}
                </span>
              ) : null}
            </p>
          ) : null}
        </div>
        <div className="grid content-start gap-3">
          {tab.error.filter((e) => e in view.errors).map((e) => (
            <p key={e} className="rounded border border-red-200 bg-red-50 p-2 text-sm text-red-800">{e}: {view.errors[e]}</p>
          ))}
          {tab.ids(ev).filter((id) => id in ev).map((id) => (
            <div key={id}>
              <div className="mb-1 font-mono text-xs text-slate-500">{id}</div>
              <Value v={ev[id]} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
