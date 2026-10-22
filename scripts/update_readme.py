"""Write the results table of results/eval.json into README.md, between the results markers (run by `make eval`)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "phase_id_accuracy": "Phase identification accuracy",
    "exafs_bond_length_mae_A": "EXAFS bond length, mean abs. error (Å)",
    "pdf_bond_length_mae_A": "PDF bond length, mean abs. error (Å)",
    "exafs_cn_mae": "EXAFS coordination number, mean abs. error",
    "oxidation_accuracy": "Oxidation state within 0.5",
    "size_rel_mae_xrd": "Size from XRD, mean rel. error",
    "size_rel_mae_pdf": "Size from PDF, mean rel. error",
    "fault_detection_rate": "Planted faults detected (a check fails)",
    "false_alarm_rate": "False alarms on clean samples",
    "checks_reported": "C1–C6 reported for every sample",
    "runtime_s_mean": "Runtime per sample, mean (s)",
    "virtual_xafs_rfactor_median": "Virtual EXAFS vs spectrum, median R-factor",
}


def table(ev: dict) -> str:
    rows = ["| metric | value | threshold | |", "|---|---|---|---|"]
    for key, t in ev["thresholds"].items():
        bound = f"≥ {t['min']}" if "min" in t else f"≤ {t['max']}"
        rows.append(f"| {LABELS.get(key, key)} | {t['value']:.3g} | {bound} | {'pass' if t['pass'] else '**FAIL**'} |")
    m = ev["metrics"]
    n_clean = sum(1 for s in ev["samples"] if s["split"] != "faults")
    head = (f"`make eval` on dataset v1 ({', '.join(ev['splits'])}: {n_clean} clean samples, {len(ev['samples']) - n_clean} with "
            f"planted faults), thresholds from `eval/config.yaml`. Overall: **{'pass' if ev['passed'] else 'FAIL'}**.")
    extra = [f"Virtual EXAFS against the hidden spectrum (XAFS withheld): median R-factor {m['virtual_xafs_hidden_rfactor_median']:.3f}"
             if m.get("virtual_xafs_hidden_rfactor_median") is not None else "",
             f"Faults that only raise a warning: {m['fault_warn_or_fail_rate'] - m['fault_detection_rate']:.0%} of fault samples."
             if m.get("fault_warn_or_fail_rate") is not None else "",
             f"With the critic (`make eval-agents`): faults flagged by a check or a re-run-confirmed objection "
             f"{m['fault_detection_rate_agents']:.0%}, clean samples flagged {m['false_alarm_rate_agents']:.0%}, numbers in the "
             f"agents' prose not found in the evidence: {m['unsupported_numbers_total']}, {m['agent_wall_s_mean'] / 60:.0f} min "
             f"and {m['llm_tokens_per_sample'] / 1000:.0f}k tokens per sample." if m.get("fault_detection_rate_agents") is not None else ""]
    return "\n".join([head, "", *rows, "", *[f"{x}  " for x in extra if x], "", "Per-sample details: [`results/eval.md`](results/eval.md)."])


def main() -> None:
    ev = json.loads((ROOT / "results" / "eval.json").read_text())
    readme = ROOT / "README.md"
    text = readme.read_text()
    new, n = re.subn(r"<!-- results:start -->.*?<!-- results:end -->",
                     lambda _: f"<!-- results:start -->\n{table(ev)}\n<!-- results:end -->", text, flags=re.S)
    if n:
        readme.write_text(new)
    print("README results table " + ("updated" if n else "not found: add <!-- results:start --> / <!-- results:end --> markers"))


if __name__ == "__main__":
    main()
