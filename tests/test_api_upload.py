import json

from starlette.testclient import TestClient

import backend.app.main as api


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "UPLOADS", tmp_path)
    return TestClient(api.app)


def test_upload_saves_files_with_the_form_values_as_headers(tmp_path, monkeypatch):
    xy = "".join(f"{10 + 0.02 * i:.2f} {100 + i % 7}\n" for i in range(200))
    r = _client(tmp_path, monkeypatch).post(
        "/api/uploads", data={"composition": "Pt3Co", "wavelength_A": "0.7093", "edge": "Pt L3", "xafs_kind": "chi"},
        files={"xrd": ("my.csv", "# x=2theta_deg wavelength_A=1.5406\n" + xy), "xafs": ("chi.dat", "3.0 0.1\n3.05 0.09\n")})
    assert r.status_code == 200
    folder = tmp_path / r.json()["sample"]
    assert (folder / "xrd.xy").read_text().splitlines()[:2] == ["# x=2theta_deg wavelength_A=1.5406", "# wavelength_A=0.7093"]
    assert (folder / "xafs_chi.k").read_text().startswith("# edge=Pt_L3\n3.0 0.1")
    meta = json.loads((folder / "sample.json").read_text())
    assert meta["techniques"] == ["xrd", "xafs"] and meta["instrument"]["xrd"]["wavelength_A"] == 0.7093  # the form wins


def test_upload_rejects_bad_input_and_leaves_nothing(tmp_path, monkeypatch):
    c, gr = _client(tmp_path, monkeypatch), {"pdf": ("g.gr", "1.0 0.5\n")}
    assert c.post("/api/uploads", data={"composition": "../etc"}, files=gr).status_code == 400
    assert c.post("/api/uploads", data={"composition": "Xx2"}, files=gr).status_code == 400
    assert c.post("/api/uploads", data={"composition": "Pt", "qmax": "999"}, files=gr).status_code == 400
    assert c.post("/api/uploads", data={"composition": "Pt"}, files={"xafs": ("m.dat", "1 2\n")}).status_code == 400  # no edge
    assert c.post("/api/uploads", data={"composition": "Pt"}, files=gr, headers={"origin": "https://elsewhere.example"}).status_code == 403
    assert not any(tmp_path.iterdir())
