"""SVG generators for the circuit diagram and load-line chart."""

import xml.sax.saxutils
from collections.abc import Mapping

from .engineering import BiasInputs, OperatingPoint

# สีที่สอดคล้องกับ static/style.css
INK = "#1f2430"
MUTED = "#5d6472"
LINE = "#d6dae2"
ACTIVE = "#1c5c2a"
SATURATION = "#7a4d00"
CUTOFF = "#3c424d"
ERROR = "#a4161a"


def _esc(text: str) -> str:
    return xml.sax.saxutils.escape(text, {"\"": "&quot;"})


def _zigzag(x: float, y1: float, y2: float, amplitude: float = 5, segments: int = 6) -> str:
    """คืนค่าพิกัด polyline สำหรับตัวต้านทานแบบขีซิกแซกแนวตั้ง
    จาก (x, y1) ถึง (x, y2) ซ้าย-ขวาสลับกันระหว่างทาง"""
    pts = [f"{x},{y1}"]
    step = (y2 - y1) / segments
    for i in range(1, segments):
        y = y1 + i * step
        offset = amplitude if i % 2 == 1 else -amplitude
        pts.append(f"{x + offset},{y}")
    pts.append(f"{x},{y2}")
    return " ".join(pts)


def _ground(x: float, y: float) -> list[str]:
    """สัญลักษณ์กราวด์แบบมาตรฐาน (เส้น 3 แถวความกว้างลดลง)"""
    return [
        '<g class="w">',
        f'<line x1="{x - 11}" y1="{y}" x2="{x + 11}" y2="{y}"/>',
        f'<line x1="{x - 7}" y1="{y + 4}" x2="{x + 7}" y2="{y + 4}"/>',
        f'<line x1="{x - 3}" y1="{y + 8}" x2="{x + 3}" y2="{y + 8}"/>',
        '</g>',
    ]


