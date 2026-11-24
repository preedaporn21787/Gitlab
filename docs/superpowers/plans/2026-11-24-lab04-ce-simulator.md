# Lab 04 CE Amplifier Simulator v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real-ngspice CE voltage-divider simulator to the existing Lab 03 Flask app without breaking its three analytical bias modes, then polish the UI and record honest B1–B8 evidence.

**Architecture:** Keep `/` and `bjt_bias/` analytical code untouched; add a parallel `/simulate` route with its own validated form, a netlist/run/parse adapter, server-drawn SVG plots, and a separate template. Each submit runs one selected analysis (`.op`, `.ac`, or `.tran`) in a temporary directory and shows only that analysis' status and data.

**Tech Stack:** Python 3.12.7, Flask in `.venv`, ngspice 47 `ngspice_con` (batch mode), Python standard library (`subprocess`, `tempfile`, `pathlib`), pytest, Jinja templates, SVG generated in Python, Impeccable skill, OpenCode browser tool.

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-ce-simulator-design.md`

## Global Constraints

- Work in `C:\Users\b6809393\Desktop\Gitlab` on branch `feature/multi-bias-types`.
- Use `.\.venv\Scripts\python` for every Python/pytest command.
- Preserve `/`, `parse_inputs`, all three Lab 03 bias modes, and all 148 existing tests unchanged in behaviour.
- Call the solver as a list argument via `subprocess.run`; never use `shell=True`; always set a timeout and a per-run temporary working directory.
- Solver executable resolution order: `NGSPICE_EXECUTABLE` env var → `shutil.which("ngspice_con")` → `shutil.which("ngspice")` → `C:\Users\b6809393\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe`.
- Use `ngspice_con`, not GUI `ngspice.exe`, for automated runs.
- One form submit runs exactly one analysis; no run may reuse old plots when it fails.
- Status values are exactly `success`, `error`, `timeout`, `engine_missing`, `invalid`.
- Default fixture values are the handout §06 values: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, RL 10 kΩ, Cin = Cout = 10 µF, source 10 mV peak / 1 kHz. They are inputs, not verified outputs.
- BJT model is `NPN_REF` with line `.model NPN_REF NPN(IS=1e-14 BF=100 VAF=100)`; the UI must label it as a local reference model, not instructor-verified.
- Vin is node `vin` (source side of Cin); Vout is node `vout` (across RL). IC is `i(vic)` from a zero-volt source between VCC and RC.
- No new third-party runtime dependencies; no React/Vite; no fabricated data or hard-coded plot traces.
- Commit only files named in each task. Do not commit `.opencode/`, `flask_server.*`, or `DEBUGGING_GUIDE.md` in this plan.

## Review Focus

- `RE = 0` and other non-positive/finite inputs must be rejected before a netlist is written — pinned by Task 1 `test_re_zero_is_rejected` and Task 4 `test_invalid_re_shows_error_without_success`.
- Missing engine, nonzero exit, empty raw, or timeout must never leave a Success badge or old plots — pinned by Task 2 `test_run_simulation_engine_missing` / `test_run_simulation_reports_nonzero_exit` and Task 4 `test_engine_failure_has_no_success_badge`.
- Changing RE or source amplitude/frequency must change actual solver output — pinned by Task 2 `test_real_dc_changes_when_re_changes` and Task 4 `test_real_transient_changes_when_amplitude_changes`.
- AC/transient plots need labelled axes, units, legend, and provenance — pinned by Task 3 `test_ac_svg_has_units_and_legend` / `test_transient_svg_has_units_and_legend` and Task 4 `test_success_page_shows_engine_and_model`.
- Desktop 1280 px and mobile 390 px must not clip graphs, units, or buttons — pinned by Task 5 screenshots at both widths with a written pass/fail note.

---

## File Structure

| File | Responsibility |
|---|---|
| `bjt_bias/spice_validation.py` (new) | Parse/limit CE form values and units; return `SpiceInput` or per-field errors. |
| `bjt_bias/spice_engine.py` (new) | Build netlist, run `ngspice_con`, parse raw/log, return typed results with status. |
| `bjt_bias/spice_plots.py` (new) | Turn parsed AC/transient arrays into labelled SVG strings. |
| `app.py` (modify) | Add `/simulate` GET/POST; leave `/` unchanged. |
| `templates/simulator.html` (new) | CE form, analysis selector, status, plots, results, provenance. |
| `static/style.css` (modify) | Add simulator layout/status/responsive styles without breaking Lab 03 classes. |
| `static/simulator.js` (new) | Show/hide AC/transient setting groups; no computation. |
| `tests/test_spice_validation.py` (new) | Validation and unit conversion tests. |
| `tests/test_spice_engine.py` (new) | Netlist, raw parser, failure-path, and real-run tests. |
| `tests/test_spice_plots.py` (new) | SVG label/legend tests. |
| `tests/test_simulate_route.py` (new) | Flask test-client success/failure/regression tests. |
| `README.md` (modify) | Document ngspice/Node install, run commands, Lab 04 status. |
| `docs/validation.md` (modify) | Append B1–B8 evidence table and screenshots. |

---

### Task 1: CE form validation

**Files:**
- Create: `bjt_bias/spice_validation.py`
- Test: `tests/test_spice_validation.py`

**Interfaces:**
- Consumes: nothing from new modules.
- Produces: `ANALYSES = ("dc", "ac", "transient")`, `DEFAULTS: dict[str, str]`, `SpiceInput`, `SpiceParseResult`, `parse_spice_inputs(form: Mapping[str, str]) -> SpiceParseResult`. `SpiceInput` fields: `analysis`, `vcc_v`, `r1_ohm`, `r2_ohm`, `rc_ohm`, `re_ohm`, `rl_ohm`, `cin_f`, `cout_f`, `amplitude_v`, `frequency_hz`, `ac_start_hz`, `ac_stop_hz`, `ac_points`, `tran_stop_s`, `max_step_s`. `SpiceParseResult` fields: `inputs: SpiceInput | None`, `errors: dict[str, str]`, `raw: dict[str, str]`, `units: dict[str, str]`.

- [x] **Step 1: Write the failing tests**

Start the file with `import pytest` and `from bjt_bias.spice_validation import DEFAULTS, parse_spice_inputs`.

```python
def test_defaults_parse_to_handout_fixture():
    r = parse_spice_inputs(dict(DEFAULTS))
    assert r.errors == {}
    assert r.inputs.vcc_v == 12.0
    assert r.inputs.r1_ohm == 100_000.0
    assert r.inputs.re_ohm == 1_000.0
    assert r.inputs.amplitude_v == pytest.approx(0.010)
    assert r.inputs.frequency_hz == 1_000.0
    assert r.inputs.cin_f == 10e-6

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
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_validation.py -v`  
Expected: FAIL with import error for `bjt_bias.spice_validation`.

- [x] **Step 3: Implement `parse_spice_inputs`**

Define per-field unit factors: resistance `Ω/kΩ/MΩ`; capacitance `nF/µF`; voltage `V`; amplitude `mV/V`; frequency `Hz/kHz/MHz`; time `ms/µs`. Use finite-float parsing, convert to SI, collect every field error, and enforce: VCC `0 < v <= 60`; resistance `0 < r <= 10e6`; capacitance `0 < c <= 1e-3`; amplitude `0 < a <= 1`; frequency/sweep `1 <= f <= 1e9` with `ac_stop > ac_start`; `ac_points` integer `10..1000`; `1e-6 <= tran_stop <= 1.0`; `1e-9 <= max_step < tran_stop`. Unknown analysis falls back to `"dc"` with an `analysis` error. Keep raw strings and chosen units in the result for redisplay.

- [x] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_validation.py -v`  
Expected: 4 passed.

