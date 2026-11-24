# Lab 04 — BJT CE Amplifier Simulator v1: Design

Date: 2026-11-24  
Status: approved  
Scope: Lab 04 handout sections 01–08 (through the UI skill step). Browser acceptance B1–B8 is recorded only as evidence, not as a promise of Playwright MCP availability.

## Acceptance cases from the handout (§09)

These are the exact B1–B8 cases the evidence table must cover. The method column records what actually ran; no case is marked PASS without an executed browser/tool observation.

| Case | Action | Expected / evidence |
|---|---|---|
| B1 Regression | Open Fixed / Emitter / Divider with Lab 03 values | A1–A5 values still match; read values from the page |
| B2 DC SPICE | Select CE reference, Run DC | VB/VE/VC/VCE/IC from ngspice output; model name + run status visible |
| B3 Change RE | Change only RE, run again | Operating point and/or gain changes; before/after values |
| B4 AC | Run AC, view Bode plot | Frequency axis, gain magnitude, phase, units, chart + engine output |
| B5 Transient | Run `.tran` at 10 mV peak, 1 kHz | Vin/Vout vs time, time/voltage labels, inversion direction, screenshot + phase summary |
| B6 Change Source | Change amplitude or frequency, run again | Waveform changes; before/after images |
| B7 Invalid / Fail | Set RE = 0 or simulate an unavailable engine | Clear error, no hang, no fake success; observed message |
| B8 UI | Desktop/phone viewport, switch modes | Graphs/units/buttons readable, nothing important clipped; two screenshots |

## Intent and why

Extend the existing ENG29 2121 Lab 03 Flask app into the first working Common-Emitter amplifier simulator. The student must be able to open the app, choose the reference CE voltage-divider circuit, change part/source values, run real `ngspice` DC/AC/transient analyses, read values with units and provenance, and see a usable UI on desktop and mobile. Lab 03 analytical DC bias and its tests must keep working.

## Goals

- Preserve `app.py` `/` route, all three analytical bias modes, `bjt_bias/engineering.py`, and the existing 148 tests unchanged in behaviour.
- Add one reference CE voltage-divider circuit with editable VCC, R1, R2, RC, RE, RL, Cin, Cout, source amplitude and source frequency.
- Run real `ngspice` batch analyses for that circuit:
  - DC `.op`: VB, VE, VC, VCE, IC with units and operating status.
  - AC `.ac`: frequency, `|Vout/Vin|`, phase; named Vin reference node; labelled axes.
  - Transient `.tran`: time, Vin, Vout; visible inversion and unit labels.
- Keep SPICE output and analytical Lab 03 output visually separate and labelled by source.
- Validate all form numbers before building a netlist; run the solver with a list argument, explicit timeout, and a per-run temporary directory. Never use `shell=True`.
- Show engine status, engine version, BJT model name/parameters, run timestamp and error/timeout states. Never keep old plots with a Success status.
- Apply Impeccable `critique → polish → audit` to the running UI, touching only UI files, and record desktop (~1280 px) and mobile (~390 px) evidence.
- Update README setup/run instructions and append B1–B8 evidence to `docs/validation.md`. Finish with a reviewed Git commit.

## Non-goals

- No free-form circuit editor, drag-and-drop, FET, other bias modes under SPICE, emitter bypass capacitor, animated overlays, external deployment, or new chart framework.
- No rewriting the Flask architecture or replacing the Lab 03 form.
- No fabricated traces, hard-coded “success” numbers, or derived numbers presented as solver output.

## Anti-goals (what would make this fail)

- A failed or missing `ngspice` run still showing a green Success badge and previous graphs.
- Mixing analytical and SPICE values in one unlabelled table.
- A graph without units or without a named Vin/Vout reference.
- Breaking the Lab 03 regression cases A1–A5 while adding the simulator.

## Constraints and environment findings

