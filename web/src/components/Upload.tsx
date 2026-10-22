"use client";
import { useEffect, useRef, useState } from "react";
import { Compass, FileArrowUp, Play, Sparkle, Trash, UploadSimple, X } from "@phosphor-icons/react";
import { API } from "@/lib/api";
import CompositionField from "@/components/PeriodicTable";

type Kind = "xrd" | "pdf" | "xafs_mu" | "xafs_chi";
type Inspected = {
  name: string; technique: Kind | null; confidence: "high" | "medium" | "low"; reason: string; x_label: string; x_range: [number, number] | null;
  n_points: number; preview: { x: number[]; y: number[] } | null; edge: string | null; header: Record<string, unknown>; warnings: string[];
};
type Item = { file: File; info?: Inspected; kind: Kind | "skip" };

const KINDS: [Kind, string][] = [["xrd", "XRD pattern"], ["pdf", "PDF, G(r)"], ["xafs_mu", "XAFS, μ(E)"], ["xafs_chi", "XAFS, χ(k)"]];
const LABEL = "grid min-w-0 gap-1 text-sm font-medium text-fg-2";

function Spark({ p }: { p: Inspected["preview"] }) {
  if (!p?.x.length) return <div className="h-10 w-28 rounded-sm bg-surface-warm" aria-hidden />;
  const [x0, x1] = [p.x[0], p.x[p.x.length - 1]];
  const pts = p.x.map((x, i) => `${(((x - x0) / (x1 - x0 || 1)) * 112).toFixed(1)},${(36 - p.y[i] * 32).toFixed(1)}`).join(" ");
  return <svg width="112" height="40" className="shrink-0 rounded-sm bg-bg" aria-hidden><polyline points={pts} fill="none" stroke="var(--series-1)" strokeWidth={1.25} /></svg>;
}

