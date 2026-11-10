# BJT Common-Emitter DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Flask app that computes the DC operating point of an NPN BJT common-emitter voltage-divider bias circuit, validates input, warns on the operating region, and cross-checks its own arithmetic with an independent nodal solve.

**Architecture:** A pure-Python package `bjt_bias` holds all engineering logic (two solvers, region classification, agreement check) and returns frozen dataclasses. `app.py` is a thin Flask layer that parses the form through `bjt_bias.validation`, calls `analyze()`, and renders one server-side template. No JavaScript, no database.

**Tech Stack:** Python 3.12.7, Flask 3.x, pytest 8.x, local `.venv`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.th.md`

## Global Constraints

- Python 3.12.7; dependencies limited to `Flask>=3.0` and `pytest>=8.0` in `requirements.txt`.
- Always invoke tests as `python -m pytest` from the repo root (bare `pytest` will not put the repo root on `sys.path`, so `import bjt_bias` fails).
- `bjt_bias/` must never import Flask. Only `app.py` imports Flask.
- `templates/index.html` must contain no `<script>` tag and no arithmetic beyond display filters.
- Result numbers must never be hardcoded in `bjt_bias/`, `app.py`, or `templates/`. The golden values `1.323675` and `4.446227` may appear only under `tests/`.
- Currents are displayed in mA to 3 decimals; voltages in V to 3 decimals.
- Cross-check tolerance: `1e-9` relative difference.
- UI copy is Thai; engineering symbols stay in English (VCC, R1, β, VBE).
- Scope is DC bias only. No AC, transient, graphs, schematic editor, FET, or PNP.
- Existing `electrical.py` must not be modified.
- Commit after every task; push once at the end.

## Review Focus

Failure modes most likely to bite a user of this app, each pinned by a test in the owning task:

1. **Cutoff solved with the active-region equations** — produces negative currents and a collector voltage above the supply. Task 2 pins the short-circuit result; Task 3 pins the region label.
2. **`RE = 0` or any zero resistance** — divides by zero in the nodal solve. Task 5 rejects it before the solver is reached.
3. **Non-numeric, empty, or whitespace-only input** — a bare `float()` call raises an uncaught `ValueError` and returns HTTP 500. Task 5 rejects it; Task 6 proves the page re-renders with HTTP 200.
4. **`VBE ≥ VCC` or negative `VBE`** — yields nonsense currents or a negative base-emitter drop. Task 5 rejects it.
5. **Non-finite input (`NaN`, `inf`)** — `float("nan")` parses happily and poisons every downstream number. Task 5 rejects it.
6. **Saturation reported as if the constant-β model were valid** — I_C is an upper bound, not a physical value. Task 3 pins the warning text.

---

### Task 1: Green baseline, environment, and repo repair

**Files:**
- Create: `requirements.txt`
- Create: `bjt_bias/__init__.py`
- Modify: `test_electrical.py` (delete orphaned lines 27–32)
- Modify: `README.md` (resolve three conflict markers)

**Interfaces:**
- Consumes: nothing.
- Produces: an importable `bjt_bias` package and a passing suite that later tasks extend.

- [ ] **Step 1: Create the virtual environment and install dependencies**

Run (PowerShell, from repo root):

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install "Flask>=3.0" "pytest>=8.0"
```

- [ ] **Step 2: Write `requirements.txt`**

```
Flask>=3.0
pytest>=8.0
```

- [ ] **Step 3: Create `bjt_bias/__init__.py`**

Empty file apart from a one-line docstring: `"""BJT common-emitter DC bias calculations."""`

- [ ] **Step 4: Delete the orphaned block in `test_electrical.py`**

Delete lines 27–32, i.e. everything after the closing `if __name__ == "__main__": unittest.main()` block:

```python
if resistance_ohm <= 0:
    raise ValueError("Resistance must be positive")
     def test_invalid_resistance(self):
        for resistance in (0, -5):
            with self.assertRaises(ValueError):
                analyze_dc(12, resistance)
```

This block duplicates coverage already provided by `test_zero_resistance` and `test_negative_resistance`. Keep lines 1–26 exactly as they are.

- [ ] **Step 5: Resolve the `README.md` conflict markers**

The file currently contains `<<<<<<< HEAD`, `=======`, and `>>>>>>>` markers around two different texts: a Thai description of an automated plant-watering system, and a Thai description of this Gitlab repo for the Compro/electrical lab.

Preserve **both Thai texts verbatim**. Remove every marker line. Structure:

```markdown
# Gitlab

ใช้สำหรับเรียนแลป Compro ไฟฟ้า

## ระบบรดน้ำต้นไม้อัตโนมัติ

<the plant-watering Thai paragraph, verbatim>

## แล็บ Compro ไฟฟ้า

<the existing DC-analyzer lab description, verbatim>
```

Do not add the BJT section yet — Task 7 does that.

- [ ] **Step 6: Run the existing suite**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: `4 passed` (the four tests in `test_electrical.py`). No `IndentationError`.

- [ ] **Step 7: Commit**

```powershell
git add requirements.txt bjt_bias/__init__.py test_electrical.py README.md
git commit -m "chore: repair merge leftovers and set up venv baseline"
```

---

### Task 2: Thevenin solver and operating point

**Files:**
- Create: `bjt_bias/engineering.py`
- Test: `tests/test_engineering.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `BiasInputs(vcc_v, r1_ohm, r2_ohm, rc_ohm, re_ohm, beta, vbe_v)` — frozen dataclass, all `float`.
  - `OperatingPoint(ib_a, ic_a, ie_a, vb_v, vc_v, ve_v, vce_v)` — frozen dataclass, all `float`, SI units.
  - `solve_thevenin(inputs: BiasInputs) -> OperatingPoint`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_engineering.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt_bias.engineering'`.

- [ ] **Step 3: Implement `bjt_bias/engineering.py`**

Define the two frozen dataclasses with the field names above. Implement `solve_thevenin`:

```python
V_BB = VCC * R2 / (R1 + R2)
R_BB = R1 * R2 / (R1 + R2)
```

If `V_BB <= vbe_v`, return the declared cutoff result — `ib_a=ic_a=ie_a=0.0`, `ve_v=0.0`, `vb_v=V_BB`, `vc_v=vcc_v`, `vce_v=vcc_v` — and do not evaluate the active-region formulas. Otherwise:

```python
I_B = (V_BB - vbe_v) / (R_BB + (beta + 1) * RE)
I_C = beta * I_B
I_E = (beta + 1) * I_B
V_B = V_BB - I_B * R_BB
V_E = I_E * RE
V_C = VCC - I_C * RC
V_CE = V_C - V_E
```

`V_B` must come from `V_BB - I_B * R_BB`, never from `V_E + V_BE`; Task 4 depends on that independence.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```powershell
git add bjt_bias/engineering.py tests/test_engineering.py
git commit -m "feat: add Thevenin solver for CE bias operating point"
```

---

### Task 3: Region classification

**Files:**
- Modify: `bjt_bias/engineering.py`
- Test: `tests/test_engineering.py`

**Interfaces:**
- Consumes: `BiasInputs`, `OperatingPoint` from Task 2.
- Produces:
  - `RegionReport(region: str, label_th: str, message_th: str)` — frozen dataclass; `region` is exactly one of `"active"`, `"saturation"`, `"cutoff"`.
  - `classify_region(inputs: BiasInputs, op: OperatingPoint) -> RegionReport`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_engineering.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: FAIL with `ImportError: cannot import name 'RegionReport'`.

- [ ] **Step 3: Implement `RegionReport` and `classify_region`**

Evaluation order is fixed and matters:

1. If `V_BB <= vbe_v` (recompute `V_BB` from `inputs`) → cutoff: label `"คัตออฟ"`, message `"ทรานซิสเตอร์หยุดนำ ไม่มีกระแสคอลเลกเตอร์"`.
2. Else if `op.vce_v <= 0.3` or `op.vc_v <= op.vb_v` → saturation: label `"อิ่มตัว"`, message stating that the constant-β model is invalid here and the reported I_C is only an upper bound, including the words `"ขอบเขตบน"`.
3. Else → active: label `"แอคทีฟ"`, message `""`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: `12 passed`.

- [ ] **Step 5: Commit**

```powershell
git add bjt_bias/engineering.py tests/test_engineering.py
git commit -m "feat: classify cutoff, active, and saturation regions"
```

---

### Task 4: Independent nodal solve, agreement check, and `analyze()`

**Files:**
- Modify: `bjt_bias/engineering.py`
- Test: `tests/test_engineering.py`

**Interfaces:**
- Consumes: everything from Tasks 2 and 3.
- Produces:
  - `solve_nodal(inputs: BiasInputs) -> OperatingPoint`
  - `CheckResult(applicable: bool, max_relative_difference: float, passed: bool)` — frozen dataclass.
  - `check_agreement(primary: OperatingPoint, check: OperatingPoint) -> CheckResult`
  - `AnalysisResult(inputs, primary, check, region)` — frozen dataclass.
  - `analyze(inputs: BiasInputs) -> AnalysisResult`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_engineering.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: FAIL with `ImportError: cannot import name 'solve_nodal'`.

