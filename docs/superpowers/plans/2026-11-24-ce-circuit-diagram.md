# CE Circuit Diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one server-drawn CE voltage-divider circuit diagram to the `/simulate` page.

**Architecture:** Add `ce_circuit_svg()` to the existing `bjt_bias/plotting.py`, pass its
output from the `/simulate` route, and render it in the left input card above the form.
The diagram is static topology with a small caption; formulas, ngspice execution and
plot data are untouched.

**Tech Stack:** Python standard library, Flask/Jinja, inline SVG, pytest.

**Spec:** `docs/superpowers/specs/2026-11-24-ce-circuit-diagram-design.md`

## Global Constraints

- Work in `C:\Users\b6809393\Desktop\Gitlab` on branch `feature/multi-bias-types`.
- Use `.\.venv\Scripts\python` for Python/pytest commands.
- Do not change `bjt_bias/spice_engine.py`, `bjt_bias/spice_validation.py`, `bjt_bias/spice_plots.py`, or any Lab 03 result.
- One diagram only; no per-analysis variants.
- No new dependencies and no client-side chart library.
- Do not claim screenshot evidence; the user will capture images.

## Review Focus

- The SVG must include every labelled part so a student can map the form to the circuit.
- The diagram must remain legible at 390 px; its viewBox should scale with the card.
- The route must still render on GET and POST, including invalid-input and engine-error pages.

---

### Task 1: Add the CE circuit SVG generator

**Files:**
- Modify: `bjt_bias/plotting.py`
- Test: `tests/test_spice_plots.py`

**Interfaces:**
- Produces: `ce_circuit_svg(labels: Mapping[str, str] | None = None) -> str`
  returning an SVG string with a `role="img"` and an accessible title.

- [x] **Step 1: Write the failing test**

```python
def test_ce_circuit_svg_has_parts_and_labels():
    svg = ce_circuit_svg({"vcc": "12 V", "r1": "100 kฮฉ", "rc": "2.2 kฮฉ"})
    assert svg.startswith("<svg")
    assert 'role="img"' in svg
    for label in ("+VCC", "R1", "R2", "RC", "RE", "Q1", "Cin", "Cout", "RL", "Vin", "Vout", "GND"):
        assert label in svg
    assert "<script" not in svg.lower()
```

- [x] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_spice_plots.py::test_ce_circuit_svg_has_parts_and_labels -q`  
Expected: FAIL because `ce_circuit_svg` is not defined.

- [x] **Step 3: Implement `ce_circuit_svg`**

Draw the single CE voltage-divider topology in a `360x260` viewBox using the existing
`_zigzag()` and `_ground()` helpers where practical. Use teal strokes, ink labels and a
light-blue transistor fill. Accept optional display labels but keep the topology static.

- [x] **Step 4: Run the test to verify it passes**

Run the command from Step 2. Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add bjt_bias/plotting.py tests/test_spice_plots.py
git commit -m "feat: draw the CE reference circuit"
```

### Task 2: Render the diagram on `/simulate`

**Files:**
- Modify: `app.py`, `templates/simulator.html`, `static/style.css`
- Test: `tests/test_simulate_route.py`

**Interfaces:**
- Consumes: `ce_circuit_svg()` from Task 1.
- Produces: `circuit_svg` in the `/simulate` template context on GET and every POST branch.

- [x] **Step 1: Write the failing test**

```python
def test_simulate_page_shows_ce_circuit(client):
    html = client.get("/simulate").data
    assert b'class="sim-circuit"' in html
    assert b"CE voltage-divider" in html
    assert b"<svg" in html
    assert b"Vout" in html
```

Add a second assertion that an invalid POST still contains `class="sim-circuit"` and no
Success badge.

- [x] **Step 2: Run test to verify it fails**

Run: `.\.venv\Scripts\python -m pytest tests/test_simulate_route.py::test_simulate_page_shows_ce_circuit -q`  
Expected: FAIL because the template has no `sim-circuit` block.

- [x] **Step 3: Wire the route and template**

In every `render_template("simulator.html", ...)` call, pass
`circuit_svg=ce_circuit_svg(...)`. Insert the SVG in the left input card above the form,
with a visible caption and the DC/AC capacitor note. Add responsive CSS so the SVG scales
to the card width and does not overflow at 390 px.

- [x] **Step 4: Run the route test and the full suite**

Run: `.\.venv\Scripts\python -m pytest tests/test_simulate_route.py -q`  
Then: `.\.venv\Scripts\python -m pytest -q`  
Expected: all tests pass.

- [x] **Step 5: Commit**

```bash
git add app.py templates/simulator.html static/style.css tests/test_simulate_route.py
git commit -m "feat: show the CE circuit on the simulator page"
```
