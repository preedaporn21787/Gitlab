"""Tests for SVG plotting utilities."""

import math
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


def _parse_svg(svg: str) -> ET.Element:
    return ET.fromstring(svg)


def test_circuit_svg_empty_labels_is_valid_svg():
    svg = circuit_svg({})
    root = _parse_svg(svg)
    assert root.tag.endswith("svg")
    assert "role" in root.attrib
    assert root.attrib["role"] == "img"
    assert root.find("{http://www.w3.org/2000/svg}title") is not None


def test_circuit_svg_with_labels_shows_values():
    labels = {
        "vcc": "12.0 V",
        "r1": "100 kΩ",
        "r2": "22 kΩ",
        "rc": "2.2 kΩ",
        "re": "1.0 kΩ",
    }
    svg = circuit_svg(labels)
    root = _parse_svg(svg)
    text = "".join(root.itertext())
    assert "100 kΩ" in text
    assert "22 kΩ" in text
    assert "2.2 kΩ" in text
    assert "1.0 kΩ" in text
    assert "12.0 V" in text


def test_circuit_svg_has_node_labels():
    svg = circuit_svg({})
    root = _parse_svg(svg)
    text = "".join(root.itertext())
    assert "V_B" in text
    assert "V_C" in text
    assert "V_E" in text


def test_circuit_svg_escapes_special_characters():
    labels = {"r1": "<script>alert(1)</script>"}
    svg = circuit_svg(labels)
    assert "<script" not in svg
    assert "&lt;script&gt;" in svg


def test_circuit_svg_no_script_tag():
    svg = circuit_svg({})
    assert "<script" not in svg.lower()


def test_load_line_svg_is_valid_svg():
    op = solve_thevenin(GOLDEN)
    svg = load_line_svg(GOLDEN, op)
    root = _parse_svg(svg)
    assert root.tag.endswith("svg")
    assert "role" in root.attrib


def test_load_line_y_intercept_matches_formula():
    op = solve_thevenin(GOLDEN)
    svg = load_line_svg(GOLDEN, op)
    root = _parse_svg(svg)
    text = "".join(root.itertext())
    expected_ma = GOLDEN.vcc_v / (GOLDEN.rc_ohm + GOLDEN.re_ohm) * 1000.0
    assert f"{expected_ma:.1f}" in text or f"{expected_ma:.0f}" in text


def test_load_line_q_point_matches_operating_point():
    op = solve_thevenin(GOLDEN)
    svg = load_line_svg(GOLDEN, op)
    assert f"{op.vce_v:.2f}" in svg or f"{op.ic_a * 1000:.2f}" in svg


def test_load_line_cutoff_does_not_crash():
    cutoff = BiasInputs(12.0, 47_000.0, 1_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    op = solve_thevenin(cutoff)
    svg = load_line_svg(cutoff, op)
    _parse_svg(svg)  # must parse


def test_load_line_saturation_clamps_and_marks_out_of_range():
    sat = BiasInputs(12.0, 47_000.0, 22_000.0, 1_000.0, 100.0, 150.0, 0.7)
    op = solve_thevenin(sat)
    svg = load_line_svg(sat, op)
    _parse_svg(svg)  # must parse
    assert "out of range" in svg.lower()


def test_load_line_changes_with_vcc():
    low = BiasInputs(12.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    high = BiasInputs(24.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    op_low = solve_thevenin(low)
    op_high = solve_thevenin(high)
    svg_low = load_line_svg(low, op_low)
    svg_high = load_line_svg(high, op_high)
    assert svg_low != svg_high
