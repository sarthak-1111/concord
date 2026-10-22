"""Cross-technique checks C1–C7. Each returns pass | warn | fail (or skip) with the numbers compared, the
tolerance (from config.yaml) and a short templated explanation. Pure functions of the tool outputs: no LLM."""
from concord.config import settings
from concord.tools.pdfcalc import spherical_envelope


def _tol(check: str) -> dict:
    return settings()["checks"][check]


def result(cid: str, name: str, status: str, values: dict, tolerance: dict, explanation: str) -> dict:
    return {"id": cid, "name": name, "status": status, "values": values, "tolerance": tolerance, "explanation": explanation}


def skip(cid: str, name: str, why: str) -> dict:
    return result(cid, name, "skip", {}, {}, why)


def _grade(diff: float, warn: float, fail: float) -> str:
    return "pass" if abs(diff) <= warn else "warn" if abs(diff) <= fail else "fail"


def c1_phase(xrd: dict | None, pdf: dict | None) -> dict:
    """XRD phase ranking vs the PDF model; flags a good PDF fit with weak Bragg peaks (nanoscale or amorphous
    order) and a refined lattice that has moved away from the database value of the phase."""
    tol = _tol("C1_phase")
    name = "Phase consistency (XRD vs PDF)"
    if not xrd or not pdf:
        return skip("C1", name, "needs both XRD and PDF")
    x_best, p_best = xrd["ranking"][0], pdf["fits"][0]
    dlat = max(abs(p_best["lattice"][k] / p_best["lattice_ref"][k] - 1) for k in "abc")
    vals = {"xrd_phase": x_best["phase"], "xrd_score": round(x_best["score"], 3), "xrd_area_explained": round(x_best["obs_area_fraction_explained"], 3),
            "peak_rel_intensity": round(xrd["peak_rel_intensity"], 3), "pdf_phase": p_best["candidate"], "pdf_rw": round(p_best["rw"], 3),
            "pdf_runner_up": pdf["fits"][1]["candidate"] if len(pdf["fits"]) > 1 else None,
            "pdf_runner_up_rw": round(pdf["fits"][1]["rw"], 3) if len(pdf["fits"]) > 1 else None,
            "lattice_rel_change": round(dlat, 4)}
    t = {k: tol[k] for k in ("pdf_good_rw", "xrd_weak_rel_intensity", "lattice_warn_rel")}
    if p_best["rw"] > 2 * tol["pdf_good_rw"]:
        return result("C1", name, "fail", vals, t, f"No candidate structure fits the PDF (best Rw {p_best['rw']:.2f} for {p_best['candidate']}). "
                      "The true phase may be missing from the candidate list, or the sample label is wrong.")
    if x_best["phase"] != p_best["candidate"]:
        return result("C1", name, "fail", vals, t, f"XRD prefers {x_best['phase']} but the PDF prefers {p_best['candidate']}.")
    if xrd["peak_rel_intensity"] < tol["xrd_weak_rel_intensity"] and p_best["rw"] <= tol["pdf_good_rw"]:
        return result("C1", name, "warn", vals, t, "The PDF fits well while the indexed Bragg peaks barely rise above the background: "
                      "nanoscale or partly amorphous order.")
    if dlat > tol["lattice_warn_rel"]:
        return result("C1", name, "warn", vals, t, f"XRD and PDF agree on {p_best['candidate']}, but the refined lattice differs from the "
                      f"database value by {100 * dlat:.2f} %: a dopant, vacancies or a reduced/oxidised phase can change it.")
    status = "pass" if p_best["rw"] <= tol["pdf_good_rw"] else "warn"
    return result("C1", name, status, vals, t, f"XRD and PDF agree on {p_best['candidate']}" +
                  ("." if status == "pass" else f", but the PDF fit is mediocre (Rw {p_best['rw']:.2f})."))


def model_shells(pdf: dict, absorber: str) -> dict:
    """First shells around the absorber in the PDF-refined model: {neighbour: shell}."""
    return {s["neighbor"]: s for s in pdf["fits"][0]["shells"].get(absorber, [])}


