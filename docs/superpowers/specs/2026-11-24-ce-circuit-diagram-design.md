# CE Circuit Diagram — Design

Date: 2026-11-24  
Status: approved  
Scope: Add one reference CE voltage-divider circuit diagram to `/simulate`.

## Intent

The simulator form lists components but does not show the reference circuit. Add a single
server-drawn SVG diagram so students can connect the values in the form to the circuit that
ngspice actually runs. The target is the Lab 04 screen-target layout: a left
`Circuit & Parameters` card with the CE schematic above the fields.

## Decisions

- Add `ce_circuit_svg()` to `bjt_bias/plotting.py`; reuse the existing server-side SVG
  approach and do not add a chart or diagram library.
- Draw one circuit: `+VCC` rail, `R1`/`R2` divider, `Q1` NPN, `RC`, `RE`, `Vin` source,
  `Cin`, `Cout`, `RL`, `Vout` and a common ground rail.
- Place the SVG in `templates/simulator.html` inside the left input card, above the
  analysis fields, with a short caption that it is the same circuit as the ngspice netlist.
- Add a short note that DC sees coupling capacitors as open while AC/transient include them.
- No changes to formulas, ngspice execution, validation, plot data, or Lab 03.

## Non-goals

- No per-analysis circuit variants (DC/AC/transient) in this pass.
- No replacement of the Lab 03 bias diagrams.
- No screenshot capture in this pass; screenshot evidence remains the user's task.
