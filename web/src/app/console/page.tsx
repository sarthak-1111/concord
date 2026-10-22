"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { ChatCircle, ChartLine, List, SidebarSimple, X } from "@phosphor-icons/react";
import { API, fetcher, locate, post, type ChatReply, type Prior, type SampleRow, type Tab, type View } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";
import { useThreads, type Msg, type Step } from "@/lib/thread";
import type { Focus } from "@/components/CheckPanel";
import type { Settle } from "@/lib/insight";
import Rail from "@/components/Rail";
import Chat from "@/components/Chat";
import Workbench from "@/components/Workbench";
import Upload from "@/components/Upload";
import Planner from "@/components/Planner";
import RealOrGan from "@/components/RealOrGan";

type Run = { id: string; sid: string; mode: "fast" | "full"; local?: boolean };  // local: no stream, a single request

const tally = (v: View) => {
  const n = (s: string) => v.checks.filter((c) => c.status === s).length;
  return `${v.phase ? `Phase ${v.phase}. ` : "No candidate fits. "}${n("pass")} pass, ${n("warn")} warn, ${n("fail")} fail${n("skip") ? `, ${n("skip")} skipped` : ""}.`;
};

export default function Console() {
  const { data: samples, error: listError, mutate: refreshSamples } = useSWR<SampleRow[]>("/api/samples", fetcher);
  const [sid, setSid] = useState<string>();
  const { data: view, error, isLoading, mutate } = useSWR<View>(sid ? `/api/samples/${sid}` : null, fetcher, { shouldRetryOnError: false, revalidateOnFocus: false });
  const threads = useThreads();
  const [run, setRun] = useState<Run>();
  const { events } = useRunStream(run?.local ? undefined : run?.id);
  const [asking, setAsking] = useState<string>();
  const [tab, setTab] = useState<Tab>("checks");
  const [focus, setFocus] = useState<Focus>();
  const [pane, setPane] = useState<"chat" | "results">("chat");  // below xl only one pane shows
  const [results, setResults] = useState(true);  // xl and up: the results panel can be hidden
  const [rail, setRail] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [planning, setPlanning] = useState(false);
  const [showcase, setShowcase] = useState(false);
  const { data: ganStatus } = useSWR<{ loaded: string[] }>("/api/gan", fetcher, { revalidateOnFocus: false });
  const handled = useRef<string | undefined>(undefined);
  const searching = useRef(false);

  useEffect(() => {  // first visit: the sample named in the URL hash, else the first test sample
    if (sid || !samples?.length) return;
    const h = window.location.hash.slice(1);
    setPlanning(h === "plan");
    setSid(samples.some((s) => s.id === h) ? h : (samples.find((s) => s.split === "test") ?? samples[0]).id);
  }, [samples, sid]);

  useEffect(() => {  // links like /console#s0031 also work on an open page
    const onHash = () => {
      const h = window.location.hash.slice(1);
      setPlanning(h === "plan");
      if (h && h !== "plan") setSid(h);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {  // mirror the run's stream into its sample's thread
    if (!run || !events.length) return;
    const steps: Step[] = events.flatMap((e): Step[] => e.type === "status" ? [{ kind: "status", text: String(e.payload) }]
      : e.type === "event" ? [{ kind: "agent", author: e.payload.author, text: e.payload.content.parts.map((p: { text: string }) => p.text).join(" ") }] : []);
    const result: View | undefined = events.find((e) => e.type === "result")?.payload;
    const err = events.find((e) => e.type === "error")?.payload;
    const done = events.some((e) => e.type === "done");
    const closed = events.some((e) => e.type === "closed");
    const end = done || err || closed;
    if (result && handled.current !== run.id) {
      handled.current = run.id;
      globalMutate(`/api/samples/${result.sample_id}`, result, { revalidate: false });
      refreshSamples();
    }
    threads.update(run.sid, (msgs) => msgs.map((m) => m.kind === "run" && m.id === run.id ? {
      ...m, steps, state: err || (closed && !done) ? "error" : done ? "done" : "running", ended: end ? Date.now() : undefined,
      summary: result ? tally(result) + (run.mode === "full" && result.agents ? ` The critic took ${result.agents.rounds} round${result.agents.rounds === 1 ? "" : "s"} and raised ${result.agents.log.length} objection${result.agents.log.length === 1 ? "" : "s"}.` : "") : undefined,
      error: err ? String(err) : closed && !done ? "The connection to the API closed before the run finished." : undefined,
    } : m));
    if (end) setRun(undefined);
  }, [events]); // eslint-disable-line react-hooks/exhaustive-deps

  const select = useCallback((id: string) => {
    setSid(id);
    setPlanning(false);
    setFocus(undefined);
    setRail(false);
    history.replaceState(null, "", `#${id}`);
  }, []);
  const plan = () => { setPlanning(true); setRail(false); setUploading(false); history.replaceState(null, "", "#plan"); };

  const start = async (mode: "fast" | "full", id = sid) => {
    if (!id || run) return;
    try {
      const { run_id } = await post<{ run_id: string }>("/api/runs", { sample: id, mode });
      threads.update(id, (m) => [...m, { kind: "run", id: run_id, mode, state: "running", started: Date.now(), steps: [] }]);
      setRun({ id: run_id, sid: id, mode });
    } catch (e) {
      threads.update(id, (m) => [...m, { kind: "error", text: `The run could not start: ${(e as Error).message}` }]);
    }
  };

  const ask = async (text: string) => {
    if (!sid) return;
    const id = sid;
    const history = [...threads.get(id), { kind: "user", text } as Msg]
      .flatMap((m) => m.kind === "user" ? [{ role: "user", content: m.text }] : m.kind === "answer" ? [{ role: "assistant", content: m.answer }] : []);
    threads.update(id, (m) => [...m, { kind: "user", text }]);
    setAsking(id);
    try {
      const r = await post<ChatReply>(`/api/samples/${id}/chat`, { messages: history.slice(-12) });
      threads.update(id, (m) => [...m, { kind: "answer", ...r }]);
    } catch (e) {
      threads.update(id, (m) => [...m, { kind: "error", text: (e as Error).message }]);
    } finally {
      setAsking(undefined);
    }
  };

  const findPriors = async () => {
    if (!sid || searching.current) return;
    const id = sid, rid = `priors-${Date.now()}`, started = Date.now();
    searching.current = true;
    const finish = (patch: Partial<Extract<Msg, { kind: "run" }>>) =>
      threads.update(id, (m) => m.map((x) => (x.kind === "run" && x.id === rid ? { ...x, ended: Date.now(), ...patch } : x)));
    threads.update(id, (m) => [...m, { kind: "run", id: rid, mode: "priors", state: "running", started, steps: [{ kind: "status", text: "Searching OpenAlex, Crossref and arXiv for this material" }] }]);
    try {
      const d = await post<{ papers: number; priors: Prior[]; errors?: string[] }>(`/api/samples/${id}/priors`);
      finish({ state: "done", summary: `${d.papers} papers read, ${d.priors.length} literature values kept with their DOI.${d.errors?.length ? ` Incomplete: ${d.errors.join(", ")}.` : ""}` });
      globalMutate(`/api/samples/${id}`);
    } catch (e) {
      finish({ state: "error", error: (e as Error).message });
    } finally {
      searching.current = false;
    }
  };

  const settle = async (check: string, s: Settle) => {
    if (!sid || run) return;
    const id = sid, rid = `action-${Date.now()}`;
    const finish = (patch: Partial<Extract<Msg, { kind: "run" }>>) =>
      threads.update(id, (m) => m.map((x) => (x.kind === "run" && x.id === rid ? { ...x, ended: Date.now(), ...patch } : x)));
    threads.update(id, (m) => [...m, { kind: "run", id: rid, mode: "action", label: s.label, check, state: "running", started: Date.now(),
      steps: [{ kind: "status", text: `Testing ${check} with a deterministic re-run: ${s.action}` }] }]);
    setRun({ id: rid, sid: id, mode: "fast", local: true });
    try {
      const d = await post<{ result: Record<string, unknown> & { confirms?: boolean; error?: string }; finding: string }>(`/api/samples/${id}/actions`, { action: s.action, args: s.args });
      if (d.result.error) finish({ state: "error", error: d.finding });
      else finish({ state: "done", confirms: !!d.result.confirms, result: d.result,
        summary: `${d.finding}. ${d.result.confirms ? `This supports the doubt behind ${check}.` : `The original result holds.`}` });
    } catch (e) {
      finish({ state: "error", error: (e as Error).message });
    } finally {
      setRun(undefined);
    }
  };

  const open = (evidenceId: string) => {
    const t = locate(evidenceId);
    setTab(t.tab);
    if (t.focus) setFocus({ id: t.focus, n: Date.now() });
    setResults(true);
    setPane("results");
  };

  const uploaded = async (id: string) => {
    setUploading(false);
    await refreshSamples();
    select(id);
    start("fast", id);
  };

  const state = !sid || isLoading ? "loading" : view ? "ready" : (error as { status?: number })?.status === 404 ? "missing" : error ? "error" : "loading";
  const row = samples?.find((s) => s.id === sid);
  const busy = !!run;

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-bg text-fg">
      <a href="#conversation" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-sm focus:bg-surface focus:px-3 focus:py-2 focus:shadow-raised">Skip to the conversation</a>
      <aside className="hidden w-[264px] shrink-0 border-r border-line lg:block">
        <Rail samples={samples} error={listError} selected={sid} running={run?.sid} onSelect={select} onNew={() => setUploading(true)}
          onPlan={plan} onShowcase={() => setShowcase(true)} planning={planning} />
      </aside>
      {rail ? (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Samples">
          <button className="absolute inset-0 bg-black/30" aria-label="Close the sample list" onClick={() => setRail(false)} />
          <div className="rise absolute inset-y-0 left-0 w-[min(300px,85vw)] bg-bg shadow-raised">
            <button onClick={() => setRail(false)} className="btn btn-ghost absolute right-2 top-14 z-10 px-2" aria-label="Close"><X size={18} weight="bold" /></button>
            <Rail samples={samples} error={listError} selected={sid} running={run?.sid} onSelect={select} onNew={() => { setRail(false); setUploading(true); }}
              onPlan={plan} onShowcase={() => { setRail(false); setShowcase(true); }} planning={planning} />
          </div>
        </div>
      ) : null}

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-12 shrink-0 items-center gap-2 border-b border-line px-3 xl:hidden">
          <button onClick={() => setRail(true)} className="btn btn-ghost px-2 lg:hidden" aria-label="Open the sample list"><List size={20} weight="bold" /></button>
          <span className="min-w-0 truncate text-sm">{planning ? <span className="font-medium">Plan a measurement</span>
            : <><span className="font-medium">{view?.composition ?? row?.composition}</span> <span className="font-mono text-xs text-meta">{sid}</span></>}</span>
          <div role="tablist" aria-label="View" className={`ml-auto rounded-md bg-surface-warm p-0.5 ${planning ? "hidden" : "inline-flex"}`}>
            {([["chat", "Chat", ChatCircle], ["results", "Results", ChartLine]] as const).map(([k, label, Icon]) => (
              <button key={k} role="tab" aria-selected={pane === k} onClick={() => setPane(k)}
                className={`flex items-center gap-1 rounded-sm px-2.5 py-1 text-sm font-medium transition-colors duration-150 ${pane === k ? "bg-surface text-fg shadow-ring" : "text-muted"}`}>
                <Icon size={15} weight="bold" aria-hidden />{label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex min-h-0 flex-1">
          {planning ? (
            <section aria-label="Plan a measurement" className="min-w-0 flex-1"><Planner initial={view?.composition} ganReady={!!ganStatus?.loaded?.length} onShowcase={() => setShowcase(true)} /></section>
          ) : sid ? (
            <>
              <section aria-label="Conversation" className={`relative min-w-0 flex-1 flex-col ${pane === "chat" ? "flex" : "hidden"} xl:flex ${results ? "xl:max-w-[520px] xl:border-r xl:border-line" : ""}`}>
                <button onClick={() => setResults((x) => !x)} className="btn btn-ghost absolute right-3 top-3 z-10 hidden px-2 xl:inline-flex"
                  aria-label={results ? "Hide the results panel" : "Show the results panel"} title={results ? "Hide results" : "Show results"}>
                  <SidebarSimple size={18} weight="bold" className="-scale-x-100" />
                </button>
                <Chat sid={sid} row={row} view={view} state={state} msgs={threads.get(sid)} asking={asking === sid} busy={busy}
                  act={{ ask, run: (m) => start(m), findPriors, open, upload: () => setUploading(true) }} />
              </section>
              <section aria-label="Results" className={`min-w-0 flex-1 bg-surface/40 ${pane === "results" ? "block" : "hidden"} ${results ? "xl:block" : "xl:hidden"}`}>
                <Workbench sid={sid} view={view} state={state} tab={tab} setTab={setTab} focus={focus} open={open}
                  onRun={() => start("fast")} busy={busy} onMined={() => mutate()}
                  settling={{ runs: threads.get(sid).filter((m): m is Extract<Msg, { kind: "run" }> => m.kind === "run" && m.mode === "action"), busy, onSettle: settle }} />
              </section>
            </>
          ) : (
            <div className="grid flex-1 place-items-center p-8 text-sm text-meta">
              {listError ? <p className="text-bad">Cannot reach the API at {API}. Start it with make api.</p> : <p>Loading samples…</p>}
            </div>
          )}
        </div>
      </main>
      <Upload open={uploading} onClose={() => setUploading(false)} onUploaded={uploaded} onPlan={plan}
        onExample={() => { setUploading(false); select("s0031"); }} />
      <RealOrGan open={showcase} onClose={() => setShowcase(false)} />
    </div>
  );
}
