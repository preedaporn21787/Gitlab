"""Small, dependency-free SVG plots for real ngspice AC and transient arrays."""

import math
from collections.abc import Sequence

from .spice_engine import AcPoint, TransientPoint

WIDTH = 760
HEIGHT = 280
LEFT = 74
RIGHT = 74
TOP = 44
BOTTOM = 54
X0, X1 = LEFT, WIDTH - RIGHT
Y0, Y1 = TOP, HEIGHT - BOTTOM

GRID = "#e2e8f0"
AXIS = "#475569"
TEXT = "#334155"
GAIN_COLOR = "#2563eb"
PHASE_COLOR = "#dc2626"
VIN_COLOR = "#2563eb"
VOUT_COLOR = "#dc2626"


def _open(title: str, desc: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'role="img" aria-labelledby="plot-title plot-desc">',
        f"<title id=\"plot-title\">{title}</title>",
        f"<desc id=\"plot-desc\">{desc}</desc>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
    ]


def _frame() -> list[str]:
    return [
        f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="{AXIS}"/>',
        f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="{AXIS}"/>',
        f'<line x1="{X1}" y1="{Y0}" x2="{X1}" y2="{Y1}" stroke="{AXIS}"/>',
    ]


def _label(x: float, y: float, text: str, anchor: str = "middle") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="11" fill="{TEXT}">{text}</text>'
    )


