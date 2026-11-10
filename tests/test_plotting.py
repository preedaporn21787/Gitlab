"""Tests for SVG plotting utilities."""

import xml.etree.ElementTree as ET

import pytest

from bjt_bias.engineering import (
    BiasInputs,
    OperatingPoint,
    solve_approximate,
    solve_thevenin,
)
from bjt_bias.plotting import circuit_svg, load_line_svg

GOLDEN = BiasInputs(12.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)

NS = "{http://www.w3.org/2000/svg}"


def _parse_svg(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def _text(svg: str) -> str:
    return "".join(_parse_svg(svg).itertext())


# ---------- circuit_svg ----------

def test_circuit_svg_is_valid_svg():
    root = _parse_svg(circuit_svg({}))
    assert root.tag == f"{NS}svg"
    assert root.attrib["role"] == "img"
    assert root.find(f"{NS}title") is not None


def test_circuit_svg_has_zigzag_resistors():
    """ทุกตัวต้านทานต้องวาดเป็นขีซิกแซก (polyline หลายจุด)"""
    svg = circuit_svg({})
    polylines = _parse_svg(svg).findall(f"{NS}polyline")
    assert len(polylines) == 4, f"ต้องมี polyline 4 อัน (R1, R2, RC, RE) พบ {len(polylines)}"
    for pl in polylines:
        assert len(pl.get("points", "").split()) >= 6, "ขีซิกแซกต้องมีหลายจุด"


def test_circuit_svg_resistors_on_correct_branches():
    """ตัวต้านทานต้องแบ่งเป็น 2 คอลัมน์ (ซ้าย: R1/R2, ขวา: RC/RE) และในแต่ละคอลัมน์ต้องซ้อนกัน"""
    svg = circuit_svg({})
    polylines = _parse_svg(svg).findall(f"{NS}polyline")
    spans = []
    for pl in polylines:
        points = [
            (float(p.split(",")[0]), float(p.split(",")[1]))
            for p in pl.get("points", "").split()
        ]
        centre_x = sum(x for x, _ in points) / len(points)
        ys = [y for _, y in points]
        spans.append((centre_x, min(ys), max(ys)))

    left = [s for s in spans if s[0] < 140]
    right = [s for s in spans if s[0] >= 140]
    assert len(left) == 2, f"ต้องมีตัวต้านทาน 2 ตัวในคอลัมน์ซ้าย พบ {len(left)}"
    assert len(right) == 2, f"ต้องมีตัวต้านทาน 2 ตัวในคอลัมน์ขวา พบ {len(right)}"

    # ในแต่ละคอลัมน์ ตัวต้านทานบนและล่างต้องไม่ทับกัน
    for column in (left, right):
        (x1, top1, bot1), (x2, top2, bot2) = sorted(column, key=lambda s: s[1])
        assert bot1 <= top2, "ตัวต้านทานบนและล่างในคอลัมน์เดียวกันต้องไม่ทับกัน"


def test_circuit_svg_has_npn_emitter_arrow():
    """สัญลักษณ์ NPN ต้องมีลูกศรสามเหลี่ยมที่ขาอิมิตเตอร์ชี้ออกนอกวงกลม"""
    svg = circuit_svg({})
    polygons = _parse_svg(svg).findall(f"{NS}polygon")
    assert polygons, "ต้องมี polygon สำหรับลูกศรอิมิตเตอร์"
    points = polygons[0].get("points", "").split()
    assert len(points) == 3, "ลูกศรต้องเป็นสามเหลี่ยม 3 จุด"


def test_circuit_svg_transistor_circle_is_filled():
    """วงกลมทรานซิสเตอร์ต้องมีสีเติมอ่อน (แยกจากจุดต่อสีเข้ม)"""
    svg = circuit_svg({})
    circles = _parse_svg(svg).findall(f"{NS}circle")
    # วงกลมทรานซิสเตอร์คือวงที่รัศมีใหญ่ที่สุด และต้องมี fill
    largest = max(circles, key=lambda c: float(c.get("r", 0)))
    assert float(largest.get("r", 0)) >= 20, "วงกลมทรานซิสเตอร์ต้องมีขนาดใหญ่"
    assert largest.get("fill"), "วงกลมทรานซิสเตอร์ต้องมีสีเติม"
    # จุดต่อสีเข้มต้องไม่มี fill (ใช้ class ระบุสีแทน)
    for c in circles:
        if float(c.get("r", 0)) < 10:
            assert not c.get("fill"), "จุดต่อควรใช้สีจาก class ไม่ใช่ fill"


def test_circuit_svg_has_ground_symbols():
    """ต้องมีสัญลักษณ์กราวด์ใต้ R2 และ RE (เส้น 3 แถวความกว้างลดลง)"""
    svg = circuit_svg({})
    root = _parse_svg(svg)
    grounds = root.findall(f"{NS}g")
    assert len(grounds) == 2, "ต้องมีกลุ่มสัญลักษณ์กราวด์ 2 กลุ่ม"
    for g in grounds:
        assert len(g.findall(f"{NS}line")) == 3, "สัญลักษณ์กราวด์ต้องมี 3 เส้น"


def test_circuit_svg_shows_component_values():
    labels = {
        "vcc": "12.0 V",
        "r1": "100 kΩ",
        "r2": "22 kΩ",
        "rc": "2.2 kΩ",
        "re": "1.0 kΩ",
    }
    text = _text(circuit_svg(labels))
    for value in ["12.0 V", "100 kΩ", "22 kΩ", "2.2 kΩ", "1.0 kΩ"]:
        assert value in text, f"ไม่พบค่า {value} ในแผนภาพวงจร"


def test_circuit_svg_shows_device_names():
    text = _text(circuit_svg({"beta": "100"}))
    for name in ["R", "Q", "NPN", "β"]:
        assert name in text, f"ไม่พบชื่ออุปกรณ์ {name}"


def test_circuit_svg_shows_beta_value():
    text = _text(circuit_svg({"beta": "150"}))
    assert "150" in text
    assert "β" in text


def test_circuit_svg_matches_reference_no_extra_labels():
    """ภาพอ้างอิงไม่มีป้ายโหนดแรงดันและไม่มีลูกศรกระแส — ต้องไม่มีในภาพเราเช่นกัน"""
    text = _text(circuit_svg({}))
    for absent in ["V_B", "V_C", "V_E", "I_B", "I_C", "I_E"]:
        assert absent not in text, f"ภาพอ้างอิงไม่มี {absent} — ไม่ควรแสดง"


def test_circuit_svg_escapes_special_characters():
    svg = circuit_svg({"r1": "<script>alert(1)</script>"})
    assert "<script" not in svg
    assert "&lt;script&gt;" in svg


def test_circuit_svg_no_script_tag():
    assert "<script" not in circuit_svg({}).lower()


# ---------- load_line_svg ----------

def test_load_line_svg_is_valid_svg():
    root = _parse_svg(load_line_svg(GOLDEN, solve_thevenin(GOLDEN)))
    assert root.tag == f"{NS}svg"
    assert root.attrib["role"] == "img"
    assert root.find(f"{NS}title") is not None


def test_load_line_y_intercept_matches_formula():
    op = solve_thevenin(GOLDEN)
    text = _text(load_line_svg(GOLDEN, op))
    expected_ma = GOLDEN.vcc_v / (GOLDEN.rc_ohm + GOLDEN.re_ohm) * 1000.0
    assert f"{expected_ma:.1f}" in text or f"{expected_ma:.0f}" in text


def test_load_line_q_point_matches_operating_point():
    op = solve_thevenin(GOLDEN)
    svg = load_line_svg(GOLDEN, op)
    assert f"{op.vce_v:.2f}" in svg or f"{op.ic_a * 1000:.2f}" in svg


def test_load_line_cutoff_does_not_crash():
    cutoff = BiasInputs(12.0, 47_000.0, 1_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    _parse_svg(load_line_svg(cutoff, solve_thevenin(cutoff)))


def test_load_line_saturation_clamps_and_marks_out_of_range():
    sat = BiasInputs(12.0, 47_000.0, 22_000.0, 1_000.0, 100.0, 150.0, 0.7)
    svg = load_line_svg(sat, solve_thevenin(sat))
    _parse_svg(svg)
    assert "out of range" in svg.lower()


def test_load_line_changes_with_vcc():
    low = BiasInputs(12.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    high = BiasInputs(24.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    assert load_line_svg(low, solve_thevenin(low)) != load_line_svg(
        high, solve_thevenin(high)
    )