def c2_bond_lengths(exafs: dict | None, pdf: dict | None, absorber: str) -> dict:
    """Fitted EXAFS R (never raw FT peak positions) vs the matching pair distance of the PDF-refined model."""
    tol = _tol("C2_bond_length")
    name = "Bond lengths (EXAFS R vs PDF model)"
    if not exafs or not pdf:
        return skip("C2", name, "needs EXAFS and PDF")
    model = model_shells(pdf, absorber)
    rows, worst = [], 0.0
    for s in exafs["fit"]["shells"]:
        m = model.get(s["neighbor"])
        if m is None:
            continue
        d = s["R_A"] - m["R_A"]
        rows.append({"pair": f"{absorber}-{s['neighbor']}", "exafs_R_A": round(s["R_A"], 4), "exafs_err": s["R_err"] and round(s["R_err"], 4),
                     "pdf_model_R_A": round(m["R_A"], 4), "diff_A": round(d, 4)})
        worst = max(worst, abs(d))
    if not rows:
        return skip("C2", name, "no EXAFS shell has a matching pair in the PDF model")
    status = _grade(worst, tol["warn_A"], tol["fail_A"])
    expl = ("EXAFS bond lengths match the PDF-refined model." if status == "pass" else
            f"EXAFS and the PDF model disagree by up to {worst:.3f} Å: local distortion, a second phase, or strain the average structure does not capture.")
    return result("C2", name, status, {"pairs": rows, "max_abs_diff_A": round(worst, 4)}, tol, expl)


def c3_coordination(exafs: dict | None, pdf: dict | None, absorber: str) -> dict:
    """EXAFS N vs model coordination × spherical surface-truncation factor γ0(R; D_PDF)."""
    tol = _tol("C3_coordination")
    name = "Coordination numbers (EXAFS N vs model)"
    if not exafs or not pdf:
        return skip("C3", name, "needs EXAFS and PDF")
    fit = pdf["fits"][0]
    model = model_shells(pdf, absorber)
    rows, worst, extra = [], 0.0, []
    for s in exafs["fit"]["shells"]:
        m = model.get(s["neighbor"])
        if m is None:
            continue
        trunc = float(spherical_envelope(m["R_A"], 10 * fit["psize_nm"])) if fit.get("psize_nm") else 1.0
        expected = m["N"] * trunc
        d = s["N"] - expected
        rows.append({"pair": f"{absorber}-{s['neighbor']}", "exafs_N": round(s["N"], 2), "exafs_err": s["N_err"] and round(s["N_err"], 2),
                     "model_N_bulk": round(m["N"], 2), "surface_factor": round(trunc, 3), "model_N": round(expected, 2), "diff": round(d, 2)})
        worst = max(worst, abs(d))
    probe = exafs.get("extra_shell")
    if probe and probe["significant"]:
        extra.append(probe)
    if not rows and not extra:
        return skip("C3", name, "no EXAFS shell has a matching pair in the PDF model")
    status = _grade(worst, tol["warn_abs"], tol["fail_abs"])
    expl = "EXAFS coordination matches the PDF model after surface truncation."
    if status != "pass":
        expl = f"EXAFS coordination differs from the model by up to {worst:.1f}: segregation, vacancies or a disordered surface."
    if extra:
        status = "fail"
        e = extra[0]
        expl = (f"EXAFS needs a {e['pair']} shell (N = {e['N']:.2f} ± {e['N_err']:.2f} at {e['R_A']:.2f} Å, R-factor "
                f"{e['rfactor_without']:.4f} → {e['rfactor_with']:.4f}) that the PDF model does not contain: a surface oxide or second phase.")
    return result("C3", name, status, {"pairs": rows, "extra_shell": extra[0] if extra else None, "max_abs_diff": round(worst, 2)}, tol, expl)


