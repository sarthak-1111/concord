"use client";
import { useEffect, useState } from "react";
import { CaretDown, CheckCircle, CircleDashed, CircleNotch, IntersectThree, MagnifyingGlass, Monitor, Moon, Plus, SealCheck, Sun } from "@phosphor-icons/react";
import type { SampleRow } from "@/lib/api";

const GROUPS: [string | null, string][] = [["test", "Test"], ["faults", "Planted faults"], ["uploaded", "Your uploads"], ["val", "Validation"], ["train", "Training"], [null, "Other"]];
const THEMES = ["system", "light", "dark"] as const;

function ThemeToggle() {
  const [theme, setTheme] = useState<(typeof THEMES)[number]>("system");
  useEffect(() => {
    try { setTheme((localStorage.getItem("concord.theme") as typeof theme) ?? "system"); } catch { /* blocked storage: system theme */ }
  }, []);
  const next = () => {
    const t = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    setTheme(t);
    if (t === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
    try { if (t === "system") localStorage.removeItem("concord.theme"); else localStorage.setItem("concord.theme", t); } catch { /* not remembered */ }
  };
  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  return (
    <button onClick={next} className="btn btn-ghost px-2" aria-label={`Theme: ${theme}. Change theme`} title={`Theme: ${theme}`}>
      <Icon size={18} weight="bold" aria-hidden />
    </button>
  );
}

export default function Rail({ samples, error, selected, running, onSelect, onNew }: {
  samples?: SampleRow[]; error?: Error; selected?: string; running?: string; onSelect: (id: string) => void; onNew: () => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<Record<string, boolean>>({ test: true, faults: true, uploaded: true });
  const sel = samples?.find((s) => s.id === selected);
  const query = q.trim().toLowerCase();
  const shown = (samples ?? []).filter((s) => `${s.id} ${s.composition} ${s.techniques.join(" ")}`.toLowerCase().includes(query));
  return (
    <nav aria-label="Samples" className="flex h-full min-h-0 flex-col gap-3 p-3">
      <div className="flex items-center justify-between px-1 pt-1">
        <div className="flex items-center gap-2">
          <IntersectThree size={24} weight="duotone" className="text-accent" aria-hidden />
          <span className="font-display text-xl font-medium tracking-tight">Concord</span>
        </div>
        <ThemeToggle />
      </div>
      <button onClick={onNew} className="btn btn-quiet justify-start"><Plus size={16} weight="bold" aria-hidden />Analyse your own data</button>
      <label className="relative block">
        <span className="sr-only">Search samples</span>
        <MagnifyingGlass size={16} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-meta" aria-hidden />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search s0031, Pt3Co…" spellCheck={false} autoComplete="off" className="field pl-8" />
      </label>
      <div className="-mx-1 min-h-0 flex-1 overflow-y-auto overscroll-contain px-1 pb-2" translate="no">
        {!samples ? (
          <div className="grid gap-1.5 px-1" aria-busy="true">
            {error ? <p className="text-sm text-bad">Cannot reach the API. Start it with <code className="chip">make api</code>.</p>
              : Array.from({ length: 8 }, (_, i) => <div key={i} className="h-8 animate-pulse rounded-sm bg-surface-warm" />)}
          </div>
        ) : null}
        {samples && shown.length === 0 ? <p className="px-2 text-sm text-meta">No sample matches.</p> : null}
        {GROUPS.map(([split, label]) => {
          const rows = shown.filter((s) => (s.split ?? null) === split);
          if (!rows.length) return null;
          const key = split ?? "other";
          const isOpen = !!query || open[key] || sel?.split === split;
          return (
            <section key={key} className="mt-2">
              <button onClick={() => setOpen((o) => ({ ...o, [key]: !isOpen }))} aria-expanded={isOpen}
                className="eyebrow flex w-full items-center justify-between rounded-sm px-2 py-1 hover:text-fg">
                <span>{label} <span className="font-normal tabular-nums">{rows.length}</span></span>
                <CaretDown size={12} weight="bold" className={`transition-transform duration-150 ${isOpen ? "" : "-rotate-90"}`} aria-hidden />
              </button>
              {isOpen ? (
                <ul className="mt-0.5 grid gap-px">
                  {rows.map((s) => {
                    const active = s.id === selected;
                    const state = running === s.id ? "running" : s.agents ? "reviewed by the critic" : s.analysed ? "analysed" : "not analysed";
                    return (
                      <li key={s.id}>
                        <button onClick={() => onSelect(s.id)} aria-current={active ? "page" : undefined}
                          className={`flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm transition-colors duration-150 ${active ? "bg-surface-warm text-fg" : "text-fg-2 hover:bg-surface-warm/60"}`}>
                          <span className="min-w-0 flex-1 truncate font-medium">{s.composition}</span>
                          <span className="font-mono text-xs text-meta">{s.id}</span>
                          <span title={state} className="text-meta">
                            {running === s.id ? <CircleNotch size={14} weight="bold" className="animate-spin text-accent" aria-hidden />
                              : s.agents ? <SealCheck size={14} weight="fill" className="text-accent" aria-hidden />
                              : s.analysed ? <CheckCircle size={14} weight="bold" aria-hidden /> : <CircleDashed size={14} weight="bold" aria-hidden />}
                            <span className="sr-only">{state}</span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              ) : null}
            </section>
          );
        })}
      </div>
      <p className="flex flex-wrap gap-x-3 gap-y-1 px-1 text-[11px] text-meta">
        <span className="inline-flex items-center gap-1"><SealCheck size={12} weight="fill" className="text-accent" aria-hidden />critic</span>
        <span className="inline-flex items-center gap-1"><CheckCircle size={12} weight="bold" aria-hidden />tools</span>
        <span className="inline-flex items-center gap-1"><CircleDashed size={12} weight="bold" aria-hidden />not run</span>
      </p>
    </nav>
  );
}
