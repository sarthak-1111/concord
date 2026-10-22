from pymatgen.core import Lattice, Structure

from concord.analysis import bond_valence
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


def test_c4_absorber_missing_from_the_model_is_a_wrong_label_not_a_metal():
    rutile = Structure.from_spacegroup("P4_2/mnm", Lattice.tetragonal(4.59, 2.96), ["Ti", "O"], [[0, 0, 0], [0.305, 0.305, 0]])
    bvs = bond_valence(rutile, rutile, "Ce")
    assert bvs["absent"] and bond_valence(rutile, rutile, "Ti")["formal_valence"] == 4.0
    out = c4_oxidation(_x(4.0, 4.0), bvs)
    assert out["status"] == "fail" and "Ce is not in the refined model TiO2" in out["explanation"] and "metallic" not in out["explanation"]
