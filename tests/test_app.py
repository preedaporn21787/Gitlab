import pytest

from app import create_app

VALID = {
    "vcc": "12", "r1": "47000", "r2": "10000",
    "rc": "4700", "re": "1000", "beta": "150", "vbe": "0.7",
}

VALID_UNITS = {**VALID, "r1_unit": "Ω", "r2_unit": "Ω", "rc_unit": "Ω", "re_unit": "Ω"}


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_renders_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Input Parameters" in body
    assert "Circuit: Common-Emitter Amplifier" in body
    assert "DC Bias Results" in body
    assert "<form" in body
    assert "<svg" in body          # แผนภาพวงจรเรนเดอร์แม้ยังไม่คำนวณ


def test_valid_post_shows_numbers(client):
    body = client.post("/", data=VALID_UNITS).get_data(as_text=True)
    assert "1.32" in body          # I_C in mA (2 ตำแหน่ง)
    assert "4.45" in body          # V_CE in V (2 ตำแหน่ง)
    assert "Active region" in body
    assert "Exact" in body
    assert "Approx." in body
    assert "<svg" in body          # กราฟเส้นโหลดไลน์


def test_ib_shown_in_microamps(client):
    body = client.post("/", data=VALID_UNITS).get_data(as_text=True)
    assert "8.8" in body           # I_B ≈ 8.8 µA


def test_invalid_post_returns_200_with_message(client):
    response = client.post("/", data={**VALID, "r1": "abc"})
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "ต้องเป็นตัวเลข" in body
    assert 'class="error"' in body
    assert "1.32" not in body
    assert "load-line" not in body  # ไม่มีกราฟเมื่ออินพุตผิด


def test_invalid_post_preserves_typed_value(client):
    body = client.post("/", data={**VALID, "r1": "abc"}).get_data(as_text=True)
    assert 'value="abc"' in body


def test_zero_re_does_not_crash(client):
    response = client.post("/", data={**VALID, "re": "0"})
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "ต้องมากกว่า 0" in body
    assert 'class="error"' in body


def test_cutoff_case_is_labelled(client):
    body = client.post("/", data={**VALID, "r2": "1000"}).get_data(as_text=True)
    assert "Cutoff" in body
    assert "ไม่ใช้บังคับ" in body


def test_saturation_case_is_labelled(client):
    body = client.post(
        "/", data={**VALID, "rc": "1000", "r2": "22000", "re": "100"}
    ).get_data(as_text=True)
    assert "Saturation" in body
    assert "ขอบเขตบน" in body


def test_kohm_unit_gives_same_result_as_ohm(client):
    body_kohm = client.post(
        "/", data={**VALID, "r1": "47", "r1_unit": "kΩ"}
    ).get_data(as_text=True)
    body_ohm = client.post("/", data=VALID_UNITS).get_data(as_text=True)
    assert "1.32" in body_kohm
    assert "4.45" in body_kohm
    assert "Active region" in body_kohm
    # ตัวเลขสำคัญต้องตรงกัน
    for token in ["1.32", "4.45", "Active region", "8.8"]:
        assert token in body_ohm


def test_different_input_renders_different_result(client):
    first = client.post("/", data=VALID_UNITS).get_data(as_text=True)
    second = client.post("/", data={**VALID, "r2": "22000"}).get_data(as_text=True)
    assert first != second


def test_higher_vcc_raises_collector_current(client):
    low = client.post("/", data=VALID_UNITS).get_data(as_text=True)
    high = client.post("/", data={**VALID, "vcc": "24"}).get_data(as_text=True)
    assert "1.32" in low
    assert "1.32" not in high


def test_template_has_no_script_tag():
    with open("templates/index.html", encoding="utf-8") as handle:
        assert "<script" not in handle.read().lower()
