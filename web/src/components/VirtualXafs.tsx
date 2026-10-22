import { Lightbulb } from "@phosphor-icons/react";
import { type VirtualXafs as V } from "@/lib/api";
import { fmt } from "@/components/Value";
import { Figure } from "@/components/TechniqueTabs";

export default function VirtualXafs({ v, plot, reason }: { v: V | null; plot?: string; reason?: string }) {
  if (!v) {
    return (
      <section className="text-sm text-muted">
        <h2 className="font-display text-xl font-medium text-fg">Virtual XAFS</h2>
        <p className="mt-1">No prediction: {reason ?? "it needs a PDF-refined model"}.</p>
      </section>
    );
  }
  return (
    <section aria-labelledby="vx-h" className="grid gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <h2 id="vx-h" className="font-display text-xl font-medium">Virtual XAFS</h2>
        <span className="rounded-sm bg-bad px-2 py-0.5 text-[11px] font-bold tracking-wide text-accent-on">{v.label}</span>
      </div>
      <p className="max-w-[70ch] text-sm text-fg-2">
        {v.absorber} {v.edge} EXAFS computed with FEFF from the PDF-refined model ({v.candidates.join(", ")}). {v.members} ensemble
        members over lattice, displacement, size and equally good candidates; Debye temperature {fmt(v.theta_K_range[0])} to {fmt(v.theta_K_range[1])} K.
        The band is the 5 to 95 % range.
      </p>
      {plot ? (
        <div className="rounded-md border-2 border-dashed border-bad/50 p-1">
          <Figure src={plot} alt={`Predicted ${v.absorber} ${v.edge} EXAFS band, ${v.label}`} />
        </div>
      ) : null}
      <div className="flex gap-2 rounded-md bg-warn-bg p-3 text-sm text-fg-2">
        <Lightbulb size={18} weight="fill" className="mt-0.5 shrink-0 text-warn" aria-hidden />
        <p><span className="font-semibold text-fg">Recommendation. </span>{v.recommendation}</p>
      </div>
      {v.vs_measured ? (
        <p className="text-sm text-fg-2">
          Against the measured spectrum: R-factor <span className="tabular-nums">{fmt(v.vs_measured.rfactor_R)}</span> in R {v.vs_measured.r_window.join(" to ")} Å
          (0.05 or less is a good EXAFS fit; a large value means the PDF model and the EXAFS disagree).
        </p>
      ) : null}
      {v.per_candidate && Object.keys(v.per_candidate).length ? (
        <p className="text-xs text-meta">
          Per candidate, used by C7: {Object.entries(v.per_candidate).map(([c, r]) => `${c} R ${fmt(r)}`).join(", ")}
        </p>
      ) : null}
    </section>
  );
}
