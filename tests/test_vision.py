import numpy as np

from concord.vision import eye_adapter
from concord.vision.features import residual_features


def test_thinning_keeps_a_perfect_oversampled_fit_random():
    rng = np.random.default_rng(0)
    r = np.arange(1, 30, 0.01)
    model = np.sin(3 * r) * np.exp(-r / 10)
    noise = np.convolve(rng.normal(0, 0.02, len(r)), np.ones(15) / 15, mode="same")  # correlated over ~π/Qmax
    raw = residual_features(r, model + noise, model)
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
