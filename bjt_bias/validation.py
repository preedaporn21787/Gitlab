"""Parsing and validation of the BJT bias form."""

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .engineering import BiasInputs

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

    for field in FIELDS:
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
            inputs=None, errors=errors, warnings=warnings, raw=raw, units=units
        )

    inputs = BiasInputs(
        vcc_v=values["vcc"],
        r1_ohm=values["r1"],
        r2_ohm=values["r2"],
        rc_ohm=values["rc"],
        re_ohm=values["re"],
        beta=values["beta"],
        vbe_v=values["vbe"],
    )
    return ParseResult(inputs=inputs, errors={}, warnings=warnings, raw=raw, units=units)
