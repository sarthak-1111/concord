"""Concord web API. Extends CrystaLenz's run-and-stream server (POST /api/runs, then WS /api/runs/{id}/stream) with
sample listing, per-sample result views and plot files. Run it with `make api` (binds to localhost).

  GET  /api/samples                  samples in dataset/samples (metadata only, never ground truth)
  GET  /api/samples/{id}             result view: checks, evidence, plots, critic log, report (404 until analysed)
  GET  /api/samples/{id}/export      ?format=json (full analysis + agent run) or ?format=md (report)
  POST /api/samples/{id}/priors      search the open literature for the sample's material (cached afterwards)
  POST /api/runs                     {sample, mode: "fast" | "full"} → {run_id}
  WS   /api/runs/{run_id}/stream     progress events, then {type: "result", payload: view}, then {type: "done"}
  GET  /files/{id}/...               plot images
"""
import asyncio
import json
import uuid
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from concord import literature
from concord.agents.evidence import bundle
from concord.agents.pipeline import report_markdown, run_sample_async
from concord.analysis import analyze, load_inputs, to_json
from concord.config import ROOT
from concord.vision.check import plots

SAMPLES = ROOT / "dataset" / "samples"
RUNS = ROOT / "results" / "runs"
ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
RUN_REQUESTS: dict[str, dict] = {}
RUNS.mkdir(parents=True, exist_ok=True)


def _foreign(request: Request) -> bool:
    """A browser POST from another site: CORS blocks reading the reply, not the request itself."""
    return request.headers.get("origin") not in (None, *ORIGINS)


def _folder(sid: str) -> Path | None:
    folder = (SAMPLES / sid).resolve()
    return folder if folder.parent == SAMPLES.resolve() and folder.is_dir() else None


def _agents(sid: str) -> dict | None:
    p = RUNS / sid / "agents.json"
    return json.loads(p.read_text()) if p.exists() else None


def _plots(sid: str, a: dict, mtime: float) -> dict[str, str]:
    """Plot URLs; re-rendered when the analysis is newer than the last rendering."""
    index = RUNS / sid / "plots.json"
    if index.exists() and index.stat().st_mtime >= mtime:
        names = json.loads(index.read_text())
    else:
        names = {k: Path(v).name for k, v in plots(a, RUNS / sid).items()}
        index.write_text(json.dumps(names))
    return {k: f"/files/{sid}/{n}?v={int(index.stat().st_mtime)}" for k, n in names.items()}


def view(sid: str) -> dict | None:
    cached, after_agents = RUNS / f"{sid}.json", RUNS / sid / "analysis.json"
    if after_agents.exists() and (not cached.exists() or after_agents.stat().st_mtime >= cached.stat().st_mtime):
        cached = after_agents  # the agents' copy carries the fixes the visual inspection kept
    if not cached.exists():
        return None
    a, mtime = json.loads(cached.read_text()), cached.stat().st_mtime
    ag = _agents(sid)
    v = a.get("virtual_xafs")
    priors = literature.for_result(a)
    return {
        "sample_id": sid, "composition": a["inputs"]["composition"], "techniques": a["inputs"]["techniques"],
        "assumed": a["inputs"].get("assumed", []), "phase": a["phase"], "checks": a["checks"], "errors": a["errors"],
        "timings_s": a["timings_s"], "evidence": ag["evidence"] if ag else bundle(a), "plots": _plots(sid, a, mtime),
        "virtual_xafs": v and {k: v.get(k) for k in ("label", "absorber", "edge", "candidates", "members", "theta_K_range",
                                                      "recommendation", "vs_measured", "per_candidate")},
        "agents": ag and {**{k: ag.get(k) for k in ("model", "log", "rounds", "confirmed", "unsupported_numbers", "wall_s", "llm")},
                          "stale": (RUNS / sid / "agents.json").stat().st_mtime < mtime},  # analysis re-run after the agents
        "vision": ag and {t: {"accepted": x["accepted"], "verdict": x["visual"]["verdict"], "inspector": x["visual"]["inspector"],
                              "issues": x["visual"]["issues"], "numerical": x["numerical"], "steps": x.get("steps", [])}
                          for t, x in (ag.get("vision") or {}).items() if "visual" in x},
        "report_md": ag["report_md"] if ag else report_markdown({"analysis": {**a, "priors": priors}}),
        "priors": priors,
    }