- [x] **Step 5: Commit**

```bash
git add bjt_bias/spice_validation.py tests/test_spice_validation.py
git commit -m "feat: validate CE simulator inputs and units"
```

---

### Task 2: ngspice adapter and raw parser

**Files:**
- Create: `bjt_bias/spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: `SpiceInput` from Task 1.
- Produces: `MODEL_NAME`, `MODEL_LINE`, `OperatingPoint`, `AcPoint`, `TransientPoint`, `SimulationResult`, `executable_path() -> Path | None`, `engine_version(path: Path) -> str | None`, `build_netlist(inputs: SpiceInput) -> str`, `parse_raw_plot(raw_text: str) -> tuple[str, dict[str, list[complex]], int]`, `run_simulation(inputs: SpiceInput, timeout_s: float = 30.0) -> SimulationResult`. `SimulationResult` fields: `status`, `analysis`, `message`, `model`, `engine_version`, `netlist`, `log`, `raw_path`, `op`, `ac`, `transient`. `AcPoint`: `frequency_hz`, `gain`, `phase_deg`. `TransientPoint`: `time_s`, `vin_v`, `vout_v`.

- [x] **Step 1: Write the failing tests**

```python
def test_build_netlist_contains_reference_nodes_and_one_directive():
    inputs = parse_spice_inputs(dict(DEFAULTS, analysis="dc")).inputs
    net = build_netlist(inputs)
    assert ".op" in net and ".ac" not in net and ".tran" not in net
    assert "VIN vin 0 DC 0 AC 0.01 SIN(0 0.01 1000)" in net
    assert ".model NPN_REF NPN(IS=1e-14 BF=100 VAF=100)" in net
    assert "VIC vcc rctop DC 0" in net

