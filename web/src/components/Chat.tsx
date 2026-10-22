"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowUp, BookOpen, CaretDown, CheckCircle, CircleNotch, IntersectThree, Lightning, UploadSimple, UsersThree, WarningCircle, XCircle,
} from "@phosphor-icons/react";
import type { ChatReply, SampleRow, View } from "@/lib/api";
import type { Msg } from "@/lib/thread";
import { NUMBER, sources } from "@/lib/insight";
import { fmt } from "@/components/Value";
import { TONE } from "@/components/CheckPanel";
import { Chip } from "@/components/CriticLog";
import Generated from "@/components/Generated";

type Actions = {
  ask: (text: string) => void;
  run: (mode: "fast" | "full") => void;
  findPriors: () => void;
  open: (evidenceId: string) => void;
  upload: () => void;
};

const SUGGEST: Record<Exclude<ChatReply["suggest"], "none">, [string, typeof Lightning]> = {
  run_fast: ["Run tools and checks", Lightning], run_full: ["Run the agents", UsersThree], find_priors: ["Search the literature", BookOpen],
};
const RUN_LABEL = { fast: "Tools and checks", full: "Fitting agents, inspection and critic", priors: "Literature search", action: "Re-run" };

/** The answer with every number that matches an evidence value marked; a click opens where it came from. */
function Sourced({ text, cites, evidence, open }: { text: string; cites: string[]; evidence?: Record<string, unknown>; open: (id: string) => void }) {
  if (!evidence) return <>{text}</>;
  const find = sources(evidence, cites);
  const out: React.ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(NUMBER)) {
    const src = find(m[0].trim());
    if (!src || m.index === undefined) continue;
    out.push(text.slice(last, m.index));
    out.push(
      <button key={m.index} onClick={() => open(src.id)} title={`${src.id}${src.path ? `, ${src.path}` : ""} = ${fmt(src.value)}`}
        className="rounded-[3px] font-medium tabular-nums underline decoration-meta decoration-dotted underline-offset-[3px] hover:bg-surface-warm hover:decoration-accent">
        {m[0]}
      </button>);
    last = m.index + m[0].length;
  }
  out.push(text.slice(last));
  return <>{out}</>;
}

function questions(view: View): string[] {
  const flagged = view.checks.find((c) => c.status === "fail") ?? view.checks.find((c) => c.status === "warn");
  const has = (id: string) => view.checks.some((c) => c.id === id && c.status !== "skip");
  return [
    flagged && `Why does ${flagged.id} ${flagged.status}?`,
    view.techniques.includes("pdf") && "How good is the PDF fit?",
    has("C6") && "Do the XRD and PDF sizes agree?",
    view.virtual_xafs && "What does the virtual XAFS recommend?",
    has("C2") && "Do EXAFS and the PDF model agree on bond lengths?",
  ].filter(Boolean).slice(0, 3) as string[];
}