- [ ] **Step 3: Implement the nodal solver and agreement check**

`solve_nodal` uses KCL at the base node with `I_B = (V_B - vbe_v) / ((beta + 1) * RE)`, solved directly for `V_B`:

```python
conductance = 1 / R1 + 1 / R2 + 1 / ((beta + 1) * RE)
V_B = (VCC / R1 + vbe_v / ((beta + 1) * RE)) / conductance
```

then `I_E = (V_B - vbe_v) / RE`, `I_B = I_E / (beta + 1)`, `I_C = beta * I_B`, and the same `V_E`, `V_C`, `V_CE` relations as Task 2. Apply the same cutoff short-circuit when `V_BB <= vbe_v`, returning the identical declared result so the two methods stay comparable.

`check_agreement` computes, over the seven quantities, `max |primary - check| / max(1.0, |primary|)`. It is `applicable=False, passed=True` when `primary.ic_a == 0.0 and primary.ib_a == 0.0` (the cutoff case); otherwise `passed = difference < 1e-9`.

`analyze` returns `AnalysisResult(inputs, primary=solve_thevenin(inputs), check=check_agreement(primary, solve_nodal(inputs)), region=classify_region(inputs, primary))`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_engineering.py -q`
Expected: `20 passed` (12 previous + 4 parametrised + 4 others).

- [ ] **Step 5: Commit**

```powershell
git add bjt_bias/engineering.py tests/test_engineering.py
git commit -m "feat: add independent nodal solve and agreement check"
```

---

### Task 5: Form validation

**Files:**
- Create: `bjt_bias/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: `BiasInputs` from Task 2.
- Produces:
  - `ParseResult(inputs: BiasInputs | None, errors: dict[str, str], warnings: list[str], raw: dict[str, str])` — frozen dataclass.
  - `parse_inputs(form: Mapping[str, str]) -> ParseResult`
  - Field keys are exactly `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_validation.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_validation.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt_bias.validation'`.

- [ ] **Step 3: Implement `bjt_bias/validation.py`**

`parse_inputs` reads each key from `form`, strips it, and converts with `float()`. Reject when the key is absent, empty after stripping, not parseable, or not finite (`math.isfinite`). Then apply the range rules from the spec: `VCC > 0`; `R1, R2, RC, RE > 0`; `beta >= 1`; `0 <= VBE < VCC`. Collect every error rather than stopping at the first, keyed by field name, with a short Thai message naming the rule. Return `inputs=None` whenever `errors` is non-empty. Warnings: a single entry when `VBE` is outside `0.6–0.8` V. `raw` is the stripped-or-original string per field so the template can re-display what the user typed.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_validation.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add bjt_bias/validation.py tests/test_validation.py
git commit -m "feat: validate and parse bias form input"
```

---

### Task 6: Flask app, template, and stylesheet

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `parse_inputs` from Task 5; `analyze` from Task 4.
- Produces: `create_app() -> Flask` and a module-level `app`; Jinja filters `ma` (amps → mA string, 3 dp) and `v` (volts string, 3 dp).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_app.py`:

