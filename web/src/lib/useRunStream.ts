"use client";
import { useEffect, useState } from "react";

export type RunEvent = {
  type: "status" | "event" | "result" | "error" | "done" | "closed" | string;
  payload?: any;
};

/** Events of one run; a new run id starts from an empty list, never showing the previous run's events. */
export function useRunStream(runId?: string) {
  const [state, setState] = useState<{ id?: string; events: RunEvent[] }>({ events: [] });

  useEffect(() => {
    if (!runId) return;
    setState({ id: runId, events: [] });
    const add = (evt: RunEvent) => setState((s) => (s.id === runId ? { ...s, events: [...s.events, evt] } : s));
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_API_WS}/api/runs/${runId}/stream`);
    ws.onmessage = (ev) => {
      try {
        add(JSON.parse(ev.data));
      } catch {
        // ignore a garbled frame
      }
    };
    ws.onerror = () => ws.close();
    ws.onclose = () => add({ type: "closed" });  // without "done" first, the run broke off
    return () => { ws.onclose = null; ws.close(); };
  }, [runId]);

  return { events: state.id === runId ? state.events : [] };
}
