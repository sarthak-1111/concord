"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import useSWR from "swr";
import { Atom, MagnifyingGlass, Trash, X } from "@phosphor-icons/react";
import { fetcher } from "@/lib/api";
import { NAMES, SYMBOLS, formula, parseFormula, place, type Block } from "@/lib/elements";

const TINT: Record<Block, string> = {  // a light tint per block, so the table reads at a glance; identity is also in the legend
  s: "color-mix(in oklab, var(--series-1) 14%, var(--surface))", p: "color-mix(in oklab, var(--series-3) 14%, var(--surface))",
  d: "color-mix(in oklab, var(--series-4) 16%, var(--surface))", f: "color-mix(in oklab, var(--series-2) 13%, var(--surface))",
};
const BLOCK: Record<Block, string> = { s: "s-block", p: "p-block", d: "d-block (transition metals)", f: "f-block (lanthanides, actinides)" };
const MAX = 6;  // the API accepts formulas of up to six elements
const CELLS = SYMBOLS.map((s, i) => ({ s, z: i + 1, name: NAMES[i], ...place(i + 1) }));

/** Pick a composition from the periodic table: click elements, set their amounts, see which library phases apply. */
export function PeriodicTable({ open, value, onClose, onPick }: { open: boolean; value: string; onClose: () => void; onPick: (formula: string) => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [parts, setParts] = useState<[string, number][]>([]);
  const [query, setQuery] = useState("");
  const { data } = useSWR<{ phases: Record<string, string[]> }>(open ? "/api/elements" : null, fetcher, { revalidateOnFocus: false });
  const lib = data?.phases ?? {};

  useEffect(() => {
    const d = ref.current;
    if (open && d && !d.open) { setParts(parseFormula(value)); setQuery(""); d.showModal(); }
    if (!open && d?.open) d.close();
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const q = query.trim().toLowerCase();
  const hit = (c: (typeof CELLS)[number]) => !q || c.s.toLowerCase() === q || c.name.toLowerCase().includes(q) || String(c.z) === q;
  const matches = CELLS.filter(hit);
  const chosen = new Set(parts.map(([s]) => s));
  const toggle = (s: string) => setParts((p) => p.some(([x]) => x === s) ? p.filter(([x]) => x !== s) : p.length < MAX ? [...p, [s, 1]] : p);
  const candidates = useMemo(() => [...new Set(parts.flatMap(([s]) => lib[s] ?? []))], [parts, lib]);
  const f = formula(parts);

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="pt-h"
      className="m-auto max-h-[calc(100dvh-24px)] w-[min(1120px,calc(100vw-24px))] overscroll-contain rounded-lg bg-surface p-0 text-fg shadow-raised backdrop:bg-black/40">
      {open ? (
        <div className="grid gap-4 p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <span className="eyebrow inline-flex items-center gap-1"><Atom size={13} weight="bold" aria-hidden />Composition</span>
              <h2 id="pt-h" className="mt-1 font-display text-2xl font-medium">Pick the elements of your sample</h2>
              <p className="mt-1 text-sm text-muted">Click elements, then set how many of each. A dot marks elements with candidate structures in the library.</p>
            </div>
            <button type="button" onClick={onClose} className="btn btn-ghost -mr-2 -mt-1 px-2" aria-label="Close"><X size={18} weight="bold" /></button>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <label className="relative w-full sm:w-64">
              <span className="sr-only">Find an element</span>
              <MagnifyingGlass size={16} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-meta" aria-hidden />
              <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find: Pt, platinum, 78…" autoComplete="off" spellCheck={false}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (matches.length === 1) { toggle(matches[0].s); setQuery(""); } } }}
                className="field py-1.5 pl-8" />
            </label>
            <ul className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted" aria-label="Legend">
              {(Object.keys(BLOCK) as Block[]).map((b) => (
                <li key={b} className="inline-flex items-center gap-1.5"><span className="size-3 rounded-[3px] shadow-ring" style={{ background: TINT[b] }} aria-hidden />{BLOCK[b]}</li>
              ))}
              <li className="inline-flex items-center gap-1.5"><span className="size-1.5 rounded-full bg-accent" aria-hidden />in the library</li>
            </ul>
          </div>

          <div className="overflow-x-auto pb-1">
            <div role="group" aria-label="Periodic table" className="grid min-w-[760px] grid-cols-[repeat(18,minmax(0,1fr))] gap-[3px]" style={{ gridTemplateRows: "repeat(7,auto) 10px repeat(2,auto)" }}>
              {CELLS.map((c) => {
                const on = chosen.has(c.s), phases = lib[c.s];
                return (
                  <button key={c.s} type="button" onClick={() => toggle(c.s)} aria-pressed={on}
                    title={`${c.name}${phases ? `. In the library: ${phases.join(", ")}` : ""}`}
                    aria-label={`${c.name}, ${c.s}, ${c.z}${phases ? `, ${phases.length} library phase${phases.length === 1 ? "" : "s"}` : ""}`}
                    style={{ gridRow: c.row, gridColumn: c.col, background: on ? undefined : TINT[c.block] }}
                    className={`relative grid aspect-square min-w-0 place-content-center rounded-[4px] text-center transition-[opacity,transform,box-shadow] duration-150 active:scale-95
                      ${on ? "bg-accent text-accent-on shadow-raised" : "text-fg hover:shadow-ring"} ${hit(c) ? "" : "opacity-25"}`}>
                    <span className={`absolute left-1 top-0.5 text-[9px] tabular-nums ${on ? "text-accent-on/80" : "text-meta"}`}>{c.z}</span>
                    {phases ? <span className={`absolute right-1 top-1 size-1.5 rounded-full ${on ? "bg-accent-on" : "bg-accent"}`} aria-hidden /> : null}
                    <span className="text-[15px] font-semibold leading-none">{c.s}</span>
                    <span className={`mt-0.5 hidden truncate px-0.5 text-[8.5px] leading-none lg:block ${on ? "text-accent-on/80" : "text-muted"}`}>{c.name}</span>
                  </button>
                );
              })}
              <span style={{ gridRow: 6, gridColumn: 3 }} className="grid place-content-center text-[10px] text-meta" aria-hidden>57-71</span>
              <span style={{ gridRow: 7, gridColumn: 3 }} className="grid place-content-center text-[10px] text-meta" aria-hidden>89-103</span>
            </div>
          </div>

          <div className="grid gap-3 border-t border-line pt-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
            <div className="grid min-w-0 gap-2">
              {parts.length ? (
                <ul className="flex flex-wrap gap-2" aria-label="Selected elements">
                  {parts.map(([s, n], i) => (
                    <li key={s} className="inline-flex items-center gap-1 rounded-md bg-bg py-1 pl-2.5 pr-1 shadow-ring">
                      <label htmlFor={`amt-${s}`} className="text-sm font-semibold">{s}</label>
                      <input id={`amt-${s}`} type="number" min={0.01} step="any" value={n} aria-label={`Amount of ${NAMES[SYMBOLS.indexOf(s)]}`}
                        onChange={(e) => { const v = +e.target.value; if (v > 0) setParts((p) => p.map((x, j) => (j === i ? [s, v] : x))); }}
                        className="field w-16 px-1.5 py-0.5 text-right text-[13px] tabular-nums" />
                      <button type="button" onClick={() => toggle(s)} className="btn btn-ghost px-1" aria-label={`Remove ${s}`}><Trash size={14} /></button>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-meta">No elements picked yet.</p>}
              {parts.length >= MAX ? <p className="text-xs text-warn">Up to {MAX} elements.</p> : null}
              {parts.length ? (
                <p className="text-xs text-muted">
                  {candidates.length ? <>Candidate structures Concord will compare: <span className="text-fg-2">{candidates.join(", ")}</span>.</>
                    : <>No library structure contains these elements yet, so the fits will have no candidates.</>}
                </p>
              ) : null}
            </div>
            <div className="flex items-center justify-end gap-2">
              <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
              <button type="button" disabled={!f} onClick={() => { onPick(f); onClose(); }} className="btn btn-primary">
                Use <span translate="no" className="font-semibold">{f || "formula"}</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </dialog>
  );
}

/** A composition text field with the periodic table one click away (the table is portalled out of any form or label). */
export default function CompositionField({ value, onChange, name, onBlur, onPick }: {
  value: string; onChange: (v: string) => void; name?: string; onBlur?: () => void; onPick?: (formula: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <span className="flex gap-1.5">
      <input name={name} required value={value} onChange={(e) => onChange(e.target.value)} onBlur={onBlur}
        placeholder="Pt3Co…" autoComplete="off" spellCheck={false} className="field min-w-0 flex-1 font-normal" />
      <button type="button" onClick={() => setOpen(true)} className="btn btn-quiet shrink-0 px-2.5" title="Pick from the periodic table" aria-label="Pick from the periodic table">
        <Atom size={18} weight="bold" aria-hidden /><span className="hidden sm:inline">Periodic table</span>
      </button>
      {open ? createPortal(<PeriodicTable open value={value} onClose={() => setOpen(false)} onPick={(f) => { onChange(f); onPick?.(f); }} />, document.body) : null}
    </span>
  );
}