def circuit_svg(labels: Mapping[str, str]) -> str:
    """วาดแผนภาพวงจรไบแอสแบบแบ่งแรงดันเป็นสตริง SVG.

    เลย์เอาต์อ้างอิงภาพเป้าหมาย: ขาซ้ายคือตัวแบ่งแรงดัน (R1/R2) ขาขวาคือ RC/RE
    ทรานซิสเตอร์ NPN อยู่กลางระหว่างสองขา ป้ายอุปกรณ์เป็นอักษร Italic Serif
    `labels` คือค่าที่พร้อมแสดง เช่น {"r1": "100 kΩ", "vcc": "12.0 V", ...}
    """

    def label_for(key: str) -> str:
        return labels.get(key, "") if labels else ""

    vcc_text = label_for("vcc")
    r1_text = label_for("r1")
    r2_text = label_for("r2")
    rc_text = label_for("rc")
    re_text = label_for("re")
    beta_text = label_for("beta")

    # ตำแหน่งหลัก
    top_y = 42
    ground_y = 292
    left_x = 95
    right_x = 200
    base_x = 155
    base_y = 190
    circle_cx, circle_cy, circle_r = 163, 190, 28

    lines: list[str] = []
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 320" '
        'role="img" aria-label="วงจรไบแอสแบบแบ่งแรงดัน">'
    )
    lines.append('<title>วงจรทรานซิสเตอร์ NPN คอมมอน-อีมิเตอร์ ไบแอสแบ่งแรงดัน</title>')
    lines.append(
        '<style>'
        '.w{stroke:#1f2430;stroke-width:1.8;fill:none;}'
        '.tc{stroke:#1f2430;stroke-width:1.8;}'
        '.g{fill:#1f2430;}'
        '.lbl{font-family:Georgia,"Times New Roman",serif;font-style:italic;'
        'font-size:13px;fill:#1f2430;}'
        '</style>'
    )

    # ---------- ราง VCC ด้านบน ----------
    lines.append(f'<line x1="{left_x}" y1="{top_y}" x2="{right_x}" y2="{top_y}" class="w"/>')
    lines.append(f'<circle cx="{right_x}" cy="{top_y}" r="4" class="g"/>')
    if vcc_text:
        lines.append(
            f'<text x="{right_x}" y="{top_y - 12}" text-anchor="middle" class="lbl">'
            f'V<tspan dy="4" font-size="9">CC</tspan>'
            f'<tspan dy="-4"> = {_esc(vcc_text)}</tspan></text>'
        )

    # ---------- ขาซ้าย: ตัวแบ่งแรงดัน ----------
    # R1: จากราง VCC ลงมาที่โหนดเบส
    lines.append(f'<line x1="{left_x}" y1="{top_y}" x2="{left_x}" y2="76" class="w"/>')
    lines.append(f'<polyline points="{_zigzag(left_x, 76, 140)}" class="w"/>')
    lines.append(f'<line x1="{left_x}" y1="140" x2="{left_x}" y2="{base_y}" class="w"/>')
    # โหนดเบส + สายไปขาเบสของทรานซิสเตอร์
    lines.append(f'<circle cx="{left_x}" cy="{base_y}" r="3.5" class="g"/>')
    lines.append(f'<line x1="{left_x}" y1="{base_y}" x2="{base_x}" y2="{base_y}" class="w"/>')
    # R2: จากโหนดเบสลงกราวด์
    lines.append(f'<line x1="{left_x}" y1="{base_y}" x2="{left_x}" y2="210" class="w"/>')
    lines.append(f'<polyline points="{_zigzag(left_x, 210, 270)}" class="w"/>')
    lines.append(f'<line x1="{left_x}" y1="270" x2="{left_x}" y2="{ground_y}" class="w"/>')
    lines.extend(_ground(left_x, ground_y))

    # ---------- ขาขวา: RC และ RE ----------
    # RC: จากราง VCC ลงมาที่ขาคอลเลกเตอร์
    lines.append(f'<line x1="{right_x}" y1="{top_y}" x2="{right_x}" y2="76" class="w"/>')
    lines.append(f'<polyline points="{_zigzag(right_x, 76, 140)}" class="w"/>')
    # RE: จากขาอิมิตเตอร์ลงกราวด์
    lines.append(f'<polyline points="{_zigzag(right_x, 240, 282)}" class="w"/>')
    lines.append(f'<line x1="{right_x}" y1="282" x2="{right_x}" y2="{ground_y}" class="w"/>')
    lines.extend(_ground(right_x, ground_y))

    # ---------- ทรานซิสเตอร์ NPN ----------
    lines.append(
        f'<circle cx="{circle_cx}" cy="{circle_cy}" r="{circle_r}" '
        f'fill="#dce9f5" class="tc"/>'
    )
    # แท่งฐาน
    lines.append(f'<line x1="{base_x}" y1="178" x2="{base_x}" y2="202" class="w"/>')
    # ขาคอลเลกเตอร์: จากปลายบนของแท่งฐานขึ้นไปขวายัง RC
    lines.append(f'<line x1="{base_x}" y1="178" x2="{right_x}" y2="140" class="w"/>')
    # ขาอิมิตเตอร์: จากปลายล่างของแท่งฐานลงไปขวายัง RE
    lines.append(f'<line x1="{base_x}" y1="202" x2="{right_x}" y2="240" class="w"/>')
    # ลูกศรขาอิมิตเตอร์ของ NPN ชี้ออกนอกตัวทรานซิสเตอร์ (ลงขวา)
    lines.append('<polygon points="188.8,230.5 180.7,227.6 184.6,223.1" fill="#1f2430"/>')

    # ---------- ป้ายชื่ออุปกรณ์ ----------
    def name_label(x: float, y: float, name: str, sub: str, anchor: str) -> str:
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="lbl">'
            f'{name}<tspan dy="4" font-size="9">{sub}</tspan></text>'
        )

    def value_label(x: float, y: float, value: str, anchor: str) -> str:
        return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="lbl">{_esc(value)}</text>'

    lines.append(name_label(left_x - 14, 100, "R", "1", "end"))
    if r1_text:
        lines.append(value_label(left_x - 14, 118, r1_text, "end"))
    lines.append(name_label(left_x - 14, 240, "R", "2", "end"))
    if r2_text:
        lines.append(value_label(left_x - 14, 258, r2_text, "end"))
    lines.append(name_label(right_x + 14, 100, "R", "C", "start"))
    if rc_text:
        lines.append(value_label(right_x + 14, 118, rc_text, "start"))
    lines.append(name_label(right_x + 14, 240, "R", "E", "start"))
    if re_text:
        lines.append(value_label(right_x + 14, 258, re_text, "start"))

    # ป้ายทรานซิสเตอร์
    lines.append(name_label(right_x + 14, 168, "Q", "1", "start"))
    lines.append(f'<text x="{right_x + 14}" y="186" class="lbl">NPN</text>')
    if beta_text:
        lines.append(f'<text x="{right_x + 14}" y="204" class="lbl">(β = {_esc(beta_text)})</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def load_line_svg(inputs: BiasInputs, op: OperatingPoint) -> str:
    """วาดกราฟเส้นโหลดไลน์ I_C–V_CE เป็นสตริง SVG.

    จุด Q วาดที่ (V_CE, I_C) ของจุดทำงาน ถ้าจุดอยู่นอกช่วงแกน
    จะถูกตรึงไว้ที่ขอบและกำกับว่า "out of range"
    """
    vcc = inputs.vcc_v
    rc_plus_re = inputs.rc_ohm + inputs.re_ohm
    i_max_ma = vcc / rc_plus_re * 1000.0

    # พื้นที่วาด: viewBox 360x260, เหลือขอบสำหรับแกน
    plot_left, plot_right = 50, 330
    plot_top, plot_bottom = 30, 220

    # สเกลแกน X: 0 → VCC, แกน Y: 0 → i_max_ma
    def x_of(vce: float) -> float:
        return plot_left + (vce / vcc) * (plot_right - plot_left)

    def y_of(ic_ma: float) -> float:
        return plot_bottom - (ic_ma / i_max_ma) * (plot_bottom - plot_top)

    q_x = x_of(op.vce_v)
    q_y = y_of(op.ic_a * 1000.0)

    q_clamped_x = max(plot_left, min(plot_right, q_x))
    q_clamped_y = max(plot_top, min(plot_bottom, q_y))
    out_of_range = not (plot_left <= q_x <= plot_right and plot_top <= q_y <= plot_bottom)

    lines: list[str] = []
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 260" '
        'role="img" aria-label="กราฟเส้นโหลดไลน์ I_C–V_CE">'
    )
    lines.append('<title>กราฟเส้นโหลดไลน์และจุดทำงาน Q</title>')
    lines.append(
        '<style>.t{font-family:sans-serif;font-size:11px;fill:#1f2430;}'
        '.s{font-family:sans-serif;font-size:10px;fill:#5d6472;}'
        '.w{stroke:#1f2430;stroke-width:2;fill:none;}'
        '.c{stroke:#d6dae2;stroke-width:1;fill:none;}'
        '.q{fill:#1c5c2a;stroke:#1c5c2a;stroke-width:2;}'
        '.o{fill:#a4161a;stroke:#a4161a;stroke-width:2;}'
        '.g{fill:#1f2430;}</style>'
    )

    # เส้นกริดแนวตั้ง (ทุก 2 V หรือแบ่ง 5 tac)
    for i in range(6):
        v = vcc * i / 5.0
        x = x_of(v)
        lines.append(f'<line x1="{x}" y1="{plot_top}" x2="{x}" y2="{plot_bottom}" class="c"/>')
        lines.append(f'<text x="{x}" y="{plot_bottom + 15}" class="s" text-anchor="middle">{v:.0f}</text>')

    # เส้นกริดแนวนอน (ทุก 20% ของ i_max)
    for i in range(6):
        ic = i_max_ma * i / 5.0
        y = y_of(ic)
        lines.append(f'<line x1="{plot_left}" y1="{y}" x2="{plot_right}" y2="{y}" class="c"/>')
        lines.append(f'<text x="{plot_left - 8}" y="{y + 4}" class="s" text-anchor="end">{ic:.0f}</text>')

    # ป้ายแกน
    lines.append(f'<text x="190" y="252" class="t" text-anchor="middle">V_CE (V)</text>')
    lines.append(
        f'<text x="20" y="125" class="t" text-anchor="middle" transform="rotate(-90 20 125)">I_C (mA)</text>'
    )

    # เส้นแกน
    lines.append(f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" class="w"/>')
    lines.append(f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" class="w"/>')

    # เส้นโหลดไลน์: (0, I_max) → (VCC, 0)
    lines.append(
        f'<line x1="{plot_left}" y1="{y_of(i_max_ma)}" x2="{x_of(vcc)}" y2="{y_of(0)}" class="w"/>'
    )
    lines.append(
        f'<text x="{plot_right - 5}" y="{y_of(i_max_ma) - 5}" class="s" text-anchor="end">เส้นโหลดไลน์</text>'
    )

    # จุด Q
    if out_of_range:
        lines.append(
            f'<circle cx="{q_clamped_x}" cy="{q_clamped_y}" r="5" class="o"/>'
        )
        lines.append(
            f'<text x="{q_clamped_x}" y="{q_clamped_y - 8}" class="s" text-anchor="middle">out of range</text>'
        )
    else:
        lines.append(f'<circle cx="{q_x}" cy="{q_y}" r="5" class="q"/>')
        lines.append(
            f'<text x="{q_x}" y="{q_y - 8}" class="s" text-anchor="middle">Q</text>'
        )

    # ค่าจุด Q
    lines.append(
        f'<text x="{plot_left}" y="{plot_top - 8}" class="t">'
        f'V_CE = {op.vce_v:.2f} V, I_C = {op.ic_a * 1000:.2f} mA</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)
