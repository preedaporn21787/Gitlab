from bjt_bias.spice_engine import AcPoint, TransientPoint
from bjt_bias.spice_plots import ac_svg, transient_svg


def test_ac_svg_has_units_and_legend():
    svg = ac_svg([AcPoint(10.0, 2.0, -180.0), AcPoint(100.0, 1.0, -190.0)])
    assert "Frequency (Hz)" in svg
    assert "Gain (dB)" in svg
    assert "Phase (°)" in svg
    assert "Gain" in svg and "Phase" in svg
    assert "log" in svg.lower()


def test_transient_svg_has_units_and_legend():
    svg = transient_svg([
        TransientPoint(0.0, 0.01, -0.1),
        TransientPoint(0.001, -0.01, 0.1),
    ])
    assert "Time (ms)" in svg
    assert "Voltage (V)" in svg
    assert "Vin" in svg and "Vout" in svg
    assert "<polyline" in svg


def test_empty_points_return_empty_string():
    assert ac_svg([]) == "" and transient_svg([]) == ""
