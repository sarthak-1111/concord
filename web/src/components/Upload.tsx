"use client";
import { useEffect, useRef, useState } from "react";
import { UploadSimple, X } from "@phosphor-icons/react";
import { API } from "@/lib/api";

const LABEL = "grid min-w-0 gap-1 text-sm font-medium text-fg-2";
const FILE = "block w-full min-w-0 text-sm text-muted file:mr-3 file:rounded-sm file:border-0 file:bg-surface-warm file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-fg-2 hover:file:bg-line";

export default function Upload({ open, onClose, onUploaded }: { open: boolean; onClose: () => void; onUploaded: (id: string) => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [xafs, setXafs] = useState(false);

  useEffect(() => {
    const d = ref.current;
    if (open && d && !d.open) d.showModal();
    if (!open && d?.open) d.close();
  }, [open]);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;  // React clears currentTarget once the handler awaits
    setBusy(true);
    setError(undefined);
    try {
      const r = await fetch(`${API}/api/uploads`, { method: "POST", body: new FormData(form) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.error ?? r.statusText);
      form.reset();
      setXafs(false);
      onUploaded(d.sample);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog ref={ref} onClose={onClose} aria-labelledby="upload-h"
      className="m-auto w-[min(520px,calc(100vw-32px))] overscroll-contain rounded-lg bg-surface p-0 text-fg shadow-raised backdrop:bg-black/30">
      <form onSubmit={submit} className="grid gap-4 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="upload-h" className="font-display text-2xl font-medium">Analyse your own data</h2>
            <p className="mt-1 text-sm text-muted">Any of XRD, PDF and XAFS of one sample. The tools run as soon as it is uploaded.</p>
          </div>
          <button type="button" onClick={onClose} className="btn btn-ghost -mr-2 -mt-1 px-2" aria-label="Close"><X size={18} weight="bold" /></button>
        </div>
        <label className={LABEL}>Composition
          <input name="composition" required placeholder="Pt3Co…" autoComplete="off" spellCheck={false} className="field font-normal" />
        </label>
        <div className="grid gap-3">
          <label className={LABEL}>XRD<span className="text-xs font-normal text-meta">2θ or Q, intensity</span><input name="xrd" type="file" className={FILE} /></label>
          <label className={LABEL}>PDF<span className="text-xs font-normal text-meta">G(r)</span><input name="pdf" type="file" className={FILE} /></label>
          <label className={LABEL}>XAFS<span className="text-xs font-normal text-meta">μ(E) or χ(k)</span>
            <input name="xafs" type="file" className={FILE} onChange={(e) => setXafs(!!e.target.files?.length)} />
          </label>
        </div>
        {xafs ? (
          <div className="grid gap-3 rounded-md bg-bg p-3 sm:grid-cols-2">
            <fieldset className="grid gap-1 text-sm text-fg-2">
              <legend className="mb-1 font-medium">The XAFS file contains</legend>
              <label className="flex items-center gap-2"><input type="radio" name="xafs_kind" value="mu" defaultChecked className="accent-[var(--accent)]" /> μ(E)</label>
              <label className="flex items-center gap-2"><input type="radio" name="xafs_kind" value="chi" className="accent-[var(--accent)]" /> χ(k)</label>
            </fieldset>
            <label className={LABEL}>Absorption edge
              <input name="edge" required placeholder="Pt L3…" autoComplete="off" className="field font-normal" />
            </label>
          </div>
        ) : null}
        <details className="text-sm text-muted">
          <summary className="cursor-pointer">Instrument values (otherwise read from the file headers or assumed)</summary>
          <div className="mt-2 grid gap-3 sm:grid-cols-2">
            <label className={LABEL}>X-ray wavelength (Å)
              <input name="wavelength_A" type="number" step="any" min="0.1" max="3" placeholder="1.5406" className="field font-normal" />
            </label>
            <label className={LABEL}>PDF Qmax (Å⁻¹)
              <input name="qmax" type="number" step="any" min="5" max="60" placeholder="25" className="field font-normal" />
            </label>
          </div>
        </details>
        {error ? <p role="alert" className="rounded-md bg-bad-bg p-3 text-sm text-bad">{error}</p> : null}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
          <button disabled={busy} className="btn btn-primary"><UploadSimple size={16} weight="bold" aria-hidden />{busy ? "Uploading…" : "Upload and analyse"}</button>
        </div>
      </form>
    </dialog>
  );
}
