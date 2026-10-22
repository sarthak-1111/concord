import numpy as np

from concord.vision import eye_adapter
from concord.vision.features import residual_features


def test_thinning_keeps_a_perfect_oversampled_fit_random():
    rng = np.random.default_rng(0)
    r = np.arange(1, 30, 0.01)
    model = np.sin(3 * r) * np.exp(-r / 10)
    noise = np.convolve(rng.normal(0, 0.02, len(r)), np.ones(15) / 15, mode="same")  # correlated over ~π/Qmax
    raw = residual_features(r, model + noise, model, step=0.01)  # thinned by 1: every point
    thin = residual_features(r, model + noise, model, step=0.15)
    assert raw["durbin_watson"] < 0.2 and thin["durbin_watson"] > 1.0
    assert not thin["structured_regions"] and not thin["concentrated_regions"]


def test_missing_peak_is_structured_and_localised():
    r = np.arange(1, 30, 0.01)
    model = np.sin(3 * r) * np.exp(-r / 10)
    obs = model + 0.5 * np.exp(-0.5 * ((r - 2.0) / 0.08) ** 2) + np.random.default_rng(1).normal(0, 0.005, len(r))
    f = residual_features(r, obs, model, step=0.15)
    assert f["concentrated_regions"] == [f["regions"][0]["region"]]


def test_eye_adapter_loads_module_from_path(tmp_path, monkeypatch):
    mod = tmp_path / "eye_stub.py"
    mod.write_text("def inspect(image, context):\n    return {'verdict': 'reject', 'issues': [{'region': 'r<5', 'pattern': 'ripple'}]}\n")
    fn = eye_adapter.load(str(mod))
    out = eye_adapter.inspect(fn, tmp_path / "plot.png", {})
    assert out["verdict"] == "reject" and out["issues"][0]["region"] == "r<5" and out["inspector"] == "eye"


def test_diffraction_residual_peaks_are_grouped():
    tt = np.arange(10, 90, 0.02)
    model = 100 * np.exp(-0.5 * ((tt - 40) / 1.0) ** 2)
    obs = model + 30 * np.exp(-0.5 * ((tt - 60) / 1.0) ** 2) + np.random.default_rng(2).normal(0, 0.5, len(tt))
    f = residual_features(tt, obs, model, peak_width=2.4)
    assert len(f["unexplained_peaks"]) == 1 and abs(f["unexplained_peaks"][0] - 60) < 0.5
    assert f["durbin_watson"] is None and not f["structured_regions"] and not f["concentrated_regions"]
    assert not residual_features(tt, model, model, peak_width=2.4)["unexplained_peaks"]


def test_zoom_window_covers_the_largest_misfit():
    from concord.vision.render import zoom_window
    x = np.linspace(0, 10, 1001)
    calc = np.sin(x)
    lo, hi = zoom_window(x, calc + 0.5 * np.exp(-0.5 * ((x - 7) / 0.2) ** 2), calc)
    assert lo < 7 < hi and hi - lo < 2