- Project: `C:\Users\b6809393\Desktop\Gitlab`, branch `feature/multi-bias-types`, Python 3.12.7 with Flask in `.venv`.
- `ngspice_con.exe` 47 is installed for the user at `C:\Users\b6809393\AppData\Local\Programs\ngspice-47\Spice64\bin` and is on the user PATH. Batch smoke test `ngspice_con -b -o run.log -r run.raw circuit.cir` works; the raw file contains separate `AC Analysis`, `Operating Point`, and `Transient Analysis` blocks. Use `ngspice_con`, not the GUI `ngspice.exe`, for automated runs.
- Node.js 26 portable and npx 11.20.0 are installed at `C:\Users\b6809393\AppData\Local\Programs\node-v26.13.1-win-x64`. `npx impeccable install --yes --providers=opencode --scope=project` installed Impeccable skills into `.opencode/` and engine v0.1.27.
- No instructor-verified starter kit or BJT model was supplied with the repo or Downloads. Decision: define one explicit, documented local reference model in code/config (params written in the netlist and printed in the UI), not presented as instructor-verified, and keep it easy to override. This is a builder call that should be confirmed during design approval because it changes which reference numbers the lab uses.
- Handout baseline fixture (§06), used as the form defaults and B2/B5 input: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, RL = 10 kΩ, Cin = Cout = 10 µF, source = 10 mV peak / 1 kHz. These are inputs, not verified results; a quick real `.op` check with an explicit local NPN model gave VB ≈ 1.95 V, VE ≈ 1.29 V, VC ≈ 9.19 V, IC ≈ 1.28 mA, close to the Lab 03 analytical 1.23 mA.
- Existing style: `templates/index.html` + `static/style.css`, package `bjt_bias/`. Reuse this structure; no React/Vite.
- Keep dependencies to Flask plus standard library. Draw result SVGs server-side from parsed arrays; do not add a chart library unless a real need appears.

## Approaches considered

1. **Install tools first, then integrate (chosen by the human partner).** Installed ngspice, Node/npx, and Impeccable, then build the real adapter and verify with actual runs. Highest fidelity to the handout; cost was extra setup time. Installation is already complete.
2. **Write adapter/UI first with explicit “engine unavailable” states, install later.** Faster to get code on disk, but no real plots or B2–B6 evidence until tools exist. Rejected for now, but the error states remain mandatory in the chosen approach.
3. **UI-only pass through section 08.** Rejected: it skips the real simulation requirement in section 07 and would leave no meaningful plots to polish.

## How it will be built (decided parts)

- Keep the current `/` analytical route and template intact. Add a separate `/simulate` route and `templates/simulator.html`; the header links the two pages. This gives a clean regression boundary and avoids changing `parse_inputs`.
- New backend modules under `bjt_bias/`:
  - `spice_validation.py` — parse and limit numeric/unit fields for the CE form; return per-field errors and normalized SI values.
  - `spice_engine.py` — build a netlist string from validated values, run `ngspice_con` with `subprocess.run([...], timeout=..., cwd=<temp run dir>)`, parse `.raw` into typed arrays, read `.log` for warnings/errors, and return a `SimulationResult` with status/metadata.
  - `spice_plots.py` — generate labelled SVG plots for AC magnitude/phase versus frequency and Vin/Vout versus time from the parsed arrays.
- Netlist reference: `VCC vcc 0 DC <vcc>`; `R1 vcc base`, `R2 base 0`, `RC rc_top collector`, `RE emitter 0`; a zero-volt `VIC vcc rc_top DC 0` to measure IC; `Q1 collector base emitter NPN_REF`; `VIN vin 0 DC 0 AC <amp> SIN(0 <amp> <freq>)`; `Cin vin base`, `Cout collector vout`, `RL vout 0`. Vin is measured at node `vin` (source side of Cin); Vout at node `vout` (across RL). DC sees coupling capacitors open; AC/transient include them.
- One analysis directive per run (`.op`, `.ac`, `.tran`) so each raw file has one plot and the UI never mixes analyses. **One form submit runs exactly one selected analysis**, chosen by the radio/tab; tabs select what the next Run will execute, not three analyses in one request. Status is therefore a single Success/Error/Timeout for that run. Default sweep/stop values are editable only if needed for B4/B5; bounds are enforced.
- UI: simulator page uses a three-column desktop layout (parameters | plots | results), stacked at narrow widths. Analysis tabs are radio-style controls with visible labels. Include status badge, engine version, model badge, run timestamp, units in every axis and table, legends, and an error panel. Use small progressive-enhancement JS only for tab switching/default population.
- UI refinement will use the Impeccable skill on the running page, restricted to `templates/simulator.html`, `static/style.css`, and any small `static/simulator.js`. Numerical formulas and real plot data are off-limits to that pass.
- Verification order: unit tests for validation/parser; Flask test-client checks that `/` still passes A1–A5 and `/simulate` handles success and failure; real `ngspice` runs for the baseline fixture; browser snapshots at desktop and mobile widths; then B1–B8 recorded honestly in `docs/validation.md`.

## Left to the builder (explicit builder calls)

- Exact BJT model parameter values and final default sweep/time ranges, chosen by real runs and recorded in the UI/docs.
- SVG sizing, colour tokens, responsive breakpoints, and whether tab switching uses a few lines of JS or CSS-only controls.
- File names for screenshots and how to capture them with the available browser tool; claim Playwright MCP only if that tool is actually used.
- Whether to commit the Impeccable `.opencode/` installation or leave it untracked; decide from its contents and repo conventions at commit time.

A reviewer will read this document before implementation and may return a short list of questions; those will be resolved before work starts.
