import type { Check, View } from "@/lib/api";
import { fmt } from "@/components/Value";

const SHORT: Record<string, string> = { C1: "phase", C2: "bond lengths", C3: "coordination", C4: "oxidation state", C5: "disorder", C6: "size", C7: "joint fit" };
const list = (xs: string[]) => (xs.length < 3 ? xs.join(" and ") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);

/** One plain line on the whole sample, from the check statuses and fitted values only. */
export function verdict(v: View): { tone: "ok" | "warn" | "bad"; head: string; detail: string } {
  const fails = v.checks.filter((c) => c.status === "fail"), warns = v.checks.filter((c) => c.status === "warn");
  const ev = v.evidence as Record<string, any>;
  const best = ev["pdf.best"] && ev[`pdf.fit.${ev["pdf.best"]}`];
  const size = best?.psize_nm ?? ev["xrd.size"]?.sphere_diameter_nm;
  const sz = typeof size === "number" ? `, about ${fmt(size)} nm` : "";
  const what = v.phase ? `${v.phase}${sz}` : `no candidate phase fits${sz}`;
  const techs = v.techniques.map((t) => t.toUpperCase());
  if (fails.length) return { tone: "bad", head: "Conflict", detail: `${list(fails.map((c) => SHORT[c.id] ?? c.name))} disagree${fails.length === 1 ? "s" : ""} between techniques. ${v.phase ? "Best model: " : ""}${v.phase ? what : what[0].toUpperCase() + what.slice(1)}.` };
  if (warns.length) return { tone: "warn", head: "Mostly consistent", detail: `${what}; ${list(warns.map((c) => SHORT[c.id] ?? c.name))} need${warns.length === 1 ? "s" : ""} a look.` };
  return { tone: "ok", head: "Consistent", detail: `${what}, agreed by ${list(techs)}.` };
}

export type Settle = { action: string; args: Record<string, string>; label: string };

/** The critic's deterministic re-runs that test a flagged check, as buttons the user can press. */
export function settlers(c: Check, v: View): Settle[] {
  const vals = (c.values ?? {}) as Record<string, any>;
  const cands: string[] = ((v.evidence as any).sample?.candidates ?? []).filter((x: string) => x !== v.phase);
  const other = vals.pdf_runner_up ?? cands[0];
  const oxide = /O(?![a-z])/.test(v.composition);
  const has = (t: string) => v.techniques.includes(t) || (t === "exafs" && v.techniques.includes("xafs") && "exafs.fit" in v.evidence);
  const refit: Settle[] = other && has("pdf") ? [{ action: "pdf_fit_candidate", args: { candidate: other }, label: `Refit the PDF as ${other}` }] : [];
  const scan: Settle[] = has("exafs") ? [{ action: "exafs_window_scan", args: {}, label: "Scan the EXAFS k-range" }] : [];
  const shell: Settle[] = has("exafs") && !oxide ? [{ action: "exafs_probe_shell", args: { neighbor: "O", distance_A: "2.0" }, label: "Probe an O shell at 2.0 Å" }] : [];
  const envelope: Settle[] = has("pdf") ? [{ action: "pdf_toggle_envelope", args: {}, label: "PDF envelope on or off" }] : [];
  const phase2: Settle[] = has("xrd") ? [{ action: "xrd_add_phase", args: {}, label: "Add a second XRD phase" }] : [];
  const strongest: Settle[] = has("xrd") ? [{ action: "xrd_size_strongest", args: {}, label: "XRD size from the strongest peak" }] : [];
  const menu: Record<string, Settle[]> = {
    C1: [...refit, ...phase2], C2: [...scan, ...shell], C3: [...scan, ...shell], C4: shell,
    C5: [...scan, ...envelope], C6: [...strongest, ...envelope], C7: refit,
  };
  return (menu[c.id] ?? []).slice(0, 2);
}

/** Where a number in a reply comes from: the first evidence value it rounds to (the number guard's rule). */
export function sources(evidence: Record<string, unknown>, prefer: string[]): (raw: string) => { id: string; path: string; value: number } | undefined {
  const leaves: { id: string; path: string; value: number }[] = [];
  const walk = (id: string, path: string, v: unknown) => {
    if (typeof v === "number" && isFinite(v)) leaves.push({ id, path, value: v });
    else if (Array.isArray(v)) v.forEach((x, i) => walk(id, `${path}[${i}]`, x));
    else if (v && typeof v === "object") Object.entries(v).forEach(([k, x]) => walk(id, path ? `${path}.${k}` : k, x));
  };
  for (const id of [...prefer.filter((p) => p in evidence), ...Object.keys(evidence).filter((k) => !prefer.includes(k))]) walk(id, "", evidence[id]);
  return (raw: string) => {
    const pct = raw.endsWith("%"), s = raw.replace("%", "").replace("−", "-"), x = parseFloat(s);
    const dec = s.includes(".") ? s.split(".")[1].length : 0;
    const match = (c: number, d: number, v: number) => Math.abs(c - v) <= 0.5 * 10 ** -d + 1e-12 || (v !== 0 && Math.abs(c - v) / Math.abs(v) <= 0.005);
    return leaves.find(({ value }) => match(x, dec, value) || match(Math.abs(x), dec, Math.abs(value)) || (pct && match(x / 100, dec + 2, value)));
  };
}

export const NUMBER = /(?<![\w.])([-+−]?\d+(?:\.\d+)?)(?!\w|\.\d)(\s?%)?/g;
