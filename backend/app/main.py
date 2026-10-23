"""Concord web API. Extends CrystaLenz's run-and-stream server (POST /api/runs, then WS /api/runs/{id}/stream) with
sample listing, per-sample result views and plot files. Run it with `make api` (binds to localhost).

  GET  /api/samples                  samples in dataset/samples and uploads/ (metadata only, never ground truth)
  POST /api/uploads                  multipart: composition + any of xrd, pdf, pdf_iq (raw I(Q), reduced to G(r) with the
                                     default settings), xafs files (+ edge, wavelength, qmax) → {sample}
  GET  /api/samples/{id}             result view: checks, evidence, plots, critic log, report (404 until analysed)
  GET  /api/samples/{id}/export      ?format=json (full analysis + agent run) or ?format=md (report)
  POST /api/samples/{id}/priors      search the open literature for the sample's material (cached afterwards)
  POST /api/samples/{id}/chat        {messages: [{role, content}]} → {answer, cites, suggest, unsupported_numbers}
  GET  /api/samples/{id}/curves      fit curves for interactive plots (data, model, difference, reflections, virtual band)
  POST /api/samples/{id}/actions     {action, args} → one deterministic re-run from the critic's menu: {result, finding}
  POST /api/uploads/inspect          multipart files → per file: detected technique, preview, edge (nothing is saved)
  POST /api/plans                    {composition, candidates?, size_nm?, realistic?} → simulated candidates per technique
                                     and which technique separates them (SIMULATED, NOT MEASURED; never analysed as data)
  GET  /api/samples/{id}/tweak/{t}   the fit settings of technique t (xrd, pdf, exafs) the user can change: {params}
  POST /api/samples/{id}/tweak/{t}   {values} → that fit redone with them: curve, metrics, checks and which ones change
  POST /api/samples/{id}/tweak-apply {overrides: {t: values}} → the whole analysis re-run with them (original kept) → view
  POST /api/samples/{id}/restore     back to the analysis before the user's settings → view
  POST /api/samples/{id}/preprocess {params} → the raw I(Q) (pdf_iq.dat, pdf_bkg.dat) reduced step by step to G(r)
  POST /api/samples/{id}/preprocess/save  {params} → that G(r) with the sample's other data as a new upload: {sample}
  POST /api/samples/{id}/generate    {realistic?} → the techniques the user did not measure, simulated from the fitted model
                                     (+ the GAN's instrument realism); GENERATED, NOT MEASURED, never analysed
  GET  /api/elements                 {phases: {element: [library phases with it as a cation]}} for the periodic table
  GET  /api/gan                      which realism GANs are loaded
  GET  /api/gan/showcase             ?technique=xrd&seed=0 → a real spectrum, its simulation and the GAN's version
  POST /api/runs                     {sample, mode: "fast" | "full"} → {run_id}
  WS   /api/runs/{run_id}/stream     progress events, then {type: "result", payload: view}, then {type: "done"}
  GET  /files/{id}/...               plot images
"""
import asyncio
import os
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
from concord.agents.chat import answer
from concord.agents.evidence import bundle
from concord.agents.pipeline import report_markdown, run_sample_async
from concord.agents.resolver import ACTIONS, run_action
from concord.analysis import _cations, analyze, infer_inputs, load_inputs, to_json
from concord.data_builder.fetch import systems
from concord import gan, generate, planner, tweak
from concord.config import ROOT
from concord.upload_inspect import columns, inspect_file
from concord.tools import pdf as pdft, sq_to_gr
from concord.llm.client import LLMError
from concord.vision.check import plots
from concord.vision.render import fit_curves

SAMPLES = ROOT / "dataset" / "samples"
UPLOADS = ROOT / "uploads"
MAX_UPLOAD = 20 * 2**20  # bytes per request
NUMBERS = re.compile(r"[-+0-9.eE]+(?:[ \t]+[-+0-9.eE]+)+")  # a plain whitespace-separated row of numbers
RUNS = ROOT / "results" / "runs"
ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"] + [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]  # public host
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


