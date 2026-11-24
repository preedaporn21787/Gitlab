# Debugging: Form Values and Function Inputs When Regex Changes Don't Affect Web Results

## Scenario
> **Problem**: The calculated number is correct, but after changing a regex (RE) pattern, the result on the webpage doesn't change.

> **Question**: How do you investigate the values sent from the form and the values that go into the function?

This guide follows the **systematic debugging** methodology to find the root cause.

---

## Phase 1: Root Cause Investigation

### 1. Reproduce the Issue Consistently
- Can you trigger the issue reliably?
- What are the exact steps?
  1. Submit the form with specific input values
  2. Observe the calculated result on the webpage
  3. Change the regex pattern
  4. Submit the same form values again
  5. Observe that the result hasn't changed

### 2. Check Recent Changes
- What changed that could cause this?
- Use `git diff` to see what was modified
- Look for changes to regex patterns, form handling, or data flow
- Check if the regex change is even being applied

### 3. Gather Evidence - Investigate Form Values

#### A. What values are actually sent from the form?
Since this is a Flask app, the form data is sent via `request.form`. To investigate:

**Check the raw form data:**
```python
# In your Flask route, add temporary debugging
print("Raw form data:", dict(request.form))
```

**Observe what's actually being submitted:**
- Do the input values include units (e.g., "1kΩ" vs "1000")?
- Are there extra spaces or characters?
- Is the bias_type being submitted correctly?

**In this codebase, examine `validation.py` `parse_inputs()`:**
- The function reads `form.get(field)` for each input
- Units are read separately via `form.get(field + "_unit")`
- Values are stripped: `str(text).strip()`

**Common issues:**
- Form submitting "1kΩ" but the code expects just "1" with a separate unit selector
- The unit selector might not be sending the expected value
- Extra whitespace or invisible characters

#### B. What values actually go into the function?
Trace the data flow from form → `parse_inputs()` → `analyze()`:

```
Form submission
    ↓
parse_inputs(request.form) in validation.py
    ↓
returns ParseResult with .inputs (BiasInputs) and .raw, .units
    ↓
analyze(parsed.inputs) in engineering.py
    ↓
returns AnalysisResult with primary/approximate OperatingPoints
    ↓
Results displayed in template
```

**To investigate what goes into `analyze()`:**
- Add a print statement before the function call
- Or use a debugger to inspect the `parsed` object

```python
# In app.py index() route, add:
print("=== Parsed inputs ===")
print(f"vcc_v: {parsed.inputs.vcc_v}")
print(f"r1_ohm: {parsed.inputs.r1_ohm}")
print(f"beta: {parsed.inputs.beta}")
print(f"bias_type: {parsed.inputs.bias_type}")
```

### 4. Check Data Flow at Each Boundary

**Boundary 1: Form → parse_inputs**
- Log the raw `request.form` dictionary
- Check that all expected fields are present
- Verify unit fields have expected values

**Boundary 2: parse_inputs → analyze**
- Log the `parsed.inputs` dataclass values
- Check that converted values (in ohms, volts) are correct
- Verify `bias_type` is what you expect

**Boundary 3: analyze → template**
- Log the `result` object
- Check that primary/approximate values are as expected
- Verify the region classification

### 5. Reproduce with Minimal Input
- Try the simplest possible input that triggers the calculation
- Confirm the issue exists with minimal data
- Then introduce the regex change and see if it has any effect

---

## Phase 2: Pattern Analysis

### 1. Find Working Examples
- What input values produce correct results *before* the regex change?
- Note the exact values and which bias type is selected
- Compare with values after the regex change

### 2. Compare Against References
- The reference implementation is the `parse_inputs()` function
- Read it completely - every line
- Understand exactly what it expects and what it produces

### 3. Identify Differences
Between "regex change doesn't affect result" vs "regex change affects result":

| Scenario | What's happening |
|----------|-----------------|
| **Regex not matching** | The form value doesn't match the regex, so the original value is kept |
| **Regex matching but wrong group** | The regex matches but extracts the wrong part |
| **Regex applied in wrong place** | The regex is in JavaScript but this app has no client-side JS |
| **Regex change has no effect** | The regex isn't in the data flow path at all |

### 4. Understand Dependencies
- What other components does this need?
- The app relies on form fields: vcc, r1, r2, rc, re, beta, vbe, bias_type, rb, and their units
- Changing one field's regex might not affect results if other fields determine the output

---

## Phase 3: Hypothesis and Testing

### 1. Form Single Hypothesis
> "I think the regex change isn't affecting the webpage result because: **the regex is not in the server-side data flow**, or **the form values bypass the regex**, or **the regex matches but doesn't change the parsed value**."

### 2. Test Minimally
**Hypothesis A: The regex is not being used**
- Test: Add a deliberate bad regex and see if anything changes
- Test: Remove the regex entirely and see if results change

**Hypothesis B: The form values don't go through the regex**
- Test: Submit the form with explicit values and check what `request.form` contains
- Test: Print the raw form data before parsing

