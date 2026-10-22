"use client";
import { useCallback, useEffect, useState } from "react";
import type { ChatReply } from "@/lib/api";

export type Step = { kind: "status" | "agent"; author?: string; text: string };
export type Msg =
  | { kind: "user"; text: string }
  | ({ kind: "answer" } & ChatReply)
  | { kind: "error"; text: string }
  | { kind: "run"; id: string; mode: "fast" | "full" | "priors"; state: "running" | "done" | "error"; started: number; ended?: number; steps: Step[]; summary?: string; error?: string };

const key = (sid: string) => `concord.thread.${sid}`;

function load(sid: string): Msg[] {
  try {
    const msgs: Msg[] = JSON.parse(localStorage.getItem(key(sid)) ?? "[]");
    // a run that was streaming when the page closed never got its end
    return msgs.map((m) => (m.kind === "run" && m.state === "running" ? { ...m, state: "error", error: "interrupted: the page was closed during the run" } : m));
  } catch {
    return [];
  }
}

/** One conversation per sample, kept in this browser only. */
export function useThreads() {
  const [threads, setThreads] = useState<Record<string, Msg[]>>({});
  const get = useCallback((sid: string) => threads[sid] ?? (typeof window === "undefined" ? [] : load(sid)), [threads]);
  // the updater stays pure (React may run it twice); storage is written after the render
  const update = useCallback((sid: string, fn: (msgs: Msg[]) => Msg[]) => {
    setThreads((all) => ({ ...all, [sid]: fn(all[sid] ?? load(sid)).slice(-60) }));
  }, []);
  useEffect(() => {
    for (const [sid, msgs] of Object.entries(threads)) {
      try { localStorage.setItem(key(sid), JSON.stringify(msgs)); } catch { /* storage full or blocked: the thread lives until reload */ }
    }
  }, [threads]);
  return { get, update };
}
