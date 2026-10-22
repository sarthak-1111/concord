"use client";
import { ArrowCounterClockwise, BookOpen, ChartLine, CheckCircle, DownloadSimple, FileText, Lightning, ListChecks, UsersThree, WarningCircle, Waveform, XCircle } from "@phosphor-icons/react";
import { API, curvesKey, type Tab, type View } from "@/lib/api";
import { verdict } from "@/lib/insight";
import CheckPanel, { CheckStrip, type Focus, type Settling } from "@/components/CheckPanel";
import TechniqueTabs, { type Studio } from "@/components/TechniqueTabs";
import VirtualXafs from "@/components/VirtualXafs";
import CriticLog from "@/components/CriticLog";
import Priors from "@/components/Priors";

const TABS: [Tab, string, typeof ListChecks][] = [
  ["checks", "Checks", ListChecks], ["fits", "Fits", ChartLine], ["virtual", "Virtual XAFS", Waveform],
  ["critic", "Critic", UsersThree], ["literature", "Literature", BookOpen], ["report", "Report", FileText],
];

function Skeleton() {
  return (
    <div className="grid gap-4 p-6" aria-busy="true" aria-label="Loading results">
      <div className="h-7 w-48 animate-pulse rounded bg-surface-warm" />
      <div className="grid grid-cols-7 gap-1.5">{Array.from({ length: 7 }, (_, i) => <div key={i} className="h-12 animate-pulse rounded-sm bg-surface-warm" />)}</div>
      <div className="h-64 animate-pulse rounded-md bg-surface-warm" />
    </div>
  );
}

const VERDICT = { ok: [CheckCircle, "text-ok"], warn: [WarningCircle, "text-warn"], bad: [XCircle, "text-bad"] } as const;

export default function Workbench({ sid, view, state, tab, setTab, focus, open, onRun, busy, onMined, settling, onStudio, onRestore }: {
  sid: string; view?: View; state: "loading" | "missing" | "error" | "ready"; tab: Tab; setTab: (t: Tab) => void; focus?: Focus;
  open: (evidenceId: string) => void; onRun: () => void; busy: boolean; onMined: () => void; settling: Omit<Settling, "view">;
  onStudio: (s: Studio) => void; onRestore: () => void;
}) {
  if (state === "loading") return <Skeleton />;
  if (!view) {
    return (
      <div className="grid h-full place-items-center p-8">
        <div className="max-w-sm text-center">
          <ChartLine size={32} className="mx-auto text-meta" aria-hidden />
          <h2 className="mt-3 font-display text-xl font-medium">{state === "error" ? "Results unavailable" : "No results yet"}</h2>
          <p className="mt-1 text-sm text-muted">
            {state === "error" ? "The API did not answer. Start it with make api, then reload."
              : "Fits, cross-checks, the virtual XAFS and the critic review appear here once the tools have run."}
          </p>
          {state === "missing" ? (
            <button disabled={busy} onClick={onRun} className="btn btn-primary mt-4"><Lightning size={16} weight="fill" aria-hidden />Run tools and checks</button>
          ) : null}
        </div>
      </div>
    );
  }
  const vd = verdict(view), [VIcon, vColor] = VERDICT[vd.tone];
  const notes = [...Object.entries(view.errors).map(([k, v]) => ({ bad: true, text: `${k} failed: ${v}` })),
    ...view.assumed.map((a) => ({ bad: false, text: `Assumed ${a}, not in the file headers.` })),
    ...Object.entries(view.user_settings ?? {}).map(([t, v]) => ({ bad: false, text: `${t.toUpperCase()} fitted with your settings: ${Object.entries(v).map(([k, x]) => `${k} ${String(x)}`).join(", ")}.` }))];
  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="grid gap-4 border-b border-line px-6 pt-5 pb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="font-mono text-xs text-meta">{sid} · {view.techniques.map((t) => t.toUpperCase()).join(" · ")} · tools {view.timings_s.total} s</div>
            <h1 translate="no" className="mt-0.5 font-display text-[28px] font-medium leading-tight">{view.composition}</h1>
            <p className="mt-1 flex items-start gap-1.5 text-sm text-fg-2">
              <VIcon size={18} weight="fill" className={`mt-px shrink-0 ${vColor}`} aria-hidden />
              <span><span className={`font-semibold ${vColor}`}>{vd.head}.</span> {vd.detail}</span>
            </p>
          </div>
          <div className="flex gap-1">
            {view.restorable ? (
              <button disabled={busy} onClick={onRestore} className="btn btn-ghost" title="Go back to the analysis before your changes"><ArrowCounterClockwise size={16} weight="bold" aria-hidden />Original</button>
            ) : null}
            <a href={`${API}/api/samples/${sid}/export?format=md`} className="btn btn-ghost" title="Download the report as Markdown"><FileText size={16} weight="bold" aria-hidden />Report</a>
            <a href={`${API}/api/samples/${sid}/export?format=json`} className="btn btn-ghost" title="Download the full analysis as JSON"><DownloadSimple size={16} weight="bold" aria-hidden />Data</a>
          </div>
        </div>
        <CheckStrip checks={view.checks} onOpen={(id) => open(`check.${id}`)} />
        {notes.length ? (
          <ul className="grid gap-1 text-xs">
            {notes.map((n) => <li key={n.text} className={n.bad ? "text-bad" : "text-muted"}>{n.text}</li>)}
          </ul>
        ) : null}
      </header>
      <div role="tablist" aria-label="Results" className="flex gap-1 overflow-x-auto border-b border-line px-4">
        {TABS.map(([key, label, Icon]) => {
          const count = key === "critic" ? view.agents?.log.length : key === "literature" ? view.priors.length : undefined;
          return (
            <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)}
              className={`-mb-px flex shrink-0 items-center gap-1.5 border-b-2 px-2 py-2.5 text-sm font-medium transition-colors duration-150 ${tab === key ? "border-accent text-fg" : "border-transparent text-muted hover:text-fg"}`}>
              <Icon size={16} weight={tab === key ? "fill" : "regular"} aria-hidden />{label}
              {count ? <span className="rounded-full bg-surface-warm px-1.5 text-[11px] tabular-nums text-muted">{count}</span> : null}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" className="@container min-h-0 flex-1 overflow-y-auto px-6 py-5">
        <div key={tab} className="rise">
          {tab === "checks" ? <CheckPanel checks={view.checks} focus={focus} settling={{ view, ...settling }} /> : null}
          {tab === "fits" ? <TechniqueTabs key={view.sample_id} view={view} focus={focus} onStudio={onStudio} /> : null}
          {tab === "virtual" ? <VirtualXafs v={view.virtual_xafs} plot={view.plots.virtual_xafs} reason={view.errors.virtual_xafs} curvesUrl={curvesKey(view)} /> : null}
          {tab === "critic" ? <CriticLog view={view} onOpen={open} /> : null}
          {tab === "literature" ? <Priors sid={view.sample_id} priors={view.priors} onMined={onMined} /> : null}
          {tab === "report" ? (
            <article className="max-w-[80ch] whitespace-pre-wrap rounded-md bg-surface p-5 font-mono text-[13px] leading-relaxed text-fg-2 shadow-ring">{view.report_md}</article>
          ) : null}
        </div>
      </div>
    </div>
  );
}