**Hypothesis C: The regex matches but extracts wrong group**
- Test: Print the extracted groups from any regex
- Test: Compare the extracted value with what's actually parsed

**Hypothesis D: The regex change is in the wrong file/location**
- Test: Search all files for the regex pattern
- Test: Verify the changed file is actually being loaded

### 3. Verify Before Continuing
- Did the hypothesis explain the issue?
- If yes → proceed to Phase 4
- If no → form a new hypothesis

### 4. When You Don't Know
- Say "I don't understand X"
- Add more diagnostic instrumentation
- Trace the data flow at more boundaries

---

## Phase 4: Implementation

### 1. Create a Failing/Test Case
Before fixing, reproduce the issue with a test:
```python
# Test that form values are what we expect
def test_form_data_passes_through():
    with app.test_client() as client:
        response = client.post("/", data={
            "vcc": "12",
            "r1": "1000",
            "r1_unit": "Ω",
            "r2": "2000",
            "r2_unit": "Ω",
            "rc": "3000",
            "rc_unit": "Ω",
            "re": "1000",
            "re_unit": "Ω",
            "beta": "100",
            "vbe": "0.7",
            "bias_type": "voltage_divider",
        })
        # Check the result contains expected values
```

### 2. Implement Single Fix
Address the root cause identified:
- If regex isn't being applied → apply it in the right place
- If form values are wrong → fix form handling
- If data flow is broken → fix the boundary

### 3. Verify Fix
- Test passes now?
- No other tests broken?
- Issue actually resolved?

### 4. If Fix Doesn't Work
- STOP
- Count how many fixes you've tried
- If ≥ 3: Question the architecture
- Discuss with your human partner

---

## Phase 5: Common Causes in This Codebase

Based on the actual code structure, here are the most likely causes:

### Cause 1: Regex not in server-side path
This Flask app has **no regex** in the Python code. The parsing uses `float()` conversion. If the user changed a regex in a different context (e.g., JavaScript that was removed, or a different app), it wouldn't affect this server-rendered app.

**Fix**: Understand that this app uses unit selectors (dropdowns) + numeric input, not regex parsing of unit strings.

### Cause 2: Form unit selectors, not regex
The form uses `<select>` dropdowns for units (Ω/kΩ), and the Python code reads both the numeric value and the unit separately. Changing a regex that might have been used for unit validation wouldn't affect the calculation because the unit is handled explicitly.

**Evidence**: Look at `validation.py` lines 42-50 - `UNIT_FACTORS` converts based on explicit unit strings, not regex.

### Cause 3: Bias type changes the entire calculation path
The `bias_type` field determines which calculation function is used:
- `voltage_divider` → `solve_thevenin()` / `solve_approximate()`
- `fixed` → `solve_fixed_bias()`
- `emitter_single` → `solve_emitter_bias_single_supply()`

If the bias_type isn't changing or is defaulting to "voltage_divider", changing other regexes won't affect the result because different code paths are taken.

**Fix**: Verify the `bias_type` is being submitted and read correctly.

### Cause 4: Cached webpage or browser cache
Since this is server-rendered, the browser shouldn't cache calculation results. But if the user is looking at a cached HTML page or using the browser Back button, they might not see updated results.

**Fix**: Always click "Calculate DC Bias" fresh after making changes.

---

## Recommended Investigation Procedure

1. **Add diagnostic prints** to the Flask route:
   ```python
   parsed = parse_inputs(request.form)
   print("=== Raw form ===", dict(request.form))
   print("=== Parsed raw ===", parsed.raw)
   print("=== Parsed units ===", parsed.units)
   print("=== Parsed inputs ===", parsed.inputs)
   ```

2. **Submit the form** with known values and observe the console output

3. **Change the regex** (if there is one) and submit again

4. **Compare the before/after outputs** to find the discrepancy

5. **Trace which boundary** the discrepancy occurs at

6. **Fix the root cause** based on evidence

---

## Quick Checklist

- [ ] Did you add `print(dict(request.form))` to see actual submitted values?
- [ ] Did you print `parsed.raw` and `parsed.units` from `parse_inputs()`?
- [ ] Did you print `parsed.inputs` to see what goes into `analyze()`?
- [ ] Is the `bias_type` being submitted and read correctly?
- [ ] Are you using the correct bias type for your circuit?
- [ ] Is the webpage showing fresh results (not cached)?
- [ ] Is there actually a regex in the data flow, or are you thinking of unit selectors?

---

## If 3+ Fixes Failed: Question Architecture

If you've tried:
1. Adding debug prints
2. Verifying form data
3. Tracing the data flow
4. Checking the bias type path

And the issue persists, the architecture question is: **Is this app's design using regex for input parsing, or does it use unit selectors + explicit conversion?**

Based on the codebase, this app **does not use regex** for parsing numeric inputs - it uses `float()` conversion with explicit unit selectors. If you're seeing a "regex" issue, it may be a conceptual mismatch about how this app works.