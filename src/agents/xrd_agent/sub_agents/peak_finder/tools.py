import numpy as np
from google.adk.tools import ToolContext

from concord.tools import xrd
from src.data_store.data_store import XRD_DATA_STORE

def find_and_fit_peaks(payload: dict, tool_context: ToolContext) -> dict:
    """
    Finds and fits peaks in preprocessed XRD data using Voigt profiles.
    Expects payload to include:
      - path
      - peak_min_prominence (float)
      - peak_min_distance_pts (int)
      - peak_min_height_rel (float)
      - fit_window_deg (float)
    """
    try:
        path = payload["path"]
        if path not in XRD_DATA_STORE:
            return {"success": False, "path": path, "message": "No data found in store for given path."}

        loop_iter = tool_context.state.get("loop_iteration", 1)

        stored = XRD_DATA_STORE[path]
        loop_data = stored.get("loops", {}).get(loop_iter)
        if not loop_data:
            return {
                "success": False,
                "path": path,
                "message": f"No preprocessed data found for loop {loop_iter}."
            }
        
        theta = np.array(stored["two_theta_deg"])
        I = np.array(loop_data.get("intensity_corr"))
        meta = loop_data.get("meta", {})

        # Parameters (payload > meta > defaults)
        prom = float(payload.get("peak_min_prominence", meta.get("peak_min_prominence", 0.1)))
        dist = int(payload.get("peak_min_distance_pts", meta.get("peak_min_distance_pts", 25)))
        h_rel = float(payload.get("peak_min_height_rel", meta.get("peak_min_height_rel", 0.15)))
        fit_win = float(payload.get("fit_window_deg", meta.get("fit_window_deg", 0.8)))

        top = float(I.max()) if np.ptp(I) > 0 else 1.0
        step = float(np.median(np.diff(theta)))
        results = xrd.find_and_fit_peaks(theta, I, height_rel=h_rel, prominence_rel=prom / top,
                                         min_distance_deg=dist * step, fit_window_deg=fit_win)
        for r in results:
            r["intensity"] = r["height"]

        # update store
        loop_data.update({
            "peaks": results,
            "meta": {
                **meta,
                "peak_min_prominence": prom,
                "peak_min_distance_pts": dist,
                "peak_min_height_rel": h_rel,
                "fit_window_deg": fit_win
            }
        })

        return {
            "success": True,
            "path": path,
            "sample_name": meta.get("sample_name"),
            "params": {
                "peak_min_prominence": prom,
                "peak_min_distance_pts": dist,
                "peak_min_height_rel": h_rel,
                "fit_window_deg": fit_win
            },
            "peaks": results,
            "message": f"Found and fitted {len(results)} peaks in loop {loop_iter}."
        }

    except Exception as e:
        return {"success": False, "path": payload.get("path"), "message": f"Failed: {str(e)}"}
