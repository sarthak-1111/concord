"use client";
import { useEffect, useState } from "react";
import useSWR, { mutate as globalMutate } from "swr";
import { API, fetcher, type SampleRow, type View } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";
import SampleList from "@/components/SampleList";
import CheckPanel from "@/components/CheckPanel";
import TechniqueTabs from "@/components/TechniqueTabs";
import VirtualXafs from "@/components/VirtualXafs";
import CriticLog from "@/components/CriticLog";
import EventCard from "@/components/EventCard";
import Priors from "@/components/Priors";
import Upload from "@/components/Upload";

const BUTTON = "rounded-lg px-3 py-2 text-sm font-medium shadow-sm transition disabled:cursor-not-allowed disabled:opacity-50";

export default function Workbench() {
  const { data: samples, error: listError, mutate: refreshSamples } = useSWR<SampleRow[]>("/api/samples", fetcher);
  const [sid, setSid] = useState<string>();
  const { data: view, error, isLoading, mutate } = useSWR<View>(sid ? `/api/samples/${sid}` : null, fetcher, { shouldRetryOnError: false, revalidateOnFocus: false });
  const [run, setRun] = useState<{ id: string; sample: string; mode: string }>();
  const { events } = useRunStream(run?.id);
  const failed = events.some((e) => e.type === "error");
  const running = !!run && !failed && !events.some((e) => e.type === "done");

  useEffect(() => {  // first visit: the sample named in the URL hash, else the first test sample
    if (sid || !samples?.length) return;
    const h = window.location.hash.slice(1);
    setSid(samples.some((s) => s.id === h) ? h : (samples.find((s) => s.split === "test") ?? samples[0]).id);
  }, [samples, sid]);

  useEffect(() => {  // links like /console#s0031 also work on an open page
    const onHash = () => window.location.hash.length > 1 && setSid(window.location.hash.slice(1));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    const r = events.find((e) => e.type === "result");
    if (r?.payload) {
      globalMutate(`/api/samples/${r.payload.sample_id}`, r.payload, { revalidate: false });
      refreshSamples();
    }
  }, [events, refreshSamples]);

  const select = (id: string) => {
    setSid(id);
    history.replaceState(null, "", `#${id}`);
  };
  const start = async (mode: "fast" | "full", id = sid) => {
    const r = await fetch(`${API}/api/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sample: id, mode }) });
    const d = await r.json();
    if (d.run_id && id) setRun({ id: d.run_id, sample: id, mode });
  };
  const uploaded = async (id: string) => {
    await refreshSamples();
    select(id);
    start("fast", id);
  };
  const composition = view?.composition ?? samples?.find((s) => s.id === sid)?.composition;

  return (
    <main className="min-h-screen md:pl-64">
      <aside className="flex max-h-[45vh] flex-col gap-3 border-b border-slate-200 bg-[#f9f2e4] p-3 md:fixed md:left-0 md:top-0 md:h-screen md:max-h-none md:w-64 md:border-b-0 md:border-r">
        <div>
          <div className="text-xl font-semibold text-slate-900">Concord</div>
          <p className="text-xs text-slate-600">XRD, PDF and XAFS of one sample, cross-checked</p>
        </div>
        <Upload onUploaded={uploaded} />
        {samples ? <SampleList samples={samples} selected={sid} onSelect={select} />
          : <p className="text-sm text-slate-600">{listError ? "Cannot reach the API. Start it with make api." : "Loading samples…"}</p>}
      </aside>

      <div className="mx-auto grid max-w-[1600px] gap-5 p-4 md:p-6">
        {sid ? (
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">{sid} <span className="font-normal text-slate-500">· {composition}</span></h1>
              {view ? (
                <p className="mt-1 text-sm text-slate-700">
                  Phase: <b>{view.phase ?? "none (no candidate structure fits)"}</b> · {view.techniques.map((t) => t.toUpperCase()).join(" + ")} · tools {view.timings_s.total} s
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <button disabled={running} onClick={() => start("fast")} className={`${BUTTON} bg-[#d6512f] text-white hover:bg-[#c24728]`}>Run fast · tools only</button>
              <button disabled={running} onClick={() => start("full")} className={`${BUTTON} border border-[#d6512f] bg-white text-[#d6512f] hover:bg-orange-50`}>Run full · with critic</button>
              {view ? (
                <>
                  <a href={`${API}/api/samples/${sid}/export?format=md`} className={`${BUTTON} border border-slate-300 bg-white text-slate-700 hover:bg-slate-50`}>Report .md</a>
                  <a href={`${API}/api/samples/${sid}/export?format=json`} className={`${BUTTON} border border-slate-300 bg-white text-slate-700 hover:bg-slate-50`}>Data .json</a>
                </>
              ) : null}
            </div>
          </header>
        ) : null}

        {run ? (
          <section aria-live="polite" className="rounded-xl border border-slate-200 bg-white/80 p-3">
            <div className="flex items-center gap-2 text-sm text-slate-700">
              {running ? <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-[#d6512f] border-t-transparent" /> : null}
              {run.mode} run of {run.sample}: {running ? "running…" : failed ? "failed" : "done"}
            </div>
            <div className="mt-2 grid max-h-80 gap-2 overflow-y-auto">
              {events.map((e, i) => e.type === "event" ? <EventCard key={i} event={e} />
                : e.type === "status" || e.type === "error"
                  ? <p key={i} className={`text-sm ${e.type === "error" ? "text-red-700" : "text-slate-600"}`}>{String(e.payload)}</p> : null)}
            </div>
          </section>
        ) : null}

        {!sid ? null : (error as { status?: number })?.status === 404 ? (
          <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
            Not analysed yet. <b>Run fast</b> takes about half a minute and needs no LLM; <b>Run full</b> adds the visual inspection and the critic.
          </p>
        ) : error ? (
          <p className="text-sm text-red-700">Could not load {sid}: {error.message}</p>
        ) : isLoading || !view ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : (
          <>
            {Object.keys(view.errors).length || view.assumed.length ? (
              <div className="grid gap-1 text-sm">
                {Object.entries(view.errors).map(([k, v]) => <p key={k} className="rounded bg-red-50 p-2 text-red-800">{k} failed: {v}</p>)}
                {view.assumed.map((a) => <p key={a} className="rounded bg-amber-50 p-2 text-amber-900">Assumed {a} (not in the file headers).</p>)}
              </div>
            ) : null}
            <CheckPanel checks={view.checks} />
            <div className="grid items-start gap-5 2xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
              <TechniqueTabs key={view.sample_id} view={view} />
              <VirtualXafs v={view.virtual_xafs} plot={view.plots.virtual_xafs} />
            </div>
            <CriticLog view={view} />
            <Priors sid={view.sample_id} priors={view.priors} onMined={() => mutate()} />
          </>
        )}
      </div>
    </main>
  );
}
