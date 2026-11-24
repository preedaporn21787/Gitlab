"""Netlist generation, batch execution, and raw-result parsing for ngspice."""

import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .spice_validation import SpiceInput

MODEL_NAME = "NPN_REF"
MODEL_LINE = ".model NPN_REF NPN(IS=1e-14 BF=100 VAF=100)"
FALLBACK_EXECUTABLE = Path(
    r"C:\Users\b6809393\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe"
)
ERROR_MARKERS = ("Error on line", "Simulation interrupted", "Fatal error")


@dataclass(frozen=True)
class OperatingPoint:
    vb_v: float
    ve_v: float
    vc_v: float
    vce_v: float
    ic_a: float


@dataclass(frozen=True)
class AcPoint:
    frequency_hz: float
    gain: float
    phase_deg: float


@dataclass(frozen=True)
class TransientPoint:
    time_s: float
    vin_v: float
    vout_v: float


@dataclass(frozen=True)
class SimulationResult:
    status: str
    analysis: str
    message: str
    model: str = MODEL_NAME
    engine_version: str | None = None
    netlist: str = ""
    log: str = ""
    raw_path: str | None = None
    op: OperatingPoint | None = None
    ac: tuple[AcPoint, ...] = ()
    transient: tuple[TransientPoint, ...] = ()


def executable_path() -> Path | None:
    """Resolve the batch-capable ngspice executable without trusting PATH alone."""
    configured = os.environ.get("NGSPICE_EXECUTABLE")
    if configured and Path(configured).is_file():
        return Path(configured)
    for name in ("ngspice_con", "ngspice"):
        found = shutil.which(name)
        if found:
            return Path(found)
    if FALLBACK_EXECUTABLE.is_file():
        return FALLBACK_EXECUTABLE
    return None


def engine_version(path: Path) -> str | None:
    try:
        proc = subprocess.run(
            [str(path), "-v"], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"ngspice-\d+", proc.stdout + "\n" + proc.stderr)
    return match.group(0) if match else None


def _fmt(value: float) -> str:
    return f"{value:.10g}"


def build_netlist(inputs: SpiceInput) -> str:
    """Build one netlist with exactly one analysis directive."""
    lines = [
        "* CE voltage-divider amplifier v1 - real ngspice run",
        f"VCC vcc 0 DC {_fmt(inputs.vcc_v)}",
        "VIC vcc rctop DC 0",
        f"R1 vcc base {_fmt(inputs.r1_ohm)}",
        f"R2 base 0 {_fmt(inputs.r2_ohm)}",
        f"RC rctop collector {_fmt(inputs.rc_ohm)}",
        f"RE emitter 0 {_fmt(inputs.re_ohm)}",
        f"Q1 collector base emitter {MODEL_NAME}",
        f"VIN vin 0 DC 0 AC {_fmt(inputs.amplitude_v)} "
        f"SIN(0 {_fmt(inputs.amplitude_v)} {_fmt(inputs.frequency_hz)})",
        f"Cin vin base {_fmt(inputs.cin_f)}",
        f"Cout collector vout {_fmt(inputs.cout_f)}",
        f"RL vout 0 {_fmt(inputs.rl_ohm)}",
        MODEL_LINE,
    ]
    if inputs.analysis == "ac":
        lines.append(
            f".ac dec {_fmt(float(inputs.ac_points))} "
            f"{_fmt(inputs.ac_start_hz)} {_fmt(inputs.ac_stop_hz)}"
        )
    elif inputs.analysis == "transient":
        lines.append(f".tran {_fmt(inputs.max_step_s)} {_fmt(inputs.tran_stop_s)}")
    else:
        lines.append(".op")
    lines.append(".end")
    return "\n".join(lines) + "\n"


