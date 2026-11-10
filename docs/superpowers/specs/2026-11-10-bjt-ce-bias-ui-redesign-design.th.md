# เอกสารออกแบบ: ปรับหน้าเว็บเป็น UI แลป 3 คอลัมน์ + แผนภาพวงจร + เส้นโหลดไลน์ + วิธีคำนวณสองแบบ

วันที่: 2026-11-10
สถานะ: รออนุมัติ
ขนาดงาน: โปรเจกต์ (หลายส่วนงาน)
ต่อยอดจาก: `2026-11-10-bjt-ce-bias-design.th.md` (สเปกเดิมยังมีผลในส่วนที่เอกสารนี้ไม่แก้)

## เจตนา (Intent)

อาจารย์กำหนด UI เป้าหมายของแลปเป็นหน้าเดียว 3 คอลัมน์ (อินพุต | วงจร | ผลลัพธ์)
พร้อมส่วนหัว ที่มีชื่อแลปและตราสัญลักษณ์รายวิชา ผู้ใช้ส่งภาพเป้าหมายมาและระบุว่า
"ประมาณนี้"

หน้าเว็บปัจจุบันเป็นฟอร์มแนวตั้งคอลัมน์เดียว ไม่มีภาพวงจร ไม่มีกราฟ
และแสดงวิธีคำนวณเดียว จึงยังไม่ตรงกับเป้าหมายของแลป

เป้าหมายของงานนี้: ทำให้หน้าเว็บมีหน้าตาและการทำงานใกล้เคียงภาพเป้าหมาย
โดยยังคงความถูกต้องทางวิศวกรรมและเทสต์ที่มีอยู่

## สิ่งที่ผู้ใช้ตัดสินใจแล้ว (Decisions)

| หัวข้อ | ข้อสรุป |
|---|---|
| ภาษา | **ผสม** — ป้าย/หัวข้อ/ปุ่ม/ตารางเป็นอังกฤษ, ข้อความ error และคำเตือนเป็นไทย, คำอธิบายล่างหน้าเป็นไทย |
| หน่วย | **มี dropdown หน่วย** สำหรับตัวต้านทาน (Ω / kΩ) |
| วิธีคำนวณ | **แสดงทั้งสองวิธีเทียบกัน** — exact เป็นหลัก, approximate แสดงคู่กัน |

## เป้าหมาย (Goals)

- เลย์เอาต์ 3 คอลัมน์ตามภาพ: Input Parameters | Circuit | DC Bias Results
- ส่วนหัวมีชื่อแลป ชื่อรายวิชา และตราสัญลักษณ์ (วาดด้วย SVG ในหน้า ไม่ใช้ไฟล์ภาพนอก)
- แผนภาพวงจรแสดงค่าอุปกรณ์จริงที่ผู้ใช้กรอก (เช่น R1 100 kΩ) และอัปเดตตามอินพุต
- ตารางผลลัพธ์มีสองคอลัมน์: Exact และ Approx. พร้อมบรรทัดบอกส่วนต่างระหว่างวิธี
- กราฟเส้นโหลดไลน์ I_C–V_CE พร้อมจุด Q (ตามที่ผู้ใช้เลือกไว้ก่อนหน้า)
- แบนเนอร์เขตการทำงาน (เขียว/เหลือง/เทา) พร้อมบรรทัดเหตุผลเชิงตัวเลข
- คง invariant เดิม: **ไม่มี JavaScript**, ไม่มี dependency ใหม่, ทุกภาพเป็น SVG
- รองรับหน้าจอแคบ: 3 คอลัมน์ → 2 → 1

## สิ่งที่ไม่ทำ (Non-goals)

- ไม่มี AC / transient / กราฟตอบสนองความถี่
- ไม่มี interactive zoom, pan, hover tooltip, ปุ่มดาวน์โหลด
- ไม่มี schematic editor หรือเลือกอุปกรณ์จากคลัง
- ไม่รองรับ PNP หรือ FET
- ไม่มี dropdown หน่วย mV / MΩ / µA (ตามที่ผู้ใช้เลือก "V / kΩ")
- ไม่เปลี่ยนวิธี exact ที่มีอยู่ และไม่แตะ `electrical.py`

