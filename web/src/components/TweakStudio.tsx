"use client";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { ArrowCounterClockwise, ArrowRight, CircleNotch, Sliders } from "@phosphor-icons/react";
import { fetcher, post, type Check, type FitCurve, type View } from "@/lib/api";
import { useLive } from "@/lib/useLive";
import { Field, Shell, type Param } from "@/components/Studio";
import { CheckStrip, StatusPill } from "@/components/CheckPanel";
import Plot from "@/components/Plot";
import Value from "@/components/Value";

type Refit = { technique: string; values: Record<string, unknown>; curve: FitCurve; metrics: Record<string, unknown>; checks: Check[];
  changed: { id: string; from: Check["status"]; to: Check["status"] }[]; timing_s: number };
const NAME: Record<string, string> = { xrd: "XRD", pdf: "PDF", exafs: "EXAFS", xanes: "XANES" };

/** "Open in analysis": change a fit's parameters, see the re-fit and how every cross-check would move, keep or drop it. */
export default function TweakStudio({ sid, technique, open, onClose, onApplied }: {
  sid: string; technique: string; open: boolean; onClose: () => void; onApplied: (v: View, summary: string) => void;
}) {
  const { data, error: loadError } = useSWR<{ params: Param[] }>(open ? `/api/samples/${sid}/tweak/${technique}` : null, fetcher, { revalidateOnFocus: false });
  const initial = useMemo(() => Object.fromEntries((data?.params ?? []).map((p) => [p.name, p.value])), [data]);
  const [values, setValues] = useState<Record<string, unknown>>();
  useEffect(() => { if (data) setValues(initial); }, [data, initial]);
  const dirty = !!values && JSON.stringify(values) !== JSON.stringify(initial);
  const live = useLive(open && values ? values : undefined, (v) => post<Refit>(`/api/samples/${sid}/tweak/${technique}`, { values: v }), 600);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string>();
  const r = live.out, c = r?.curve;

  const keep = async () => {
    setSaving(true);
    setSaveError(undefined);
    try {
      const v = await post<View>(`/api/samples/${sid}/tweak-apply`, { overrides: { [technique]: values } });
      const diff = Object.entries(values ?? {}).filter(([k, x]) => JSON.stringify(x) !== JSON.stringify(initial[k])).map(([k, x]) => `${k} ${String(x)}`);
      onApplied(v, `Re-analysed with your ${NAME[technique]} settings: ${diff.join(", ")}.`);
    } catch (e) {
      setSaveError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Shell open={open} onClose={onClose} eyebrow={<><Sliders size={13} weight="bold" aria-hidden />Open in analysis</>}
      title={`${NAME[technique] ?? technique} fit of ${sid}`}
      aside={
        <div className="grid gap-5">
          {loadError ? <p role="alert" className="text-sm text-bad">{loadError.message}</p> : null}
          {!data && !loadError ? Array.from({ length: 5 }, (_, i) => <div key={i} className="h-12 animate-pulse rounded-sm bg-surface-warm" />) : null}
          {data && values ? data.params.map((p) => <Field key={p.name} p={p} value={values[p.name]} onChange={(v) => setValues((x) => ({ ...x!, [p.name]: v }))} />) : null}
          {data && !data.params.length ? <p className="text-sm text-muted">This fit has no settings to change.</p> : null}
          {data?.params.length ? (
            <div className="grid gap-2 border-t border-line pt-4">
              <button disabled={!dirty || saving || live.busy || !!live.error} onClick={keep} className="btn btn-primary justify-center">
                {saving ? <CircleNotch size={16} weight="bold" className="animate-spin" aria-hidden /> : <ArrowRight size={16} weight="bold" aria-hidden />}
                {saving ? "Re-analysing…" : "Keep and re-analyse"}
              </button>
              <button disabled={!dirty} onClick={() => setValues(initial)} className="btn btn-ghost justify-center"><ArrowCounterClockwise size={16} weight="bold" aria-hidden />Back to the analysis values</button>
              {saveError ? <p role="alert" className="text-sm text-bad">{saveError}</p> : null}
              <p className="text-xs text-meta">Keeping re-runs the whole analysis with these settings and records them in the report. The original analysis can be restored.</p>
            </div>
          ) : null}
        </div>
      }>
      <div className="grid gap-5">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {live.busy ? <span className="inline-flex items-center gap-1.5 text-muted"><CircleNotch size={14} weight="bold" className="animate-spin" aria-hidden />Refitting…</span>
            : r ? <span className="text-muted">Refitted in {r.timing_s} s</span> : null}
          {live.error ? <span role="alert" className="text-bad">{live.error}</span> : null}
        </div>
        {c ? (
          <div className={`min-w-0 rounded-md bg-surface p-3 shadow-ring transition-opacity duration-200 ${live.busy ? "opacity-60" : ""}`}>
            <div className="mb-2 text-sm font-medium">{c.title}</div>
            <Plot x={c.x} xLabel={c.x_label} yLabel={c.y_label} window={c.window} height={300} ariaLabel={`${c.title}: data, model and difference`}
              series={[{ key: "obs", label: "data", y: c.obs, color: "var(--series-1)", width: 1.25 }, { key: "calc", label: "model", y: c.calc, color: "var(--series-2)", width: 1.5 }]}
              diff={{ y: c.diff, label: "difference (data minus model)" }} />
          </div>
        ) : <div className="h-80 animate-pulse rounded-md bg-surface-warm" aria-busy="true" />}
        {r ? (
          <div className="grid gap-5 @3xl:grid-cols-2">
            <section className="min-w-0">
              <h3 className="eyebrow mb-2">Fit</h3>
              <Value v={r.metrics} />
            </section>
            <section className="min-w-0">
              <h3 className="eyebrow mb-2">Cross-checks with this fit</h3>
              <CheckStrip checks={r.checks} onOpen={() => undefined} />
              {r.changed.length ? (
                <ul className="mt-3 grid gap-1.5 text-sm">
                  {r.changed.map((x) => (
                    <li key={x.id} className="flex items-center gap-2"><span className="font-mono text-xs text-meta">{x.id}</span><StatusPill status={x.from} /><ArrowRight size={12} aria-hidden /><StatusPill status={x.to} /></li>
                  ))}
                </ul>
              ) : <p className="mt-3 text-sm text-muted">No check changes status.</p>}
            </section>
          </div>
        ) : null}
      </div>
    </Shell>
  );
}
