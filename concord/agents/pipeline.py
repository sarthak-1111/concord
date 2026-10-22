"""Concord orchestration on Google ADK.

analysis (deterministic tools + checks C1–C6) → vision (plots, eye module or fallback judge)
→ loop[generator → critic → resolver] (≤ critic.max_rounds) → reporter.
The generator writes the structural model from the evidence bundle; the critic (separate prompt, evidence and
claims only) objects with citations and may request a re-run from a fixed menu; the resolver discards uncited
objections, re-runs the requested tools, adds their results to the evidence and runs the number guard. The
loop ends when nothing valid is left to answer. The report's tables are assembled from data, not written by the LLM.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import AsyncGenerator, Literal

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

from concord.agents.evidence import _r, bundle, number_guard
from concord import literature
from concord.agents.resolver import ACTIONS, run_action
from concord.analysis import analyze, load_inputs, to_json
from concord.config import ROOT, settings
from concord.llm.adk_model import model_for
from concord.trace import CURRENT_TRACE, Trace
from concord.vision.check import inspect_fits

RUNS: dict[str, dict] = {}  # ADK session id → raw analysis (structures, paths); session state holds only JSON


class Claim(BaseModel):
    statement: str
    evidence: list[str] = Field(description="ids from the evidence bundle that support the statement")


class StructuralModel(BaseModel):
    phase: str | None = Field(description="identified phase (a candidate name), or null when no candidate fits")
    summary: str = Field(description="two to four sentences: the structural model and how the techniques agree")
    claims: list[Claim]
    responses: list[str] = Field(default_factory=list, description="how each objection of the previous round was handled")


class Objection(BaseModel):
    claim: int | None = Field(description="index of the claim objected to; null for something the claims leave out")
    text: str
    evidence: list[str] = Field(description="ids from the evidence bundle that support the objection")
    action: Literal[tuple(ACTIONS)] | None = Field(description="re-run that would settle the objection, or null")
    args: dict[str, str] = Field(default_factory=dict)


class Critique(BaseModel):
    objections: list[Objection]
    verdict: Literal["accept", "revise"]


class ReportText(BaseModel):
    headline: str = Field(description="one sentence: what the sample is")
    techniques: dict[str, str] = Field(description="one or two sentences per technique present: xrd, pdf, exafs, xanes")
    limitations: list[str]


GENERATOR = """You are the analyst of Concord, which combines X-ray diffraction (XRD), the pair distribution function (PDF)
and X-ray absorption (EXAFS, XANES) of one sample into one structural model.
You get an EVIDENCE bundle (JSON, id -> value) computed by deterministic, tested code, including the cross-technique
checks check.C1 ... check.C6, and possibly OBJECTIONS from a reviewer with the results of tool re-runs.
Rules:
1. Every number you write is copied from the evidence (rounding allowed). Never compute, convert or estimate a number.
2. Every claim lists the evidence ids that support it.
3. Each check with status warn or fail gets a claim that explains it physically, or says the data deviate from every candidate.
4. If check.C1 fails because no candidate fits, set phase to null.
5. Answer each objection in `responses`: change the claim, or show with evidence ids why it stands.
6. prior.* entries are literature values for other samples (with DOI): context for a claim, never proof of this sample.
Reply with JSON only."""

CRITIC = """You are an independent reviewer of a structural analysis of X-ray data. You see only the evidence bundle and
the analyst's claims. Look for claims the evidence does not support, warn or fail checks that the claims ignore or explain
away without evidence, and numbers that are not in the evidence.
Rules:
1. Each objection cites evidence ids that exist in the bundle; objections without valid ids are discarded.
2. When a re-run could settle the objection, request one action from this menu, else action null:
{menu}
3. A check that passes close to its tolerance, or a value that hints at something the model does not contain (an
   oxidised XANES component or non-zero valence in a metallic model, a lattice moved away from the database value,
   a size or coordination number that the techniques do not share), deserves an objection with a re-run that tests it.