def _analysis_file(sid: str) -> Path | None:
    cached, after_agents = RUNS / f"{sid}.json", RUNS / sid / "analysis.json"
    if after_agents.exists() and (not cached.exists() or after_agents.stat().st_mtime >= cached.stat().st_mtime):
        cached = after_agents  # the agents' copy carries the fixes the visual inspection kept
    return cached if cached.exists() else None


def view(sid: str) -> dict | None:
    cached, after_agents = _analysis_file(sid), RUNS / sid / "analysis.json"
    if not cached:
        return None
    a, mtime = json.loads(cached.read_text()), cached.stat().st_mtime
    ag = _agents(sid)
    fresh = ag and cached != after_agents  # analysed again after the critic (e.g. with the user's settings): its numbers win
    v = a.get("virtual_xafs")
    priors = literature.for_result(a)
    folder = _folder(sid)
    return {
        "sample_id": sid, "composition": a["inputs"]["composition"], "techniques": a["inputs"]["techniques"],
        "assumed": a["inputs"].get("assumed", []), "phase": a["phase"], "checks": a["checks"], "errors": a["errors"],
        "timings_s": a["timings_s"], "evidence": {**ag["evidence"], **bundle(a)} if fresh else ag["evidence"] if ag else bundle(a),
        "plots": _plots(sid, a, mtime),
        "virtual_xafs": v and {k: v.get(k) for k in ("label", "absorber", "edge", "candidates", "members", "theta_K_range",
                                                      "recommendation", "vs_measured", "per_candidate")},
        "agents": ag and {**{k: ag.get(k) for k in ("model", "log", "rounds", "confirmed", "unsupported_numbers", "wall_s", "llm", "error")},
                          "stale": {k[6:]: v["status"] for k, v in ag["evidence"].items() if k.startswith("check.")}
                          != {c["id"]: c["status"] for c in a["checks"]}},  # the critic saw other check results
        "vision": ag and {t: {"accepted": x["accepted"], "verdict": x["visual"]["verdict"], "inspector": x["visual"]["inspector"],
                              "issues": x["visual"]["issues"], "numerical": x["numerical"], "steps": x.get("steps", [])}
                          for t, x in (ag.get("vision") or {}).items() if "visual" in x},
        "fitting": (ag.get("fitting") if ag else None) or None,
        "report_md": ag["report_md"] if ag and not fresh else report_markdown({"analysis": {**a, "priors": priors}}),
        "priors": priors,
        "raw_pdf": bool(folder and (folder / "pdf_iq.dat").exists()),
        "user_settings": a["inputs"].get("user_settings") or {},
        "restorable": (RUNS / f"{sid}.original.json").exists(),
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


def _composition(raw) -> str:
    comp = str(raw or "").strip()
    if not re.fullmatch(r"(?:[A-Z][a-z]?(?:\d+(?:\.\d+)?)?){1,6}", comp):
        raise ValueError("give the composition as a formula, e.g. Pt3Co or CeO2")
    if not all(Element.is_valid_symbol(e) for e in re.findall(r"[A-Z][a-z]?", comp)):
        raise ValueError(f"unknown element in {comp}")
    return comp


async def inspect_upload(request: Request) -> JSONResponse:
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if int(request.headers.get("content-length") or 0) > MAX_UPLOAD:
        return JSONResponse({"error": f"upload larger than {MAX_UPLOAD // 2**20} MB"}, status_code=413)
    async with request.form(max_files=4, max_fields=4) as form:
        comp = str(form.get("composition") or "").strip() or None
        files = [f for _, f in form.multi_items() if getattr(f, "filename", None)]
        out = [await asyncio.to_thread(inspect_file, f.filename, await f.read(), comp) for f in files]
    return JSONResponse({"files": out})


async def make_plan(request: Request) -> JSONResponse:
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    d = await request.json()
    try:
        comp, size = _composition(d.get("composition")), float(d.get("size_nm") or 3.0)
        if not 1.0 <= size <= 20.0:
            raise ValueError("particle size must be between 1 and 20 nm")
        cands = [str(c) for c in d["candidates"]] if d.get("candidates") else None
        realism = gan.realism if d.get("realistic") and gan.available()["loaded"] else None
        return JSONResponse(await asyncio.to_thread(planner.plan, comp, cands, size, realism=realism))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


def _tweakable(request: Request) -> tuple[Path, dict] | JSONResponse:
    sid, tech = request.path_params["sid"], request.path_params.get("tech", "xrd")
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    path = _folder(sid) and _analysis_file(sid)
    if not path:
        return JSONResponse({"error": "analyse the sample first"}, status_code=404)
    if tech not in tweak.TECHNIQUES:
        return JSONResponse({"error": f"technique one of {', '.join(tweak.TECHNIQUES)}"}, status_code=400)
    return _folder(sid), json.loads(path.read_text())


async def tweak_params(request: Request) -> JSONResponse:
    t = _tweakable(request)
    if isinstance(t, JSONResponse):
        return t
    try:
        return JSONResponse({"params": to_json(tweak.params(t[1], request.path_params["tech"]))})
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


async def tweak_refit(request: Request) -> JSONResponse:
    t = _tweakable(request)
    if isinstance(t, JSONResponse):
        return t
    values = (await request.json()).get("values") or {}
    if not isinstance(values, dict):
        return JSONResponse({"error": "values must be an object"}, status_code=400)
    try:
        return JSONResponse(to_json(await asyncio.to_thread(tweak.refit, t[0], t[1], request.path_params["tech"], values)))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


async def tweak_apply(request: Request) -> JSONResponse:
    t = _tweakable(request)
    if isinstance(t, JSONResponse):
        return t
    sid, (folder, a) = request.path_params["sid"], t
    new = (await request.json()).get("overrides") or {}
    if not isinstance(new, dict) or not all(isinstance(v, dict) for v in new.values()):
        return JSONResponse({"error": "overrides must be {technique: {setting: value}}"}, status_code=400)
    overrides = {**(a["inputs"].get("user_settings") or {}), **new}  # earlier changes to other techniques stay
    try:
        res = await asyncio.to_thread(tweak.apply, folder, a, overrides)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    cached, original = RUNS / f"{sid}.json", RUNS / f"{sid}.original.json"
    if cached.exists() and not original.exists():
        shutil.copy2(cached, original)  # keeps its time, so a restore gives the agents' copy its precedence back
    cached.write_text(json.dumps(to_json(res)))
    return JSONResponse(await asyncio.to_thread(view, sid))


async def restore(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    original = RUNS / f"{sid}.original.json"
    if not _folder(sid) or not original.exists():
        return JSONResponse({"error": "nothing to restore"}, status_code=404)
    shutil.copy2(original, RUNS / f"{sid}.json")
    original.unlink()
    (RUNS / sid / "plots.json").unlink(missing_ok=True)  # the restored file is older than the plots of the tweak
    return JSONResponse(await asyncio.to_thread(view, sid))


PREPROCESS = {"bkg_scale": (0.0, 1.5), "qmin": (0.1, 3.0), "qmax": (5.0, 60.0), "qmaxinst": (5.0, 60.0), "rpoly": (0.1, 2.5),
              "rmax": (10.0, 60.0), "lorch": None}  # what the user may set, and the allowed range


def _reduce(folder: Path, composition: str, params: dict) -> dict:
    """The folder's raw intensity reduced with the user's params over the file header's instrument values."""
    raw = sq_to_gr.load_raw(folder / "pdf_iq.dat")
    bkg = sq_to_gr.load_raw(folder / "pdf_bkg.dat") if (folder / "pdf_bkg.dat").exists() else None
    h = raw["header"]
    kw = {k: float(h[k]) for k in ("qmin", "qmax", "qmaxinst", "wavelength_A") if h.get(k) is not None}
    for k, v in params.items():
        if k not in PREPROCESS:
            raise ValueError(f"unknown setting {k}; one of {', '.join(PREPROCESS)}")
        if PREPROCESS[k] is None:
            kw[k] = bool(v)
            continue
        lo, hi = PREPROCESS[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
            raise ValueError(f"{k} must be a number from {lo} to {hi}")
        kw[k] = float(v)
    out = sq_to_gr.reduce(raw["q"], raw["i"], composition=composition, background=bkg and (bkg["q"], bkg["i"]), **kw)
    out["instrument"] = {k: h[k] for k in ("qdamp", "qbroad") if h.get(k) is not None}
    return out


async def preprocess(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    folder = _folder(sid)
    if not folder or not (folder / "pdf_iq.dat").exists():
        return JSONResponse({"error": "this sample has no raw PDF intensity (pdf_iq.dat)"}, status_code=404)
    params = (await request.json()).get("params") or {}
    if not isinstance(params, dict):
        return JSONResponse({"error": "params must be an object"}, status_code=400)
    try:
        out = await asyncio.to_thread(_reduce, folder, load_inputs(folder)["composition"], params)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    out.pop("gr_full")
    if (folder / "pdf.gr").exists():  # the G(r) the analysis used, to compare with
        r, g, _ = pdft.load_gr(folder / "pdf.gr")
        out["current"] = {"r": _round(r, 6), "g": _round(g)}
    return JSONResponse(to_json(out))


async def preprocess_save(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    src = _folder(sid)
    if not src or not (src / "pdf_iq.dat").exists():
        return JSONResponse({"error": "this sample has no raw PDF intensity (pdf_iq.dat)"}, status_code=404)
    params, meta = (await request.json()).get("params") or {}, load_inputs(src)
    if not isinstance(params, dict):
        return JSONResponse({"error": "params must be an object"}, status_code=400)
    try:
        out = await asyncio.to_thread(_reduce, src, meta["composition"], params)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    folder = UPLOADS / f"u{uuid.uuid4().hex[:7]}"
    folder.mkdir(parents=True)
    for name in ("xrd.xy", "xafs_mu.dat", "xafs_chi.k", "pdf_iq.dat", "pdf_bkg.dat"):
        if (src / name).exists():
            shutil.copy2(src / name, folder / name)
    p, g = out["params"], out["gr_full"]
    sq_to_gr.write_gr(folder / "pdf.gr", g["r"], g["y"], {"qmax": p["qmax"], "qmin": p["qmin"], **out["instrument"]}, g.get("dy"))
    inst = {**meta["instrument"], "pdf": {**meta["instrument"].get("pdf", {}), "qmax": p["qmax"], "qmin": p["qmin"]}}
    (folder / "sample.json").write_text(json.dumps({**meta, "sample_id": folder.name, "instrument": inst, "origin": f"G(r) re-reduced from {sid}",
                                                    "preprocess": {k: p[k] for k in PREPROCESS if k in p}}, indent=1))
    return JSONResponse({"sample": folder.name})


async def generate_missing(request: Request) -> JSONResponse:
    sid, cached = request.path_params["sid"], RUNS / f"{request.path_params['sid']}.json"
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if not _folder(sid) or not cached.exists():
        return JSONResponse({"error": "analyse the sample first: the curves come from its fitted model"}, status_code=404)
    d = await request.json() if int(request.headers.get("content-length") or 0) else {}
    realism = gan.realism if d.get("realistic", True) and gan.available()["loaded"] else None
    try:
        return JSONResponse(await asyncio.to_thread(generate.generate, json.loads(cached.read_text()), realism))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


async def elements(request: Request) -> JSONResponse:
    phases: dict[str, list[str]] = {}
    for x in systems():
        for e in sorted(_cations(x["formula"])):
            phases.setdefault(e, []).append(x["name"])
    return JSONResponse({"phases": phases})


async def gan_status(request: Request) -> JSONResponse:
    return JSONResponse(await asyncio.to_thread(gan.available))


async def gan_showcase(request: Request) -> JSONResponse:
    tech, seed = request.query_params.get("technique", "xrd"), request.query_params.get("seed", "0")
    if tech not in ("xrd", "pdf", "exafs") or not seed.isdigit():
        return JSONResponse({"error": "technique xrd, pdf or exafs and a whole-number seed"}, status_code=400)
    try:
        return JSONResponse(await asyncio.to_thread(gan.showcase, tech, int(seed)))
    except Exception as exc:  # the GAN repo is optional: say why the demo is unavailable
        return JSONResponse({"error": f"the GAN demo is unavailable: {exc}"}, status_code=503)


async def upload(request: Request) -> JSONResponse:
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if int(request.headers.get("content-length") or 0) > MAX_UPLOAD:
        return JSONResponse({"error": f"upload larger than {MAX_UPLOAD // 2**20} MB"}, status_code=413)
    async with request.form(max_files=4, max_fields=10) as form:  # closes the spooled files
        return await _save_upload(form)


async def _save_upload(form) -> JSONResponse:
    """A user's own data as a sample folder: each file saved under the name the analysis expects, the form's
    instrument values added to its '# key=value' header (they override the file's own), metadata inferred."""
    folder = None
    try:
        comp = _composition(form.get("composition"))
        elements = set(re.findall(r"[A-Z][a-z]?", comp))
        files = {k: form[k] for k in ("xrd", "pdf", "pdf_iq", "xafs") if getattr(form.get(k), "filename", None)}
        if not files:
            raise ValueError("upload at least one of the XRD, PDF and XAFS files")
        edge = str(form.get("edge") or "").strip().replace(" ", "_")
        if "xafs" in files and not (re.fullmatch(r"([A-Z][a-z]?)_(K|L1|L2|L3)", edge) and edge.split("_")[0] in elements):
            raise ValueError("XAFS needs the edge of an element in the composition, e.g. Pt L3 or Co K")
        heads = {"xrd": {"wavelength_A": _number(form, "wavelength_A", 0.1, 3.0)}, "pdf": {"qmax": _number(form, "qmax", 5.0, 60.0)},
                 "pdf_iq": {"qmax": _number(form, "qmax", 5.0, 60.0)}, "xafs": {"edge": edge}}
        names = {"xrd": "xrd.xy", "pdf": "pdf.gr", "pdf_iq": "pdf_iq.dat", "xafs": "xafs_chi.k" if form.get("xafs_kind") == "chi" else "xafs_mu.dat"}
        folder = UPLOADS / f"u{uuid.uuid4().hex[:7]}"
        folder.mkdir(parents=True)
        for kind, f in files.items():
            raw = await f.read()
            lines = raw.decode("utf-8", errors="replace").splitlines(keepends=True)
            n = next((i for i, line in enumerate(lines) if not line.startswith("#")), len(lines))
            if kind in ("xrd", "pdf_iq") and inspect_file(f.filename, raw, comp)["x_label"].startswith("Q"):
                heads[kind]["x"] = "q_inv_A"
            head = " ".join(f"{k}={v}" for k, v in heads[kind].items() if v is not None)
            body = "".join(lines[n:])
            if not all(NUMBERS.fullmatch(line.strip()) for line in lines[n:] if line.strip()):
                # CSV or a text header row: rewritten as two plain columns, which is what the loaders read
                xy = columns(f.filename, raw)
                if xy is None or len(xy[0]) < 2:
                    raise ValueError(f"{f.filename}: could not read two columns of numbers")
                body = "".join(f"{a:.8g} {b:.8g}\n" for a, b in zip(*xy))
            (folder / names[kind]).write_text("".join(lines[:n]) + (f"# {head}\n" if head else "") + body)
        if "pdf_iq" in files and "pdf" not in files:  # raw total scattering: reduced to G(r), re-reducible in preprocessing
            out = _reduce(folder, comp, {})
            p, g = out["params"], out["gr_full"]
            sq_to_gr.write_gr(folder / "pdf.gr", g["r"], g["y"], {"qmax": p["qmax"], "qmin": p["qmin"]}, g.get("dy"))
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


async def chat(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    v = _folder(sid) and await asyncio.to_thread(view, sid)
    if not v:
        return JSONResponse({"error": "analyse the sample first: the answers come from its results"}, status_code=404)
    msgs = [m for m in (await request.json()).get("messages", [])
            if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    if not msgs or msgs[-1]["role"] != "user":
        return JSONResponse({"error": "the last message must be a question"}, status_code=400)
    try:
        return JSONResponse(await asyncio.to_thread(answer, v["evidence"], msgs))
    except LLMError as exc:  # carries no endpoint address
        return JSONResponse({"error": f"the language model is unavailable: {exc}"}, status_code=503)


def _round(v, digits: int = 5):
    """Arrays as lists of floats with a few significant digits: the plots need shape, not 17 digits."""
    return [None if x is None or x != x else float(f"{x:.{digits}g}") for x in (v.tolist() if hasattr(v, "tolist") else v)]


def curves(sid: str) -> dict | None:
    cached = _analysis_file(sid)  # the agents' copy when newer: it carries the fits the fitting agents kept
    if not cached:
        return None
    a = json.loads(cached.read_text())
    out = {}
    for tech, c in fit_curves(a).items():
        obs, calc = (_round(c[k]) for k in ("obs", "calc"))
        out[tech] = {"title": c["title"], "x_label": c["xlabel"], "y_label": c["ylabel"], "x": _round(c["x"], 6), "obs": obs, "calc": calc,
                     "diff": [o - m if o is not None and m is not None else None for o, m in zip(obs, calc)],
                     "ticks": _round(c.get("ticks") or []), "window": c.get("window")}
    if v := a.get("virtual_xafs"):
        e = (a.get("exafs") or {}).get("fit", {}).get("curves", {})
        out["virtual"] = {"title": f"Virtual EXAFS {v['absorber']} {v['edge']}, {v['label']}", "x_label": "R (Å, not phase corrected)",
                          "y_label": "|χ(R)| (Å⁻³)", "x": _round(v["r"], 6), "lo": _round(v["chir_lo"]), "median": _round(v["chir_median"]),
                          "hi": _round(v["chir_hi"]), "measured": {"x": _round(e["r"], 6), "y": _round(e["chir_mag_data"])} if e.get("r") else None}
    return out


async def sample_curves(request: Request) -> JSONResponse:
    sid = request.path_params["sid"]
    c = _folder(sid) and await asyncio.to_thread(curves, sid)
    return JSONResponse(c) if c else JSONResponse({"error": "not analysed yet"}, status_code=404)


async def action(request: Request) -> JSONResponse:
    sid, cached = request.path_params["sid"], RUNS / f"{request.path_params['sid']}.json"
    if _foreign(request):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    data = await request.json()
    name, args = data.get("action"), data.get("args") or {}
    if not _folder(sid) or not cached.exists():
        return JSONResponse({"error": "analyse the sample first"}, status_code=404)
    if name not in ACTIONS or not isinstance(args, dict):
        return JSONResponse({"error": f"unknown re-run; one of {', '.join(ACTIONS)}"}, status_code=400)
    run = {"folder": _folder(sid), "meta": load_inputs(_folder(sid)), "res": json.loads(cached.read_text()), "out_dir": RUNS / sid}
    result, finding = await asyncio.to_thread(run_action, run, name, {k: str(v) for k, v in args.items()})
    return JSONResponse({"action": name, "args": args, "result": to_json(result), "finding": finding})


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
            await send("status", "Running the tools and checks: XRD, PDF, EXAFS, XANES, virtual XAFS, C1 to C7")
            res = await asyncio.to_thread(analyze, _folder(sid))
            cached.write_text(json.dumps(to_json(res)))
        if req["mode"] == "full":
            await send("status", "Fitting agents for XRD, PDF and EXAFS, visual inspection, then the generator and critic loop (gpt-oss)")
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
    Route("/api/samples/{sid}/chat", chat, methods=["POST"]),
    Route("/api/samples/{sid}/curves", sample_curves),
    Route("/api/samples/{sid}/actions", action, methods=["POST"]),
    Route("/api/uploads", upload, methods=["POST"]),
    Route("/api/uploads/inspect", inspect_upload, methods=["POST"]),
    Route("/api/plans", make_plan, methods=["POST"]),
    Route("/api/samples/{sid}/generate", generate_missing, methods=["POST"]),
    Route("/api/samples/{sid}/preprocess", preprocess, methods=["POST"]),
    Route("/api/samples/{sid}/preprocess/save", preprocess_save, methods=["POST"]),
    Route("/api/samples/{sid}/tweak/{tech}", tweak_params, methods=["GET"]),
    Route("/api/samples/{sid}/tweak/{tech}", tweak_refit, methods=["POST"]),
    Route("/api/samples/{sid}/tweak-apply", tweak_apply, methods=["POST"]),
    Route("/api/samples/{sid}/restore", restore, methods=["POST"]),
    Route("/api/elements", elements),
    Route("/api/gan", gan_status),
    Route("/api/gan/showcase", gan_showcase),
    Route("/api/runs", create_run, methods=["POST"]),
    WebSocketRoute("/api/runs/{run_id}/stream", stream_run),
    Mount("/files", StaticFiles(directory=RUNS), name="files"),
])
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