/** The opening message: what the tools found, from the data only. */
function Brief({ row, view, state, act, busy }: { row?: SampleRow; view?: View; state: string; act: Actions; busy: boolean }) {
  if (state === "loading") {
    return <div className="grid gap-2" aria-busy="true">{[80, 95, 60].map((w) => <div key={w} className="h-3.5 animate-pulse rounded bg-surface-warm" style={{ width: `${w}%` }} />)}</div>;
  }
  if (!view) {
    return (
      <div className="grid gap-3">
        <p className="text-[15px] text-fg-2">
          <b className="font-medium text-fg">{row?.composition ?? "This sample"}</b>
          {row ? <> has {row.techniques.map((t) => t.toUpperCase()).join(", ")} data</> : null} and has not been analysed yet.
          The tools and checks usually take under a minute and need no language model; the agents fit each technique, inspect every fit
          visually and review the result, which takes about 25 minutes.
        </p>
        {state === "error" ? <p className="text-sm text-bad">The results could not be loaded. Is the API running?</p> : null}
        <div className="flex flex-wrap gap-2">
          <button disabled={busy} onClick={() => act.run("fast")} className="btn btn-primary"><Lightning size={16} weight="fill" aria-hidden />Run tools and checks</button>
          <button disabled={busy} onClick={() => act.run("full")} className="btn btn-quiet"><UsersThree size={16} weight="bold" aria-hidden />Run the agents</button>
        </div>
      </div>
    );
  }
  const n = (s: string) => view.checks.filter((c) => c.status === s).length;
  const flagged = view.checks.filter((c) => c.status === "fail" || c.status === "warn");
  const a = view.agents;
  return (
    <div className="grid gap-3 text-[15px] text-fg-2">
      <p>
        <b className="font-medium text-fg">{view.composition}</b>, measured with {view.techniques.map((t) => t.toUpperCase()).join(", ")}.{" "}
        {view.phase ? <>The fits identify <b className="font-medium text-fg">{view.phase}</b>.</> : <>No candidate structure fits.</>}{" "}
        {n("pass")} of {view.checks.length} cross-checks pass{flagged.length ? ", and these need a look:" : "."}
      </p>
      {flagged.length ? (
        <ul className="grid gap-1.5">
          {flagged.map((c) => {
            const t = TONE[c.status];
            return (
              <li key={c.id}>
                <button onClick={() => act.open(`check.${c.id}`)} className="group flex w-full gap-2 rounded-sm text-left">
                  <t.Icon size={18} weight="fill" className={`mt-0.5 shrink-0 ${t.fg}`} aria-label={t.label} />
                  <span className="min-w-0">
                    <span className="font-medium text-fg group-hover:text-accent">{c.id} {c.name}.</span>{" "}
                    <span className="line-clamp-2">{c.explanation}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {a ? (
        <p>
          The critic reviewed the analysis in {a.rounds} round{a.rounds === 1 ? "" : "s"} and raised {a.log.length || "no"} objection{a.log.length === 1 ? "" : "s"}
          {a.log.length ? `, ${a.confirmed.length || "none"} upheld by a re-run` : ""}.{" "}
          <button onClick={() => act.open("rerun.")} className="text-accent hover:underline">Open the review</button>
          {a.stale ? <span className="text-warn"> It predates the current checks.</span> : null}
        </p>
      ) : (
        <p>The critic has not reviewed this sample yet.</p>
      )}
    </div>
  );
}

function Activity({ m }: { m: Extract<Msg, { kind: "run" }> }) {
  const [open, setOpen] = useState(m.state === "running");
  const [, tick] = useState(0);
  useEffect(() => {
    if (m.state !== "running") return setOpen(false);
    const t = setInterval(() => tick((x) => x + 1), 1000);
    return () => clearInterval(t);
  }, [m.state]);
  const secs = Math.round(((m.ended ?? Date.now()) - m.started) / 1000);
  const took = secs < 120 ? `${secs} s` : `${Math.round(secs / 60)} min`;
  const Icon = m.state === "running" ? CircleNotch : m.state === "done" ? CheckCircle : XCircle;
  return (
    <div className="rounded-md bg-surface shadow-ring">
      <button onClick={() => setOpen((x) => !x)} aria-expanded={open} className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm">
        <Icon size={16} weight="bold" aria-hidden className={m.state === "running" ? "animate-spin text-accent" : m.state === "done" ? "text-ok" : "text-bad"} />
        <span className="font-medium text-fg">{m.label ?? RUN_LABEL[m.mode]}</span>
        <span className="text-meta tabular-nums">{m.state === "running" ? `running, ${took}` : m.state === "done" ? took : "stopped"}</span>
        <CaretDown size={12} weight="bold" className={`ml-auto text-meta transition-transform duration-150 ${open ? "" : "-rotate-90"}`} aria-hidden />
      </button>
      {open && m.steps.length ? (
        <ol className="grid max-h-72 gap-2 overflow-y-auto border-t border-line px-3 py-2 text-sm" aria-live="polite">
          {m.steps.slice(-40).map((s, i) => (
            <li key={i} className="text-muted">
              {s.author ? <span className="mr-1.5 font-mono text-xs text-fg-2">{s.author}</span> : null}
              <span className={s.author ? "line-clamp-3 whitespace-pre-wrap" : ""}>{s.text}</span>
            </li>
          ))}
        </ol>
      ) : null}
      {m.summary ? <p className="border-t border-line px-3 py-2 text-sm text-fg-2">{m.summary}</p> : null}
      {m.error ? <p role="alert" className="border-t border-line px-3 py-2 text-sm text-bad">{m.error}</p> : null}
    </div>
  );
}

function Message({ m, act, busy, evidence }: { m: Msg; act: Actions; busy: boolean; evidence?: Record<string, unknown> }) {
  if (m.kind === "user") {
    return <div className="ml-auto max-w-[85%] whitespace-pre-wrap rounded-lg bg-surface-warm px-4 py-2.5 text-[15px] text-fg">{m.text}</div>;
  }
  if (m.kind === "run") return <Activity m={m} />;
  if (m.kind === "error") return <p role="alert" className="rounded-md bg-bad-bg px-3 py-2 text-sm text-bad">{m.text}</p>;
  const s = m.suggest !== "none" ? SUGGEST[m.suggest] : null;
  const SIcon = s?.[1];
  return (
    <div className="grid gap-2.5">
      <div className="whitespace-pre-wrap text-[15px] text-fg"><Sourced text={m.answer} cites={m.cites} evidence={evidence} open={act.open} /></div>
      {m.unsupported_numbers.length ? (
        <p className="flex items-start gap-1.5 text-sm text-warn">
          <WarningCircle size={16} weight="fill" className="mt-0.5 shrink-0" aria-hidden />
          Not found in the evidence: {m.unsupported_numbers.join(", ")}. Treat {m.unsupported_numbers.length === 1 ? "it" : "them"} as unverified.
        </p>
      ) : null}
      {m.cites.length || s ? (
        <div className="flex flex-wrap items-center gap-1.5">
          {m.cites.map((c) => <Chip key={c} id={c} onOpen={act.open} />)}
          {s ? (
            <button disabled={busy} onClick={() => (m.suggest === "find_priors" ? act.findPriors() : act.run(m.suggest === "run_full" ? "full" : "fast"))}
              className="btn btn-quiet ml-auto py-1 text-[13px]">{SIcon ? <SIcon size={14} weight="bold" aria-hidden /> : null}{s[0]}</button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default function Chat({ sid, row, view, state, msgs, asking, busy, act, ganReady }: {
  sid: string; row?: SampleRow; view?: View; state: "loading" | "missing" | "error" | "ready"; msgs: Msg[];
  asking: boolean; busy: boolean; act: Actions; ganReady: boolean;
}) {
  const [text, setText] = useState("");
  const scroller = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const ready = state === "ready";

  useEffect(() => { scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" }); }, [msgs.length, asking, sid]);
  useEffect(() => {  // grow with the text, up to about eight lines
    const el = input.current;
    if (el) { el.style.height = "auto"; el.style.height = `${Math.min(el.scrollHeight, 200)}px`; }
  }, [text]);

  const send = (q = text) => {
    if (!q.trim() || asking || !ready) return;
    act.ask(q.trim());
    setText("");
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scroller} id="conversation" tabIndex={-1} className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        <div className="mx-auto grid max-w-[720px] gap-6 px-4 py-6 sm:px-6">
          <div className="rise grid gap-3">
            <div className="flex items-center gap-2 text-sm text-meta">
              <span className="grid size-6 place-items-center rounded-full bg-accent text-accent-on"><IntersectThree size={14} weight="bold" aria-hidden /></span>
              <span className="font-medium text-fg-2">Concord</span>
              <span className="font-mono text-xs">{sid}</span>
            </div>
            <Brief row={row} view={view} state={state} act={act} busy={busy} />
            {view ? <Generated key={view.sample_id} view={view} ganReady={ganReady} /> : null}
          </div>
          <div className="grid gap-6" aria-live="polite">{msgs.map((m, i) => <div key={i} className="rise"><Message m={m} act={act} busy={busy} evidence={view?.evidence} /></div>)}</div>
          {asking ? (
            <div className="grid gap-2" aria-live="polite" aria-busy="true">
              <span className="text-sm text-meta">Reading the evidence…</span>
              {[90, 70].map((w) => <div key={w} className="h-3 animate-pulse rounded bg-surface-warm" style={{ width: `${w}%` }} />)}
            </div>
          ) : null}
          {ready && !msgs.some((m) => m.kind === "user") && view ? (
            <div className="flex flex-wrap gap-2">
              {questions(view).map((q) => (
                <button key={q} onClick={() => send(q)} className="rounded-full px-3 py-1.5 text-sm text-fg-2 shadow-ring transition-colors duration-150 hover:bg-surface-warm">{q}</button>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(); }} className="mx-auto w-full max-w-[720px] px-4 pb-4 sm:px-6">
        <div className="rounded-lg bg-surface shadow-raised ring-1 ring-line transition-shadow duration-150 focus-within:ring-accent/60">
          <label htmlFor="ask" className="sr-only">Ask about {sid}</label>
          <textarea id="ask" ref={input} rows={1} value={text} onChange={(e) => setText(e.target.value)} disabled={!ready}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); } }}
            placeholder={ready ? `Ask about ${view?.composition ?? sid}…` : "Run the tools first, then ask about the results…"}
            className="block max-h-[200px] w-full resize-none bg-transparent px-4 pt-3.5 pb-1 text-[15px] text-fg placeholder:text-meta focus:outline-none focus-visible:shadow-none disabled:cursor-not-allowed" />
          <div className="flex items-center gap-1 px-2 pb-2">
            <button type="button" onClick={act.upload} className="btn btn-ghost px-2" title="Analyse your own data" aria-label="Analyse your own data"><UploadSimple size={18} weight="bold" /></button>
            <button type="button" disabled={busy} onClick={() => act.run("fast")} className="btn btn-ghost px-2" title="Run the tools and checks, about 30 s">
              <Lightning size={18} weight="bold" aria-hidden /><span className="hidden sm:inline">Checks</span>
            </button>
            <button type="button" disabled={busy} onClick={() => act.run("full")} className="btn btn-ghost px-2" title="Fitting agents, visual inspection and critic review, about 25 min">
              <UsersThree size={18} weight="bold" aria-hidden /><span className="hidden sm:inline">Agents</span>
            </button>
            <button type="button" disabled={busy || !ready} onClick={act.findPriors} className="btn btn-ghost px-2" title="Search the open literature for this material">
              <BookOpen size={18} weight="bold" aria-hidden /><span className="hidden sm:inline">Literature</span>
            </button>
            <button type="submit" disabled={!text.trim() || asking || !ready} aria-label="Send"
              className="btn btn-primary ml-auto size-8 justify-center rounded-sm p-0"><ArrowUp size={16} weight="bold" /></button>
          </div>
        </div>
        <p className="mt-2 text-center text-[11px] text-meta">Answers come from this sample&apos;s evidence only; a number the evidence lacks is flagged.</p>
      </form>
    </div>
  );
}