4. Do not repeat an objection that an earlier re-run settled; the log shows them.
5. prior.* entries are literature values for other samples (with DOI). Cite one to motivate a re-run (for example a
   probe shell at the literature distance), never as proof on its own.
6. If the claims are sound, return no objections and verdict "accept".
Reply with JSON only."""

REPORTER = """Write the prose parts of the final report of a Concord analysis for a materials scientist: a one-sentence
headline, one or two sentences per technique present (keys xrd, pdf, exafs, xanes), and the limitations. Base it on the
final model, the evidence and the objection log. Copy every number from them; never add one. Reply with JSON only."""


def _dump(x) -> str:
    return json.dumps(x, separators=(",", ":"), default=str)


def _generator_instruction(ctx) -> str:
    st = ctx.state
    parts = [GENERATOR, "EVIDENCE:\n" + _dump(st["evidence"])]
    last = [e for e in st.get("log", []) if e["round"] == st.get("round", 0)]
    if st.get("model"):
        parts.append("YOUR PREVIOUS MODEL:\n" + _dump(st["model"]))
    if last:
        parts.append("OBJECTIONS AND RE-RUNS OF THE LAST ROUND:\n" + _dump(last))
    return "\n\n".join(parts)


def _critic_instruction(ctx) -> str:
    st = ctx.state
    menu = "\n".join(f"- {k}: {v}" for k, v in ACTIONS.items())
    return "\n\n".join([CRITIC.replace("{menu}", menu), "EVIDENCE:\n" + _dump(st["evidence"]),
                        "CLAIMS:\n" + _dump(st.get("model")), "LOG OF EARLIER ROUNDS:\n" + _dump(st.get("log", []))])


def _reporter_instruction(ctx) -> str:
    st = ctx.state
    return "\n\n".join([REPORTER, "FINAL MODEL:\n" + _dump(st.get("model")), "EVIDENCE:\n" + _dump(st["evidence"]),
                        "OBJECTION LOG:\n" + _dump(st.get("log", []))])


def _event(ctx: InvocationContext, author: str, text: str, delta: dict, escalate: bool = False) -> Event:
    return Event(invocation_id=ctx.invocation_id, author=author, branch=ctx.branch,
                 content=types.Content(role="model", parts=[types.Part(text=text)]),
                 actions=EventActions(state_delta=delta, escalate=escalate or None))


class AnalysisAgent(BaseAgent):
    """Runs the deterministic tools and checks; puts the evidence bundle into the session state."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        folder, comp = Path(ctx.session.state["sample_folder"]), ctx.session.state.get("composition")
        pre = ctx.session.state.get("precomputed")  # analysis JSON from an earlier run of the same tools (eval)
        res = json.loads(Path(pre).read_text()) if pre else await asyncio.to_thread(analyze, folder, None, comp)
        try:
            res["priors"] = await asyncio.to_thread(literature.for_result, res, True)
        except Exception as exc:  # literature is context: a failed search never stops the analysis
            res["priors"], res.setdefault("errors", {})["priors"] = [], f"literature search failed ({type(exc).__name__})"
        RUNS[ctx.session.id] = {"folder": folder, "meta": load_inputs(folder, comp), "res": res, "out_dir": ctx.session.state["out_dir"]}
        statuses = ", ".join(f"{c['id']} {c['status']}" for c in res["checks"])
        yield _event(ctx, self.name, f"analysis done: phase {res['phase']}; {statuses}",
                     {"analysis": to_json(res), "evidence": bundle(to_json(res)), "log": [], "round": 0})


