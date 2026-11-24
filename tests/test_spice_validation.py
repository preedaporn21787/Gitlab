import pytest

from bjt_bias.spice_validation import DEFAULTS, parse_spice_inputs


def test_defaults_parse_to_handout_fixture():
    r = parse_spice_inputs(dict(DEFAULTS))
    assert r.errors == {}
    assert r.inputs.vcc_v == 12.0
    assert r.inputs.r1_ohm == 100_000.0
    assert r.inputs.re_ohm == 1_000.0
    assert r.inputs.amplitude_v == pytest.approx(0.010)
    assert r.inputs.frequency_hz == 1_000.0
    assert r.inputs.cin_f == pytest.approx(10e-6)


def test_re_zero_is_rejected():
    form = dict(DEFAULTS, re="0")
    r = parse_spice_inputs(form)
    assert r.inputs is None
    assert "re" in r.errors


def test_unit_conversion_and_sweep_validation():
    form = dict(DEFAULTS, analysis="ac", ac_start="20", ac_start_unit="Hz",
                ac_stop="200", ac_stop_unit="kHz", ac_points="50")
    r = parse_spice_inputs(form)
    assert r.errors == {}
    assert r.inputs.ac_stop_hz == 200_000.0
    bad = parse_spice_inputs(dict(form, ac_stop="10", ac_stop_unit="Hz"))
    assert "ac_stop" in bad.errors


def test_transient_step_must_be_smaller_than_stop():
    form = dict(DEFAULTS, analysis="transient", tran_stop="1", tran_stop_unit="ms",
                max_step="2", max_step_unit="ms")
    assert "max_step" in parse_spice_inputs(form).errors