def test_parse_raw_plot_reads_complex_ac_values():
    raw = """Title: test
Plotname: AC Analysis
Flags: complex
No. Variables: 3
No. Points: 2
Variables:
\t0\tfrequency\tfrequency\tgrid=3
\t1\tv(vin)\tvoltage
\t2\tv(vout)\tvoltage
Values:
0\t1.000000000000000e+01,0.000000000000000e+00
\t1.000000000000000e+00,0.000000000000000e+00
\t2.000000000000000e-01,1.000000000000000e-01
1\t2.000000000000000e+01,0.000000000000000e+00
\t1.000000000000000e+00,0.000000000000000e+00
\t3.000000000000000e-01,-2.000000000000000e-01
"""
    name, variables, points = parse_raw_plot(raw)
    assert name == "AC Analysis"
    assert points == 2
    assert variables["v(vout)"][1] == complex(0.3, -0.2)

def test_run_simulation_engine_missing(monkeypatch):
    monkeypatch.setattr("bjt_bias.spice_engine.executable_path", lambda: None)
    inputs = parse_spice_inputs(dict(DEFAULTS)).inputs
    result = run_simulation(inputs)
    assert result.status == "engine_missing"
    assert result.op is None and result.ac == () and result.transient == ()

def test_run_simulation_reports_nonzero_exit(monkeypatch, tmp_path):
    fake = tmp_path / "fake_engine.bat"
    fake.write_text("@echo off\necho Error on line 3 >&2\nexit /b 2\n", encoding="utf-8")
    monkeypatch.setattr("bjt_bias.spice_engine.executable_path", lambda: fake)
    inputs = parse_spice_inputs(dict(DEFAULTS)).inputs
    result = run_simulation(inputs)
    assert result.status == "error"
    assert "Error on line 3" in result.log

@pytest.mark.skipif(executable_path() is None, reason="ngspice not installed")
def test_real_dc_changes_when_re_changes():
    base = run_simulation(parse_spice_inputs(dict(DEFAULTS)).inputs)
    changed = run_simulation(parse_spice_inputs(dict(DEFAULTS, re="2")).inputs)
    assert base.status == "success" and changed.status == "success"
    assert base.op.ic_a > changed.op.ic_a
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_engine.py -v`  
Expected: FAIL with import error for `bjt_bias.spice_engine`.

- [x] **Step 3: Implement netlist builder, parser, and runner**

Build the netlist exactly as pinned in Global Constraints: VCC/VIC/R1/R2/RC/RE/Q1/VIN/Cin/Cout/RL, `MODEL_LINE`, and one analysis directive selected by `inputs.analysis`. Format numbers with `f"{value:.10g}"`. In `run_simulation`, resolve executable, create `tempfile.TemporaryDirectory()`, write `circuit.cir`, call `subprocess.run([exe, "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"], cwd=tmp, capture_output=True, text=True, timeout=timeout_s)`, then read `run.log` and `run.raw`. Treat `engine_missing`, `TimeoutExpired`, nonzero return, empty raw, or log containing `Error on line` / `Simulation interrupted` / `Fatal error` as the matching non-success status with empty data. On success call `parse_raw_plot` and populate `op` from `v(base)`, `v(emitter)`, `v(collector)`, `i(vic)`; `ac` from `frequency`, `v(vout)/v(vin)` with `phase_deg = degrees(atan2(imag, real))`; `transient` from `time`, `v(vin)`, `v(vout)`. `engine_version` parses `ngspice-47` from the `-v` banner with a 5 s timeout.

- [x] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_engine.py -v`  
Expected: 5 passed (real-run test skipped only if executable resolution fails).