```python
import pytest

from app import create_app

VALID = {
    "vcc": "12", "r1": "47000", "r2": "10000",
    "rc": "4700", "re": "1000", "beta": "150", "vbe": "0.7",
}


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_renders_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "VCC" in body
    assert "<form" in body


def test_valid_post_shows_numbers(client):
    body = client.post("/", data=VALID).get_data(as_text=True)
    assert "1.324" in body      # I_C in mA
    assert "4.446" in body      # V_CE in V
    assert "แอคทีฟ" in body
    assert "ผ่าน" in body


def test_invalid_post_returns_200_with_message(client):
    response = client.post("/", data={**VALID, "r1": "abc"})
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "R1" in body
    assert "1.324" not in body


def test_invalid_post_preserves_typed_value(client):
    body = client.post("/", data={**VALID, "r1": "abc"}).get_data(as_text=True)
    assert 'value="abc"' in body


def test_zero_re_does_not_crash(client):
    response = client.post("/", data={**VALID, "re": "0"})
    assert response.status_code == 200
    assert "RE" in response.get_data(as_text=True)


def test_cutoff_case_is_labelled(client):
    body = client.post("/", data={**VALID, "r2": "1000"}).get_data(as_text=True)
    assert "คัตออฟ" in body
    assert "ไม่ใช้บังคับ" in body


def test_saturation_case_is_labelled(client):
    body = client.post(
        "/", data={**VALID, "rc": "1000", "r2": "22000", "re": "100"}
    ).get_data(as_text=True)
    assert "อิ่มตัว" in body


def test_different_input_renders_different_result(client):
    first = client.post("/", data=VALID).get_data(as_text=True)
    second = client.post("/", data={**VALID, "r2": "22000"}).get_data(as_text=True)
    assert first != second


def test_higher_vcc_raises_collector_current(client):
    low = client.post("/", data=VALID).get_data(as_text=True)
    high = client.post("/", data={**VALID, "vcc": "24"}).get_data(as_text=True)
    assert "1.324" in low
    assert "1.324" not in high


def test_template_has_no_script_tag():
    with open("templates/index.html", encoding="utf-8") as handle:
        assert "<script" not in handle.read().lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_app.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `app.py`**

```python
def create_app() -> Flask: ...
```

Register `ma` and `v` template filters. `GET /` renders `index.html` with no result. `POST /` calls `parse_inputs(request.form)`; when `result.inputs` is `None`, re-render with `result.errors`, `result.warnings`, and `result.raw`; otherwise call `analyze(result.inputs)` and render with the analysis, warnings, and raw values. Always HTTP 200. Add `app = create_app()` and `if __name__ == "__main__": app.run(debug=True)` so `python app.py` serves on `http://127.0.0.1:5000`.

- [ ] **Step 4: Implement `templates/index.html` and `static/style.css`**

One page, Thai labels with English symbols: `แรงดันไฟเลี้ยง VCC (V)`, `ตัวต้านทาน R1 (Ω)`, `R2 (Ω)`, `RC (Ω)`, `RE (Ω)`, `อัตราขยายกระแส β`, `แรงดันฐาน-อิมิตเตอร์ VBE (V)`. Each input is `<input type="text" name="vcc" value="{{ raw.get('vcc', '') }}">` — `type="text"`, not `number`, so invalid input can be re-displayed. Errors listed per field near the form. Result block shows the seven quantities with units, the region banner (`class="region-{{ region.region }}"`), and one cross-check line: `ตรวจสอบด้วยวิธี nodal: ต่างกัน {{ '%.1e'|format(check.max_relative_difference) }} ({{ 'ผ่าน' if check.passed else 'ไม่ผ่าน' }})`, plus `ไม่ใช้บังคับ` when `check.applicable` is false. No `<script>`. `style.css`: single column, max-width 640px, three banner colours (`.region-active`, `.region-saturation`, `.region-cutoff`).

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: all tests pass, including the four pre-existing `test_electrical.py` tests.

- [ ] **Step 6: Start the server and check it by hand**

Run: `.\.venv\Scripts\python app.py`
Open `http://127.0.0.1:5000`, submit `12 / 47000 / 10000 / 4700 / 1000 / 150 / 0.7`, confirm I_C = 1.324 mA, V_CE = 4.446 V, banner green, cross-check "ผ่าน". Change R2 to 22000 and confirm the numbers change. Stop the server.

- [ ] **Step 7: Commit**

```powershell
git add app.py templates/index.html static/style.css tests/test_app.py
git commit -m "feat: add Flask UI for CE bias operating point"
```

---

### Task 7: README, full verification, and push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: everything.
- Produces: the shipped repository.

- [ ] **Step 1: Add the BJT lab section to `README.md`**

Append a `## แล็บ BJT Common-Emitter DC Bias (ENG29 2121)` section that states what the app computes, lists the seven inputs, and gives the run instructions:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Then `http://127.0.0.1:5000`. Also state how to run the tests (`.\.venv\Scripts\python -m pytest -q`) and note that results are cross-checked by an independent nodal solve.

- [ ] **Step 2: Prove no results are hardcoded**

Run each; every one must return nothing:

```powershell
Select-String -Path templates\index.html -Pattern "<script"
Select-String -Path bjt_bias\engineering.py -Pattern "1\.323675|4\.446227"
Select-String -Path app.py -Pattern "1\.323675|4\.446227"
```

- [ ] **Step 3: Run the whole suite**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: all tests pass, no failures, no errors.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: document the BJT bias lab and how to run it"
```

- [ ] **Step 5: Push**

```powershell
git push origin main
```

Expected: the branch is published to `github.com/preedaporn21787/Gitlab.git`. If authentication fails, report the failure and the exact command output; do not rewrite history or force-push.