class VisionAgent(BaseAgent):
    """Plots every fit, has the eye module (or the fallback judge) inspect it, and adds the verdicts as evidence."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        run = RUNS[ctx.session.id]
        vis = await asyncio.to_thread(inspect_fits, run["res"], Path(ctx.session.state["out_dir"]), run)
        analysis = to_json(run["res"])  # a kept fix changes the fits and the checks
        ev = bundle(analysis)
        for tech, v in vis.items():
            if "visual" not in v:  # the virtual XAFS plot is shown, not judged
                continue
            ev[f"vision.{tech}"] = _r({"accepted": v["accepted"], "verdict": v["visual"]["verdict"], "inspector": v["visual"]["inspector"],
                                       "issues": v["visual"]["issues"], "numerical": v["numerical"],
                                       "durbin_watson": v["features"]["durbin_watson"], "structured_regions": v["features"]["structured_regions"],
                                       "unexplained_peaks": v["features"]["unexplained_peaks"], "fixes_tried": v["steps"]})
        text = "; ".join(f"{t} {'accepted' if v['accepted'] else 'rejected'} ({v['visual']['inspector']})"
                         + "".join(f", {s['action']} {'kept' if s['kept'] else 'reverted'}" for s in v["steps"]) for t, v in vis.items() if "visual" in v)
        yield _event(ctx, self.name, f"visual inspection: {text}", {"analysis": analysis, "evidence": ev, "vision": to_json(vis)})


class ResolverAgent(BaseAgent):
    """Discards uncited objections, re-runs requested tools, number-guards the analyst, ends the loop when done."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        st = ctx.session.state
        run, ev, rnd = RUNS[ctx.session.id], dict(st["evidence"]), st.get("round", 0) + 1
        model = st.get("model") or {}
        entries = []
        for i, o in enumerate((st.get("critique") or {}).get("objections", [])):
            cited = [e for e in o.get("evidence", []) if e in ev]
            entry = {"round": rnd, "id": f"R{rnd}.{i + 1}", "objection": o["text"], "claim": o.get("claim"), "cited": cited,
                     "action": o.get("action"), "args": o.get("args") or {}}
            if not cited:
                entry.update(status="discarded", finding="no valid evidence id cited")
            elif o.get("action"):
                result, finding = await asyncio.to_thread(run_action, run, o["action"], o.get("args"))
                key = f"rerun.{entry['id']}.{o['action']}"
                ev[key] = _r(to_json({k: v for k, v in result.items() if not k.startswith("_")}))
                entry.update(status="confirmed" if result.get("confirms") else "not confirmed", finding=finding, result_id=key)
            else:
                entry.update(status="open", finding="no re-run requested; the analyst must answer it")
            entries.append(entry)
        text = " ".join([model.get("summary", "")] + [c["statement"] for c in model.get("claims", [])])
        if bad := number_guard(text, ev):
            entries.append({"round": rnd, "id": f"R{rnd}.guard", "objection": f"numbers not in the evidence: {', '.join(bad)}",
                            "claim": None, "cited": [], "action": None, "args": {}, "status": "number_guard",
                            "finding": "copy numbers from the evidence or remove them"})
        live = [e for e in entries if e["status"] != "discarded"]
        msg = f"round {rnd}: {len(live)} objection(s) to answer, {len(entries) - len(live)} discarded"
        yield _event(ctx, self.name, msg, {"evidence": ev, "log": st.get("log", []) + entries, "round": rnd}, escalate=not live)


def root_agent() -> SequentialAgent:
    generator = LlmAgent(name="generator", model=model_for("generator"), instruction=_generator_instruction,
                         output_schema=StructuralModel, output_key="model", include_contents="none", disallow_transfer_to_parent=True, disallow_transfer_to_peers=True)
    critic = LlmAgent(name="critic", model=model_for("critic"), instruction=_critic_instruction,
                      output_schema=Critique, output_key="critique", include_contents="none", disallow_transfer_to_parent=True, disallow_transfer_to_peers=True)
    loop = LoopAgent(name="debate", sub_agents=[generator, critic, ResolverAgent(name="resolver")],
                     max_iterations=settings()["critic"]["max_rounds"])
    reporter = LlmAgent(name="reporter", model=model_for("report"), instruction=_reporter_instruction,
                        output_schema=ReportText, output_key="report_text", include_contents="none", disallow_transfer_to_parent=True, disallow_transfer_to_peers=True)
    return SequentialAgent(name="concord", sub_agents=[AnalysisAgent(name="analysis"), VisionAgent(name="vision"), loop, reporter])