def c4_oxidation(xanes: dict | None, bvs: dict | None) -> dict:
    """XANES valence (linear combination of valence standards) vs the bond-valence sum of the PDF-refined structure.
    A metallic model gets the tolerance of metallic references, whose XANES valence is precise. A valence that the
    refined bond lengths and the XANES edge both move away from the formal value, in the same direction, is mixed
    valence or non-stoichiometry even when each shift alone is within tolerance: two techniques agree on it."""
    tol = _tol("C4_oxidation")
    name = "Oxidation state (XANES vs bond-valence sum)"
    if not xanes or not bvs:
        return skip("C4", name, "needs XANES and a PDF-refined structure")
    formal, metal = bvs["formal_valence"], bvs["formal_valence"] == 0
    d = xanes["valence"] - bvs["valence"]
    status = _grade(d, *((tol["metal_warn_abs"], tol["metal_fail_abs"]) if metal else (tol["warn_abs"], tol["fail_abs"])))
    d_bvs, d_edge = bvs["valence"] - formal, xanes["valence_edge"] - formal
    shifted = not metal and abs(d_bvs) > tol["bvs_shift_min"] and abs(d_edge) > tol["xanes_shift_min"] and d_bvs * d_edge > 0
    vals = {"xanes_valence": round(xanes["valence"], 2), "xanes_edge_valence": round(xanes["valence_edge"], 2), "lcf": xanes.get("lcf_weights"),
            "bvs_valence": round(bvs["valence"], 3), "formal_valence": round(formal, 3), "diff": round(d, 2), "metallic_model": metal,
            "xanes_fidelity": "low (simple edge model)"}
    if shifted:
        status = "fail"
        expl = (f"The refined bond lengths (bond-valence sum {bvs['valence']:.2f}) and the XANES edge ({xanes['valence_edge']:.2f}) both put "
                f"the valence {'below' if d_bvs < 0 else 'above'} the formal {formal:g}: mixed valence or non-stoichiometry "
                "(for example reduced cations with oxygen vacancies) that the stoichiometric model lacks.")
    elif status == "pass":
        expl = "XANES and the bond-valence sum agree."
    elif metal:
        expl = (f"XANES shows an oxidised component (valence {xanes['valence']:.2f}) that the metallic model lacks: a surface oxide "
                "or oxidised species.")
    else:
        expl = (f"XANES says {xanes['valence']:.1f}, the refined structure implies {bvs['valence']:.1f}: mixed valence, a surface "
                "phase or vacancies the average structure misses.")
    return result("C4", name, status, vals, tol, expl)


def c5_disorder(exafs: dict | None, pdf: dict | None, absorber: str) -> dict:
    """EXAFS σ² vs PDF pair width. EXAFS sees correlated motion of neighbours, so it is expected to be smaller
    than the uncorrelated PDF width (U_i + U_j); differences are explained, not flagged blindly."""
    tol = _tol("C5_disorder")
    name = "Disorder (EXAFS σ² vs PDF pair width)"
    if not exafs or not pdf:
        return skip("C5", name, "needs EXAFS and PDF")
    fit = pdf["fits"][0]
    model = model_shells(pdf, absorber)
    rows = []
    for s in exafs["fit"]["shells"]:
        m = model.get(s["neighbor"])
        if m is None or s["neighbor"] not in fit["uiso"] or absorber not in fit["uiso"]:
            continue
        uncorr = fit["uiso"][absorber] + fit["uiso"][s["neighbor"]]
        corr = uncorr * max(1 - fit["delta2"] / m["R_A"] ** 2, 0.05)
        rows.append({"pair": f"{absorber}-{s['neighbor']}", "exafs_sigma2": round(s["sigma2"], 5), "pdf_uncorrelated_sigma2": round(uncorr, 5),
                     "pdf_with_delta2_sigma2": round(corr, 5), "ratio_exafs_to_pdf": round(s["sigma2"] / uncorr, 3)})
    if not rows:
        return skip("C5", name, "no matching pair")
    worst = min(rows, key=lambda r: min(abs(r["ratio_exafs_to_pdf"] - tol["ratio_low"]), abs(r["ratio_exafs_to_pdf"] - tol["ratio_high"])))
    ratios = [r["ratio_exafs_to_pdf"] for r in rows]
    ok = all(tol["ratio_low"] <= x <= tol["ratio_high"] for x in ratios)
    status = "pass" if ok else "warn"
    expl = (f"EXAFS σ² is {min(ratios):.2f}–{max(ratios):.2f} × the uncorrelated PDF width, as expected: EXAFS measures the "
            "relative motion of bonded neighbours, which move together, while U_i + U_j counts their motions independently.")
    if not ok:
        expl = (f"EXAFS/PDF disorder ratio {min(ratios):.2f}–{max(ratios):.2f} is outside {tol['ratio_low']}–{tol['ratio_high']}: "
                "static disorder (a distorted or split first shell) or a surface layer seen differently by the two probes.")
    return result("C5", name, status, {"pairs": rows}, tol, expl)


