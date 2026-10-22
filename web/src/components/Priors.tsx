"use client";
import { useState } from "react";
import { API, type Prior } from "@/lib/api";
import { fmt } from "@/components/Value";

const value = (p: Prior) =>
  (Array.isArray(p.value) ? p.value.map(fmt).join("–") : fmt(p.value)) + (p.uncertainty ? ` ± ${fmt(p.uncertainty)}` : "") + (p.unit ? ` ${p.unit}` : "");

export default function Priors({ sid, priors, onMined }: { sid: string; priors: Prior[]; onMined: () => void }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string>();
  const search = async () => {
    setBusy(true);
    setNote(undefined);
    try {
      const r = await fetch(`${API}/api/samples/${sid}/priors`, { method: "POST" });
      const d = await r.json();
      setNote(d.error ?? `${d.papers} papers, ${d.priors.length} priors${d.errors?.length ? `; incomplete: ${d.errors.join(", ")}` : ""}`);
      onMined();
    } finally {
      setBusy(false);
    }
  };
  return (
    <section aria-labelledby="priors-h" className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="priors-h" className="text-lg font-semibold text-slate-900">Literature priors</h2>
        <button onClick={search} disabled={busy} className="text-sm font-medium text-[#d6512f] hover:underline disabled:opacity-50">
          {busy ? "Searching OpenAlex, Crossref, arXiv…" : priors.length ? "Search again" : "Search open literature"}
        </button>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Values reported for other samples of this material, read from abstracts with the sentence they come from. Context for the
        critic and the report; they never constrain this sample&apos;s fits.
      </p>
      {note ? <p className="mt-1 text-sm text-slate-700">{note}</p> : null}
      {priors.length ? (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs text-slate-500">
                <th className="px-2 py-1 font-medium">quantity</th>
                <th className="px-2 py-1 font-medium">value</th>
                <th className="px-2 py-1 font-medium">source</th>
                <th className="px-2 py-1 font-medium">sentence</th>
              </tr>
            </thead>
            <tbody>
              {priors.map((p, i) => (
                <tr key={i} className="border-b border-slate-100 align-top">
                  <td className="px-2 py-1 whitespace-nowrap">{p.quantity.replace("_", " ")} {p.pair ?? p.element ?? ""}</td>
                  <td className="px-2 py-1 whitespace-nowrap tabular-nums">{value(p)}</td>
                  <td className="px-2 py-1 whitespace-nowrap">
                    <a href={`https://doi.org/${p.doi}`} target="_blank" rel="noreferrer" className="text-[#d6512f] hover:underline">doi:{p.doi}</a>
                    <span className="text-slate-500"> · {p.year} · {p.source}</span>
                  </td>
                  <td className="px-2 py-1 text-slate-700" title={p.title}>{p.snippet}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !note ? <p className="mt-2 text-sm text-slate-500">No priors cached for this material yet.</p> : null}
    </section>
  );
}