def parse_raw_plot(raw_text: str) -> tuple[str, dict[str, list[complex]], int]:
    """Parse the first plot in an ngspice raw file into named complex arrays."""
    lines = raw_text.splitlines()
    plot_name = ""
    n_vars = 0
    n_points = 0
    var_names: list[str] = []
    values_start = -1

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("Plotname:") and not plot_name:
            plot_name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("No. Variables:"):
            n_vars = int(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("No. Points:"):
            n_points = int(stripped.split(":", 1)[1].strip())
        elif stripped == "Variables:":
            for var_line in lines[index + 1:index + 1 + n_vars]:
                parts = [part for part in var_line.split("\t") if part]
                if len(parts) >= 2:
                    var_names.append(parts[1])
        elif stripped == "Values:":
            values_start = index + 1
            break

    if not plot_name or n_vars <= 0 or n_points <= 0 or len(var_names) != n_vars:
        raise ValueError("raw file does not contain a complete plot")

    tokens: list[str] = []
    for line in lines[values_start:]:
        if not line.strip():
            continue
        parts = [part for part in re.split(r"[\t ]+", line.strip()) if part]
        if parts and re.fullmatch(r"\d+", parts[0]):
            parts = parts[1:]
        tokens.extend(parts)

    variables: dict[str, list[complex]] = {name: [] for name in var_names}
    for point_index in range(n_points):
        chunk = tokens[point_index * n_vars:(point_index + 1) * n_vars]
        if len(chunk) < n_vars:
            break
        for name, token in zip(var_names, chunk):
            if "," in token:
                real, imag = token.split(",", 1)
                variables[name].append(complex(float(real), float(imag)))
            else:
                variables[name].append(complex(float(token), 0.0))

    if any(len(values) < n_points for values in variables.values()):
        raise ValueError("raw file plot has incomplete values")
    return plot_name, variables, n_points


def _only(values: list[complex], name: str) -> float:
    if not values:
        raise ValueError(f"missing {name}")
    return values[0].real


def _extract(inputs: SpiceInput, variables: dict[str, list[complex]]):
    if inputs.analysis == "dc":
        vb = _only(variables.get("v(base)", []), "v(base)")
        ve = _only(variables.get("v(emitter)", []), "v(emitter)")
        vc = _only(variables.get("v(collector)", []), "v(collector)")
        ic = _only(variables.get("i(vic)", []), "i(vic)")
        return None, (), (), OperatingPoint(vb, ve, vc, vc - ve, ic)

    if inputs.analysis == "ac":
        freqs = variables.get("frequency", [])
        vins = variables.get("v(vin)", [])
        vouts = variables.get("v(vout)", [])
        if not (freqs and vins and vouts and len(freqs) == len(vins) == len(vouts)):
            raise ValueError("AC plot is missing frequency, vin, or vout")
        points = []
        for f, vin, vout in zip(freqs, vins, vouts):
            ratio = vout / vin if vin else complex(float("nan"), float("nan"))
            points.append(
                AcPoint(
                    frequency_hz=f.real,
                    gain=abs(ratio),
                    phase_deg=math.degrees(math.atan2(ratio.imag, ratio.real)),
                )
            )
        return None, tuple(points), (), None

    times = variables.get("time", [])
    vins = variables.get("v(vin)", [])
    vouts = variables.get("v(vout)", [])
    if not (times and vins and vouts and len(times) == len(vins) == len(vouts)):
        raise ValueError("transient plot is missing time, vin, or vout")
    points = tuple(
        TransientPoint(t.real, vin.real, vout.real)
        for t, vin, vout in zip(times, vins, vouts)
    )
    return None, (), points, None


def run_simulation(inputs: SpiceInput, timeout_s: float = 30.0) -> SimulationResult:
    """Run one real ngspice analysis and return typed values with a status."""
    netlist = build_netlist(inputs)
    exe = executable_path()
    if exe is None:
        return SimulationResult(
            status="engine_missing", analysis=inputs.analysis,
            message="ไม่พบ ngspice_con หรือ ngspice ใน PATH", netlist=netlist,
        )
    version = engine_version(exe)

    with tempfile.TemporaryDirectory(prefix="ce-sim-") as workdir:
        tmp = Path(workdir)
        (tmp / "circuit.cir").write_text(netlist, encoding="utf-8")
        try:
            proc = subprocess.run(
                [str(exe), "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"],
                cwd=tmp, capture_output=True, text=True, timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return SimulationResult(
                status="timeout", analysis=inputs.analysis,
                message=f"ngspice หมดเวลา ({timeout_s:g} s)", model=MODEL_NAME,
                engine_version=version, netlist=netlist,
            )
        except OSError as exc:
            return SimulationResult(
                status="error", analysis=inputs.analysis, message=str(exc),
                model=MODEL_NAME, engine_version=version, netlist=netlist,
            )

        log_file = tmp / "run.log"
        log = (
            log_file.read_text(encoding="utf-8", errors="replace")
            if log_file.is_file()
            else proc.stdout + "\n" + proc.stderr
        )
        raw_file = tmp / "run.raw"
        raw_text = (
            raw_file.read_text(encoding="utf-8", errors="replace")
            if raw_file.is_file() else ""
        )
        if proc.returncode != 0:
            return SimulationResult(
                status="error", analysis=inputs.analysis,
                message=f"ngspice ออกด้วยรหัส {proc.returncode}", model=MODEL_NAME,
                engine_version=version, netlist=netlist, log=log,
            )
        if not raw_text.strip() or any(marker in log for marker in ERROR_MARKERS):
            return SimulationResult(
                status="error", analysis=inputs.analysis,
                message="ngspice ไม่ได้ผลลัพธ์ที่ใช้ได้", model=MODEL_NAME,
                engine_version=version, netlist=netlist, log=log,
            )
        try:
            _, variables, _ = parse_raw_plot(raw_text)
            _, ac_points, tran_points, op = _extract(inputs, variables)
        except (ValueError, ZeroDivisionError, IndexError) as exc:
            return SimulationResult(
                status="error", analysis=inputs.analysis,
                message=f"อ่านผล ngspice ไม่สำเร็จ: {exc}", model=MODEL_NAME,
                engine_version=version, netlist=netlist, log=log,
            )
        return SimulationResult(
            status="success", analysis=inputs.analysis,
            message="จำลองสำเร็จด้วย ngspice จริง", model=MODEL_NAME,
            engine_version=version, netlist=netlist, log=log,
            raw_path="run.raw", op=op, ac=ac_points, transient=tran_points,
        )