- [x] **Step 5: Commit**

```bash
git add bjt_bias/spice_engine.py tests/test_spice_engine.py
git commit -m "feat: run and parse real ngspice CE analyses"
```

---

### Task 3: Result plots from parsed arrays

**Files:**
- Create: `bjt_bias/spice_plots.py`
- Test: `tests/test_spice_plots.py`

**Interfaces:**
- Consumes: `AcPoint` and `TransientPoint` from Task 2.
- Produces: `ac_svg(points: Sequence[AcPoint]) -> str`, `transient_svg(points: Sequence[TransientPoint]) -> str`. Each returns a standalone `<svg viewBox="0 0 760 280" role="img">` with `<title>` and `<desc>`, or `""` for empty input.

- [x] **Step 1: Write the failing tests**

```python
from bjt_bias.spice_engine import AcPoint, TransientPoint
from bjt_bias.spice_plots import ac_svg, transient_svg

def test_ac_svg_has_units_and_legend():
    svg = ac_svg([AcPoint(10.0, 2.0, -180.0), AcPoint(100.0, 1.0, -190.0)])
    assert "Frequency (Hz)" in svg
    assert "Gain (dB)" in svg
    assert "Phase (°)" in svg
    assert "Gain" in svg and "Phase" in svg
    assert "log" in svg.lower()

def test_transient_svg_has_units_and_legend():
    svg = transient_svg([
        TransientPoint(0.0, 0.01, -0.1),
        TransientPoint(0.001, -0.01, 0.1),
    ])
    assert "Time (ms)" in svg
    assert "Voltage (V)" in svg
    assert "Vin" in svg and "Vout" in svg
    assert "<polyline" in svg

def test_empty_points_return_empty_string():
    assert ac_svg([]) == "" and transient_svg([]) == ""
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_plots.py -v`  
Expected: FAIL with import error for `bjt_bias.spice_plots`.

- [x] **Step 3: Implement the two SVG builders**

Use only string building and `math.log10`. AC: x is log10(frequency), left y is `20*log10(gain)` in dB, right y is phase in degrees; draw axes, grid lines, two polylines, legend, and tick labels. Transient: x is time in ms, y is volts; draw axes, grid, Vin/Vout polylines, legend, and tick labels. Clamp/omit non-finite points. No external library.

- [x] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_plots.py -v`  
Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add bjt_bias/spice_plots.py tests/test_spice_plots.py
git commit -m "feat: draw labelled AC and transient SVGs"
```

---

### Task 4: Simulator route, template, and UI shell

**Files:**
- Modify: `app.py`
- Create: `templates/simulator.html`, `static/simulator.js`
- Modify: `static/style.css`
- Test: `tests/test_simulate_route.py`

**Interfaces:**
- Consumes: `parse_spice_inputs`/`DEFAULTS` (Task 1), `run_simulation`/`MODEL_NAME` (Task 2), `ac_svg`/`transient_svg` (Task 3).
- Produces: `create_app()` now exposes `GET/POST /simulate`; template context names `raw`, `units`, `errors`, `analysis`, `defaults`, `sim_result`, `ac_plot`, `tran_plot`, `engine`, `model`; status CSS classes `status-success`, `status-error`, `status-timeout`, `status-engine_missing`, `status-invalid`.

- [x] **Step 1: Write the failing route tests**

Use this preamble in `tests/test_simulate_route.py` so the snippets below are runnable:

```python
import re
from types import SimpleNamespace

import pytest

from app import create_app
from bjt_bias.spice_engine import MODEL_NAME, OperatingPoint, executable_path
from bjt_bias.spice_validation import DEFAULTS

@pytest.fixture
def client():
    return create_app().test_client()

def svg_points(data):
    return re.findall(rb'points="([^"]+)"', data)
```

```python
def test_get_simulate_shows_defaults_and_nav(client):
    resp = client.get("/simulate")
    assert resp.status_code == 200
    assert b"CE Amplifier Simulator" in resp.data
    assert b'href="/"' in resp.data
    assert b"12" in resp.data

def test_invalid_re_shows_error_without_success(client):
    resp = client.post("/simulate", data=dict(DEFAULTS, re="0"))
    assert resp.status_code == 200
    assert b"status-invalid" in resp.data
    assert b"status-success" not in resp.data

def test_success_page_shows_engine_and_model(client, monkeypatch):
    fake = SimpleNamespace(
        status="success", analysis="dc", message="ok", model=MODEL_NAME,
        engine_version="ngspice-47", netlist="* test", log="", raw_path="run.raw",
        op=OperatingPoint(1.9, 1.3, 9.2, 7.9, 0.00128), ac=(), transient=(),
    )
    monkeypatch.setattr("app.run_simulation", lambda inputs: fake)
    resp = client.post("/simulate", data=dict(DEFAULTS))
    assert b"status-success" in resp.data
    assert b"ngspice-47" in resp.data
    assert b"NPN_REF" in resp.data
    assert b"1.28" in resp.data

def test_engine_failure_has_no_success_badge(client, monkeypatch):
    fake = SimpleNamespace(
        status="engine_missing", analysis="dc", message="not found", model=MODEL_NAME,
        engine_version=None, netlist="", log="", raw_path=None,
        op=None, ac=(), transient=(),
    )
    monkeypatch.setattr("app.run_simulation", lambda inputs: fake)
    resp = client.post("/simulate", data=dict(DEFAULTS))
    assert b"status-engine_missing" in resp.data
    assert b"status-success" not in resp.data

def test_real_transient_changes_when_amplitude_changes(client):
    if executable_path() is None:
        pytest.skip("ngspice not installed")
    a = client.post("/simulate", data=dict(DEFAULTS, analysis="transient"))
    b = client.post("/simulate", data=dict(DEFAULTS, analysis="transient", amplitude="20"))
    assert b"status-success" in a.data and b"status-success" in b.data
    assert svg_points(a.data) and svg_points(b.data)
    assert svg_points(a.data) != svg_points(b.data)

def test_lab3_index_still_works(client):
    resp = client.post("/", data={"bias_type": "voltage_divider", "vcc": "12", "r1": "100",
                                  "r1_unit": "kΩ", "r2": "22", "r2_unit": "kΩ", "rc": "2.2",
                                  "rc_unit": "kΩ", "re": "1", "re_unit": "kΩ", "beta": "100",
                                  "vbe": "0.7"})
    assert resp.status_code == 200
    assert b"1.23" in resp.data
```

- [x] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_simulate_route.py -v`  
Expected: FAIL because `/simulate` returns 404 and imports do not exist.

- [x] **Step 3: Add the `/simulate` route**

In `app.py`, import the Task 1–3 interfaces and register `@app.route("/simulate", methods=["GET", "POST"])`. On GET render with `DEFAULTS` and no result. On POST call `parse_spice_inputs`; if `inputs is None`, render with `status invalid` and no plots. Otherwise call `run_simulation`, build `ac_plot`/`tran_plot` only from that run's arrays, and render `simulator.html`. Add a navigation link to `/simulate` in `index.html` only if existing tests still pass; do not alter the form or calculation path.

- [x] **Step 4: Build the template and styles**

Create `templates/simulator.html` with: header nav back to `/`; form fields prefilled from `raw` or `DEFAULTS`; radio group `analysis` with `dc/ac/transient`; shared parameter fieldset; `#ac-settings` and `#tran-settings` groups; Run button; status panel using `status-{{ sim_result.status }}`; DC table when `sim_result.op`; plot panels when `ac_plot`/`tran_plot`; provenance footer showing engine version, `MODEL_NAME`, and “local reference model”. Add matching classes to `static/style.css` using existing tokens, with a three-column desktop grid collapsing to one column at 760 px. Add `static/simulator.js` to toggle the two setting groups based on the selected radio; no physics or fetching in JS.

