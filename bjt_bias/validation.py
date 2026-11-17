"""Parsing and validation of the BJT bias form."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .engineering import BiasInputs

BIAS_TYPES = ("voltage_divider", "fixed", "emitter_single")

BIAS_TYPE_LABELS = {
    "voltage_divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter_single": "Emitter Bias (Single Supply)",
}

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

# ค่าเริ่มต้นของหน่วยสำหรับแต่ละฟิลด์ (ใช้เมื่อไม่ส่งหน่วยมากับฟอร์ม)
DEFAULT_UNIT = {
    "vcc": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rc": "Ω",
    "re": "Ω",
    "beta": "",
    "vbe": "V",
}

# ตัวคูณแปลงเป็นหน่วยฐาน (Ω หรือ V หรือตัวเลขเปล่า)
UNIT_FACTORS = {
    "vcc": {"V": 1.0},
    "r1": {"Ω": 1.0, "kΩ": 1000.0},
    "r2": {"Ω": 1.0, "kΩ": 1000.0},
    "rc": {"Ω": 1.0, "kΩ": 1000.0},
    "re": {"Ω": 1.0, "kΩ": 1000.0},
    "beta": {"": 1.0},
    "vbe": {"V": 1.0},
}

VBE_TYPICAL_MIN_V = 0.6
VBE_TYPICAL_MAX_V = 0.8


@dataclass(frozen=True)
class ParseResult:
    """Validated inputs, per-field errors, advisory warnings, and raw text."""

    inputs: BiasInputs | None
    errors: dict[str, str]
    warnings: list[str]
    raw: dict[str, str]
    units: dict[str, str]
    bias_type: str


def _parse_number(raw_value: str | None, label: str) -> tuple[float | None, str | None]:
    text = "" if raw_value is None else str(raw_value).strip()
    if text == "":
        return None, f"กรุณากรอก {label}"
    try:
        value = float(text)
    except ValueError:
        return None, f"{label} ต้องเป็นตัวเลข"
    if not math.isfinite(value):
        return None, f"{label} ต้องเป็นค่าจำกัด (ไม่ใช่ NaN หรือ inf)"
    return value, None


def parse_inputs(form: Mapping[str, str]) -> ParseResult:
    """Validate every field, collecting all errors instead of stopping at the first."""
    raw: dict[str, str] = {}
    units: dict[str, str] = {}
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    bias_type = form.get("bias_type")
    bias_type = bias_type if bias_type in BIAS_TYPES else "voltage_divider"
    raw["bias_type"] = bias_type

    # อ่านค่า RB สำหรับ fixed bias และ emitter bias แหล่งจ่ายเดียว
    rb_text = form.get("rb")
    raw["rb"] = "" if rb_text is None else str(rb_text).strip()
    rb_unit_text = form.get("rb_unit")
    rb_unit = "" if rb_unit_text is None else str(rb_unit_text).strip()
    if not rb_unit:
        rb_unit = "kΩ"
    units["rb"] = rb_unit
    raw["rb_unit"] = rb_unit_text if rb_unit_text is not None else ""
    rb_value: float | None = None
    if bias_type in ("fixed", "emitter_single"):
        rb_value, rb_error = _parse_number(raw["rb"], "RB")
        if rb_error is None:
            factor = UNIT_FACTORS["r1"].get(rb_unit)
            if factor is None:
                errors["rb"] = "หน่วยของ RB ไม่ถูกต้อง"
            else:
                rb_value = rb_value * factor
                if not math.isfinite(rb_value):
                    errors["rb"] = "RB ต้องเป็นค่าจำกัด (ไม่ใช่ NaN หรือ inf)"
                elif rb_value <= 0:
                    errors["rb"] = "RB ต้องมากกว่า 0"
        else:
            errors["rb"] = rb_error

    # R1/R2 จำเป็นเฉพาะ voltage divider; fixed และ emitter_single ใช้ RB แทน
    divider_required = bias_type == "voltage_divider"

    for field in FIELDS:
        if field in ("r1", "r2") and not divider_required:
            # ข้ามการบังคับกรอก R1/R2 เมื่อไม่ใช่ตัวแบ่งแรงดัน
            text = form.get(field)
            raw[field] = "" if text is None else str(text).strip()
            unit_text = form.get(field + "_unit")
            unit = "" if unit_text is None else str(unit_text).strip()
            units[field] = unit if unit else DEFAULT_UNIT[field]
            raw[field + "_unit"] = unit_text if unit_text is not None else ""
            continue

        if field == "re" and bias_type == "fixed":
            # ข้ามการบังคับกรอก RE เมื่อเป็น fixed bias (อิมิตเตอร์ต่อตรงเข้ากราวด์ ไม่มี RE)
            text = form.get(field)
            raw[field] = "" if text is None else str(text).strip()
            unit_text = form.get(field + "_unit")
            unit = "" if unit_text is None else str(unit_text).strip()
            units[field] = unit if unit else DEFAULT_UNIT[field]
            raw[field + "_unit"] = unit_text if unit_text is not None else ""
            continue

        label = FIELD_LABELS[field]
        text = form.get(field)
        raw[field] = "" if text is None else str(text).strip()

        unit_text = form.get(field + "_unit")
        unit = "" if unit_text is None else str(unit_text).strip()
        units[field] = unit if unit else DEFAULT_UNIT[field]
        raw[field + "_unit"] = unit_text if unit_text is not None else ""

        value, error = _parse_number(raw[field], label)
        if error is None:
            factor = UNIT_FACTORS[field].get(units[field])
            if factor is None:
                errors[field] = f"หน่วยของ {label} ไม่ถูกต้อง"
            else:
                converted = value * factor
                if not math.isfinite(converted):
                    errors[field] = f"{label} ต้องเป็นค่าจำกัด (ไม่ใช่ NaN หรือ inf)"
                else:
                    values[field] = converted
        else:
            errors[field] = error

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "VCC ต้องมากกว่า 0"

    for field in RESISTANCE_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = f"{FIELD_LABELS[field]} ต้องมากกว่า 0"

    # R1/R2/RE ที่เว้นว่างได้: กำหนดค่า default กัน BiasInputs พัง
    if bias_type != "voltage_divider":
        values.setdefault("r1", 0.0)
        values.setdefault("r2", 0.0)
    if bias_type == "fixed":
        values.setdefault("re", 0.0)

    if "beta" in values and values["beta"] < 1:
        errors["beta"] = "β ต้องมีค่าอย่างน้อย 1"

    if "vbe" in values:
        vbe = values["vbe"]
        if vbe < 0:
            errors["vbe"] = "VBE ต้องไม่ติดลบ"
        elif "vcc" in values and vbe >= values["vcc"]:
            errors["vbe"] = "VBE ต้องน้อยกว่า VCC"

    warnings: list[str] = []
    if "vbe" in values and not (
        VBE_TYPICAL_MIN_V <= values["vbe"] <= VBE_TYPICAL_MAX_V
    ):
        warnings.append(
            f"VBE = {values['vbe']} V อยู่นอกช่วงปกติ "
            f"{VBE_TYPICAL_MIN_V}–{VBE_TYPICAL_MAX_V} V"
        )

    if errors:
        return ParseResult(
            inputs=None,
            errors=errors,
            warnings=warnings,
            raw=raw,
            units=units,
            bias_type=bias_type,
        )

    inputs = BiasInputs(
        vcc_v=values["vcc"],
        r1_ohm=values["r1"],
        r2_ohm=values["r2"],
        rc_ohm=values["rc"],
        re_ohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
        bias_type=bias_type,
        rb_ohm=rb_value if rb_value is not None else 0.0,
    )
    return ParseResult(
        inputs=inputs, errors={}, warnings=warnings, raw=raw, units=units,
        bias_type=bias_type,
    )
