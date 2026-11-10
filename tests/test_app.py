import pytest

from app import create_app

VALID = {
    "vcc": "12", "r1": "47000", "r2": "10000",
    "rc": "4700", "re": "1000", "beta": "150", "vbe": "0.7",
}


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_renders_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "VCC" in body
    assert "<form" in body


def test_valid_post_shows_numbers(client):
    body = client.post("/", data=VALID).get_data(as_text=True)
    assert "1.324" in body      # I_C in mA
    assert "4.446" in body      # V_CE in V
    assert "แอคทีฟ" in body
    assert "ผ่าน" in body


def test_invalid_post_returns_200_with_message(client):
    response = client.post("/", data={**VALID, "r1": "abc"})
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "R1" in body
    assert "1.324" not in body


def test_invalid_post_preserves_typed_value(client):
    body = client.post("/", data={**VALID, "r1": "abc"}).get_data(as_text=True)
    assert 'value="abc"' in body


def test_zero_re_does_not_crash(client):
    response = client.post("/", data={**VALID, "re": "0"})
    assert response.status_code == 200
    assert "RE" in response.get_data(as_text=True)


def test_cutoff_case_is_labelled(client):
    body = client.post("/", data={**VALID, "r2": "1000"}).get_data(as_text=True)
    assert "คัตออฟ" in body
    assert "ไม่ใช้บังคับ" in body


def test_saturation_case_is_labelled(client):
    body = client.post(
        "/", data={**VALID, "rc": "1000", "r2": "22000", "re": "100"}
    ).get_data(as_text=True)
    assert "อิ่มตัว" in body


def test_different_input_renders_different_result(client):
    first = client.post("/", data=VALID).get_data(as_text=True)
    second = client.post("/", data={**VALID, "r2": "22000"}).get_data(as_text=True)
    assert first != second


def test_higher_vcc_raises_collector_current(client):
    low = client.post("/", data=VALID).get_data(as_text=True)
    high = client.post("/", data={**VALID, "vcc": "24"}).get_data(as_text=True)
    assert "1.324" in low
    assert "1.324" not in high


def test_template_has_no_script_tag():
    with open("templates/index.html", encoding="utf-8") as handle:
        assert "<script" not in handle.read().lower()
