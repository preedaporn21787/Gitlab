import subprocess
import sys
from pathlib import Path

import pytest

from bjt_bias.spice_engine import (
    build_netlist,
    executable_path,
    parse_raw_plot,
    run_simulation,
)
from bjt_bias.spice_validation import DEFAULTS, parse_spice_inputs


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


@pytest.mark.skipif(executable_path() is None, reason="ngspice not installed")
def test_module_version_check_reports_console_engine_without_hanging():
    project_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "bjt_bias.spice_engine"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0
    assert "ngspice_con" in proc.stdout.lower()
    assert "ngspice-47" in proc.stdout
