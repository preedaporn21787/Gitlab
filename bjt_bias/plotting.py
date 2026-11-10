"""SVG generators for the circuit diagram and load-line chart."""

import math
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


def circuit_svg(labels: Mapping[str, str]) -> str:
    """วาดแผนภาพวงจรไบแอสแบบแบ่งแรงดันเป็นสตริง SVG.

    `labels` คือค่าที่พร้อมแสดง เช่น {"r1": "100 kΩ", "vcc": "12.0 V", ...}
    ถ้าเป็นดิกทันนีเปล่า จะวาดเฉพาะสัญลักษณ์และชื่ออุปกรณ์ ไม่มีค่า
    """

    def label_for(key: str, default: str) -> str:
        return labels.get(key, default) if labels else default

    vcc_text = label_for("vcc", "VCC")
    r1_text = label_for("r1", "R1")
    r2_text = label_for("r2", "R2")
    rc_text = label_for("rc", "RC")
    re_text = label_for("re", "RE")

    lines: list[str] = []
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 420" '
        'role="img" aria-label="วงจรไบแอสแบบแบ่งแรงดัน">'
    )
    lines.append('<title>วงจรทรานซิสเตอร์ NPN คอมมอน-อีมิเตอร์ ไบแอสแบ่งแรงดัน</title>')
    lines.append(
        '<style>.t{font-family:sans-serif;font-size:12px;fill:#1f2430;}'
        '.s{font-family:sans-serif;font-size:11px;fill:#5d6472;}'
        '.w{stroke:#1f2430;stroke-width:2;fill:none;}'
        '.c{stroke:#d6dae2;stroke-width:1;fill:none;}'
        '.g{fill:#1f2430;}</style>'
    )

    # ราง VCC ด้านบน (y=60) และกราวด์ (y=380)
    lines.append(f'<line x1="40" y1="60" x2="280" y2="60" class="w"/>')
    lines.append(f'<text x="140" y="52" class="t" text-anchor="middle">{_esc(vcc_text)}</text>')
    lines.append('<line x1="40" y1="380" x2="280" y2="380" class="w"/>')
    lines.append('<text x="30" y="392" class="s" text-anchor="end">กราวด์</text>')

    # R1: จาก VCC rail ลงมาที่โหนดเบส (x=140, y=60 → y=190)
    lines.append(f'<line x1="140" y1="70" x2="140" y2="180" class="w"/>')
    lines.append(f'<text x="100" y="135" class="t" transform="rotate(-90 100 135)">{_esc(r1_text)}</text>')
    # ขีดตัวต้านทาน R1
    for y in (90, 110, 130, 150, 170):
        lines.append(f'<line x1="130" y1="{y}" x2="150" y2="{y}" class="c"/>')

    # R2: จากโหนดเบสลงกราวด์ (x=140, y=190 → y=380)
    lines.append(f'<line x1="140" y1="200" x2="140" y2="370" class="w"/>')
    lines.append(f'<text x="180" y="300" class="t" transform="rotate(90 180 300)">{_esc(r2_text)}</text>')
    for y in (220, 240, 260, 280, 300, 320, 340, 360):
        lines.append(f'<line x1="130" y1="{y}" x2="150" y2="{y}" class="c"/>')

    # RC: จาก VCC rail ไปคอลเลกเตอร์ (x=140, y=60 → x=200, y=60 แล้วลง)
    lines.append(f'<line x1="150" y1="70" x2="190" y2="70" class="w"/>')
    lines.append(f'<line x1="190" y1="70" x2="190" y2="200" class="w"/>')
    lines.append(f'<text x="215" y="135" class="t" transform="rotate(-90 215 135)">{_esc(rc_text)}</text>')
    for x in (160, 180, 200, 220, 240):
        lines.append(f'<line x1="{x}" y1="60" x2="{x}" y2="80" class="c"/>')

    # RE: จากอิมิตเตอร์ลงกราวด์ (x=200, y=200 → x=200, y=370)
    lines.append(f'<line x1="200" y1="210" x2="200" y2="360" class="w"/>')
    lines.append(f'<text x="240" y="300" class="t" transform="rotate(90 240 300)">{_esc(re_text)}</text>')
    for y in (230, 250, 270, 290, 310, 330, 350):
        lines.append(f'<line x1="190" y1="{y}" x2="210" y2="{y}" class="c"/>')

    # สัญลักษณ์ทรานซิสเตอร์ NPN วงกลมที่ (200, 200)
    lines.append('<circle cx="200" cy="200" r="26" class="w"/>')
    lines.append('<line x1="180" y1="195" x2="220" y2="205" class="w"/>')  # ขั้วเบส
    lines.append('<line x1="175" y1="205" x2="225" y2="195" class="w"/>')  # ขั้วเบสขวาง
    lines.append(f'<text x="200" y="166" class="t" text-anchor="middle">Q₁ NPN</text>')
    lines.append(f'<text x="200" y="234" class="s" text-anchor="middle">(β)</text>')

    # โหนดเบส (x=140, y=200) เชื่อมจาก R2
    lines.append(f'<line x1="140" y1="190" x2="140" y2="200" class="w"/>')
    lines.append(f'<circle cx="140" cy="200" r="3" class="g"/>')
    lines.append(f'<text x="118" y="208" class="t">V_B</text>')

    # โหนดคอลเลกเตอร์ (x=200, y=200) เชื่อมจาก RC
    lines.append(f'<line x1="190" y1="200" x2="200" y2="200" class="w"/>')
    lines.append(f'<circle cx="200" cy="200" r="3" class="g"/>')
    lines.append(f'<text x="220" y="208" class="t">V_C</text>')

    # โหนดอิมิตเตอร์ (x=200, y=200) เชื่อมไป RE
    lines.append(f'<line x1="200" y1="200" x2="200" y2="210" class="w"/>')
    lines.append(f'<circle cx="200" cy="200" r="3" class="g"/>')
    lines.append(f'<text x="220" y="228" class="t">V_E</text>')

    # ลูกศรกระแส
    lines.append(f'<line x1="132" y1="200" x2="138" y2="200" class="w" marker-end="url(#arrow)"/>')
    lines.append(f'<text x="110" y="194" class="s">I_B</text>')
    lines.append(f'<line x1="190" y1="70" x2="190" y2="200" class="w" marker-end="url(#arrow)"/>')
    lines.append(f'<text x="212" y="130" class="s">I_C</text>')
    lines.append(f'<line x1="200" y1="210" x2="200" y2="360" class="w" marker-end="url(#arrow)"/>')
    lines.append(f'<text x="218" y="300" class="s">I_E</text>')

    lines.append(
        '<defs><marker id="arrow" markerWidth="6" markerHeight="6" '
        'refX="5" refY="3" orient="auto"><polygon points="0,0 6,3 0,6" fill="#1f2430"/></marker></defs>'
    )

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
