"""COD fallback: phases grouped and ranked from search rows (no network), and lowercase compositions."""
from concord import cod


def test_pick_groups_origin_choices_and_puts_the_formula_first():
    rows = [{"file": 1, "formula": "- Fe3 O4 -", "sg": "F d -3 m :1", "year": "1938"},
            {"file": 2, "formula": "- Fe3 O4 -", "sg": "F d -3 m :2", "year": "2001"},
            {"file": 3, "formula": "- Fe3 O4 -", "sg": "F d -3 m :2", "year": "1990"},
            {"file": 4, "formula": "- Fe2 O3 -", "sg": "R -3 c :H", "year": "1970"},
            {"file": 5, "formula": "- Fe O -", "sg": "F m -3 m", "year": "1960"}]
    groups = cod.pick(rows, "Fe2O3")
    assert [g[0]["file"] for g in groups] == [4, 2, 5]  # own formula first, then most determined; newest entry first
    assert len(groups[1]) == 3  # origin choices :1 and :2 are one phase


def test_lowercase_composition_is_cased():
    from backend.app.main import _composition
    assert _composition("pt3co") == "Pt3Co" and _composition("CEO2") == "CeO2" and _composition("tio2") == "TiO2"
    assert _composition("Pt3Co") == "Pt3Co"