## สิ่งที่ถือว่าล้มเหลว (Anti-goals)

- หน้าเว็บใช้ JavaScript หรือเพิ่ม dependency ภายนอก
- แผนภาพวงจรแสดงค่าคงที่ตายตัว ไม่เปลี่ยนตามอินพุต
- จุด Q บนกราฟไม่อยู่บนเส้นโหลดไลน์
- ตัวเลข Exact กับ Approx. สลับกันหรือปนกันจนอ่านไม่ออก
- เทสต์ที่ผ่านเพราะ assertion ล้น (เช่น assert แค่ status 200)
- การแปลงหน่วยผิดเงียบ ๆ (กรอก 100 kΩ แล้วคำนวณเป็น 100 Ω)

## ข้อจำกัด (Constraints)

- Python 3.12, Flask 3.1, pytest 9.2 — ห้ามเพิ่ม dependency
- เทมเพลตห้ามมี `<script>` (มีเทสต์ล็อกไว้แล้ว)
- `bjt_bias/` ต้องไม่ import Flask
- เทสต์รันด้วย `.\.venv\Scripts\python -m pytest -q` จากราก repo
- ต้องรันบน PowerShell 5.1 / Windows ได้ (ไฟล์ `.ps1` ต้องเป็น ASCII)

## แนวทางที่พิจารณา (Approaches)

### 1. SVG สร้างฝั่งเซิร์ฟเวอร์ + ไฟล์นิ่งสำหรับส่วนหัว — **เลือกใช้**

`bjt_bias/plotting.py` เป็นฟังก์ชันบริสุทธิ์คืนสตริง `<svg>` ทั้งก้อน
ไอคอนในส่วนหัวและแผนภาพวงจรวาดด้วย SVG เช่นกัน

- ข้อดี: ไม่เพิ่ม dependency, ไม่ใช้ JS, สีตรงกับ CSS, ทดสอบได้ด้วยการ parse XML,
  คมทุกขนาดซูม พิมพ์ลงรายงานได้
- ข้อเสีย: ต้องเขียนพิกัด SVG เอง

### 2. Chart.js / Canvas ฝั่งเบราว์เซอร์ — **ตัดออก**

- ตัดเพราะ: ผิด invariant "ห้ามมี `<script>`" ที่มีเทสต์ล็อกอยู่ และสเปกเดิม
  ระบุ no-JS เป็น anti-goal อีกทั้งต้องพึ่ง CDN

### 3. Matplotlib สร้าง PNG — **ตัดออก**

- ตัดเพราะ: เพิ่ม dependency, เป็น raster ที่แตกเมื่อพิมพ์, ตั้งสีให้ตรง CSS ยาก,
  ต้องจัดการไฟล์ชั่วคราว

## การออกแบบ (Design)

### 1. เลย์เอาต์และภาษา

```
┌───────────────────────────────────────────────────────────────┐
│ [chip icon] Lab 02: BJT DC Bias Web App     [code icon]       │
│             ENG29 2121 – Common Emitter      Computer         │
│             (Voltage Divider Bias)           Programming for  │
│                                              Electrical Eng.  │
├────────────────┬────────────────────┬─────────────────────────┤
│ Input          │ Circuit:           │ DC Bias Results         │
│ Parameters     │ Common-Emitter     │ ┌─────────────────────┐ │
│                │ Amplifier          │ │ V_B  exact  approx  │ │
│ V_CC [12.0][V] │                    │ │ ...                 │ │
│ R_1 [100][kΩ]  │   (SVG schematic)  │ └─────────────────────┘ │
│ ...            │                    │ [Active region banner]  │
│ [Calculate]    │                    │                         │
├────────────────┴────────────────────┴─────────────────────────┤
│ [Week 2 Goal banner]                                          │
├───────────────────────────────────────────────────────────────┤
│ Thai explanation paragraph                                    │
└───────────────────────────────────────────────────────────────┘
```