def c6_size(xrd: dict | None, pdf: dict | None) -> dict:
    """Crystallite size (XRD, sphere-equivalent) vs PDF particle diameter."""
    tol = _tol("C6_size")
    name = "Size (XRD vs PDF)"
    if not xrd or not pdf or not pdf["fits"][0].get("psize_nm") or not xrd.get("sphere_diameter_nm"):
        return skip("C6", name, "needs an XRD size and a nanoparticle PDF fit")
    dx, dp = xrd["sphere_diameter_nm"], pdf["fits"][0]["psize_nm"]
    rel = (dx - dp) / dp
    status = _grade(rel, tol["warn_rel"], tol["fail_rel"])
    vals = {"xrd_sphere_diameter_nm": round(dx, 2), "xrd_scherrer_nm": round(xrd["scherrer_median_nm"], 2),
            "pdf_diameter_nm": round(dp, 2), "rel_diff": round(rel, 3)}
    if status == "pass":
        expl = "XRD and PDF sizes agree once the Scherrer column length is converted to a sphere diameter."
    elif rel < 0:
        expl = ("XRD coherent domains are smaller than the PDF particle: multi-domain (twinned) particles, or strain broadening "
                "counted as size.")
    else:
        expl = ("XRD sees larger crystallites than the PDF particle diameter: XRD is volume-weighted (large particles dominate) "
                "while the PDF envelope is closer to a number average, or a disordered surface shell shortens the PDF range.")
    return result("C6", name, status, vals, tol, expl)


def c7_joint(xrd: dict | None, pdf: dict | None, virtual: dict | None) -> dict:
    """Joint score per candidate: mean of XRD profile misfit (1 - correlation), PDF Rw and, when XAFS was measured,
    the R-factor of the EXAFS predicted from that candidate's PDF model against the measurement."""
    tol = _tol("C7_joint")
    name = "Joint simulation score (XRD + PDF + EXAFS)"
    if not xrd or not pdf:
        return skip("C7", name, "needs XRD and PDF")
    corr = {r["phase"]: r["profile_corr"] for r in xrd["ranking"]}
    exafs = (virtual or {}).get("per_candidate", {})
    parts = []
    for f in pdf["fits"][:3]:
        p = {"xrd": 1 - max(corr.get(f["candidate"], 0.0), 0.0), "pdf": f["rw"]}
        if f["candidate"] in exafs:
            p["exafs"] = exafs[f["candidate"]]
        parts.append((f["candidate"], p))
    used = set.intersection(*(set(p) for _, p in parts))  # every candidate scored on the same techniques
    rows = [{"candidate": c, **{k: round(v, 4) for k, v in p.items()}, "score": round(sum(p[k] for k in used) / len(used), 4)} for c, p in parts]
    rows.sort(key=lambda r: r["score"])
    reported = pdf["fits"][0]["candidate"]
    margin = rows[1]["score"] - rows[0]["score"] if len(rows) > 1 else None
    vals = {"candidates": rows, "margin": margin and round(margin, 4), "techniques": sorted(used)}
    if rows[0]["candidate"] != reported:
        return result("C7", name, "fail", vals, tol, f"Scored on all techniques together, {rows[0]['candidate']} beats the reported {reported}.")
    if margin is not None and margin < tol["min_margin"]:
        return result("C7", name, "warn", vals, tol, f"{reported} wins the joint score by only {margin:.3f}: the techniques do not "
                      f"separate it from {rows[1]['candidate']}.")
    return result("C7", name, "pass", vals, tol, f"{reported} has the best joint score" + (f" (margin {margin:.3f})." if margin else "."))
