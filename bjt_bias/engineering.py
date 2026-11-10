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
