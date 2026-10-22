"""concord — one command per job.

  concord analyze <folder> [--composition Pt3Co]   tools + checks C1-C6 + visual inspection + critic loop → report
  concord analyze <folder> --fast                  tools + checks only (no LLM), seconds per sample
  concord priors Pt3Co [--phase TiO2-anatase]      literature priors with DOIs (OpenAlex, Crossref, arXiv)
  concord eval                                     evaluation on dataset v1 (same as `make eval`)
  concord health                                   is the LLM endpoint up?

A sample folder holds any of xrd.xy, pdf.gr, xafs_mu.dat / xafs_chi.k, plus sample.json (or --composition).
"""
import argparse
import json
import sys
from pathlib import Path

from concord.config import ROOT


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="concord", description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 2)[2])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyse one sample folder")
    a.add_argument("folder", type=Path)
    a.add_argument("--composition", help="needed when the folder has no sample.json, e.g. Pt3Co")
    a.add_argument("--fast", action="store_true", help="deterministic tools and checks only (no LLM)")
    a.add_argument("--out", type=Path, help="output folder (default results/runs/<folder name>)")
    p = sub.add_parser("priors", help="mine literature priors for a composition")
    p.add_argument("composition")
    p.add_argument("--phase", help="identified phase, e.g. TiO2-anatase (searches that polymorph)")
    p.add_argument("--refresh", action="store_true", help="search again instead of using the cache")
    sub.add_parser("eval", help="run the evaluation (make eval)")
    sub.add_parser("health", help="check the LLM endpoint")
    args = ap.parse_args(argv)

    if args.cmd == "health":
        from concord.llm.client import LLMClient
        print(json.dumps(LLMClient.from_env().health(), indent=1))
        return 0
    if args.cmd == "priors":
        from concord.literature import describe, mine
        r = mine(args.composition, args.phase, refresh=args.refresh)
        print(f"{r['material']}: {r['papers']} papers, {r['sentences']} sentences, {len(r['priors'])} priors"
              + (f" (incomplete: {', '.join(r['errors'])})" if r["errors"] else ""))
        for x in r["priors"]:
            print(f"  {describe(x):<40} doi:{x['doi']}  «{x['snippet'][:100]}»")
        return 0
    if args.cmd == "eval":
        from concord.evaluate import main as eval_main
        sys.argv = ["concord eval"]
        return eval_main()
    out = args.out or ROOT / "results" / "runs" / args.folder.resolve().name
    if args.fast:
        from concord.agents.pipeline import report_markdown
        from concord.analysis import analyze, to_json
        from concord.literature import for_result
        from concord.vision.check import plots
        res = analyze(args.folder, composition=args.composition)
        a = to_json(res)
        a["priors"] = for_result(a)  # cached priors only: fast mode stays offline
        out.mkdir(parents=True, exist_ok=True)
        (out / "analysis.json").write_text(json.dumps(a))
        plots(res, out)
        (out / "report.md").write_text(md := report_markdown({"analysis": a}))
        print(md)
        for k, v in res["errors"].items():
            print(f"  error in {k}: {v}")
        for x in res["inputs"].get("assumed", []):
            print(f"  assumed {x} (not in the file headers)")
        print(f"→ {out / 'report.md'}, plots and analysis.json in {out} ({res['timings_s']['total']} s)")
        return 0
    from concord.agents.pipeline import run_sample
    from concord.llm.client import EndpointDown
    try:
        r = run_sample(args.folder, out, composition=args.composition)
    except EndpointDown as exc:
        print(f"LLM endpoint unreachable: {exc}\nRun with --fast for the deterministic analysis without agents.")
        return 2
    print(r["report_md"])
    print(f"→ {Path(r['out_dir']) / 'report.md'}  ({r['wall_s']} s, {r['rounds']} critic round(s), "
          f"{r['llm']['llm_calls']} LLM calls, {r['llm']['prompt_tokens'] + r['llm']['completion_tokens']} tokens)")
    if r["unsupported_numbers"]:
        print(f"  number guard: not found in the evidence: {', '.join(r['unsupported_numbers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
