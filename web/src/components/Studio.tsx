"use client";
import { useEffect, useRef } from "react";
import { X } from "@phosphor-icons/react";
import { fmt } from "@/components/Value";

export type Param = {
  name: string; label: string; kind: "float" | "int" | "bool" | "choice"; value: unknown; default?: unknown;
  min?: number; max?: number; step?: number; choices?: string[]; unit?: string; help?: string;
};

/** A full-screen workspace over the app: parameters on the left, live results on the right. */
export function Shell({ open, onClose, eyebrow, title, aside, children }: {
  open: boolean; onClose: () => void; eyebrow: React.ReactNode; title: string; aside: React.ReactNode; children: React.ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (open && d && !d.open) d.showModal();
    if (!open && d?.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} aria-label={title}
      className="m-0 h-[100dvh] max-h-none w-screen max-w-none overscroll-contain bg-bg p-0 text-fg backdrop:bg-black/40">
      {open ? (
        <div className="flex h-full flex-col">
          <header className="flex shrink-0 items-center gap-3 border-b border-line px-4 py-3 sm:px-6">
            <div className="min-w-0 flex-1">
              <div className="eyebrow inline-flex items-center gap-1">{eyebrow}</div>
              <h2 className="truncate font-display text-xl font-medium">{title}</h2>
            </div>
            <button onClick={onClose} className="btn btn-ghost px-2" aria-label="Close"><X size={20} weight="bold" /></button>
          </header>
          <div className="grid min-h-0 flex-1 grid-cols-1 overflow-y-auto lg:grid-cols-[320px_minmax(0,1fr)] lg:overflow-hidden">
            <aside className="border-b border-line p-4 lg:overflow-y-auto lg:border-b-0 lg:border-r sm:p-6">{aside}</aside>
            <main className="@container min-w-0 p-4 lg:overflow-y-auto sm:p-6">{children}</main>
          </div>
        </div>
      ) : null}
    </dialog>
  );
}

/** One parameter: slider plus number for numbers, a switch for booleans, a select for choices. */
export function Field({ p, value, onChange }: { p: Param; value: unknown; onChange: (v: unknown) => void }) {
  const id = `f-${p.name}`;
  const changed = p.default !== undefined && JSON.stringify(value) !== JSON.stringify(p.value);
  const head = (
    <span className="flex items-baseline justify-between gap-2">
      <label htmlFor={id} className="text-sm font-medium text-fg-2">{p.label}{changed ? <span className="ml-1.5 text-xs text-accent">changed</span> : null}</label>
      {p.kind === "float" || p.kind === "int" ? <span className="text-xs tabular-nums text-muted">{fmt(value as number)}{p.unit ? ` ${p.unit}` : ""}</span> : null}
    </span>
  );
  return (
    <div className="grid gap-1.5">
      {p.kind === "bool" ? (
        <div className="flex items-center justify-between gap-3">
          <label htmlFor={id} className="text-sm font-medium text-fg-2">{p.label}</label>
          <button id={id} type="button" role="switch" aria-checked={!!value} onClick={() => onChange(!value)}
            className={`relative h-6 w-10 shrink-0 rounded-full transition-colors duration-200 ${value ? "bg-accent" : "bg-surface-warm shadow-ring"}`}>
            <span className={`absolute left-0 top-0.5 size-5 rounded-full bg-surface shadow-raised transition-transform duration-200 ${value ? "translate-x-[18px]" : "translate-x-0.5"}`} />
          </button>
        </div>
      ) : p.kind === "choice" ? (
        <>{head}<select id={id} value={String(value)} onChange={(e) => onChange(e.target.value)} className="field py-1.5">
          {(p.choices ?? []).map((c) => <option key={c} value={c}>{c}</option>)}
        </select></>
      ) : (
        <>{head}
          <div className="flex items-center gap-2">
            <input id={id} type="range" min={p.min} max={p.max} step={p.step ?? (p.kind === "int" ? 1 : "any")} value={Number(value)}
              onChange={(e) => onChange(p.kind === "int" ? Math.round(+e.target.value) : +e.target.value)} className="min-w-0 flex-1 accent-[var(--accent)]" />
            <input type="number" aria-label={`${p.label} value`} min={p.min} max={p.max} step={p.step ?? "any"} value={Number(value)}
              onChange={(e) => e.target.value !== "" && onChange(+e.target.value)} className="field w-20 px-2 py-1 text-right text-[13px] tabular-nums" />
          </div>
        </>
      )}
      {p.help ? <p className="text-xs text-meta">{p.help}</p> : null}
    </div>
  );
}
