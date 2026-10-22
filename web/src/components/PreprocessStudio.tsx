"use client";
import { useEffect, useState } from "react";
import { ArrowRight, CircleNotch, Funnel, WarningCircle } from "@phosphor-icons/react";
import { post } from "@/lib/api";
import { useLive } from "@/lib/useLive";
import { Field, Shell, type Param } from "@/components/Studio";
import Plot from "@/components/Plot";
import Value from "@/components/Value";

type XY = { q?: number[]; r?: number[]; y?: number[]; sample?: number[]; background?: number[] | null };
type Reduced = {
  params: Record<string, number | boolean | null>; warnings: string[]; quality: Record<string, unknown>;
  steps: { raw: XY; corrected: XY; sq: XY; fq: XY; gr: XY }; current?: { r: number[]; g: number[] } | null;
};

const SPEC = (p: Reduced["params"], qtop: number): Param[] => [
  { name: "bkg_scale", label: "Background scale", kind: "float", value: p.bkg_scale ?? 1, min: 0, max: 1.5, step: 0.01, help: "How much of the container measurement is subtracted." },
  { name: "qmin", label: "Qmin", kind: "float", value: p.qmin ?? 0.5, min: 0.1, max: 3, step: 0.05, unit: "Å⁻¹" },
  { name: "qmax", label: "Qmax", kind: "float", value: p.qmax ?? qtop, min: 5, max: qtop, step: 0.1, unit: "Å⁻¹", help: "Higher Qmax sharpens G(r) but brings in more noise." },
  { name: "qmaxinst", label: "Qmax for the corrections", kind: "float", value: p.qmaxinst ?? qtop, min: 5, max: qtop, step: 0.1, unit: "Å⁻¹" },
  { name: "rpoly", label: "rpoly", kind: "float", value: p.rpoly ?? 0.9, min: 0.1, max: 2.5, step: 0.05, unit: "Å", help: "Shortest distance the smooth correction may touch; larger values flatten low r." },
  { name: "rmax", label: "rmax", kind: "float", value: p.rmax ?? 30, min: 10, max: 60, step: 1, unit: "Å" },
  { name: "lorch", label: "Lorch window", kind: "bool", value: !!p.lorch, help: "Damps termination ripples at the cost of resolution." },
];

const Panel = ({ title, children, busy }: { title: string; children: React.ReactNode; busy: boolean }) => (
  <section className={`min-w-0 rounded-md bg-surface p-3 shadow-ring transition-opacity duration-200 ${busy ? "opacity-60" : ""}`}>
    <h3 className="mb-2 text-sm font-medium">{title}</h3>{children}
  </section>
);