async def samples(request: Request) -> JSONResponse:
    split_file = SAMPLES.parent / "splits.json"
    splits = json.loads(split_file.read_text()) if split_file.exists() else {}
    split_of = {s: name for name, ids in splits.items() for s in ids}
    rows = []
    for d in sorted(p for p in SAMPLES.iterdir() if p.is_dir()) if SAMPLES.exists() else []:
        meta = load_inputs(d)
        rows.append({"id": d.name, "composition": meta["composition"], "techniques": meta["techniques"], "split": split_of.get(d.name),
                     "analysed": (RUNS / f"{d.name}.json").exists(), "agents": (RUNS / d.name / "agents.json").exists()})
    return JSONResponse(rows)


async def sample(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    if not _folder(sid):
        return JSONResponse({"error": f"no sample {sid}"}, status_code=404)
    v = await asyncio.to_thread(view, sid)
    return JSONResponse(v) if v else JSONResponse({"error": "not analysed yet"}, status_code=404)


async def export(request: Request) -> Response:
    sid, fmt = request.path_params["sid"], request.query_params.get("format", "json")
    cached = RUNS / f"{sid}.json"
    if not _folder(sid) or not cached.exists() or fmt not in ("json", "md"):
        return JSONResponse({"error": "nothing to export"}, status_code=404)
    head = {"Content-Disposition": f'attachment; filename="concord_{sid}.{fmt}"'}
    if fmt == "md":
        return Response((await asyncio.to_thread(view, sid))["report_md"], media_type="text/markdown", headers=head)
    body = {"analysis": json.loads(cached.read_text()), "agents": _agents(sid)}
    return Response(json.dumps(body, indent=1), media_type="application/json", headers=head)


async def mine_priors(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    cached = RUNS / f"{sid}.json"
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not _folder(sid) or not cached.exists():
        return JSONResponse({"error": "analyse the sample first: the search uses its identified phase"}, status_code=404)
    a = json.loads(cached.read_text())
    r = await asyncio.to_thread(literature.mine, a["inputs"]["composition"], a["phase"])
    return JSONResponse({k: r[k] for k in ("material", "papers", "sentences", "priors", "errors")})


async def create_run(request: Request) -> JSONResponse:
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    data = await request.json()
    sid, mode = data.get("sample", ""), data.get("mode", "fast")
    if not _folder(sid) or mode not in ("fast", "full"):
        return JSONResponse({"error": "need an existing sample and mode fast or full"}, status_code=400)
    run_id = str(uuid.uuid4())
    RUN_REQUESTS[run_id] = {"sample": sid, "mode": mode}
    return JSONResponse({"run_id": run_id})


async def stream_run(ws: WebSocket) -> None:
    if ws.headers.get("origin") not in ORIGINS:  # CORS does not cover WebSockets; runs cost LLM time
        await ws.close(code=1008)
        return
    await ws.accept()
    req = RUN_REQUESTS.pop(ws.path_params["run_id"], None)

    async def send(kind: str, payload=None) -> None:
        await ws.send_json({"type": kind, "payload": payload})

    async def on_event(event) -> None:
        text = " ".join(p.text for p in (event.content.parts if event.content else []) if p.text)
        if text:
            await send("event", {"author": event.author, "content": {"parts": [{"text": text[:4000]}]}})

    try:
        if req is None:
            await send("error", "unknown run id")
            return
        sid, cached = req["sample"], RUNS / f"{req['sample']}.json"
        if req["mode"] == "fast" or not cached.exists():
            await send("status", "running the tools and checks: XRD, PDF, EXAFS, XANES, virtual XAFS, C1–C7")
            res = await asyncio.to_thread(analyze, SAMPLES / sid)
            cached.write_text(json.dumps(to_json(res)))
        if req["mode"] == "full":
            await send("status", "visual inspection and generator–critic loop (gpt-oss)")
            await run_sample_async(SAMPLES / sid, RUNS / sid, on_event=on_event, precomputed=cached)
        await send("result", await asyncio.to_thread(view, sid))
        await send("done")
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # reported to the page; LLM errors carry no endpoint address
        await send("error", f"{type(exc).__name__}: {exc}")
    finally:
        await ws.close()


app = Starlette(routes=[
    Route("/api/samples", samples),
    Route("/api/samples/{sid}", sample),
    Route("/api/samples/{sid}/export", export),
    Route("/api/samples/{sid}/priors", mine_priors, methods=["POST"]),
    Route("/api/runs", create_run, methods=["POST"]),
    WebSocketRoute("/api/runs/{run_id}/stream", stream_run),
    Mount("/files", StaticFiles(directory=RUNS), name="files"),
])
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
