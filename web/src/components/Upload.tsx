"use client";
import { useState } from "react";
import { API } from "@/lib/api";

const INPUT = "w-full rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm outline-none focus:border-[#d68e2f] focus:ring-2 focus:ring-[#d68e2f]/30";
const LABEL = "grid min-w-0 gap-0.5 text-xs text-slate-600";

export default function Upload({ onUploaded }: { onUploaded: (id: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [xafs, setXafs] = useState(false);

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
    <details className="rounded-lg border border-slate-200 bg-white/70 p-2 text-sm">
      <summary className="cursor-pointer font-medium text-slate-800">Analyse your own data</summary>
      <form onSubmit={submit} className="mt-2 grid min-w-0 gap-2">
        <label className={LABEL}>Composition
          <input name="composition" required placeholder="Pt3Co" className={INPUT} />
        </label>
        <label className={LABEL}>XRD pattern (2θ or Q, intensity)
          <input name="xrd" type="file" className="w-full min-w-0 text-xs" />
        </label>
        <label className={LABEL}>PDF, G(r)
          <input name="pdf" type="file" className="w-full min-w-0 text-xs" />
        </label>
        <label className={LABEL}>XAFS
          <input name="xafs" type="file" className="w-full min-w-0 text-xs" onChange={(e) => setXafs(!!e.target.files?.length)} />
        </label>
        {xafs ? (
          <>
            <fieldset className="flex gap-3 text-xs text-slate-700">
              <legend className="sr-only">XAFS file contains</legend>
              <label><input type="radio" name="xafs_kind" value="mu" defaultChecked /> μ(E)</label>
              <label><input type="radio" name="xafs_kind" value="chi" /> χ(k)</label>
            </fieldset>
            <label className={LABEL}>Absorption edge
              <input name="edge" required placeholder="Pt L3" className={INPUT} />
            </label>
          </>
        ) : null}
        <details className="text-xs text-slate-600">
          <summary className="cursor-pointer">Instrument (otherwise read from the file headers or assumed)</summary>
          <div className="mt-1 grid gap-2">
            <label className={LABEL}>X-ray wavelength (Å)
              <input name="wavelength_A" type="number" step="any" min="0.1" max="3" placeholder="1.5406" className={INPUT} />
            </label>
            <label className={LABEL}>PDF Qmax (Å⁻¹)
              <input name="qmax" type="number" step="any" min="5" max="60" placeholder="25" className={INPUT} />
            </label>
          </div>
        </details>
        <button disabled={busy} className="rounded-lg bg-[#d6512f] px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-[#c24728] disabled:opacity-50">
          {busy ? "Uploading…" : "Upload and analyse"}
        </button>
        {error ? <p role="alert" className="text-xs text-red-700">{error}</p> : null}
      </form>
    </details>
  );
}