- [x] **Step 5: Run route and full tests**

Run: `.\.venv\Scripts\python -m pytest tests/test_simulate_route.py -v` then `.\.venv\Scripts\python -m pytest -q`  
Expected: route tests pass; full suite passes (existing 148 plus new tests).

- [x] **Step 6: Commit**

```bash
git add app.py templates/simulator.html static/style.css static/simulator.js templates/index.html tests/test_simulate_route.py
git commit -m "feat: add CE simulator page with provenance and error states"
```

---

### Task 5: Impeccable audit, browser evidence, and documentation

**Files:**
- Modify: `README.md`, `docs/validation.md`
- Create: `docs/captures/README.md` (screenshot files will be added by the user)

**Interfaces:**
- Consumes: the working app from Task 4 and the B1–B8 table in the spec.
- Produces: updated setup docs, completed B1–B8 evidence table, before/after UI notes, detector scans at 1280 px and 390 px. Screenshot files are intentionally deferred to the user.

- [x] **Step 1: Load skills and start the real server**

Load the `impeccable` skill and the `browser` skill. Start Flask with `.\.venv\Scripts\python app.py` in the background and confirm `http://127.0.0.1:5000/` and `/simulate` respond.

- [x] **Step 2: Run Impeccable critique on the running simulator**

Follow the loaded skill's critique workflow against the running `/simulate` page. Keep all calculations, mode choices, plot data, and units. Prioritize input grouping, graph readability, error states, responsive layout, engine status, and provenance. Record a short audit with the smallest useful improvement list; do not edit numerical formulas.

- [x] **Step 3: Apply polish only to UI files**

After reviewing the critique, change only `templates/simulator.html`, `static/style.css`, and `static/simulator.js`. Re-run `.\.venv\Scripts\python -m pytest -q` and confirm no calculation or route test regresses.

- [x] **Step 4: Capture real browser evidence**

Using the browser tool and Impeccable detector at ~1280 px and ~390 px, exercise B1–B8 from the spec. For B4/B5/B6, compare values or SVG point sets from two different inputs and note the engine log/version that proves the data came from real runs. Record `PASS`, `FAIL`, or `NOT RUN` honestly with the method actually used; never claim Playwright MCP unless that tool executed. Screenshot files are deferred to the user, so the evidence column records rendered DOM/detector observations instead of inventing image paths.

- [x] **Step 5: Update documentation**

In `README.md`, document ngspice 47 portable install and `ngspice_con`, the Node/npx + Impeccable install, how to run `.venv` Flask, and the two routes. In `docs/validation.md`, keep A1–A5 intact and append the B1–B8 table with inputs, expected, observed, evidence path, and status; include ngspice version, model line/name, and unresolved issues.

- [x] **Step 6: Verify and commit**

Run: `.\.venv\Scripts\python -m pytest -q` and `git status --short`.  
Expected: all tests pass; only intended files are staged. Do not stage `.opencode/`, `flask_server.*`, or `DEBUGGING_GUIDE.md`.

```bash
git add README.md docs/validation.md docs/captures
git commit -m "docs: record Lab 04 simulator verification and UI audit"
```

---

## Self-Review Checklist (completed by planner)

- Spec coverage: goals map to Tasks 1–5; UI skill to Task 5; B1–B8 to Task 5; error paths to Tasks 2/4; regression to Task 4/5.
- Every step names one test, one signature, one command, or one file set; no “handle edge cases” placeholders.
- Types/names are consistent across Tasks 1–4 (`SpiceInput`, `SimulationResult`, `AcPoint`, `TransientPoint`, `run_simulation`, `ac_svg`, `transient_svg`).
- All five Review Focus lines have a pinned test or screenshot in their owning task.
- Plan length is proportional to the spec; implementation bodies are described, not transcribed.