- CSS Grid: `grid-template-columns: 1fr 1.15fr 1fr`
- Breakpoint: ≤ 1100px → 2 คอลัมน์ (อินพุต | ผลลัพธ์, วงจรเต็มความกว้าง)
  ≤ 760px → 1 คอลัมน์
- ภาษา: อังกฤษสำหรับ UI ทั้งหมด; ไทยสำหรับ error, warning, และย่อหน้าอธิบายล่าง

### 2. ฟอร์มอินพุตและหน่วย

| ฟิลด์ | ป้าย | หน่วย |
|---|---|---|
| `vcc` | V_CC (Supply Voltage) | V (ป้ายนิ่ง) |
| `r1` | R_1 (Upper Divider) | Ω / kΩ (dropdown) |
| `r2` | R_2 (Lower Divider) | Ω / kΩ (dropdown) |
| `rc` | R_C (Collector Resistor) | Ω / kΩ (dropdown) |
| `re` | R_E (Emitter Resistor) | Ω / kΩ (dropdown) |
| `beta` | β (Current Gain) | – (ป้ายนิ่ง) |
| `vbe` | V_BE (Base-Emitter Voltage) | V (ป้ายนิ่ง) |

**การตัดสินใจของผู้สร้าง:** ฟิลด์แรงดันมีหน่วยเดียว (V) จึงใช้ป้ายนิ่งที่จัดสไตล์
ให้กว้างเท่า dropdown เพื่อให้คอลัมน์ตรงกัน แทน `<select>` ที่มีตัวเลือกเดียว
(ซึ่งกดแล้วไม่มีอะไรเกิดขึ้น)

**การแปลงหน่วย:** `UNIT_FACTORS` ใน `bjt_bias/validation.py`

```python
UNIT_FACTORS = {
    "vcc": {"V": 1.0},
    "r1": {"Ω": 1.0, "kΩ": 1000.0},
    "r2": {"Ω": 1.0, "kΩ": 1000.0},
    "rc": {"Ω": 1.0, "kΩ": 1000.0},
    "re": {"Ω": 1.0, "kΩ": 1000.0},
    "beta": {"": 1.0},
    "vbe": {"V": 1.0},
}
```

- ชื่อฟิลด์หน่วยในฟอร์ม: `<field>_unit` เช่น `r1_unit`
- หน่วยที่หายไปจากฟอร์ม → ใช้หน่วยแรกของฟิลด์นั้น (ค่าเริ่มต้น) เพื่อความเข้ากันได้ย้อนหลัง
- หน่วยที่ไม่รู้จัก → error ภาษาไทย: `"หน่วยของ R1 ไม่ถูกต้อง"`
- ค่าที่แปลงแล้วต้องยังเป็นค่าจำกัด (finite) มิฉะนั้น error
- `ParseResult` เพิ่มฟิลด์ `units: dict[str, str]` เพื่อคงหน่วยที่เลือกไว้แสดงซ้ำ

### 3. วิธีคำนวณที่สอง (Approximate)

ฟังก์ชันใหม่ใน `bjt_bias/engineering.py`:

```python
def solve_approximate(inputs: BiasInputs) -> OperatingPoint:
    """Solve assuming the base current does not load the divider."""
    v_bb, _ = _thevenin_equivalent(inputs)
    if v_bb <= inputs.vbe_v:
        return _cutoff_point(v_bb, inputs.vcc_v)

    v_b = v_bb
    v_e = v_b - inputs.vbe_v
    i_e = v_e / inputs.re_ohm
    i_b = i_e / (inputs.beta + 1.0)
    i_c = inputs.beta * i_b
    v_c = inputs.vcc_v - i_c * inputs.rc_ohm
    return OperatingPoint(
        ib_a=i_b, ic_a=i_c, ie_a=i_e,
        vb_v=v_b, vc_v=v_c, ve_v=v_e, vce_v=v_c - v_e,
    )
```

