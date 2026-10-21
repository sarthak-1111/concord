"""make eval: analyse the test and fault splits, score the results against the ground truth and compare the
metrics with the thresholds registered in eval/config.yaml. Writes results/eval.json and results/eval.md and
exits 1 when a threshold is missed. Only this module reads ground truth; concord.analysis never does."""
import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

from concord.analysis import analyze, to_json
from concord.config import ROOT
from concord.tools.pdfcalc import spherical_envelope

CHECK_IDS = ("C1", "C2", "C3", "C4", "C5", "C6")


def _analyse(folder: str) -> dict:
    t0 = time.time()
    res = to_json(analyze(folder))
    res["wall_s"] = round(time.time() - t0, 2)
    return res


def exafs_size_nm(n_fit: float, n_bulk: float, r: float) -> float | None:
    """Sphere diameter from first-shell truncation, N = N_bulk·γ0(r; D) (Calvin et al. 2005, doi:10.1063/1.2044730)."""
    ratio = n_fit / n_bulk
    if not 0.05 < ratio < 0.995:
        return None
    return brentq(lambda d: float(spherical_envelope(r, d)) - ratio, r * 1.01, 1e5) / 10


def score(res: dict, meta: dict, split: str) -> dict:
    gt = meta["ground_truth"]
    statuses = {c["id"]: c["status"] for c in res["checks"]}
    row = {"sample_id": res["sample_id"], "split": split, "faults": [f["type"] for f in meta["faults"]],
           "notes": gt["notes"], "true_phase": gt["phases"][0]["name"], "phase": res["phase"], "checks": statuses,
           "flagged": "fail" in statuses.values(), "warned": bool({"warn", "fail"} & set(statuses.values())),
           "runtime_s": res["wall_s"], "errors": res["errors"]}
    absorber = res["inputs"]["instrument"]["xafs"]["edge"].split()[0]
    true_shells = {s["neighbor"]: s for s in gt["shells"] if s["absorber"] == absorber}
    if res.get("exafs"):
        row["exafs"] = [{"pair": f"{absorber}-{s['neighbor']}", "R_err": s["R_A"] - true_shells[s["neighbor"]]["R_A"],
                         "N_err": s["N"] - true_shells[s["neighbor"]]["N"]}
                        for s in res["exafs"]["fit"]["shells"] if not s.get("extra") and s["neighbor"] in true_shells]
    if res.get("pdf"):
        model = res["pdf"]["fits"][0]["shells"].get(absorber or "", [])
        row["pdf_R_err"] = [m["R_A"] - true_shells[m["neighbor"]]["R_A"] for m in model if m["neighbor"] in true_shells]
    if res.get("xanes") and absorber in gt["oxidation_state"]:
        row["valence_err"] = res["xanes"]["valence"] - gt["oxidation_state"][absorber]
    if gt["size_nm"]:
        d = gt["size_nm"]
        sizes = {"xrd": (res.get("xrd") or {}).get("sphere_diameter_nm"),
                 "pdf": res["pdf"]["fits"][0]["psize_nm"] if res.get("pdf") else None}
        metal = res.get("exafs") and all(s["neighbor"] != "O" for s in res["exafs"]["fit"]["shells"])
        if metal:  # oxide particles keep their first shell at the surface; only metals truncate it
            fit_n = sum(s["N"] for s in res["exafs"]["fit"]["shells"] if not s.get("extra"))
            model = res["pdf"]["fits"][0]["shells"].get(absorber, [])
            if model:
                sizes["exafs"] = exafs_size_nm(fit_n, sum(m["N"] for m in model), min(m["R_A"] for m in model))
        row["size_rel_err"] = {k: (v - d) / d for k, v in sizes.items() if v}
    return row


def metrics(rows: list[dict]) -> dict:
    clean = [r for r in rows if not r["faults"]]
    faulty = [r for r in rows if r["faults"]]
    mean = lambda xs: float(np.mean(xs)) if xs else None
    flat = lambda key, sub: [abs(e[sub]) for r in clean for e in r.get(key, [])]
    m = {
        "n_clean": len(clean), "n_faults": len(faulty),
        "phase_id_accuracy": mean([r["phase"] == r["true_phase"] for r in clean]),
        "exafs_bond_length_mae_A": mean(flat("exafs", "R_err")),
        "pdf_bond_length_mae_A": mean([abs(e) for r in clean for e in r.get("pdf_R_err", [])]),
        "exafs_cn_mae": mean(flat("exafs", "N_err")),
        "oxidation_accuracy": mean([abs(r["valence_err"]) <= 0.5 for r in clean if "valence_err" in r]),
        "fault_detection_rate": mean([r["flagged"] for r in faulty]),
        "fault_warn_or_fail_rate": mean([r["warned"] for r in faulty]),
        "false_alarm_rate": mean([r["flagged"] for r in clean]),
        "warn_rate_clean": mean([r["warned"] for r in clean]),
        "checks_reported": mean([all(c in r["checks"] for c in CHECK_IDS) for r in rows]),
        "runtime_s_mean": mean([r["runtime_s"] for r in rows]),
        "runtime_s_max": max((r["runtime_s"] for r in rows), default=None),
        "llm_tokens_per_sample": 0,  # the deterministic pipeline makes no LLM calls; agents report their own
    }
    for tech in ("xrd", "pdf", "exafs"):
        errs = [abs(r["size_rel_err"][tech]) for r in clean if tech in r.get("size_rel_err", {})]
        m[f"size_rel_mae_{tech}"] = mean(errs)
        m[f"size_n_{tech}"] = len(errs)
    m["fault_detection_by_type"] = {t: mean([r["flagged"] for r in faulty if t in r["faults"]]) for t in sorted({t for r in faulty for t in r["faults"]})}
    return m


