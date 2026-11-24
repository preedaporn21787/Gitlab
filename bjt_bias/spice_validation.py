"""Parsing and validation of the CE amplifier simulator form."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

ANALYSES = ("dc", "ac", "transient")

DEFAULTS: dict[str, str] = {
    "analysis": "dc",
    "vcc": "12", "vcc_unit": "V",
    "r1": "100", "r1_unit": "kΩ",
    "r2": "22", "r2_unit": "kΩ",
    "rc": "2.2", "rc_unit": "kΩ",
    "re": "1", "re_unit": "kΩ",
    "rl": "10", "rl_unit": "kΩ",
    "cin": "10", "cin_unit": "µF",
    "cout": "10", "cout_unit": "µF",
    "amplitude": "10", "amplitude_unit": "mV",
    "frequency": "1", "frequency_unit": "kHz",
    "ac_start": "10", "ac_start_unit": "Hz",
    "ac_stop": "100", "ac_stop_unit": "kHz",
    "ac_points": "100",
    "tran_stop": "2", "tran_stop_unit": "ms",
    "max_step": "1", "max_step_unit": "µs",
}

RESISTANCE_UNITS = {"Ω": 1.0, "kΩ": 1000.0, "MΩ": 1_000_000.0}
CAPACITANCE_UNITS = {"nF": 1e-9, "µF": 1e-6}
VOLTAGE_UNITS = {"V": 1.0}
AMPLITUDE_UNITS = {"mV": 1e-3, "V": 1.0}
FREQUENCY_UNITS = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6}
TIME_UNITS = {"ms": 1e-3, "µs": 1e-6}

UNIT_FACTORS: dict[str, dict[str, float]] = {
    "vcc": VOLTAGE_UNITS,
    "r1": RESISTANCE_UNITS,
    "r2": RESISTANCE_UNITS,
    "rc": RESISTANCE_UNITS,
    "re": RESISTANCE_UNITS,
    "rl": RESISTANCE_UNITS,
    "cin": CAPACITANCE_UNITS,
    "cout": CAPACITANCE_UNITS,
    "amplitude": AMPLITUDE_UNITS,
    "frequency": FREQUENCY_UNITS,
    "ac_start": FREQUENCY_UNITS,
    "ac_stop": FREQUENCY_UNITS,
    "tran_stop": TIME_UNITS,
    "max_step": TIME_UNITS,
}

FIELD_LABELS = {
    "vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC", "re": "RE", "rl": "RL",
    "cin": "Cin", "cout": "Cout", "amplitude": "Amplitude",
    "frequency": "Frequency", "ac_start": "AC start", "ac_stop": "AC stop",
    "ac_points": "AC points", "tran_stop": "Transient stop",
    "max_step": "Max step",
}

NUMBER_FIELDS = tuple(UNIT_FACTORS) + ("ac_points",)


@dataclass(frozen=True)
class SpiceInput:
    analysis: str
    vcc_v: float
    r1_ohm: float
    r2_ohm: float
    rc_ohm: float
    re_ohm: float
    rl_ohm: float
    cin_f: float
    cout_f: float
    amplitude_v: float
    frequency_hz: float
    ac_start_hz: float
    ac_stop_hz: float
    ac_points: int
    tran_stop_s: float
    max_step_s: float


@dataclass(frozen=True)
class SpiceParseResult:
    inputs: SpiceInput | None
    errors: dict[str, str]
    raw: dict[str, str]
    units: dict[str, str]


def _read(form: Mapping[str, str], field: str, raw: dict[str, str],
          units: dict[str, str], default_unit: str = "") -> str:
    value = "" if form.get(field) is None else str(form.get(field)).strip()
    raw[field] = value
    if field in UNIT_FACTORS:
        unit = "" if form.get(field + "_unit") is None else str(form.get(field + "_unit")).strip()
        unit = unit or default_unit
        units[field] = unit
        raw[field + "_unit"] = unit
    return value


def _number(text: str, label: str) -> tuple[float | None, str | None]:
    if not text:
        return None, f"กรุณากรอก {label}"
    try:
        value = float(text)
    except ValueError:
        return None, f"{label} ต้องเป็นตัวเลข"
    if not math.isfinite(value):
        return None, f"{label} ต้องเป็นค่าจำกัด"
    return value, None


def parse_spice_inputs(form: Mapping[str, str]) -> SpiceParseResult:
    raw: dict[str, str] = {}
    units: dict[str, str] = {}
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    analysis = str(form.get("analysis") or "dc").strip()
    raw["analysis"] = analysis
    if analysis not in ANALYSES:
        errors["analysis"] = "Analysis mode ไม่ถูกต้อง"
        analysis = "dc"

    for field in NUMBER_FIELDS:
        text = _read(form, field, raw, units)
        label = FIELD_LABELS[field]
        if field == "ac_points":
            value, error = _number(text, label)
            if error is None and value is not None:
                if not value.is_integer() or not 10 <= value <= 1000:
                    errors[field] = f"{label} ต้องเป็นจำนวนเต็ม 10–1000"
                else:
                    values[field] = float(int(value))
            elif error:
                errors[field] = error
            continue

        value, error = _number(text, label)
        if error:
            errors[field] = error
            continue
        factor = UNIT_FACTORS[field].get(units[field])
        if factor is None:
            errors[field] = f"หน่วยของ {label} ไม่ถูกต้อง"
            continue
        converted = value * factor
        if not math.isfinite(converted):
            errors[field] = f"{label} ต้องเป็นค่าจำกัด"
            continue
        values[field] = converted

    if "vcc" in values and not 0 < values["vcc"] <= 60:
        errors["vcc"] = "VCC ต้องอยู่ในช่วง 0–60 V"
    for field in ("r1", "r2", "rc", "re", "rl"):
        if field in values and not 0 < values[field] <= 10e6:
            errors[field] = f"{FIELD_LABELS[field]} ต้องมากกว่า 0 และไม่เกิน 10 MΩ"
    for field in ("cin", "cout"):
        if field in values and not 0 < values[field] <= 1e-3:
            errors[field] = f"{FIELD_LABELS[field]} ต้องมากกว่า 0 และไม่เกิน 1000 µF"
    if "amplitude" in values and not 0 < values["amplitude"] <= 1:
        errors["amplitude"] = "Amplitude ต้องอยู่ในช่วง 0–1 V"
    for field in ("frequency", "ac_start", "ac_stop"):
        if field in values and not 1 <= values[field] <= 1e9:
            errors[field] = f"{FIELD_LABELS[field]} ต้องอยู่ในช่วง 1 Hz–1 GHz"
    if "ac_start" in values and "ac_stop" in values and values["ac_stop"] <= values["ac_start"]:
        errors["ac_stop"] = "AC stop ต้องมากกว่า AC start"
    if "tran_stop" in values and not 1e-6 <= values["tran_stop"] <= 1.0:
        errors["tran_stop"] = "Transient stop ต้องอยู่ในช่วง 1 µs–1 s"
    if "max_step" in values and not 1e-9 <= values["max_step"] <= 1.0:
        errors["max_step"] = "Max step ต้องอยู่ในช่วง 1 ns–1 s"
    if "max_step" in values and "tran_stop" in values and values["max_step"] >= values["tran_stop"]:
        errors["max_step"] = "Max step ต้องน้อยกว่า Transient stop"

    if errors or not all(field in values for field in NUMBER_FIELDS):
        return SpiceParseResult(None, errors, raw, units)

    try:
        inputs = SpiceInput(
            analysis=analysis,
            vcc_v=values["vcc"],
            r1_ohm=values["r1"],
            r2_ohm=values["r2"],
            rc_ohm=values["rc"],
            re_ohm=values["re"],
            rl_ohm=values["rl"],
            cin_f=values["cin"],
            cout_f=values["cout"],
            amplitude_v=values["amplitude"],
            frequency_hz=values["frequency"],
            ac_start_hz=values["ac_start"],
            ac_stop_hz=values["ac_stop"],
            ac_points=int(values["ac_points"]),
            tran_stop_s=values["tran_stop"],
            max_step_s=values["max_step"],
        )
    except (KeyError, ValueError):
        return SpiceParseResult(None, errors or {"form": "ข้อมูลไม่ครบถ้วน"}, raw, units)

    return SpiceParseResult(inputs, {}, raw, units)