/** "Open in preprocessing": the raw intensity reduced step by step to G(r), with every parameter live. */
export default function PreprocessStudio({ sid, open, onClose, onSaved }: { sid: string; open: boolean; onClose: () => void; onSaved: (newSample: string) => void }) {
  const [values, setValues] = useState<Record<string, unknown>>();
  const [spec, setSpec] = useState<Param[]>();
  const live = useLive(open ? (values ?? {}) : undefined, (v) => post<Reduced>(`/api/samples/${sid}/preprocess`, { params: v }), 250);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string>();
  const r = live.out;

  useEffect(() => {  // the first reduction (server defaults) sets the controls
    if (r && !spec) {
      const qtop = Math.floor((r.steps.raw.q?.at(-1) ?? 25) * 10) / 10;
      const s = SPEC(r.params, qtop);
      setSpec(s);
      setValues(Object.fromEntries(s.map((p) => [p.name, p.value])));
    }
  }, [r, spec]);
  useEffect(() => { if (!open) { setSpec(undefined); setValues(undefined); } }, [open]);

  const save = async () => {
    setSaving(true);
    setSaveError(undefined);
    try {
      const d = await post<{ sample: string }>(`/api/samples/${sid}/preprocess/save`, { params: values });
      onSaved(d.sample);
    } catch (e) {
      setSaveError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };
  const s = r?.steps;

  return (
    <Shell open={open} onClose={onClose} eyebrow={<><Funnel size={13} weight="bold" aria-hidden />Open in preprocessing</>} title={`From raw intensity to G(r), ${sid}`}
      aside={
        <div className="grid gap-5">
          {spec && values ? spec.map((p) => <Field key={p.name} p={p} value={values[p.name]} onChange={(v) => setValues((x) => ({ ...x!, [p.name]: v }))} />)
            : Array.from({ length: 6 }, (_, i) => <div key={i} className="h-12 animate-pulse rounded-sm bg-surface-warm" />)}
          <div className="grid gap-2 border-t border-line pt-4">
            <button disabled={!r || saving || live.busy} onClick={save} className="btn btn-primary justify-center">
              {saving ? <CircleNotch size={16} weight="bold" className="animate-spin" aria-hidden /> : <ArrowRight size={16} weight="bold" aria-hidden />}
              {saving ? "Saving…" : "Analyse this G(r)"}
            </button>
            {saveError ? <p role="alert" className="text-sm text-bad">{saveError}</p> : null}
            <p className="text-xs text-meta">Saves this G(r) with the sample&apos;s other data as a new sample in Your uploads and runs the analysis on it; the original stays as it is.</p>
          </div>
        </div>
      }>
      <div className="grid gap-4">
        <div className="flex flex-wrap items-center gap-3 text-sm">
          {live.busy ? <span className="inline-flex items-center gap-1.5 text-muted"><CircleNotch size={14} weight="bold" className="animate-spin" aria-hidden />Reducing…</span> : null}
          {live.error ? <span role="alert" className="text-bad">{live.error}</span> : null}
          {r?.warnings.map((w) => <span key={w} className="inline-flex items-center gap-1 text-warn"><WarningCircle size={14} weight="fill" aria-hidden />{w}</span>)}
        </div>
        {s ? (
          <div className="grid gap-4 @4xl:grid-cols-2">
            <Panel title="1. Raw intensity and background" busy={live.busy}>
              <Plot x={s.raw.q!} xLabel="Q (Å⁻¹)" yLabel="I(Q) (counts)" height={200} ariaLabel="Raw intensity of the sample and the scaled background"
                series={[{ key: "s", label: "sample", y: s.raw.sample!, color: "var(--series-1)" },
                  ...(s.raw.background ? [{ key: "b", label: `background × ${values?.bkg_scale ?? 1}`, y: s.raw.background.map((v) => v * Number(values?.bkg_scale ?? 1)), color: "var(--series-2)" }] : [])]} />
            </Panel>
            <Panel title="2. Structure factor S(Q)" busy={live.busy}>
              <Plot x={s.sq.q!} xLabel="Q (Å⁻¹)" yLabel="S(Q)" height={200} ariaLabel="Structure factor" series={[{ key: "sq", label: "S(Q)", y: s.sq.y!, color: "var(--series-1)" }]} />
            </Panel>
            <Panel title="3. Reduced structure function F(Q) = Q[S(Q) − 1]" busy={live.busy}>
              <Plot x={s.fq.q!} xLabel="Q (Å⁻¹)" yLabel="F(Q) (Å⁻¹)" height={200} ariaLabel="Reduced structure function" series={[{ key: "fq", label: "F(Q)", y: s.fq.y!, color: "var(--series-1)" }]} />
            </Panel>
            <Panel title="4. Pair distribution function G(r)" busy={live.busy}>
              <Plot x={s.gr.r!} xLabel="r (Å)" yLabel="G(r) (Å⁻²)" height={200} ariaLabel="Pair distribution function from these settings and the one in the analysis"
                series={[{ key: "gr", label: "these settings", y: s.gr.y!, color: "var(--series-1)", width: 1.5 },
                  ...(r.current ? [{ key: "cur", label: "used in the analysis", x: r.current.r, y: r.current.g, color: "var(--series-2)", width: 1, dash: "4 3" }] : [])]} />
            </Panel>
          </div>
        ) : !live.error ? <div className="h-96 animate-pulse rounded-md bg-surface-warm" aria-busy="true" /> : null}
        {r && Object.keys(r.quality).length ? (
          <section className="min-w-0"><h3 className="eyebrow mb-2">Quality</h3><Value v={r.quality} /></section>
        ) : null}
      </div>
    </Shell>
  );
}