def judge(m: dict, thresholds: dict) -> dict:
    out = {}
    for name, rule in thresholds.items():
        v = m.get(name)
        ok = v is not None and (v >= rule["min"] if "min" in rule else v <= rule["max"])
        out[name] = {"value": v, **rule, "pass": bool(ok)}
    return out


def markdown(m: dict, verdict: dict, rows: list[dict], cfg: dict) -> str:
    fmt = lambda v: "n/a" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
    sym = {"pass": "✓", "warn": "!", "fail": "✗", "skip": "–"}
    lines = [f"# Concord evaluation — {cfg['dataset']} ({', '.join(cfg['splits'])})", "",
             f"{m['n_clean']} clean test samples, {m['n_faults']} fault samples. Thresholds from `eval/config.yaml`.", "",
             "| metric | value | threshold | result |", "|---|---|---|---|"]
    for name, v in verdict.items():
        thr = f"≥ {v['min']}" if "min" in v else f"≤ {v['max']}"
        lines.append(f"| {name} | {fmt(v['value'])} | {thr} | {'pass' if v['pass'] else '**FAIL**'} |")
    lines += ["", "Other numbers: " + ", ".join(f"{k} {fmt(m[k])}" for k in
              ("size_rel_mae_exafs", "fault_warn_or_fail_rate", "warn_rate_clean", "runtime_s_max", "llm_tokens_per_sample")), "",
              "## Fault detection by type", "", "| fault | detected |", "|---|---|"]
    lines += [f"| {t} | {fmt(v)} |" for t, v in m["fault_detection_by_type"].items()]
    lines += ["", "## Per sample", "", "| sample | split | fault | phase (true) | " + " | ".join(CHECK_IDS) + " | s |",
              "|---|---|---|---|" + "---|" * len(CHECK_IDS) + "---|"]
    for r in rows:
        checks = " | ".join(sym.get(r["checks"].get(c), "?") for c in CHECK_IDS)
        lines.append(f"| {r['sample_id']} | {r['split']} | {', '.join(r['faults']) or '–'} | {r['phase']} ({r['true_phase']}) | {checks} | {r['runtime_s']:.0f} |")
    lines += ["", "✓ pass  ! warn  ✗ fail  – skipped (technique missing)"]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", type=Path, default=ROOT / "eval" / "config.yaml")
    ap.add_argument("--out", type=Path, default=ROOT / "results")
    ap.add_argument("--limit", type=int, default=None, help="evaluate only the first N samples (smoke test)")
    ap.add_argument("--dataset", default=None, help="override the dataset folder (development runs, e.g. dataset_big)")
    ap.add_argument("--splits", nargs="+", default=None, help="override the splits")
    ap.add_argument("--min-index", type=int, default=0, help="skip samples below this number (dataset_big s0000-s0059 = v1)")
    a = ap.parse_args()
    cfg = yaml.safe_load(a.config.read_text())
    cfg["dataset"], cfg["splits"] = a.dataset or cfg["dataset"], a.splits or cfg["splits"]
    root = ROOT / cfg["dataset"]
    splits = json.loads((root / "splits.json").read_text())
    todo = [(sid, sp) for sp in cfg["splits"] for sid in splits[sp] if int(sid[1:]) >= a.min_index][: a.limit]
    folders = [str(root / "samples" / sid) for sid, _ in todo]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=cfg.get("workers", 4)) as pool:
        results = list(pool.map(_analyse, folders))
    runs = a.out / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    rows = []
    for (sid, sp), res in zip(todo, results):
        (runs / f"{sid}.json").write_text(json.dumps(res))
        rows.append(score(res, json.loads((root / "samples" / sid / "sample.json").read_text()), sp))
    m = metrics(rows)
    verdict = judge(m, cfg["thresholds"])
    report = {"dataset": cfg["dataset"], "splits": cfg["splits"], "wall_s": round(time.time() - t0, 1), "metrics": m,
              "thresholds": verdict, "passed": all(v["pass"] for v in verdict.values()), "samples": rows}
    (a.out / "eval.json").write_text(json.dumps(to_json(report), indent=1))
    (a.out / "eval.md").write_text(markdown(m, verdict, rows, cfg))
    print(markdown(m, verdict, rows, cfg).split("## Fault")[0])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
