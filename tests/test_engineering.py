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


from bjt_bias.engineering import RegionReport, classify_region

SAT_THRESHOLD = 0.3


def _op_with_vce(vce_v: float) -> OperatingPoint:
    return OperatingPoint(
        ib_a=1e-5, ic_a=1e-3, ie_a=1.01e-3,
        vb_v=2.0, vc_v=2.0 + vce_v, ve_v=2.0, vce_v=vce_v,
    )


def test_golden_is_active():
    report = classify_region(GOLDEN, solve_thevenin(GOLDEN))
    assert report.region == "active"
    assert report.label_th == "แอคทีฟ"
    assert report.message_th == ""


def test_saturation_case_is_saturation():
    report = classify_region(SATURATED, solve_thevenin(SATURATED))
    assert report.region == "saturation"
    assert report.label_th == "อิ่มตัว"
    assert "ขอบเขตบน" in report.message_th


def test_cutoff_case_is_cutoff():
    report = classify_region(CUTOFF, solve_thevenin(CUTOFF))
    assert report.region == "cutoff"
    assert report.label_th == "คัตออฟ"
    assert "หยุดนำ" in report.message_th


def test_vce_exactly_at_threshold_is_saturation():
    report = classify_region(GOLDEN, _op_with_vce(SAT_THRESHOLD))
    assert report.region == "saturation"


def test_vce_just_above_threshold_is_active():
    report = classify_region(GOLDEN, _op_with_vce(SAT_THRESHOLD + 0.0001))
    assert report.region == "active"


def test_base_collector_forward_bias_is_saturation_even_with_high_vce():
    op = OperatingPoint(
        ib_a=1e-5, ic_a=1e-3, ie_a=1.01e-3,
        vb_v=5.0, vc_v=4.9, ve_v=4.3, vce_v=0.6,
    )
    assert classify_region(GOLDEN, op).region == "saturation"


from bjt_bias.engineering import (
    AnalysisResult, CheckResult, analyze, check_agreement, solve_nodal,
)

FIXED_CASES = [
    BiasInputs(12.0, 47_000.0, 10_000.0, 4_700.0, 1_000.0, 150.0, 0.7),
    BiasInputs(9.0, 22_000.0, 4_700.0, 2_200.0, 470.0, 100.0, 0.7),
    BiasInputs(15.0, 100_000.0, 22_000.0, 3_300.0, 680.0, 250.0, 0.65),
    BiasInputs(5.0, 10_000.0, 2_200.0, 1_000.0, 220.0, 80.0, 0.7),
]


@pytest.mark.parametrize("inputs", FIXED_CASES)
def test_nodal_matches_thevenin(inputs):
    primary = solve_thevenin(inputs)
    check = solve_nodal(inputs)
    assert check.ic_a == pytest.approx(primary.ic_a, rel=1e-9, abs=1e-12)
    assert check.ib_a == pytest.approx(primary.ib_a, rel=1e-9, abs=1e-15)
    assert check.ie_a == pytest.approx(primary.ie_a, rel=1e-9, abs=1e-12)
    assert check.vb_v == pytest.approx(primary.vb_v, rel=1e-9, abs=1e-9)
    assert check.vc_v == pytest.approx(primary.vc_v, rel=1e-9, abs=1e-9)
    assert check.ve_v == pytest.approx(primary.ve_v, rel=1e-9, abs=1e-9)
    assert check.vce_v == pytest.approx(primary.vce_v, rel=1e-9, abs=1e-9)


def test_check_passes_on_agreeing_results():
    result = check_agreement(solve_thevenin(GOLDEN), solve_nodal(GOLDEN))
    assert result.applicable is True
    assert result.passed is True
    assert result.max_relative_difference < 1e-9


def test_check_is_not_applicable_in_cutoff():
    result = check_agreement(solve_thevenin(CUTOFF), solve_nodal(CUTOFF))
    assert result.applicable is False
    assert result.passed is True


def test_check_fails_when_a_value_is_corrupted():
    primary = solve_thevenin(GOLDEN)
    corrupted = OperatingPoint(
        ib_a=primary.ib_a, ic_a=primary.ic_a * 1.01, ie_a=primary.ie_a,
        vb_v=primary.vb_v, vc_v=primary.vc_v, ve_v=primary.ve_v,
        vce_v=primary.vce_v,
    )
    result = check_agreement(primary, corrupted)
    assert result.applicable is True
    assert result.passed is False
    assert result.max_relative_difference > 1e-9


def test_analyze_bundles_everything():
    result = analyze(GOLDEN)
    assert isinstance(result, AnalysisResult)
    assert result.primary == solve_thevenin(GOLDEN)
    assert result.check.applicable is True
    assert result.region.region == "active"


