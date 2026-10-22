import type { View } from "@/lib/api";
import Value from "@/components/Value";

const STATUS: Record<string, [string, string]> = {
  confirmed: ["upheld by re-run", "bg-bad-bg text-bad"],
  "not confirmed": ["refuted by re-run", "bg-ok-bg text-ok"],
  failed: ["re-run failed, not settled", "bg-warn-bg text-warn"],
  open: ["open, no re-run requested", "bg-warn-bg text-warn"],
  discarded: ["discarded, no evidence cited", "bg-surface-warm text-meta"],
  number_guard: ["number guard", "bg-surface-warm text-fg-2"],
};

export const Chip = ({ id, onOpen }: { id: string; onOpen?: (id: string) => void }) =>
  onOpen ? <button onClick={() => onOpen(id)} className="chip hover:text-accent" title="Show in the results">{id}</button> : <span className="chip">{id}</span>;

export default function CriticLog({ view, onOpen }: { view: View; onOpen?: (id: string) => void }) {
  const a = view.agents;
  if (!a) {
    return (
      <section className="max-w-[70ch] text-sm text-muted">
        <h2 className="font-display text-xl font-medium text-fg">Critic review</h2>
        <p className="mt-1">
          The generator and critic have not run for this sample. Run the critic to add a visual inspection of every fit and up to three
          rounds in which a critic (gpt-oss, separate prompt, evidence only) objects with cited evidence and the tools settle each objection.
        </p>
      </section>
    );
  }
  const m = a.model;
  const tokens = (a.llm?.prompt_tokens ?? 0) + (a.llm?.completion_tokens ?? 0);
  return (
    <section aria-labelledby="critic-h" className="grid gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="critic-h" className="font-display text-xl font-medium">Critic review</h2>
        <span className="text-sm text-meta tabular-nums">{a.rounds} round{a.rounds === 1 ? "" : "s"}, {a.llm?.llm_calls ?? 0} LLM calls, {tokens.toLocaleString()} tokens, {Math.round(a.wall_s / 60)} min</span>
      </div>
      {a.stale ? <p className="rounded-md bg-warn-bg p-3 text-sm text-fg-2">The checks have changed since this review was written. Run the critic again to refresh it.</p> : null}
      {a.error ? <p className="rounded-md bg-warn-bg p-3 text-sm text-fg-2">The LLM endpoint failed during this run ({a.error}). Below is what the agents finished.</p> : null}
      {m ? (
        <div className="rounded-md bg-surface p-4 shadow-ring">
          <div className="eyebrow">Analyst&apos;s model</div>
          <div className="mt-1 font-display text-lg font-medium">{m.phase ?? "No candidate fits"}</div>
          <p className="mt-1 text-sm text-fg-2">{m.summary}</p>
          <ol className="mt-3 grid list-decimal gap-1.5 pl-5 text-sm text-fg-2">
            {m.claims.map((c, i) => (
              <li key={i}>{c.statement} <span className="inline-flex flex-wrap gap-1 align-middle">{c.evidence.map((e) => <Chip key={e} id={e} onOpen={onOpen} />)}</span></li>
            ))}
          </ol>
        </div>
      ) : null}
      <div>
        <div className="eyebrow">Objections</div>
        {a.log.length === 0 ? <p className="mt-1 text-sm text-fg-2">The critic raised no objections.</p> : (
          <ol className="mt-1 divide-y divide-line">
            {a.log.map((e) => {
              const [label, cls] = STATUS[e.status] ?? [e.status, "bg-surface-warm text-fg-2"];
              const result = e.result_id ? view.evidence[e.result_id] : undefined;
              return (
                <li key={e.id} className="py-3">
                  <div className="flex flex-wrap items-center gap-1.5 text-xs">
                    <span className="font-mono text-meta">{e.id}</span>
                    <span className={`rounded-full px-2 py-0.5 font-semibold ${cls}`}>{label}</span>
                    {e.cited.map((c) => <Chip key={c} id={c} onOpen={onOpen} />)}
                  </div>
                  <p className="mt-1.5 text-sm text-fg">{e.objection}</p>
                  <p className="mt-1 text-sm text-muted">
                    {e.action ? <><span className="font-mono text-xs">{e.action}</span>{e.args && Object.keys(e.args).length ? ` (${Object.entries(e.args).map(([k, v]) => `${k}=${v}`).join(", ")})` : ""}: </> : null}
                    {e.finding}
                  </p>
                  {result ? (
                    <details className="mt-1 text-xs">
                      <summary className="cursor-pointer text-accent">Re-run output ({e.result_id})</summary>
                      <div className="mt-1 rounded-sm bg-surface p-2 shadow-ring"><Value v={result} /></div>
                    </details>
                  ) : null}
                </li>
              );
            })}
          </ol>
        )}
      </div>
      {a.unsupported_numbers?.length ? (
        <p className="text-sm text-bad">Numbers in the report prose that are not in the evidence: {a.unsupported_numbers.join(", ")}</p>
      ) : null}
    </section>
  );
}