- ตัดสินใจของผู้สร้าง: ยังคง `I_C = β/(β+1)·I_E` (ไม่ประมาณเป็น `I_C ≈ I_E`)
  เพื่อให้ KCL ภายในผลลัพธ์สอดคล้องกันเอง
- ใช้ `_cutoff_point` ตัวเดียวกับวิธีอื่น → พฤติกรรมคัตออฟสม่ำเสมอ

`AnalysisResult` เพิ่มสองฟิลด์:

```python
@dataclass(frozen=True)
class AnalysisResult:
    inputs: BiasInputs
    primary: OperatingPoint      # exact (Thevenin)
    approximate: OperatingPoint  # approximate
    method_gap: float            # ส่วนต่างสูงสุดระหว่างสองวิธี (สัดส่วน)
    check: CheckResult           # exact vs nodal
    region: RegionReport
```

- แยกตัวช่วย `_max_relative_difference(a, b) -> float` ออกมาใช้ทั้ง
  `check_agreement` และการคำนวณ `method_gap` (ตรรกะเดิม: หารด้วย `max(1, |a|)`)

### 4. เขตการทำงาน — ข้อความอังกฤษ + คำอธิบายไทย

`RegionReport` เพิ่ม `label_en` และ `detail_en` (คง `label_th` / `message_th` เดิม):

| region | label_en | detail_en ตัวอย่าง |
|---|---|---|
| active | `Active region` | `V_CE = 8.052 V > 0.3 V` |
| saturation | `Saturation` | `V_CE = -5.155 V <= 0.3 V` |
| cutoff | `Cutoff` | `V_BB = 0.250 V <= V_BE = 0.700 V` |

- **ตัดสินใจของผู้สร้าง:** คงเกณฑ์อิ่มตัวที่ 0.3 V ตามสเปกเดิม ไม่เปลี่ยนเป็น 0.2 V
  ตามภาพเป้าหมาย เพราะสเปกเดิมคือเอกสารอ้างอิงที่อนุมัติแล้ว
- แบนเนอร์แสดง `label_en` + `detail_en` และถ้ามี `message_th` ให้แสดงเป็นบรรทัดเล็กใต้ลงมา

### 5. แผนภาพวงจร — `bjt_bias/plotting.py::circuit_svg`

```python
def circuit_svg(labels: Mapping[str, str]) -> str: ...
```

- `labels` คือข้อความที่พร้อมแสดง เช่น `{"vcc": "12.0 V", "r1": "100 kΩ", ...}`
  (สร้างจาก `raw` + หน่วยที่เลือก ไม่ใช่ค่าที่แปลงแล้ว เพื่อให้ตรงกับที่ผู้ใช้พิมพ์)
- ถ้า `labels` ว่าง (หน้า GET) วาดเฉพาะสัญลักษณ์และชื่ออุปกรณ์ ไม่มีค่า
- องค์ประกอบ: ราง VCC ด้านบน, R1 ลงมาที่โหนดเบส, R2 ลงกราวด์, RC ไปคอลเลกเตอร์,
  RE ไปอิมิตเตอร์, สัญลักษณ์ NPN, จุดต่อและป้าย V_B / V_C / V_E,
  ลูกศรกระแส I_B / I_C / I_E
- `viewBox="0 0 320 420"`, สีอ้างจากชุดเดียวกับ CSS (ส่งเป็นค่าคงที่ใน Python)
- มี `role="img"` และ `<title>`
- ข้อความที่แสดงต้องถูก escape ด้วย `xml.sax.saxutils.escape` ก่อนฝัง

### 6. เส้นโหลดไลน์ — `bjt_bias/plotting.py::load_line_svg`

```python
def load_line_svg(inputs: BiasInputs, op: OperatingPoint) -> str: ...
```

