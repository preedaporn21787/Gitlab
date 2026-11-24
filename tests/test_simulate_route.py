import re
from types import SimpleNamespace

import pytest

from app import create_app
from bjt_bias.spice_engine import MODEL_NAME, OperatingPoint, executable_path
from bjt_bias.spice_validation import DEFAULTS


@pytest.fixture
def client():
    return create_app().test_client()


def svg_points(data):
    return re.findall(rb'points="([^"]+)"', data)


def test_get_simulate_shows_defaults_and_nav(client):
    resp = client.get("/simulate")
    assert resp.status_code == 200
    assert b"CE Amplifier Simulator" in resp.data
    assert b'href="/"' in resp.data
    assert b"12" in resp.data


def test_invalid_re_shows_error_without_success(client):
    resp = client.post("/simulate", data=dict(DEFAULTS, re="0"))
    assert resp.status_code == 200
    assert b"status-invalid" in resp.data
    assert b"status-success" not in resp.data


def test_success_page_shows_engine_and_model(client, monkeypatch):
    fake = SimpleNamespace(
        status="success", analysis="dc", message="ok", model=MODEL_NAME,
        engine_version="ngspice-47", netlist="* test", log="", raw_path="run.raw",
        op=OperatingPoint(1.9, 1.3, 9.2, 7.9, 0.00128), ac=(), transient=(),
    )
    monkeypatch.setattr("app.run_simulation", lambda inputs: fake)
    resp = client.post("/simulate", data=dict(DEFAULTS))
    assert b"status-success" in resp.data
    assert b"ngspice-47" in resp.data
    assert b"NPN_REF" in resp.data
    assert b"1.28" in resp.data


def test_engine_failure_has_no_success_badge(client, monkeypatch):
    fake = SimpleNamespace(
        status="engine_missing", analysis="dc", message="not found", model=MODEL_NAME,
        engine_version=None, netlist="", log="", raw_path=None,
        op=None, ac=(), transient=(),
    )
    monkeypatch.setattr("app.run_simulation", lambda inputs: fake)
    resp = client.post("/simulate", data=dict(DEFAULTS))
    assert b"status-engine_missing" in resp.data
    assert b"status-success" not in resp.data


def test_real_transient_changes_when_amplitude_changes(client):
    if executable_path() is None:
        pytest.skip("ngspice not installed")
    a = client.post("/simulate", data=dict(DEFAULTS, analysis="transient"))
    b = client.post("/simulate", data=dict(DEFAULTS, analysis="transient", amplitude="20"))
    assert b"status-success" in a.data and b"status-success" in b.data
    assert svg_points(a.data) and svg_points(b.data)
    assert svg_points(a.data) != svg_points(b.data)


def test_lab3_index_still_works(client):
    resp = client.post("/", data={"bias_type": "voltage_divider", "vcc": "12", "r1": "100",
                                  "r1_unit": "kΩ", "r2": "22", "r2_unit": "kΩ", "rc": "2.2",
                                  "rc_unit": "kΩ", "re": "1", "re_unit": "kΩ", "beta": "100",
                                  "vbe": "0.7"})
    assert resp.status_code == 200
    assert b"1.23" in resp.data