def _legend(entries: Sequence[tuple[str, str]], start_x: float = 440.0) -> list[str]:
    parts: list[str] = []
    for index, (color, text) in enumerate(entries):
        x = start_x + index * 150
        parts.append(
            f'<line x1="{x:.1f}" y1="22" x2="{x + 22:.1f}" y2="22" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        parts.append(_label(x + 27, 26, text, "start"))
    return parts


def _polyline(coords: Sequence[tuple[float, float]], color: str) -> str:
    points = " ".join(f"{x:.2f},{y:.2f}" for x, y in coords)
    return (
        f'<polyline points="{points}" fill="none" stroke="{color}" '
        'stroke-width="2" stroke-linejoin="round"/>'
    )


def _pad(low: float, high: float, fraction: float = 0.08) -> tuple[float, float]:
    span = high - low
    if span <= 0:
        pad = max(abs(high) * fraction, 1.0)
        return low - pad, high + pad
    return low - span * fraction, high + span * fraction


def _freq_label(frequency_hz: float) -> str:
    if frequency_hz >= 1e6:
        return f"{frequency_hz / 1e6:g} MHz"
    if frequency_hz >= 1e3:
        return f"{frequency_hz / 1e3:g} kHz"
    return f"{frequency_hz:g} Hz"


def ac_svg(points: Sequence[AcPoint]) -> str:
    """Draw gain (dB) and phase (deg) against log frequency from real AC values."""
    finite = [
        p for p in points
        if math.isfinite(p.frequency_hz) and p.frequency_hz > 0
        and math.isfinite(p.gain) and math.isfinite(p.phase_deg)
    ]
    if not finite:
        return ""

    log_freqs = [math.log10(p.frequency_hz) for p in finite]
    logs_low, logs_high = _pad(min(log_freqs), max(log_freqs), 0.04)
    gain_db = [20 * math.log10(max(p.gain, 1e-12)) for p in finite]
    phases = [p.phase_deg for p in finite]
    gain_low, gain_high = _pad(min(gain_db), max(gain_db))
    phase_low, phase_high = _pad(min(phases), max(phases))

    def px(value: float) -> float:
        return X0 + (value - logs_low) / (logs_high - logs_low) * (X1 - X0)

    def py_gain(value: float) -> float:
        return Y1 - (value - gain_low) / (gain_high - gain_low) * (Y1 - Y0)

    def py_phase(value: float) -> float:
        return Y1 - (value - phase_low) / (phase_high - phase_low) * (Y1 - Y0)

    parts = _open(
        "Bode plot from ngspice AC analysis",
        "Gain in dB and phase in degrees versus logarithmic frequency, "
        "computed from the solver's v(vout)/v(vin).",
    )
    parts.extend(_frame())
    for index in range(5):
        fraction = index / 4
        y = Y1 - fraction * (Y1 - Y0)
        x = X0 + fraction * (X1 - X0)
        parts.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}"/>')
        parts.append(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{GRID}"/>')
        parts.append(_label(X0 - 8, y + 4, f"{gain_low + fraction * (gain_high - gain_low):.0f}", "end"))
        parts.append(_label(X1 + 8, y + 4, f"{phase_low + fraction * (phase_high - phase_low):.0f}", "start"))
        parts.append(_label(x, Y1 + 18, _freq_label(10 ** (logs_low + fraction * (logs_high - logs_low)))))

    parts.append(_polyline([(px(f), py_gain(g)) for f, g in zip(log_freqs, gain_db)], GAIN_COLOR))
    parts.append(_polyline([(px(f), py_phase(p)) for f, p in zip(log_freqs, phases)], PHASE_COLOR))
    parts.extend(_legend([(GAIN_COLOR, "Gain (dB)"), (PHASE_COLOR, "Phase (°)")]))

    parts.append(_label((X0 + X1) / 2, HEIGHT - 12, "Frequency (Hz)"))
    parts.append(_label(X1, HEIGHT - 2, "log scale", "end"))
    parts.append(
        f'<text x="18" y="{(Y0 + Y1) / 2:.1f}" text-anchor="middle" font-size="11" '
        f'fill="{TEXT}" transform="rotate(-90 18 {(Y0 + Y1) / 2:.1f})">Gain (dB)</text>'
    )
    parts.append(
        f'<text x="{WIDTH - 16}" y="{(Y0 + Y1) / 2:.1f}" text-anchor="middle" font-size="11" '
        f'fill="{TEXT}" transform="rotate(90 {WIDTH - 16} {(Y0 + Y1) / 2:.1f})">Phase (°)</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def transient_svg(points: Sequence[TransientPoint]) -> str:
    """Draw Vin and Vout versus time from real transient solver values."""
    finite = [
        p for p in points
        if math.isfinite(p.time_s) and math.isfinite(p.vin_v) and math.isfinite(p.vout_v)
    ]
    if not finite:
        return ""

    times_ms = [p.time_s * 1e3 for p in finite]
    x_low, x_high = _pad(min(times_ms), max(times_ms), 0.04)
    volts = [v for p in finite for v in (p.vin_v, p.vout_v)]
    y_low, y_high = _pad(min(volts), max(volts))

    def px(value: float) -> float:
        return X0 + (value - x_low) / (x_high - x_low) * (X1 - X0)

    def py(value: float) -> float:
        return Y1 - (value - y_low) / (y_high - y_low) * (Y1 - Y0)

    parts = _open(
        "Vin and Vout from ngspice transient analysis",
        "Input and output voltage versus time in milliseconds, from the solver's "
        "v(vin) and v(vout). A common-emitter stage inverts the input.",
    )
    parts.extend(_frame())
    for index in range(5):
        fraction = index / 4
        y = Y1 - fraction * (Y1 - Y0)
        x = X0 + fraction * (X1 - X0)
        parts.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}"/>')
        parts.append(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{GRID}"/>')
        parts.append(_label(X0 - 8, y + 4, f"{y_low + fraction * (y_high - y_low):.3f}", "end"))
        parts.append(_label(x, Y1 + 18, f"{x_low + fraction * (x_high - x_low):.2f}"))

    parts.append(_polyline([(px(t), py(p.vin_v)) for t, p in zip(times_ms, finite)], VIN_COLOR))
    parts.append(_polyline([(px(t), py(p.vout_v)) for t, p in zip(times_ms, finite)], VOUT_COLOR))
    parts.extend(_legend([(VIN_COLOR, "Vin"), (VOUT_COLOR, "Vout")]))

    parts.append(_label((X0 + X1) / 2, HEIGHT - 12, "Time (ms)"))
    parts.append(
        f'<text x="18" y="{(Y0 + Y1) / 2:.1f}" text-anchor="middle" font-size="11" '
        f'fill="{TEXT}" transform="rotate(-90 18 {(Y0 + Y1) / 2:.1f})">Voltage (V)</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)
