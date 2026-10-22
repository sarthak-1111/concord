"""The EXAFS platform's rules for a shell the model lacks (a minor or light neighbour).

Copied from fccubicsaxs/xafs_backend app/modules/agent/fitflow.py (branch ai-agent, commit f637212) by the
author's decision on 2026-10-23: SIGNIFICANT, F_TEST_P, LIGHT_SIGMA2, the light-shell starting points of
select_model, _f_test and _minor_verdict, adapted to the result of concord.tools.xafs.shell_fit.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

SIGNIFICANT = 2.0          # a minor shell's N must exceed this many uncertainties
F_TEST_P = 0.05
LIGHT_SIGMA2 = 0.004       # a light neighbour's sigma^2 until the data fixes its own
# A light neighbour (an oxide on a metal) is a minority of unknown size, at its own distance.
LIGHT_STARTS = (1.0, 0.5, 2.0, 4.0)


def _f_test(chi2r_a: float, nu_a: float, chi2r_b: float, nu_b: float) -> Optional[float]:
    """p-value that model b (more variables) fits better than a only by chance."""
    try:
        from scipy.stats import f as fdist

        dp = nu_a - nu_b
        if dp <= 0 or nu_b <= 0 or chi2r_b <= 0:
            return None
        F = ((chi2r_a * nu_a - chi2r_b * nu_b) / dp) / chi2r_b
        if F <= 0:
            return 1.0
        return float(fdist.sf(F, dp, nu_b))
    except Exception:
        return None


def nu(fit: Dict[str, Any]) -> float:
    return fit["n_idp"] - fit["n_varys"]


def f_test(base: Dict[str, Any], fit: Dict[str, Any]) -> Optional[float]:
    return _f_test(base["chi2_reduced"], nu(base), fit["chi2_reduced"], nu(fit))


def minor_verdict(base: Dict[str, Any], fit: Dict[str, Any]) -> Dict[str, Any]:
    """Whether a minor shell stays: its N above twice its uncertainty, at its distance, and the fit better by an
    F-test."""
    p = next((x for x in fit["shells"] if x.get("extra")), None)
    if not p or p["N"] is None:
        return {"keep": False, "p": None, "text": "not kept: no N came back"}
    if p["N"] <= 0 or (p["N_err"] and p["N"] < SIGNIFICANT * p["N_err"]):
        err = f" ± {p['N_err']:.2f}" if p["N_err"] else ""
        return {"keep": False, "p": None, "text": f"not kept: N {p['N']:.2f}{err} is not above {SIGNIFICANT:g} times its "
                                                  "uncertainty, so the data does not show this shell"}
    delr = p["R_A"] - p["reff_A"]
    if abs(delr) > 0.15:
        return {"keep": False, "p": None, "text": f"not kept: it moved {delr:+.3f} Å from the structure's distance"}
    pv = f_test(base, fit)
    sigmas = p["N"] / p["N_err"] if p["N_err"] else None
    if pv is None or pv >= F_TEST_P:
        return {"keep": False, "p": pv, "text": f"not kept: the fit is not better than without it (reduced chi-square "
                                                f"{base['chi2_reduced']:.3g} -> {fit['chi2_reduced']:.3g}"
                                                + (f", F-test p {pv:.2g}" if pv is not None else "") + ")"}
    return {"keep": True, "p": pv, "text": (f"kept: N {p['N']:.2f} ± {p['N_err']:.2f}"
                                            + (f" ({sigmas:.1f} times its uncertainty)" if sigmas else "")
                                            + f", reduced chi-square {base['chi2_reduced']:.3g} -> {fit['chi2_reduced']:.3g} "
                                            f"(F-test p {pv:.2g})")}


def light_shell(base: Dict[str, Any], fit_with) -> Dict[str, Any]:
    """select_model for one light shell: fit it from several starts with sigma^2 held at LIGHT_SIGMA2 (the lowest
    chi-square wins), judge it with minor_verdict, and when kept let the data fix its own sigma^2 if it can.
    fit_with(n0, sigma2) runs shell_fit with the shell added (sigma2 None: free)."""
    fit = min((fit_with(n0, LIGHT_SIGMA2) for n0 in LIGHT_STARTS), key=lambda f: f["chi2_reduced"])
    verdict = minor_verdict(base, fit)
    if verdict["keep"]:
        p = next(x for x in fit["shells"] if x.get("extra"))
        fit2 = fit_with(p["N"], None)
        q = next(x for x in fit2["shells"] if x.get("extra"))
        if (q["sigma2"] and q["sigma2_err"] and 0 < q["sigma2"] <= 0.03 and q["sigma2_err"] < 0.5 * q["sigma2"]
                and q["N"] and q["N_err"] and q["N"] > SIGNIFICANT * q["N_err"] and abs(q["R_A"] - q["reff_A"]) <= 0.15):
            pv = f_test(fit, fit2)
            if pv is not None and pv < F_TEST_P:
                return {"fit": fit2, **verdict, "text": verdict["text"] + f"; its own sigma^2 is determined (F-test p {pv:.3g})"}
        verdict["text"] += f"; its sigma^2 stays at {LIGHT_SIGMA2:g} Å^2, the data does not fix its own"
    return {"fit": fit, **verdict}


if __name__ == "__main__":  # self-check of the F-test and the verdict on hand-made results
    base = {"chi2_reduced": 10.0, "n_idp": 20.0, "n_varys": 8, "shells": []}
    good = {"chi2_reduced": 4.0, "n_idp": 20.0, "n_varys": 11, "shells": [{"extra": True, "N": 1.2, "N_err": 0.2, "R_A": 2.03, "reff_A": 2.02}]}
    assert minor_verdict(base, good)["keep"]
    weak = {**good, "shells": [{"extra": True, "N": 0.3, "N_err": 0.2, "R_A": 2.03, "reff_A": 2.02}]}
    assert not minor_verdict(base, weak)["keep"]
    same = {**good, "chi2_reduced": 9.9}
    assert not minor_verdict(base, same)["keep"]
    print("ok")
