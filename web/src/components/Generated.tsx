"use client";
import { useState } from "react";
import { CircleNotch, Sparkle } from "@phosphor-icons/react";
import { post, type View } from "@/lib/api";
import { fmt } from "@/components/Value";
import Plot from "@/components/Plot";

type Gen = {
  label: string; notes: string[];
  from: { measured: string[]; phase: string; size_nm: number; source: string; absorber: string; edge: string };
  techniques: Record<string, { x_label: string; y_label: string; x: number[]; clean: number[]; realistic: number[] | null }>;
};
const NAME: Record<string, string> = { xrd: "XRD", pdf: "PDF", exafs: "EXAFS", xafs: "XAFS" };
const ALL = [["xrd", "xrd"], ["pdf", "pdf"], ["xafs", "exafs"]] as const;  // [analysis input, generated technique]
const list = (xs: string[]) => xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs.at(-1)}`;

/** Only some techniques measured: offer the others, simulated from the fitted model and made realistic by the local GAN. */
export default function Generated({ view, ganReady }: { view: View; ganReady: boolean }) {
  const [data, setData] = useState<Gen>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const missing = ALL.filter(([i]) => !view.techniques.includes(i)).map(([, t]) => NAME[t]);
  if (!missing.length || !view.phase) return null;

  const go = async () => {
    setBusy(true);
    setError(undefined);
    try {
      setData(await post<Gen>(`/api/samples/${view.sample_id}/generate`, { realistic: ganReady }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!data) {
    return (
      <div className="grid gap-2 rounded-md bg-surface p-4 shadow-ring">
        <span className="eyebrow inline-flex items-center gap-1"><Sparkle size={13} weight="fill" aria-hidden />Fill in what you did not measure</span>
        <p className="text-sm text-fg-2">
          You measured only {list(view.techniques.map((t) => NAME[t] ?? t.toUpperCase()))}.
          {" "}{missing.length === 1 ? `The ${missing[0]}` : `The ${list(missing)}`} this material would give can be generated from the model the fits found
          {ganReady ? ", with instrument effects added by the GAN we trained locally on measured spectra" : ""}.
          {" "}They are not measurements and are never used in the checks.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={go} disabled={busy} className="btn btn-primary">
            {busy ? <CircleNotch size={16} weight="bold" className="animate-spin" aria-hidden /> : <Sparkle size={16} weight="fill" aria-hidden />}
            {busy ? "Generating…" : missing.length === 1 ? `Generate the ${missing[0]}` : missing.length === 2 ? "Generate the other two" : "Generate them"}
          </button>
          {error ? <span role="alert" className="text-sm text-bad">{error}</span> : null}
        </div>
      </div>
    );
  }

  const f = data.from;
  return (
    <div className="rise grid gap-3 rounded-md bg-surface p-4 shadow-ring">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-warn-bg px-2 py-0.5 text-[11px] font-semibold tracking-wide text-warn">{data.label}</span>
        <span className="text-sm text-muted">From {f.source}: {f.phase}, {fmt(f.size_nm)} nm.</span>
      </div>
      {Object.entries(data.techniques).map(([t, c]) => (
        <div key={t} className="min-w-0">
          <div className="mb-1 text-sm font-medium">{NAME[t]}{t === "exafs" ? `, ${f.absorber} ${f.edge}` : ""}</div>
          <Plot x={c.x} xLabel={c.x_label} yLabel={c.y_label} height={180} ariaLabel={`Generated ${NAME[t]}, not measured`}
            series={[...(c.realistic ? [{ key: "gan", label: "with the GAN's instrument effects", y: c.realistic, color: "var(--series-2)", width: 1.25 }] : []),
              { key: "clean", label: "clean simulation", y: c.clean, color: "var(--series-1)", width: 1.25, dash: c.realistic ? "4 3" : undefined }]} />
        </div>
      ))}
      {data.notes.length ? <ul className="grid gap-1 text-xs text-muted">{data.notes.map((n) => <li key={n}>{n}</li>)}</ul> : null}
      <p className="text-xs text-meta">Shown to help plan the next measurement. The checks compare measured data only; a curve made from the fitted model would only agree with itself.</p>
    </div>
  );
}
