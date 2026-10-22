from concord.checks import c4_oxidation


def _x(lcf, edge):
    return {"valence": lcf, "valence_edge": edge, "edge_eV": 0.0, "lcf_weights": {}}


def test_c4_metal_uses_the_metal_tolerance():
    metal = {"valence": 0.0, "formal_valence": 0.0}
    assert c4_oxidation(_x(0.1, 0.05), metal)["status"] == "pass"
    out = c4_oxidation(_x(0.4, 0.3), metal)
    assert out["status"] == "fail" and "oxidised component" in out["explanation"]


def test_c4_mixed_valence_needs_both_techniques():
    reduced = {"valence": 3.9, "formal_valence": 4.0}  # bonds lengthened: valence below 4
    assert c4_oxidation(_x(3.98, 3.75), reduced)["status"] == "fail"   # XANES edge agrees
    assert c4_oxidation(_x(3.98, 4.08), reduced)["status"] == "pass"   # XANES edge disagrees
    clean = {"valence": 3.995, "formal_valence": 4.0}
    assert c4_oxidation(_x(3.98, 3.75), clean)["status"] == "pass"     # XANES alone is not enough