- แกน X: V_CE ตั้งแต่ 0 ถึง VCC; แกน Y: I_C ตั้งแต่ 0 ถึง `VCC/(RC+RE)` หน่วย mA
- เส้นโหลดไลน์จาก `(0, VCC/(RC+RE))` ถึง `(VCC, 0)`
- จุด Q ที่ `(op.vce_v, op.ic_a)`
- ถ้าจุด Q อยู่นอกช่วงแกน ให้ตรึงไว้ที่ขอบและกำกับข้อความ `out of range`
- `viewBox="0 0 360 260"`, มีเส้นกริดและ tick อย่างน้อย 5 ค่า
- มี `role="img"` และ `<title>`

### 7. ชั้นเว็บ — `app.py`

- ตัวกรองใหม่: `ua` (แอมป์ → µA, 1 ตำแหน่ง), คง `ma` (mA, 2 ตำแหน่ง) และ `v` (V, 3 ตำแหน่ง)
  - **ตัดสินใจของผู้สร้าง:** ลดทศนิยมลงเป็น 2 ตำแหน่งสำหรับกระแส เพื่อให้ตารางอ่านง่าย
    และตรงกับภาพเป้าหมาย (1.50 mA / 15.1 µA)
- ตัวช่วย `_display_labels(parsed) -> dict[str, str]` สร้างข้อความสำหรับแผนภาพ
- ส่งเข้าเทมเพลต: `raw`, `units`, `errors`, `warnings`, `result`,
  `circuit_svg` (มีเสมอ), `chart_svg` (เฉพาะเมื่อมีผลลัพธ์)
- เทมเพลตเรนเดอร์ SVG ด้วย `|safe`
  - **เหตุผลที่ปลอดภัย:** สตริง SVG ประกอบจากตัวเลขที่ฟอร์แมตด้วยโค้ดเราเอง
    และข้อความที่ผ่าน `escape()` แล้ว ไม่มีข้อความผู้ใช้ดิบถูกแทรก

### 8. เทมเพลต — `templates/index.html`

- เขียนใหม่ทั้งไฟล์ คง invariant: ไม่มี `<script>`
- โครง: `<header>` → `<div class="layout">` (3 `<section>`) → `<aside class="goal">`
  → `<footer class="notes">`
- ทุก `<input>` มี `<label for>`; ทุก dropdown มี `<label>` ที่ผูกด้วย `for`
- error แสดงใต้ฟิลด์ด้วย `<p class="error">` (คงไว้ตามเทสต์เดิม)
- ค่าที่พิมพ์ไว้ต้องคงอยู่หลัง POST (ทั้งตัวเลขและหน่วย)

### 9. สไตล์ — `static/style.css`

- เขียนใหม่ทั้งไฟล์
- พาเลตต์: teal `#0f766e` (หัวข้อ/ปุ่ม), พื้น `#f1f5f9`, การ์ดขาว, เส้น `#dbe2ea`,
  ตัวอักษร `#1f2430`, เขต active เขียว, saturation เหลืองอำพัน, cutoff เทา
- การ์ดมีหัวข้อพร้อมไอคอน SVG ขนาดเล็ก
- ปุ่มเต็มความกว้าง สี teal, hover เข้มขึ้น
- ตัวเลขในตารางใช้ `font-variant-numeric: tabular-nums`

### 10. เทสต์

**`tests/test_validation.py` (แก้ + เพิ่ม)**
- แปลง `100` + `kΩ` → `100000.0` Ω
- แปลง `4.7` + `kΩ` → `4700.0` Ω
- `Ω` → ค่าเดิม
- หน่วยหายไป → ใช้ค่าเริ่มต้น ไม่ error
- หน่วยไม่รู้จัก (`"MΩ"`, `"xx"`) → error ภาษาไทย
- ค่าที่พิมพ์และหน่วยถูกเก็บใน `raw` / `units` เพื่อแสดงซ้ำ

