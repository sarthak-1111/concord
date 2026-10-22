export const API = process.env.NEXT_PUBLIC_API_HTTP ?? "http://localhost:8000";

export async function fetcher(path: string) {
  const r = await fetch(API + path);
  if (!r.ok) throw Object.assign(new Error((await r.json().catch(() => ({}))).error ?? r.statusText), { status: r.status });
  return r.json();
}

export type Status = "pass" | "warn" | "fail" | "skip";

export type Check = {
  id: string;
  name: string;
  status: Status;
  explanation: string;
  values?: Record<string, unknown>;
  tolerance?: Record<string, unknown>;
};

export type SampleRow = { id: string; composition: string; techniques: string[]; split: string | null; analysed: boolean; agents: boolean };

export type LogEntry = {
  round: number;
  id: string;
  objection: string;
  claim?: number | null;
  cited: string[];
  action?: string | null;
  args?: Record<string, string>;
  status: string;
  finding: string;
  result_id?: string;
};

export type VirtualXafs = {
  label: string;
  absorber: string;
  edge: string;
  candidates: string[];
  members: number;
  theta_K_range: [number, number];
  recommendation: string;
  vs_measured?: { rfactor_R: number; band_coverage_k: number; r_window: [number, number] } | null;
  per_candidate?: Record<string, number> | null;
};

export type Prior = {
  quantity: string;
  pair?: string;
  element?: string;
  value: number | [number, number];
  uncertainty?: number | null;
  unit: string;
  doi: string;
  title: string;
  year: number | null;
  source: string;
  snippet: string;
};

export type Vision = {
  accepted: boolean;
  verdict: string;
  inspector: string;
  issues: Record<string, string>[];
  numerical: { ok: boolean; reason: string };
  steps: { iteration: number; action: string; finding: string; kept: boolean }[];
};

export type View = {
  sample_id: string;
  composition: string;
  techniques: string[];
  assumed: string[];
  phase: string | null;
  checks: Check[];
  errors: Record<string, string>;
  timings_s: Record<string, number>;
  evidence: Record<string, unknown>;
  plots: Record<string, string>;
  virtual_xafs: VirtualXafs | null;
  agents: {
    model: { phase: string | null; summary: string; claims: { statement: string; evidence: string[] }[] } | null;
    log: LogEntry[];
    rounds: number;
    confirmed: string[];
    unsupported_numbers: string[];
    wall_s: number;
    llm: { llm_calls?: number; prompt_tokens?: number; completion_tokens?: number };
    stale: boolean;
    error?: string | null;
  } | null;
  vision: Record<string, Vision> | null;
  report_md: string;
  priors: Prior[];
};
