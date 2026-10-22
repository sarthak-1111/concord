import type { View } from "@/lib/api";
import Value from "@/components/Value";

const STATUS: Record<string, [string, string]> = {
  confirmed: ["upheld by re-run", "bg-red-100 text-red-800"],
  "not confirmed": ["refuted by re-run", "bg-emerald-100 text-emerald-800"],
  failed: ["re-run failed: not settled", "bg-amber-100 text-amber-900"],
  open: ["open: no re-run requested", "bg-amber-100 text-amber-900"],
  discarded: ["discarded: no evidence cited", "bg-slate-100 text-slate-600"],
  number_guard: ["number guard", "bg-violet-100 text-violet-800"],
};

const Chip = ({ id }: { id: string }) => <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-700">{id}</span>;

export default function CriticLog({ view }: { view: View }) {
  const a = view.agents;
  if (!a) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Critic log</h2>
        The generator–critic loop has not run for this sample. <b>Run full</b> adds visual inspection of every fit and up to
        three rounds in which a critic (gpt-oss, separate prompt, evidence only) objects with cited evidence and the tools settle each objection.
      </section>
    );
  }
  const m = a.model;
  const tokens = (a.llm?.prompt_tokens ?? 0) + (a.llm?.completion_tokens ?? 0);
  return (
    <section aria-labelledby="critic-h" className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-baseline gap-3">
        <h2 id="critic-h" className="text-lg font-semibold text-slate-900">Critic log</h2>
        <span className="text-sm text-slate-600">{a.rounds} round(s) · {a.llm?.llm_calls ?? 0} LLM calls · {tokens} tokens · {a.wall_s} s</span>
      </div>
      {a.stale ? <p className="mt-1 text-sm text-amber-800">The checks have changed since this log was written; run the full analysis again to refresh it.</p> : null}
      {a.error ? <p className="mt-1 text-sm text-amber-800">The LLM endpoint failed during this run ({a.error}); below is what the agents finished.</p> : null}
      {m ? (
        <div className="mt-3 rounded-lg bg-slate-50 p-3">
          <div className="text-sm"><span className="text-slate-500">Generator&apos;s model:</span> <b>{m.phase ?? "none: no candidate fits"}</b></div>
          <p className="mt-1 text-sm text-slate-800">{m.summary}</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-800">
            {m.claims.map((c, i) => (
              <li key={i}>{c.statement} <span className="inline-flex flex-wrap gap-1 align-middle">{c.evidence.map((e) => <Chip key={e} id={e} />)}</span></li>
            ))}
          </ol>
        </div>
      ) : null}
      {a.log.length === 0 ? <p className="mt-3 text-sm text-slate-700">The critic raised no objections.</p> : (
        <ol className="mt-3 space-y-2">
          {a.log.map((e) => {
            const [label, cls] = STATUS[e.status] ?? [e.status, "bg-slate-100 text-slate-700"];
            const result = e.result_id ? view.evidence[e.result_id] : undefined;
            return (
              <li key={e.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-mono text-slate-500">{e.id}</span>
                  <span className={`rounded-full px-2 py-0.5 font-semibold ${cls}`}>{label}</span>
                  {e.cited.map((c) => <Chip key={c} id={c} />)}
                </div>
                <p className="mt-1 text-sm text-slate-900">{e.objection}</p>
                <p className="mt-1 text-sm text-slate-600">
                  {e.action ? <><span className="font-mono">{e.action}</span>{e.args && Object.keys(e.args).length ? ` (${Object.entries(e.args).map(([k, v]) => `${k}=${v}`).join(", ")})` : ""} → </> : null}
                  {e.finding}
                </p>
                {result ? (
                  <details className="mt-1 text-xs">
                    <summary className="cursor-pointer text-[#d6512f]">re-run output ({e.result_id})</summary>
                    <div className="mt-1 rounded bg-slate-50 p-2"><Value v={result} /></div>
                  </details>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
      {a.unsupported_numbers?.length ? (
        <p className="mt-3 text-sm text-violet-800">Numbers in the report prose that are not in the evidence: {a.unsupported_numbers.join(", ")}</p>
      ) : null}
    </section>
  );
}