def report_markdown(st: dict) -> str:
    """Final report: LLM prose (number-guarded) plus tables built from the data."""
    a, model, text = st["analysis"], st.get("model") or {}, st.get("report_text") or {}
    sym = {"pass": "pass", "warn": "**warn**", "fail": "**FAIL**", "skip": "skip"}
    lines = [f"# Concord report — {a['sample_id']} ({a['inputs']['composition']})", "",
             f"**{text.get('headline', '')}**", "", f"Phase: **{model['phase'] if model else a['phase']}**", "", model.get("summary", ""), "",
             "## Key numbers (from the tools)", ""] + key_numbers(a)
    if text.get("techniques"):
        lines += ["", "## Evidence by technique", ""] + [f"- **{k.upper()}**: {v}" for k, v in text["techniques"].items()]
    lines += ["", "## Cross-technique checks", "", "| check | status | explanation |", "|---|---|---|"]
    lines += [f"| {c['id']} {c['name']} | {sym[c['status']]} | {c['explanation']} |" for c in a["checks"]]
    if v := a.get("virtual_xafs"):
        lines += ["", f"## Virtual XAFS — {v['label']}", "",
                  f"{v['absorber']} {v['edge']} EXAFS computed with FEFF from the PDF-refined model ({', '.join(v['candidates'])}; "
                  f"{v['members']} ensemble members, Debye temperature {v['theta_K_range'][0]:.0f}–{v['theta_K_range'][1]:.0f} K). "
                  + v["recommendation"]]
        if m := v.get("vs_measured"):
            lines += ["", f"Against the measured spectrum: R-factor {m['rfactor_R']:.4f} in R {m['r_window'][0]}–{m['r_window'][1]} Å."]
    if pri := a.get("priors"):
        lines += ["", "## Literature priors (other samples: context, not constraints)", ""]
        lines += [f"- {literature.describe(p)}, [doi:{p['doi']}](https://doi.org/{p['doi']}) ({p['year']}): «{p['snippet'][:220]}»" for p in pri]
    if not model:
        lines += ["", "Fast mode: tools and checks only; the generator–critic loop was not run."]
        return "\n".join(lines) + "\n"
    lines += ["", "## Claims", ""] + [f"{i}. {c['statement']} _(evidence: {', '.join(c['evidence'])})_" for i, c in enumerate(model.get("claims", []))]
    lines += ["", "## Objections and resolutions", ""]
    log = st.get("log", [])
    lines += ["| id | objection | cited | re-run | finding | status |", "|---|---|---|---|---|---|"] if log else ["The critic raised no objections."]
    lines += [f"| {e['id']} | {e['objection']} | {', '.join(e['cited']) or '–'} | {e['action'] or '–'} | {e['finding']} | {e['status']} |" for e in log]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in text.get("limitations", [])]
    return "\n".join(lines) + "\n"


