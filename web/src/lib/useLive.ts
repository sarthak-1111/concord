"use client";
import { useEffect, useRef, useState } from "react";

/** Calls `fn(input)` a short pause after `input` changes; a reply to an older input never overwrites a newer one. */
export function useLive<I, O>(input: I | undefined, fn: (input: I) => Promise<O>, delay = 350) {
  const [out, setOut] = useState<O>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const seq = useRef(0);
  const key = JSON.stringify(input ?? null);
  useEffect(() => {
    if (input === undefined) return;
    const n = ++seq.current;
    setBusy(true);
    const t = setTimeout(async () => {
      try {
        const o = await fn(input);
        if (n === seq.current) { setOut(o); setError(undefined); }
      } catch (e) {
        if (n === seq.current) setError((e as Error).message);
      } finally {
        if (n === seq.current) setBusy(false);
      }
    }, delay);
    return () => clearTimeout(t);
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return { out, busy, error };
}
