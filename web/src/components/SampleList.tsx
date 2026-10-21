"use client";
import { useEffect, useState } from "react";
import type { SampleRow } from "@/lib/api";

const SPLITS = ["test", "faults", "val", "train", "all"];

export default function SampleList({ samples, selected, onSelect }: { samples: SampleRow[]; selected?: string; onSelect: (id: string) => void }) {
  const [split, setSplit] = useState("test");
  const [q, setQ] = useState("");
  useEffect(() => {  // show the selected sample's split, e.g. after opening /console#s0031
    const s = samples.find((x) => x.id === selected);
    if (s?.split) setSplit((cur) => (cur === "all" || cur === s.split ? cur : s.split!));
  }, [selected]); // not on list refreshes, which would undo a filter the user picked
  const shown = samples.filter((s) => (split === "all" || s.split === split) && `${s.id} ${s.composition}`.toLowerCase().includes(q.toLowerCase()));
  return (
    <nav aria-label="Samples" className="flex min-h-0 flex-1 flex-col gap-2">
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter: s0031, Pt3Co…" aria-label="Filter samples"
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-[#d68e2f] focus:ring-2 focus:ring-[#d68e2f]/30" />
      <div className="flex flex-wrap gap-1">
        {SPLITS.map((s) => (
          <button key={s} onClick={() => setSplit(s)} aria-pressed={split === s}
            className={`rounded px-2 py-0.5 text-xs ${split === s ? "bg-[#d68e2f] text-white" : "border border-slate-200 bg-white/70 text-slate-700"}`}>{s}</button>
        ))}
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto pr-1">
        {shown.map((s) => (
          <li key={s.id}>
            <button onClick={() => onSelect(s.id)} aria-current={s.id === selected}
              className={`mb-1 w-full rounded-lg px-2 py-1.5 text-left text-sm transition ${s.id === selected ? "bg-white shadow ring-1 ring-[#d68e2f]" : "hover:bg-white/70"}`}>
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-slate-900">{s.id}</span>
                <span className="text-xs text-slate-500" title={s.agents ? "tools and critic run" : s.analysed ? "tools run" : "not analysed yet"}>
                  {s.agents ? "● critic" : s.analysed ? "● tools" : "○"}
                </span>
              </div>
              <div className="text-xs text-slate-600">{s.composition} · {s.techniques.map((t) => t.toUpperCase()).join(" ")}</div>
            </button>
          </li>
        ))}
        {shown.length === 0 ? <li className="text-xs text-slate-500">No sample matches.</li> : null}
      </ul>
    </nav>
  );
}