def key_numbers(a: dict) -> list[str]:
    """One line per technique, straight from the analysis result."""
    out = []
    if x := a.get("xrd"):
        r = x["ranking"][0]
        out.append(f"- **XRD**: best match {r['phase']} (profile correlation {r['profile_corr']:.3f}, {100 * r['obs_area_fraction_explained']:.0f} % "
                   f"of the peak area explained); sphere diameter {x['sphere_diameter_nm']:.1f} nm from {x['n_indexed']} indexed reflections")
    if p := a.get("pdf"):
        f = p["fits"][0]
        lat = ", ".join(f"{k} {v:.4f} Å" for k, v in f["lattice"].items() if k in "abc" and (k == "a" or abs(v - f["lattice"]["a"]) > 1e-6))
        size = f"particle diameter {f['psize_nm']:.1f} nm" if f.get("psize_nm") else "no finite-size envelope (bulk)"
        out.append(f"- **PDF**: {f['candidate']} refines to Rw {f['rw']:.3f}; {lat}; U_iso "
                   + ", ".join(f"{el} {u:.4f} Å²" for el, u in f["uiso"].items()) + f"; {size}")
    if e := a.get("exafs"):
        shells = "; ".join(f"{e['absorber']}–{s['neighbor']} N {s['N']:.1f}" + (f" ± {s['N_err']:.1f}" if s.get("N_err") else "")
                           + f" at {s['R_A']:.3f} Å, σ² {s['sigma2']:.4f} Å²" + (" (shell not in the model)" if s.get("extra") else "")
                           for s in e["fit"]["shells"])
        out.append(f"- **EXAFS** ({e['absorber']} {e['edge']}): {shells}; R-factor {e['fit']['rfactor']:.4f}")
    if n := a.get("xanes"):
        out.append(f"- **XANES**: {n['absorber']} valence {n['valence']:.2f} from a linear combination of standards, "
                   f"{n['valence_edge']:.2f} from the edge position")
    if b := a.get("bvs"):
        out.append(f"- **Bond valence** (PDF model): {b['valence']:.2f}")
    return out or ["- no technique produced a result"]


async def run_sample_async(folder: str | Path, out: Path | None = None, on_event=None, composition: str | None = None,
                           precomputed: Path | None = None) -> dict:
    folder = Path(folder).resolve()
    out = Path(out) if out else ROOT / "results" / "runs" / folder.name
    out.mkdir(parents=True, exist_ok=True)
    trace = Trace(out / "trace.jsonl")
    token = CURRENT_TRACE.set(trace)
    t0 = time.time()
    try:
        runner = InMemoryRunner(agent=root_agent(), app_name="concord")
        session = await runner.session_service.create_session(app_name="concord", user_id="local", state={"sample_folder": str(folder), "out_dir": str(out), "composition": composition,
                                                                         "precomputed": str(precomputed) if precomputed else None})
        msg = types.Content(role="user", parts=[types.Part(text=f"Analyse the sample in {folder}.")])
        async for event in runner.run_async(user_id="local", session_id=session.id, new_message=msg):
            if on_event:
                await on_event(event)
        st = (await runner.session_service.get_session(app_name="concord", user_id="local", session_id=session.id)).state
    finally:
        CURRENT_TRACE.reset(token)
    md = report_markdown(st)
    prose = " ".join([(st.get("report_text") or {}).get("headline", "")] + list((st.get("report_text") or {}).get("techniques", {}).values())
                     + list((st.get("report_text") or {}).get("limitations", [])) + [(st.get("model") or {}).get("summary", "")])
    result = {"sample_id": st["analysis"]["sample_id"], "model": st.get("model"), "log": st.get("log", []), "rounds": st.get("round", 0),
              "confirmed": [e["id"] for e in st.get("log", []) if e["status"] == "confirmed"],
              "unsupported_numbers": number_guard(prose, st["evidence"]), "report_md": md, "wall_s": round(time.time() - t0, 1),
              "llm": trace.totals(), "out_dir": str(out)}
    (out / "report.md").write_text(md)
    (out / "agents.json").write_text(json.dumps({**result, "evidence": st["evidence"], "vision": st.get("vision")}, default=str, indent=1))
    (out / "analysis.json").write_text(json.dumps(st["analysis"]))
    RUNS.pop(session.id, None)
    return result


def run_sample(folder: str | Path, out: Path | None = None, composition: str | None = None) -> dict:
    return asyncio.run(run_sample_async(folder, out, composition=composition))