export default function Upload({ open, onClose, onUploaded, onExample, onPlan }: {
  open: boolean; onClose: () => void; onUploaded: (id: string) => void; onExample: () => void; onPlan: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [composition, setComposition] = useState("");
  const [edge, setEdge] = useState("");
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState<"reading" | "uploading">();
  const [error, setError] = useState<string>();

  useEffect(() => {
    const d = ref.current;
    if (open && d && !d.open) d.showModal();
    if (!open && d?.open) d.close();
  }, [open]);

  const inspect = async (files: File[], comp = composition) => {
    if (!files.length) return;
    setBusy("reading");
    setError(undefined);
    try {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      form.append("composition", comp);
      const r = await fetch(`${API}/api/uploads/inspect`, { method: "POST", body: form });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error ?? r.statusText);
      const infos: Inspected[] = d.files;
      setItems(files.map((file, i) => ({ file, info: infos[i], kind: infos[i]?.technique ?? "skip" })));
      const e = infos.find((x) => x?.edge)?.edge;
      if (e) setEdge((cur) => cur || e);
    } catch (err) {
      setItems(files.map((file) => ({ file, kind: "skip" })));
      setError(`Could not read the files: ${(err as Error).message}`);
    } finally {
      setBusy(undefined);
    }
  };
  const add = (list: FileList | null) => inspect([...items.map((i) => i.file), ...Array.from(list ?? [])].slice(0, 3));

  const used = items.filter((i) => i.kind !== "skip");
  const dup = KINDS.find(([k]) => used.filter((i) => i.kind === k).length > 1 || (k.startsWith("xafs") && used.filter((i) => i.kind.startsWith("xafs")).length > 1));
  const xafs = used.find((i) => i.kind.startsWith("xafs"));
  const head = (key: string) => used.map((i) => i.info?.header?.[key]).find((v) => v != null);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);  // composition, edge and instrument values; the files are added below
    if (!used.length) return setError("Add at least one XRD, PDF or XAFS file, or try an example below.");
    if (dup) return setError(`Two files are marked as ${dup[0].startsWith("xafs") ? "XAFS" : dup[1]}. Keep one or change its type.`);
    for (const i of used) form.append(i.kind.startsWith("xafs") ? "xafs" : i.kind, i.file);
    if (xafs) form.append("xafs_kind", xafs.kind === "xafs_chi" ? "chi" : "mu");
    setBusy("uploading");
    setError(undefined);
    try {
      const r = await fetch(`${API}/api/uploads`, { method: "POST", body: form });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error ?? r.statusText);
      setItems([]); setEdge(""); setComposition("");
      onUploaded(d.sample);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(undefined);
    }
  };

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="upload-h"
      className="m-auto max-h-[calc(100dvh-32px)] w-[min(600px,calc(100vw-32px))] overscroll-contain rounded-lg bg-surface p-0 text-fg shadow-raised backdrop:bg-black/30">
      <form onSubmit={submit} className="grid gap-4 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="upload-h" className="font-display text-2xl font-medium">Analyse your own data</h2>
            <p className="mt-1 text-sm text-muted">Drop up to three files of one sample. Concord reads each one and works out which technique it is.</p>
          </div>
          <button type="button" onClick={onClose} className="btn btn-ghost -mr-2 -mt-1 px-2" aria-label="Close"><X size={18} weight="bold" /></button>
        </div>
        <label className={LABEL}>Composition
          <CompositionField name="composition" value={composition} onChange={setComposition}
            onBlur={() => items.length && inspect(items.map((i) => i.file))} onPick={(f) => items.length && inspect(items.map((i) => i.file), f)} />
        </label>

        <label onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); add(e.dataTransfer.files); }}
          className={`grid cursor-pointer place-items-center gap-1 rounded-md border-2 border-dashed px-4 py-6 text-center transition-colors duration-150 ${over ? "border-accent bg-accent/5" : "border-line hover:border-meta"}`}>
          <FileArrowUp size={28} weight="duotone" className="text-accent" aria-hidden />
          <span className="text-sm font-medium text-fg">{busy === "reading" ? "Reading the files…" : "Drop XRD, PDF or XAFS files here"}</span>
          <span className="text-xs text-meta">or click to browse; two columns of numbers, any extension</span>
          <input type="file" multiple className="sr-only" onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
        </label>

        {items.length ? (
          <ul className="grid gap-2" aria-live="polite">
            {items.map((it, n) => (
              <li key={it.file.name + n} className="flex items-start gap-3 rounded-md bg-bg p-3">
                <Spark p={it.info?.preview ?? null} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium" translate="no">{it.file.name}</span>
                    {it.info?.technique ? <span className={`rounded-full px-1.5 text-[11px] font-semibold ${it.info.confidence === "high" ? "bg-ok-bg text-ok" : "bg-warn-bg text-warn"}`}>{it.info.confidence}</span> : null}
                  </div>
                  <p className="text-xs text-muted">{it.info ? it.info.reason : "Not read yet."}</p>
                  {it.info?.warnings.map((w) => <p key={w} className="text-xs text-warn">{w}</p>)}
                </div>
                <label className="sr-only" htmlFor={`kind-${n}`}>Technique of {it.file.name}</label>
                <select id={`kind-${n}`} value={it.kind} onChange={(e) => setItems((xs) => xs.map((x, j) => (j === n ? { ...x, kind: e.target.value as Item["kind"] } : x)))}
                  className="field w-auto py-1 text-[13px]">
                  {KINDS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                  <option value="skip">Leave out</option>
                </select>
                <button type="button" onClick={() => setItems((xs) => xs.filter((_, j) => j !== n))} className="btn btn-ghost px-1.5" aria-label={`Remove ${it.file.name}`}><Trash size={16} /></button>
              </li>
            ))}
          </ul>
        ) : null}

        {xafs ? (
          <label className={LABEL}>Absorption edge
            <input name="edge" required value={edge} onChange={(e) => setEdge(e.target.value)} placeholder="Pt L3…" autoComplete="off" className="field font-normal" />
            {xafs.info?.edge && edge === xafs.info.edge ? <span className="text-xs font-normal text-meta">Found from the energy range of {xafs.file.name}.</span> : null}
          </label>
        ) : null}
        {used.length ? (
          <details className="text-sm text-muted">
            <summary className="cursor-pointer">Instrument values (otherwise read from the file headers or assumed)</summary>
            <div className="mt-2 grid gap-3 sm:grid-cols-2">
              <label className={LABEL}>X-ray wavelength (Å)
                <input name="wavelength_A" type="number" step="any" min="0.1" max="3" defaultValue={head("wavelength_A") as number | undefined} placeholder="1.5406" className="field font-normal" />
              </label>
              <label className={LABEL}>PDF Qmax (Å⁻¹)
                <input name="qmax" type="number" step="any" min="5" max="60" defaultValue={head("qmax") as number | undefined} placeholder="25" className="field font-normal" />
              </label>
            </div>
          </details>
        ) : null}

        {used.length > 0 && new Set(used.map((i) => i.kind.split("_")[0])).size < 3 ? (
          <p className="flex items-start gap-1.5 text-xs text-muted">
            <Sparkle size={14} weight="fill" className="mt-px shrink-0 text-accent" aria-hidden />
            Missing a technique? After the analysis, the GAN we trained locally can generate the ones you did not measure from the fitted model, clearly marked as not measured.
          </p>
        ) : null}
        {error ? <p role="alert" className="rounded-md bg-bad-bg p-3 text-sm text-bad">{error}</p> : null}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
          <button disabled={!!busy || !used.length} className="btn btn-primary"><UploadSimple size={16} weight="bold" aria-hidden />{busy === "uploading" ? "Uploading…" : "Upload and analyse"}</button>
        </div>

        <div className="grid gap-2 border-t border-line pt-4">
          <span className="eyebrow">No data yet?</span>
          <div className="grid gap-2 sm:grid-cols-2">
            <button type="button" onClick={onExample} className="flex items-start gap-3 rounded-md bg-bg p-3 text-left transition-colors duration-150 hover:bg-surface-warm">
              <Play size={20} weight="duotone" className="mt-0.5 shrink-0 text-accent" aria-hidden />
              <span><span className="block text-sm font-medium">Try an example</span><span className="text-xs text-muted">A Pt sample with a planted fault, already analysed and reviewed.</span></span>
            </button>
            <button type="button" onClick={onPlan} className="flex items-start gap-3 rounded-md bg-bg p-3 text-left transition-colors duration-150 hover:bg-surface-warm">
              <Compass size={20} weight="duotone" className="mt-0.5 shrink-0 text-accent" aria-hidden />
              <span><span className="block text-sm font-medium">Plan a measurement</span><span className="text-xs text-muted">Simulate the candidates and see which technique tells them apart.</span></span>
            </button>
          </div>
        </div>
      </form>
    </dialog>
  );
}
