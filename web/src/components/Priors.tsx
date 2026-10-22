"use client";
import { useState } from "react";
import { BookOpen } from "@phosphor-icons/react";
import { post, type Prior } from "@/lib/api";
import { fmt } from "@/components/Value";

const value = (p: Prior) =>
  (Array.isArray(p.value) ? p.value.map(fmt).join(" to ") : fmt(p.value)) + (p.uncertainty ? ` ± ${fmt(p.uncertainty)}` : "") + (p.unit ? ` ${p.unit}` : "");

export default function Priors({ sid, priors, onMined }: { sid: string; priors: Prior[]; onMined: () => void }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string>();
  const search = async () => {
    setBusy(true);
    setNote(undefined);
    try {
      const d = await post<{ papers: number; priors: Prior[]; errors?: string[] }>(`/api/samples/${sid}/priors`);
      setNote(`${d.papers} papers, ${d.priors.length} priors${d.errors?.length ? `; incomplete: ${d.errors.join(", ")}` : ""}`);
      onMined();
    } catch (e) {
      setNote((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section aria-labelledby="priors-h">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="priors-h" className="font-display text-xl font-medium">Literature priors</h2>
        <button onClick={search} disabled={busy} className="btn btn-quiet"><BookOpen size={16} weight="bold" aria-hidden />
          {busy ? "Searching OpenAlex, Crossref, arXiv…" : priors.length ? "Search again" : "Search open literature"}
        </button>
      </div>
      <p className="mt-1 max-w-[70ch] text-sm text-muted">
        Values reported for other samples of this material, read from abstracts with the sentence they come from. Context for the
        critic and the report; they never constrain this sample&apos;s fits.
      </p>
      {note ? <p role="status" className="mt-2 text-sm text-fg-2">{note}</p> : null}
      {priors.length ? (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs text-meta">
                <th className="px-2 py-1 font-medium">quantity</th>
                <th className="px-2 py-1 font-medium">value</th>
                <th className="px-2 py-1 font-medium">source</th>
                <th className="px-2 py-1 font-medium">sentence</th>
              </tr>
            </thead>
            <tbody>
              {priors.map((p, i) => (
                <tr key={i} className="border-b border-line-faint align-top">
                  <td className="px-2 py-1 whitespace-nowrap">{p.quantity.replace("_", " ")} {p.pair ?? p.element ?? ""}</td>
                  <td className="px-2 py-1 whitespace-nowrap tabular-nums">{value(p)}</td>
                  <td className="px-2 py-1 whitespace-nowrap">
                    <a href={`https://doi.org/${p.doi}`} target="_blank" rel="noreferrer" className="text-accent hover:underline">doi:{p.doi}</a>
                    <span className="text-meta">, {p.year}, {p.source}</span>
                  </td>
                  <td className="min-w-[24ch] px-2 py-1 text-fg-2" title={p.title}>{p.snippet}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !note ? <p className="mt-3 text-sm text-meta">No priors cached for this material yet. The search takes about a minute.</p> : null}
    </section>
  );
}
