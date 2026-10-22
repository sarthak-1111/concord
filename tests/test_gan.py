"""Realism GAN adapter: needs the Concord Forge clone at GAN_REPO_PATH, so the module is skipped without it (e.g. on CI)."""
import json

import numpy as np
import pytest

from concord import gan

_status = gan.available()
if not _status["loaded"]:
    pytest.skip(f"no realism GAN loaded ({'; '.join(sorted(set(_status['errors'].values())))})", allow_module_level=True)

_x = {"xrd": np.linspace(10, 90, 4000), "pdf": np.arange(0.2, 40, 0.01), "exafs": np.arange(0, 16, 0.05)}
# clean curves reaching past each model grid (xrd 20-80 deg, pdf 0.5-30.08 A, exafs 2-14.75 A^-1), with conditions
CASES = {
    "xrd": (_x["xrd"], 20 + sum(h * np.exp(-0.5 * ((_x["xrd"] - c) / 0.4) ** 2)
                                for c, h in ((39.8, 1000), (46.2, 450), (67.5, 300), (81.3, 280))), (20, 80), {}),
    "pdf": (_x["pdf"], 3 * np.sin(2 * np.pi * _x["pdf"] / 2.77) * np.exp(-_x["pdf"] / 10), (0.5, 30.08),
            {"qmax": 24.0, "qdamp": 0.03}),
    "exafs": (_x["exafs"], np.sin(5.54 * _x["exafs"]) * np.exp(-0.01 * _x["exafs"] ** 2) / (_x["exafs"] + 1), (2, 14.75),
              {"edge": "Pt L3"}),
}


@pytest.mark.parametrize("technique", gan.TECHNIQUES)
def test_realism_keeps_shape_changes_the_curve_and_is_deterministic(technique):
    x, y, (lo, hi), cond = CASES[technique]
    out = gan.realism(technique, x, y, composition="Pt3Co", seed=3, **cond)
    assert out.shape == y.shape and np.isfinite(out).all()
    inside = (x >= lo) & (x <= hi)
    assert np.linalg.norm(out[inside] - y[inside]) > 1e-3 * np.linalg.norm(y[inside])
    assert np.array_equal(out[~inside], y[~inside])  # outside the model grid the input is kept
    assert np.array_equal(out, gan.realism(technique, x, y, composition="Pt3Co", seed=3, **cond))
    assert not np.array_equal(out, gan.realism(technique, x, y, composition="Pt3Co", seed=4, **cond))


@pytest.mark.parametrize("technique", gan.TECHNIQUES)
def test_showcase_has_three_curves_on_one_grid_and_a_licence(technique):
    s = gan.showcase(technique, seed=1)
    curves = [s["real"], s["simulated"], s["gan"]]
    n = len(s["real"]["x"])
    assert 100 < n <= 600 and all(len(c["y"]) == n and c["x"] == s["real"]["x"] for c in curves)
    assert all(max(abs(v) for v in c["y"]) == pytest.approx(1, abs=1e-4) for c in curves)
    assert s["gan"]["y"] != s["simulated"]["y"] and s["technique"] == technique and s["seed"] == 1
    assert s["source"]["licence"] and s["source"]["url"].startswith("https://") and s["source"]["attribution"]
    assert 0.5 <= s["c2st"]["gan"] <= 1 and 0.5 <= s["c2st"]["classical"] <= 1  # from the clone's own report
    assert not any(c in json.dumps(s, ensure_ascii=False) for c in "\u2013\u2014")
    assert gan.showcase(technique, seed=1) == s
