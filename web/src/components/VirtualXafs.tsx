import { API, type VirtualXafs as V } from "@/lib/api";
import { fmt } from "@/components/Value";

export default function VirtualXafs({ v, plot, reason }: { v: V | null; plot?: string; reason?: string }) {
  if (!v) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Virtual XAFS</h2>
        No prediction: {reason ?? "it needs a PDF-refined model"}.
      </section>
    );
  }
  return (
    <section aria-labelledby="vx-h" className="rounded-xl border-2 border-dashed border-red-300 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="vx-h" className="text-lg font-semibold text-slate-900">Virtual XAFS</h2>
        <span className="rounded bg-red-700 px-2 py-0.5 text-xs font-bold tracking-wide text-white">{v.label}</span>
      </div>
      <p className="mt-1 text-sm text-slate-700">
        {v.absorber} {v.edge} EXAFS computed with FEFF from the PDF-refined model ({v.candidates.join(", ")}); {v.members} ensemble
        members over lattice, displacement, size and equally good candidates; Debye temperature {fmt(v.theta_K_range[0])}–{fmt(v.theta_K_range[1])} K.
        The band is the 5–95 % range.
      </p>
      {plot ? <img src={API + plot} alt={`Predicted ${v.absorber} ${v.edge} EXAFS band, ${v.label}`} className="mt-3 w-full rounded border border-slate-100" /> : null}
      <p className="mt-3 rounded bg-amber-50 p-2 text-sm text-amber-900"><span className="font-semibold">Recommendation: </span>{v.recommendation}</p>
      {v.vs_measured ? (
        <p className="mt-2 text-sm text-slate-700">
          Against the measured spectrum: R-factor {fmt(v.vs_measured.rfactor_R)} in R {v.vs_measured.r_window.join("–")} Å
          (≤ 0.05 is a good EXAFS fit; a large value means the PDF model and the EXAFS disagree).
        </p>
      ) : null}
      {v.per_candidate && Object.keys(v.per_candidate).length ? (
        <p className="mt-1 text-xs text-slate-600">
          Per candidate (used by C7): {Object.entries(v.per_candidate).map(([c, r]) => `${c} R ${fmt(r)}`).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
