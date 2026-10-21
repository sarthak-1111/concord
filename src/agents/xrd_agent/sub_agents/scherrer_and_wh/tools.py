from google.adk.tools import ToolContext

from concord.tools import xrd
from src.data_store.data_store import XRD_DATA_STORE

def scherrer_and_wh(payload: dict, tool_context: ToolContext) -> dict:
    """
    Scherrer crystallite size + Williamson-Hall strain/size analysis.
    Uses stored peaks and metadata.
    """
    try:
        path = payload["path"]
        if path not in XRD_DATA_STORE:
            return {"success": False, "path": path, "message": "No data found in store for given path."}

        loop_iter = tool_context.state.get("loop_iteration", 1)
        loop_data = XRD_DATA_STORE[path]["loops"][loop_iter]

        peaks = loop_data.get("peaks", [])
        meta = loop_data["meta"]

        beta_inst_deg = meta.get("instrument_fwhm_deg")
        res = xrd.scherrer_wh(peaks, meta.get("wavelength_angstrom", 1.5406),
                              instrument={"fwhm_deg": beta_inst_deg} if beta_inst_deg else None)
        sch = [{"two_theta": r["two_theta"], "L_nm": r["L_nm"], "beta_deg": r["beta_deg"]} for r in res["scherrer"]]
        wh_fit = res["williamson_hall"]
        wh, wh_diag = None, None
        if wh_fit and wh_fit["size_nm"]:
            wh = {"slope_strain": wh_fit["strain"], "intercept_size": wh_fit["size_nm"], "r2": wh_fit["r2"]}
        else:
            wh_diag = {"n_points": len(sch), "reason": "insufficient_points" if len(sch) < 3 else "non_positive_intercept"}

        # store results
        loop_data.update({
            "scherrer": sch,
            "williamson_hall": wh,
            "williamson_hall_diagnostics": wh_diag
        })

        return {
            "success": True,
            "path": path,
            "sample_name": meta.get("sample_name"),
            "params": {
                "wavelength_angstrom": meta.get("wavelength_angstrom", 1.5406),
                "instrument_fwhm_deg": beta_inst_deg,
            },
            "scherrer": sch,
            "williamson_hall": wh,
            "williamson_hall_diagnostics": wh_diag,
            "message": f"Scherrer and Williamson-Hall analysis complete for loop {loop_iter}."
        }

    except Exception as e:
        return {"success": False, "path": payload.get("path"), "message": f"Failed: {str(e)}"}
