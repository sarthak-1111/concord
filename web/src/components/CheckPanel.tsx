"use client";
import { useEffect, useRef, useState } from "react";
import { CheckCircle, MinusCircle, WarningCircle, XCircle, CaretDown } from "@phosphor-icons/react";
import type { Check, Status } from "@/lib/api";
import Value from "@/components/Value";

export const TONE: Record<Status, { fg: string; bg: string; label: string; Icon: typeof CheckCircle }> = {
  pass: { fg: "text-ok", bg: "bg-ok-bg", label: "pass", Icon: CheckCircle },
  warn: { fg: "text-warn", bg: "bg-warn-bg", label: "warn", Icon: WarningCircle },
  fail: { fg: "text-bad", bg: "bg-bad-bg", label: "fail", Icon: XCircle },
  skip: { fg: "text-meta", bg: "bg-surface-warm", label: "skipped", Icon: MinusCircle },
};

export function StatusPill({ status }: { status: Status }) {
  const t = TONE[status] ?? TONE.skip;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${t.fg} ${t.bg}`}>
      <t.Icon size={13} weight="bold" aria-hidden />{t.label}
    </span>
  );
}

/** The seven checks at a glance; a click opens one. */
export function CheckStrip({ checks, onOpen }: { checks: Check[]; onOpen: (id: string) => void }) {
  return (
    <ol className="grid grid-cols-4 gap-1.5 sm:grid-cols-7" aria-label="Cross-technique checks">
      {checks.map((c) => {
        const t = TONE[c.status] ?? TONE.skip;
        return (
          <li key={c.id}>
            <button onClick={() => onOpen(c.id)} title={`${c.id} ${c.name}: ${t.label}`}
              className={`flex w-full flex-col items-start gap-0.5 rounded-sm px-2 py-1.5 text-left transition-colors duration-150 hover:brightness-[0.97] ${t.bg}`}>
              <span className={`flex w-full items-center justify-between font-mono text-xs font-semibold ${t.fg}`}>
                {c.id}<t.Icon size={14} weight="fill" aria-hidden />
              </span>
              <span className="w-full truncate text-[11px] leading-tight text-muted">{c.name}</span>
              <span className="sr-only">{t.label}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

export type Focus = { id: string; n: number };  // n changes on every request, so the same check can be opened twice

function CheckRow({ c, focus }: { c: Check; focus?: Focus }) {
  const focused = focus?.id === c.id;
  const [open, setOpen] = useState(c.status === "warn" || c.status === "fail");
  const ref = useRef<HTMLLIElement>(null);
  useEffect(() => {
    if (!focused) return;
    setOpen(true);
    ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [focused, focus?.n]);
  const hasNumbers = !!(c.values && Object.keys(c.values).length);
  return (
    <li ref={ref} className={`scroll-mt-4 py-4 transition-colors duration-200 ${focused ? "rounded-md bg-surface px-3 shadow-ring" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-medium leading-snug text-fg"><span className="mr-1.5 font-mono text-sm text-meta">{c.id}</span>{c.name}</h3>
        <StatusPill status={c.status} />
      </div>
      <p className="mt-1 max-w-[70ch] text-sm text-fg-2">{c.explanation}</p>
      {hasNumbers ? (
        <>
          <button onClick={() => setOpen((x) => !x)} aria-expanded={open}
            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline">
            <CaretDown size={12} weight="bold" className={`transition-transform duration-150 ${open ? "" : "-rotate-90"}`} aria-hidden />
            {open ? "Hide numbers" : "Show numbers"}
          </button>
          {open ? (
            <div className="mt-2 grid gap-3 rounded-sm bg-surface p-3 shadow-ring">
              <Value v={c.values} />
              {c.tolerance && Object.keys(c.tolerance).length ? (
                <div><div className="eyebrow mb-1">Tolerance, config.yaml</div><Value v={c.tolerance} /></div>
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}
    </li>
  );
}

export default function CheckPanel({ checks, focus }: { checks: Check[]; focus?: Focus }) {
  const count = (s: Status) => checks.filter((c) => c.status === s).length;
  return (
    <section aria-labelledby="checks-h">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="checks-h" className="font-display text-xl font-medium">Cross-technique checks</h2>
        <span className="text-sm text-meta">{count("pass")} pass, {count("warn")} warn, {count("fail")} fail, {count("skip")} skipped</span>
      </div>
      <ul className="mt-1 divide-y divide-line">
        {checks.map((c) => <CheckRow key={c.id} c={c} focus={focus} />)}
      </ul>
    </section>
  );
}