**`tests/test_engineering.py` (เพิ่ม)**
- `solve_approximate` ตรงกับค่าที่คำนวณมือสำหรับเคส golden
- เคสคัตออฟคืนกระแสศูนย์เหมือนวิธีอื่น
- `analyze()` มี `approximate` และ `method_gap > 0`
- `method_gap` ลดลงเมื่อ β สูงขึ้น (สมบัติของวิธีประมาณ)
- exact กับ approximate ต่างกันไม่เกิน 15% ในเคสปกติ

**`tests/test_plotting.py` (ใหม่)**
- `circuit_svg({})` และ `circuit_svg(labels)` parse เป็น XML ได้
- มีป้าย `V_B`, `V_C`, `V_E`, `R1`, `RC`, `RE` ครบ
- ค่าที่ส่งเข้าไปปรากฏในภาพ (เช่น `100 kΩ`)
- ข้อความที่มีอักขระพิเศษ (`<`, `&`) ถูก escape
- ไม่มี `<script>`
- `load_line_svg`: จุดตัดแกนตรงสูตร, จุด Q ตรงกับ `op`, คัตออฟไม่ crash,
  อิ่มตัวไม่ crash และมีคำว่า `out of range`, เปลี่ยน VCC แล้วสเกลเปลี่ยน

**`tests/test_app.py` (แก้)**
- GET: มี `Input Parameters`, `Circuit`, `DC Bias Results`, `<img` ไม่มี,
  มี `<svg` ของวงจร
- POST golden: มี `1.32` (mA) และ `4.45` (V), มี `Active region`,
  มีทั้งคอลัมน์ `Exact` และ `Approx.`, มีกราฟ (`load-line`)
- POST ด้วยหน่วย kΩ: `r1=47, r1_unit=kΩ` ให้ผลเท่ากับ `r1=47000, r1_unit=Ω`
- POST ค่าไม่ถูกต้อง: ไม่มีกราฟ, มี error ไทย, ค่าที่พิมพ์ยังอยู่
- ยังคงผ่าน `test_template_has_no_script_tag`

## สัญญาข้อมูล (Data contracts)

| ผู้ผลิต | ผู้บริโภค | สัญญา |
|---|---|---|
| `validation.parse_inputs` | `app.index` | `ParseResult(inputs, errors, warnings, raw, units)` |
| `engineering.analyze` | `app.index` | `AnalysisResult(inputs, primary, approximate, method_gap, check, region)` |
| `plotting.circuit_svg` | `app.index` | `(labels: Mapping[str,str]) -> str` (SVG) |
| `plotting.load_line_svg` | `app.index` | `(inputs, op) -> str` (SVG) |
| `app.index` | `index.html` | `raw, units, errors, warnings, result, circuit_svg, chart_svg` |

## ความเสี่ยงและวิธีรับมือ

| ความเสี่ยง | วิธีรับมือ |
|---|---|
| เทสต์เดิมพังจำนวนมากเพราะเปลี่ยนภาษา UI | แก้เทสต์ไปพร้อมกันใน task เดียว และคง assertion ที่ตรวจข้อความ error ไทยไว้ |
| การแปลงหน่วยผิดเงียบ ๆ | เทสต์แปลงหน่วยทั้ง kΩ และ Ω + เทสต์ว่า kΩ ให้ผลเท่ากับค่าที่แปลงแล้ว |
| จุด Q นอกช่วงในเขตอิ่มตัว | ตรึงที่ขอบ + กำกับ `out of range` + เทสต์ล็อก |
| `\|safe` เปิดช่อง XSS | SVG ประกอบจากตัวเลขที่เราฟอร์แมต + `escape()` ข้อความ + เทสต์อักขระพิเศษ |
| เลย์เอาต์ 3 คอลัมน์ล้นบนจอเล็ก | breakpoint 2 ระดับ + เทสต์ไม่ผูกกับ CSS |

## สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- จำนวน tick และความละเอียดเส้นกริดบนกราฟ
- ตำแหน่งป้ายชื่อบนแผนภาพวงจร
- ระยะห่าง (spacing) ภายใน `<figure>` และการ์ด
- สีของไอคอนในหัวข้อการ์ด
