"use client";
import { useState } from "react";
import type { Check, Status } from "@/lib/api";
import Value from "@/components/Value";

const PILL: Record<Status, string> = {
  pass: "bg-emerald-100 text-emerald-800 border-emerald-300",
  warn: "bg-amber-100 text-amber-900 border-amber-300",
  fail: "bg-red-100 text-red-800 border-red-300",
  skip: "bg-slate-100 text-slate-500 border-slate-200",
};
const EDGE: Record<Status, string> = { pass: "border-l-emerald-500", warn: "border-l-amber-500", fail: "border-l-red-600", skip: "border-l-slate-300" };

export function StatusPill({ status }: { status: Status }) {
  return <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold uppercase ${PILL[status] ?? PILL.skip}`}>{status}</span>;
}

function CheckCard({ c }: { c: Check }) {
  const [open, setOpen] = useState(c.status === "warn" || c.status === "fail");
  const hasNumbers = !!(c.values && Object.keys(c.values).length);
  return (
    <div className={`rounded-lg border border-slate-200 border-l-4 bg-white p-3 shadow-sm ${EDGE[c.status] ?? EDGE.skip}`}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900"><span className="text-slate-500">{c.id}</span> {c.name}</h3>
        <StatusPill status={c.status} />
      </div>
      <p className="mt-1 text-sm text-slate-700">{c.explanation}</p>
      {hasNumbers ? (
        <>
          <button onClick={() => setOpen((x) => !x)} className="mt-2 text-xs font-medium text-[#d6512f] hover:underline" aria-expanded={open}>
            {open ? "Hide numbers" : "Show numbers"}
          </button>
          {open ? (
            <div className="mt-2 grid gap-2 rounded bg-slate-50 p-2">
              <Value v={c.values} />
              {c.tolerance && Object.keys(c.tolerance).length ? (
                <div><div className="text-xs font-medium text-slate-500">tolerance (config.yaml)</div><Value v={c.tolerance} /></div>
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default function CheckPanel({ checks }: { checks: Check[] }) {
  const count = (s: Status) => checks.filter((c) => c.status === s).length;
  return (
    <section aria-labelledby="checks-h">
      <div className="mb-2 flex flex-wrap items-baseline gap-3">
        <h2 id="checks-h" className="text-lg font-semibold text-slate-900">Cross-technique checks</h2>
        <span className="text-sm text-slate-600">{count("pass")} pass · {count("warn")} warn · {count("fail")} fail · {count("skip")} skipped</span>
      </div>
      <div className="grid items-start gap-3 md:grid-cols-2 2xl:grid-cols-3">
        {checks.map((c) => <CheckCard key={c.id} c={c} />)}
      </div>
    </section>
  );
}
