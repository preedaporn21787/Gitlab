import re
from pathlib import Path
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


def test_simulate_page_shows_ce_circuit(client):
    html = client.get("/simulate").data
    assert b'class="sim-circuit"' in html
    assert b"CE voltage-divider" in html
    assert b"<svg" in html
    assert b"Vout" in html

    invalid = client.post("/simulate", data=dict(DEFAULTS, re="0"))
    assert b'class="sim-circuit"' in invalid.data
    assert b"status-success" not in invalid.data


def test_ce_circuit_is_not_a_nested_card():
    css = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text("utf-8")
    block = css.split(".sim-circuit {", 1)[1].split("}", 1)[0]
    assert "border-bottom" in block
    assert "border-radius" not in block
    assert "background" not in block


def test_status_strip_precedes_form(client):
    resp = client.get("/simulate")
    body = resp.data.decode("utf-8")
    assert body.index('id="mobile-status"') < body.index('id="sim-form"')

    invalid = client.post("/simulate", data=dict(DEFAULTS, re="0"))
    head = invalid.data.decode("utf-8").split('id="sim-form"', 1)[0]
    assert 'id="mobile-status"' in head
    assert "status-invalid" in head


def test_run_button_has_pending_live_region(client):
    html = client.get("/simulate").data
    assert b'id="run-button"' in html
    assert b'id="run-pending"' in html
    assert b'aria-live="polite"' in html


def test_invalid_field_error_is_linked_and_actionable(client):
    resp = client.post("/simulate", data=dict(DEFAULTS, re="0"))
    html = resp.data.decode("utf-8")
    re_input = re.search(r'<input[^>]*id="re"[^>]*>', html)
    assert re_input is not None
    assert 'aria-describedby="re-error"' in re_input.group(0)
    assert 'id="re-error"' in html
    assert "ลอง 1 kΩ" in html
    assert 'class="warnings sim-errors"' not in html


def test_goal_line_is_visible(client):
    html = client.get("/simulate").data
    assert b'class="sim-goal"' in html
    assert "เปลี่ยนชิ้นส่วนเดียว".encode("utf-8") in html


def test_goal_line_uses_full_border_not_side_tab():
    css = (Path(__file__).resolve().parents[1] / "static" / "style.css").read_text("utf-8")
    block = css.split(".sim-goal {", 1)[1].split("}", 1)[0]
    assert "border:" in block
    assert "border-left:" not in block
    assert "text-wrap: pretty" in block
    for selector in (".source-note", ".provenance"):
        note_block = css.split(selector + " {", 1)[1].split("}", 1)[0]
        assert "text-wrap: pretty" in note_block


def _form_data_from_html(html):
    data = {}
    for tag in re.findall(r"<input\b[^>]*>", html):
        name = re.search(r'name="([^"]+)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if not name:
            continue
        if 'type="radio"' in tag and "checked" not in tag:
            continue
        data[name.group(1)] = value.group(1) if value else ""
    for name, body in re.findall(r'<select\b[^>]*name="([^"]+)"[^>]*>(.*?)</select>', html, re.S):
        selected = re.search(r'<option value="([^"]*)"[^>]*selected', body)
        data[name] = selected.group(1) if selected else ""
    return data


def test_rendered_default_form_submits_successfully(client, monkeypatch):
    html = client.get("/simulate").data.decode("utf-8")
    form_data = _form_data_from_html(html)

    captured = {}

    def fake_run(inputs):
        captured["vcc_v"] = inputs.vcc_v
        return SimpleNamespace(
            status="success", analysis="dc", message="ok", model=MODEL_NAME,
            engine_version="ngspice-47", netlist="* test", log="", raw_path="run.raw",
            op=OperatingPoint(1.9, 1.3, 9.2, 7.9, 0.00128), ac=(), transient=(),
        )

    monkeypatch.setattr("app.run_simulation", fake_run)
    resp = client.post("/simulate", data=form_data)
    assert b"status-success" in resp.data
    assert captured["vcc_v"] == 12.0
