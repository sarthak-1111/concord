from concord.agents.evidence import number_guard

EV = {"pdf.fit.Pt": {"rw": 0.0642, "lattice": {"a": 3.9217}, "psize_nm": 4.59}, "check.C6": {"values": {"rel_diff": 0.027}}}


def test_number_guard_accepts_cited_and_rounded_numbers():
    text = "Pt fits the PDF with Rw 0.064 (a = 3.922 Å), diameter 4.6 nm; XRD and PDF sizes differ by 2.7 %. Checks C1-C6 ran on s0010 (Pt3Co, L3 edge), two candidates."
    assert number_guard(text, EV) == []


def test_number_guard_flags_invented_numbers():
    assert number_guard("The particle is 6.2 nm across and Rw is 0.064.", EV) == ["6.2"]
    assert number_guard("The lattice is 3.95 Å.", EV) == ["3.95"]


def test_rerun_ignores_arguments_the_action_does_not_take():
    from concord.agents.resolver import run_action
    result, finding = run_action({}, "xrd_size_strongest", {"optional": "true"})  # the LLM added an argument
    assert "TypeError" not in finding and "unexpected keyword" not in str(result.get("error", ""))
