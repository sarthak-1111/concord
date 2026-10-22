from concord.agents.pipeline import report_markdown

ANALYSIS = {"sample_id": "s1", "inputs": {"composition": "Pt"}, "phase": None, "checks": [], "errors": {}}


def test_report_takes_a_model_without_null_fields():
    # ADK saves agent outputs without null fields: "no candidate fits" arrives with no "phase" key at all
    md = report_markdown({"analysis": ANALYSIS, "model": {"summary": "No candidate fits.", "claims": []}, "log": []})
    assert "Phase: **None**" in md and "No candidate fits." in md


def test_report_says_when_the_agents_did_not_finish():
    md = report_markdown({"analysis": ANALYSIS, "error": "EndpointDown: not responding"})
    assert "**Incomplete:**" in md and "Fast mode" not in md
