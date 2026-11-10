"""DC bias calculations for an NPN BJT common-emitter amplifier."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BiasInputs:
    """Component values and device parameters for a voltage-divider bias circuit."""

    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    beta: float
    vbe_v: float


@dataclass(frozen=True)
class OperatingPoint:
    """DC operating point in SI units: amperes and volts."""

    ib_a: float
    ic_a: float
    ie_a: float
    vb_v: float
    vc_v: float
    ve_v: float
    vce_v: float


def _thevenin_equivalent(inputs: BiasInputs) -> tuple[float, float]:
    """Return the Thevenin voltage and resistance seen by the base."""
    v_bb = inputs.vcc_v * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)
    r_bb = inputs.r1_ohm * inputs.r2_ohm / (inputs.r1_ohm + inputs.r2_ohm)
    return v_bb, r_bb


def _cutoff_point(v_bb: float, vcc_v: float) -> OperatingPoint:
    """Declared device-off result: no current, collector pulled to the supply."""
    return OperatingPoint(
        ib_a=0.0,
        ic_a=0.0,
        ie_a=0.0,
        vb_v=v_bb,
        vc_v=vcc_v,
        ve_v=0.0,
        vce_v=vcc_v,
    )


def solve_thevenin(inputs: BiasInputs) -> OperatingPoint:
    """Solve the operating point from the Thevenin equivalent of the divider."""
    v_bb, r_bb = _thevenin_equivalent(inputs)
    if v_bb <= inputs.vbe_v:
        return _cutoff_point(v_bb, inputs.vcc_v)

    i_b = (v_bb - inputs.vbe_v) / (r_bb + (inputs.beta + 1.0) * inputs.re_ohm)
    i_c = inputs.beta * i_b
    i_e = (inputs.beta + 1.0) * i_b
    v_b = v_bb - i_b * r_bb
    v_e = i_e * inputs.re_ohm
    v_c = inputs.vcc_v - i_c * inputs.rc_ohm
    return OperatingPoint(
        ib_a=i_b,
        ic_a=i_c,
        ie_a=i_e,
        vb_v=v_b,
        vc_v=v_c,
        ve_v=v_e,
        vce_v=v_c - v_e,
    )


def solve_approximate(inputs: BiasInputs) -> OperatingPoint:
    """Solve assuming base current does not load the divider (V_B = V_BB).

    Uses I_C = β/(β+1)·I_E so KCL stays self-consistent within the result.
    """
    v_bb, _ = _thevenin_equivalent(inputs)
    if v_bb <= inputs.vbe_v:
        return _cutoff_point(v_bb, inputs.vcc_v)

    v_b = v_bb
    v_e = v_b - inputs.vbe_v
    i_e = v_e / inputs.re_ohm
    i_b = i_e / (inputs.beta + 1.0)
    i_c = inputs.beta * i_b
    v_c = inputs.vcc_v - i_c * inputs.rc_ohm
    return OperatingPoint(
        ib_a=i_b,
        ic_a=i_c,
        ie_a=i_e,
        vb_v=v_b,
        vc_v=v_c,
        ve_v=v_e,
        vce_v=v_c - v_e,
    )


@dataclass(frozen=True)
class RegionReport:
    """Operating region with display copy in English and Thai."""

    region: str
    label_en: str
    label_th: str
    detail_en: str
    message_th: str


SATURATION_VCE_V = 0.3


def classify_region(inputs: BiasInputs, op: OperatingPoint) -> RegionReport:
    """Classify the operating region, checking cutoff first, then saturation."""
    v_bb, _ = _thevenin_equivalent(inputs)
    if v_bb <= inputs.vbe_v:
        return RegionReport(
            region="cutoff",
            label_en="Cutoff",
            label_th="คัตออฟ",
            detail_en=f"V_BB = {v_bb:.3f} V <= V_BE = {inputs.vbe_v:.3f} V",
            message_th="ทรานซิสเตอร์หยุดนำ ไม่มีกระแสคอลเลกเตอร์",
        )
    if op.vce_v <= SATURATION_VCE_V or op.vc_v <= op.vb_v:
        return RegionReport(
            region="saturation",
            label_en="Saturation",
            label_th="อิ่มตัว",
            detail_en=f"V_CE = {op.vce_v:.3f} V <= 0.3 V or V_C <= V_B",
            message_th=(
                "โมเดล β คงที่ใช้ไม่ได้ในเขตอิ่มตัว "
                "ค่า I_C ที่รายงานจึงเป็นเพียงขอบเขตบน ไม่ใช่ค่าทางกายภาพ"
            ),
        )
    return RegionReport(
        region="active",
        label_en="Active region",
        label_th="แอคทีฟ",
        detail_en=f"V_CE = {op.vce_v:.3f} V > 0.3 V",
        message_th="",
    )


@dataclass(frozen=True)
class CheckResult:
    """Outcome of comparing the primary solve against the independent one."""

    applicable: bool
    max_relative_difference: float
    passed: bool


@dataclass(frozen=True)
class AnalysisResult:
    """Everything the web layer needs for one set of inputs."""

    inputs: BiasInputs
    primary: OperatingPoint
    approximate: OperatingPoint
    method_gap: float
    check: CheckResult
    region: RegionReport


def solve_nodal(inputs: BiasInputs) -> OperatingPoint:
    """Solve the operating point from KCL at the base node, without Thevenin."""
    v_bb, _ = _thevenin_equivalent(inputs)
    if v_bb <= inputs.vbe_v:
        return _cutoff_point(v_bb, inputs.vcc_v)

    base_conductance = 1.0 / ((inputs.beta + 1.0) * inputs.re_ohm)
    conductance = 1.0 / inputs.r1_ohm + 1.0 / inputs.r2_ohm + base_conductance
    v_b = (inputs.vcc_v / inputs.r1_ohm + inputs.vbe_v * base_conductance) / conductance
    i_e = (v_b - inputs.vbe_v) / inputs.re_ohm
    i_b = i_e / (inputs.beta + 1.0)
    i_c = inputs.beta * i_b
    v_e = i_e * inputs.re_ohm
    v_c = inputs.vcc_v - i_c * inputs.rc_ohm
    return OperatingPoint(
        ib_a=i_b,
        ic_a=i_c,
        ie_a=i_e,
        vb_v=v_b,
        vc_v=v_c,
        ve_v=v_e,
        vce_v=v_c - v_e,
    )


def _max_relative_difference(primary: OperatingPoint, check: OperatingPoint) -> float:
    """Maximum relative difference across all seven operating-point quantities."""
    pairs = (
        (primary.ib_a, check.ib_a),
        (primary.ic_a, check.ic_a),
        (primary.ie_a, check.ie_a),
        (primary.vb_v, check.vb_v),
        (primary.vc_v, check.vc_v),
        (primary.ve_v, check.ve_v),
        (primary.vce_v, check.vce_v),
    )
    return max(
        abs(primary_value - check_value) / max(1.0, abs(primary_value))
        for primary_value, check_value in pairs
    )


def check_agreement(primary: OperatingPoint, check: OperatingPoint) -> CheckResult:
    """Compare two solves, normalising by max(1, |primary|) for each quantity."""
    if primary.ic_a == 0.0 and primary.ib_a == 0.0:
        return CheckResult(
            applicable=False, max_relative_difference=0.0, passed=True
        )

    difference = _max_relative_difference(primary, check)
    return CheckResult(
        applicable=True,
        max_relative_difference=difference,
        passed=difference < 1e-9,
    )


def analyze(inputs: BiasInputs) -> AnalysisResult:
    """Run the primary solve, the approximate solve, the independent check, and the region report."""
    primary = solve_thevenin(inputs)
    approximate = solve_approximate(inputs)
    return AnalysisResult(
        inputs=inputs,
        primary=primary,
        approximate=approximate,
        method_gap=_max_relative_difference(primary, approximate),
        check=check_agreement(primary, solve_nodal(inputs)),
        region=classify_region(inputs, primary),
    )

