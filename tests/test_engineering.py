import pytest

from bjt_bias.engineering import BiasInputs, OperatingPoint, solve_thevenin

GOLDEN = BiasInputs(12.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
SATURATED = BiasInputs(12.0, 47_000.0, 22_000.0, 1_000.0, 100.0, 150.0, 0.7)
CUTOFF = BiasInputs(12.0, 47_000.0, 1_000.0, 4_700.0, 1_000.0, 150.0, 0.7)


def test_golden_operating_point():
    op = solve_thevenin(GOLDEN)
    assert op.ib_a == pytest.approx(8.8249e-6, rel=1e-3)
    assert op.ic_a == pytest.approx(1.323675e-3, rel=1e-6)
    assert op.ie_a == pytest.approx(1.3325e-3, rel=1e-4)
    assert op.vb_v == pytest.approx(2.0325, rel=1e-6)
    assert op.vc_v == pytest.approx(5.778726, rel=1e-6)
    assert op.ve_v == pytest.approx(1.3325, rel=1e-4)
    assert op.vce_v == pytest.approx(4.446227, rel=1e-6)


def test_saturation_case_values():
    op = solve_thevenin(SATURATED)
    assert op.ic_a == pytest.approx(15.586e-3, rel=1e-4)
    assert op.vce_v == pytest.approx(-5.155, rel=1e-4)


def test_cutoff_returns_zero_currents():
    op = solve_thevenin(CUTOFF)
    assert op.ib_a == 0.0
    assert op.ic_a == 0.0
    assert op.ie_a == 0.0
    assert op.ve_v == 0.0
    assert op.vb_v == pytest.approx(0.25, rel=1e-9)
    assert op.vc_v == pytest.approx(12.0, rel=1e-12)
    assert op.vce_v == pytest.approx(12.0, rel=1e-12)


def test_cutoff_never_reports_voltage_above_supply():
    op = solve_thevenin(CUTOFF)
    assert op.vc_v <= CUTOFF.vcc_v
    assert op.vce_v <= CUTOFF.vcc_v


def test_output_changes_with_input():
    other = BiasInputs(12.0, 47_000.0, 22_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    assert solve_thevenin(GOLDEN).ic_a != solve_thevenin(other).ic_a


def test_ic_scales_with_vcc():
    higher = BiasInputs(24.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7)
    assert solve_thevenin(higher).ic_a > solve_thevenin(GOLDEN).ic_a
