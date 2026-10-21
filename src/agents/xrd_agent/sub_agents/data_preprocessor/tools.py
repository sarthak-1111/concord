import numpy as np
from google.adk.tools import ToolContext

from concord.tools import xrd
from src.data_store.data_store import XRD_DATA_STORE

def preprocess_xrd_data(payload: dict, tool_context: ToolContext) -> dict:
    """
    Preprocesses stored XRD data: smoothing + baseline correction.
    Expects payload to include 'path' to locate dataset in store.
    Optional parameters: smoothing_window, smoothing_polyorder, baseline_lambda, baseline_p.
    """
    try:
        path = payload["path"]
        if path not in XRD_DATA_STORE:
            return {"success": False, "path": path, "message": "No data found in store for given path."}

        loop_iter = tool_context.state.get("loop_iteration", 1)

        stored = XRD_DATA_STORE[path]
        theta = np.array(stored["two_theta_deg"])
        I = np.array(stored["intensity"])
        meta = stored["meta"]

        # Params (fall back to defaults if not provided)
        win = max(5, int(payload.get("smoothing_window", meta.get("smoothing_window", 31))) | 1)
        poly = min(payload.get("smoothing_polyorder", meta.get("smoothing_polyorder", 3)), win - 2)

        lam = float(payload.get("baseline_lambda", meta.get("baseline_lambda", 1e5)))
        p = float(payload.get("baseline_p", meta.get("baseline_p", 0.01)))

        pre = xrd.preprocess(I, smoothing_window=win, smoothing_polyorder=poly, baseline_lambda=lam, baseline_p=p)
        I_smooth, I_corr = pre["intensity_smooth"], pre["intensity_corr"]

        # Update store
        if "loops" not in stored:
            stored["loops"] = {}
        stored["loops"][loop_iter] = {
            "intensity_smooth": I_smooth,
            "intensity_corr": I_corr,
            "meta": {
                **meta,
                "smoothing_window": win,
                "smoothing_polyorder": poly,
                "baseline_lambda": lam,
                "baseline_p": p
            }
        }

        return {
            "success": True,
            "path": path,
            "sample_name": meta.get("sample_name"),
            "message": f"XRD data preprocessed and stored successfully for loop {loop_iter}."
        }

    except Exception as e:
        return {"success": False, "path": payload.get("path"), "message": f"Failed: {str(e)}"}
