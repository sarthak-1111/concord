"""Concord web API. Extends CrystaLenz's run-and-stream server (POST /api/runs, then WS /api/runs/{id}/stream) with
sample listing, per-sample result views and plot files. Run it with `make api` (binds to localhost).

  GET  /api/samples                  samples in dataset/samples and uploads/ (metadata only, never ground truth)
  POST /api/uploads                  multipart: composition + any of xrd, pdf, xafs files (+ edge, wavelength, qmax) → {sample}
  GET  /api/samples/{id}             result view: checks, evidence, plots, critic log, report (404 until analysed)
  GET  /api/samples/{id}/export      ?format=json (full analysis + agent run) or ?format=md (report)
  POST /api/samples/{id}/priors      search the open literature for the sample's material (cached afterwards)
  POST /api/runs                     {sample, mode: "fast" | "full"} → {run_id}
  WS   /api/runs/{run_id}/stream     progress events, then {type: "result", payload: view}, then {type: "done"}
  GET  /files/{id}/...               plot images
"""
import asyncio
import json
import re
import shutil
import uuid
from pathlib import Path

from pymatgen.core import Element

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
from concord.analysis import analyze, infer_inputs, load_inputs, to_json
from concord.config import ROOT
from concord.vision.check import plots

SAMPLES = ROOT / "dataset" / "samples"
UPLOADS = ROOT / "uploads"
MAX_UPLOAD = 20 * 2**20  # bytes per request
RUNS = ROOT / "results" / "runs"
ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
RUN_REQUESTS: dict[str, dict] = {}
RUNS.mkdir(parents=True, exist_ok=True)


def _foreign(request: Request) -> bool:
    """A browser POST from another site: CORS blocks reading the reply, not the request itself."""
    return request.headers.get("origin") not in (None, *ORIGINS)


def _folder(sid: str) -> Path | None:
    for root in (SAMPLES, UPLOADS):
        folder = (root / sid).resolve()
        if folder.parent == root.resolve() and folder.is_dir():
            return folder
    return None


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
                          "stale": {k[6:]: v["status"] for k, v in ag["evidence"].items() if k.startswith("check.")}
                          != {c["id"]: c["status"] for c in a["checks"]}},  # the critic saw other check results
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
    for root in (SAMPLES, UPLOADS):
        for d in sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []:
            meta = load_inputs(d)
            rows.append({"id": d.name, "composition": meta["composition"], "techniques": meta["techniques"],
                         "split": "uploaded" if root == UPLOADS else split_of.get(d.name),
                         "analysed": (RUNS / f"{d.name}.json").exists(), "agents": (RUNS / d.name / "agents.json").exists()})
    return JSONResponse(rows)


def _number(form, key: str, lo: float, hi: float) -> float | None:
    raw = str(form.get(key) or "").strip()
    if not raw:
        return None
    v = float(raw)  # ValueError for text: reported as a bad request
    if not lo <= v <= hi:
        raise ValueError(f"{key} {v} is outside {lo}-{hi}")
    return v


async def upload(request: Request) -> JSONResponse:
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if int(request.headers.get("content-length") or 0) > MAX_UPLOAD:
        return JSONResponse({"error": f"upload larger than {MAX_UPLOAD // 2**20} MB"}, status_code=413)
    async with request.form(max_files=3, max_fields=10) as form:  # closes the spooled files
        return await _save_upload(form)


async def _save_upload(form) -> JSONResponse:
    """A user's own data as a sample folder: each file saved under the name the analysis expects, the form's
    instrument values added to its '# key=value' header (they override the file's own), metadata inferred."""
    folder = None
    try:
        comp = str(form.get("composition") or "").strip()
        if not re.fullmatch(r"(?:[A-Z][a-z]?(?:\d+(?:\.\d+)?)?){1,6}", comp):
            raise ValueError("give the composition as a formula, e.g. Pt3Co or CeO2")
        elements = set(re.findall(r"[A-Z][a-z]?", comp))
        if not all(Element.is_valid_symbol(e) for e in elements):
            raise ValueError(f"unknown element in {comp}")
        files = {k: form[k] for k in ("xrd", "pdf", "xafs") if getattr(form.get(k), "filename", None)}
        if not files:
            raise ValueError("upload at least one of the XRD, PDF and XAFS files")
        edge = str(form.get("edge") or "").strip().replace(" ", "_")
        if "xafs" in files and not (re.fullmatch(r"([A-Z][a-z]?)_(K|L1|L2|L3)", edge) and edge.split("_")[0] in elements):
            raise ValueError("XAFS needs the edge of an element in the composition, e.g. Pt L3 or Co K")
        heads = {"xrd": {"wavelength_A": _number(form, "wavelength_A", 0.1, 3.0)}, "pdf": {"qmax": _number(form, "qmax", 5.0, 60.0)},
                 "xafs": {"edge": edge}}
        names = {"xrd": "xrd.xy", "pdf": "pdf.gr", "xafs": "xafs_chi.k" if form.get("xafs_kind") == "chi" else "xafs_mu.dat"}
        folder = UPLOADS / f"u{uuid.uuid4().hex[:7]}"
        folder.mkdir(parents=True)
        for kind, f in files.items():
            lines = (await f.read()).decode("utf-8", errors="replace").splitlines(keepends=True)
            n = next((i for i, line in enumerate(lines) if not line.startswith("#")), len(lines))
            head = " ".join(f"{k}={v}" for k, v in heads[kind].items() if v is not None)
            (folder / names[kind]).write_text("".join(lines[:n]) + (f"# {head}\n" if head else "") + "".join(lines[n:]))
        (folder / "sample.json").write_text(json.dumps(infer_inputs(folder, comp), indent=1))
    except ValueError as exc:
        if folder:
            shutil.rmtree(folder, ignore_errors=True)
        return JSONResponse({"error": str(exc)}, status_code=400)
    return JSONResponse({"sample": folder.name})


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
            res = await asyncio.to_thread(analyze, _folder(sid))
            cached.write_text(json.dumps(to_json(res)))
        if req["mode"] == "full":
            await send("status", "visual inspection and generator–critic loop (gpt-oss)")
            await run_sample_async(_folder(sid), RUNS / sid, on_event=on_event, precomputed=cached)
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
    Route("/api/uploads", upload, methods=["POST"]),
    Route("/api/runs", create_run, methods=["POST"]),
    WebSocketRoute("/api/runs/{run_id}/stream", stream_run),
    Mount("/files", StaticFiles(directory=RUNS), name="files"),
])
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
