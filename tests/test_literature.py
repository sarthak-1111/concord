from concord.literature import _uninvert, extract, material_name, mentions, sentences


def test_values_are_read_with_their_pair_and_uncertainty():
    s = "A Pt–Pt distance of 2.876(28) Å and a Pt–P bond length of 2.32(4) Å are obtained."
    assert extract(s, "bond_length", {"Pt"}) == [{"pair": "Pt–Pt", "value": 2.876, "uncertainty": 0.028, "unit": "Å"}]  # Pt–P dropped
    s = "EXAFS gives a Pt–Pt coordination number of 8.9 ± 0.5 and a Pt–Co coordination number of 2.1 after annealing."
    assert [(x["pair"], x["value"], x["uncertainty"]) for x in extract(s, "coordination_number", {"Pt", "Co"})] == [
        ("Pt–Pt", 8.9, 0.5), ("Pt–Co", 2.1, None)]
    assert extract("The Pt–O bond length of 2.02 ± 0.02 Å indicates PtOx.", "bond_length", {"Pt"})[0]["pair"] == "Pt–O"


def test_oxidation_states_and_sizes():
    ox = extract("XANES shows Ce3+ and Ce(IV) species; Cu2+ is reduced.", "oxidation_state", {"Ce", "O"})
    assert [(x["element"], x["value"]) for x in ox] == [("Ce", 3), ("Ce", 4)]
    ox = extract("XANES: the Ti 4+ oxidation state was observed with 0.02 and 0.04 O vacancies.", "oxidation_state", {"Ti", "O"})
    assert [(x["element"], x["value"]) for x in ox] == [("Ti", 4)]
    ox = extract("The average oxidation state of Pt is +0.6 from the white line.", "oxidation_state", {"Pt"})
    assert [(x["element"], x["value"]) for x in ox] == [("Pt", 0.6)]
    sizes = extract("Particles of 3.2 ± 0.4 nm and 2–5 nm clusters; a 532 nm laser.", "particle_size", {"Pt"})
    assert [x["value"] for x in sizes] == [3.2, [2.0, 5.0]]
    assert extract("The film was 30 nm thick.", "particle_size", {"Pt"}) == []  # no size word


def test_material_matching_and_text_helpers():
    assert mentions("Pt 3 Co nanoparticles", "Pt3Co") and mentions("CoPt3 films", "Pt3Co")
    assert not mentions("PtNi nanowires", "Pt") and mentions("platinum clusters", "Pt")
    assert material_name("TiO2", "TiO2-anatase") == "anatase TiO2" and material_name("Pt3Co", "Pt") == "Pt3Co"
    assert _uninvert({"EXAFS": [1], "The": [0], "fit.": [2]}) == "The EXAFS fit."
    assert sentences("The size was 3.2 nm. EXAFS (Fig. 2) shows N = 8 here.") == ["The size was 3.2 nm.", "EXAFS (Fig. 2) shows N = 8 here."]
