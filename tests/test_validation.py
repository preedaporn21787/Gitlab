import math

import pytest

from bjt_bias.validation import ParseResult, parse_inputs

VALID = {
    "vcc": "12", "r1": "47000", "r2": "10000",
    "rc": "4700", "re": "1000", "beta": "150", "vbe": "0.7",
}


def _form(**overrides):
    form = dict(VALID)
    form.update(overrides)
    return form


def test_valid_form_parses():
    result = parse_inputs(VALID)
    assert isinstance(result, ParseResult)
    assert result.errors == {}
    assert result.inputs is not None
    assert result.inputs.vcc_v == 12.0
    assert result.inputs.r1_ohm == 47000.0
    assert result.inputs.beta == 150.0
    assert result.inputs.vbe_v == 0.7


def test_whitespace_is_trimmed():
    result = parse_inputs(_form(vcc="  12  "))
    assert result.errors == {}
    assert result.inputs.vcc_v == 12.0


@pytest.mark.parametrize("field", ["vcc", "r1", "r2", "rc", "re", "beta", "vbe"])
def test_missing_field_is_an_error(field):
    form = dict(VALID)
    del form[field]
    result = parse_inputs(form)
    assert field in result.errors
    assert result.inputs is None


@pytest.mark.parametrize("field", ["vcc", "r1", "r2", "rc", "re", "beta", "vbe"])
@pytest.mark.parametrize("value", ["", "   ", "abc", "1,5"])
def test_non_numeric_is_an_error(field, value):
    result = parse_inputs(_form(**{field: value}))
    assert field in result.errors
    assert result.inputs is None


@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "-inf", "Infinity"])
def test_non_finite_is_an_error(value):
    result = parse_inputs(_form(vcc=value))
    assert "vcc" in result.errors
    assert result.inputs is None


@pytest.mark.parametrize("value", ["0", "-1", "-0.001"])
def test_vcc_must_be_positive(value):
    result = parse_inputs(_form(vcc=value))
    assert "vcc" in result.errors


@pytest.mark.parametrize("field", ["r1", "r2", "rc", "re"])
@pytest.mark.parametrize("value", ["0", "-5"])
def test_resistances_must_be_positive(field, value):
    result = parse_inputs(_form(**{field: value}))
    assert field in result.errors


@pytest.mark.parametrize("value", ["0", "0.5", "-3"])
def test_beta_must_be_at_least_one(value):
    result = parse_inputs(_form(beta=value))
    assert "beta" in result.errors


def test_beta_of_one_is_accepted():
    result = parse_inputs(_form(beta="1"))
    assert result.errors == {}


@pytest.mark.parametrize("value", ["-0.1", "12", "20"])
def test_vbe_must_be_between_zero_and_vcc(value):
    result = parse_inputs(_form(vbe=value))
    assert "vbe" in result.errors


def test_unusual_vbe_warns_without_blocking():
    result = parse_inputs(_form(vbe="0.9"))
    assert result.errors == {}
    assert result.inputs is not None
    assert any("VBE" in warning for warning in result.warnings)


def test_typical_vbe_produces_no_warning():
    assert parse_inputs(VALID).warnings == []


def test_raw_values_are_preserved_for_redisplay():
    result = parse_inputs(_form(r1="abc"))
    assert result.raw["r1"] == "abc"
    assert result.raw["vcc"] == "12"


def test_extreme_but_finite_values_are_accepted():
    result = parse_inputs(_form(beta="1000000", r1="1000000000"))
    assert result.errors == {}
    assert math.isfinite(result.inputs.beta)


def test_kohm_is_converted_to_ohm():
    result = parse_inputs(_form(r1="100", r1_unit="kΩ"))
    assert result.errors == {}
    assert result.inputs.r1_ohm == 100000.0


def test_ohm_is_not_converted():
    result = parse_inputs(_form(r1="10000", r1_unit="Ω"))
    assert result.errors == {}
    assert result.inputs.r1_ohm == 10000.0


def test_missing_unit_uses_default_without_error():
    result = parse_inputs(_form(r1="47000"))
    assert result.errors == {}
    assert result.inputs.r1_ohm == 47000.0


def test_unknown_unit_is_an_error():
    result = parse_inputs(_form(r1="100", r1_unit="MΩ"))
    assert "r1" in result.errors
    assert result.inputs is None


def test_invalid_number_with_unit_is_an_error():
    result = parse_inputs(_form(r1="abc", r1_unit="kΩ"))
    assert "r1" in result.errors
    assert result.inputs is None


def test_units_are_preserved_for_redisplay():
    result = parse_inputs(_form(r1="100", r1_unit="kΩ"))
    assert result.units["r1"] == "kΩ"
    assert result.raw["r1"] == "100"
    assert result.raw["r1_unit"] == "kΩ"


def test_all_resistance_fields_support_kohm():
    for field in ["r1", "r2", "rc", "re"]:
        result = parse_inputs(_form(**{field: "2.2", field + "_unit": "kΩ"}))
        assert result.errors == {}, f"{field} with kΩ failed"
        assert result.inputs is not None
        assert getattr(result.inputs, field + "_ohm") == 2200.0
