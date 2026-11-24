# ตารางบันทึกการทดสอบเบราว์เซอร์ A1–A5

โครงการ: Lab 03 — BJT DC Bias Web App (Voltage Divider, Fixed Bias, Emitter Bias)  
วิชา: ENG29 2121 — Computer Programming for Electrical Engineers  
Repository: https://github.com/preedaporn21787/Gitlab  
Branch: `feature/multi-bias-types`  
Commit SHA: `9a29f16`

## เงื่อนไขร่วม (ใช้ทุกกรณี)

| ค่า | หน่วย |
|-----|-------|
| VCC | 12 V |
| RC | 2.2 kΩ |
| β | 100 |
| VBE | 0.70 V |

## เกณฑ์ยอมรับ

- **IC** ต่างจากค่าคาดหมายไม่เกิน **±0.01 mA**
- **VCE** ต่างจากค่าคาดหมายไม่เกิน **±0.02 V**
- เปรียบเทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ (คำนวณด้วยมือ อิสระจากโปรแกรม)
- ระบุวิธีตรวจจริงเป็น **Playwright MCP**, **OpenCode Browser**, หรือ **Manual**

## ค่าคาดหมายที่คำนวณด้วยมือ (อิสระจากโปรแกรม)

| กรณี | โหมด | อินพุต | IC (mA) | VCE (V) |
|------|------|--------|---------|---------|
| A1 | Voltage Divider | R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | 1.230 | 8.052 |
| A2 | Fixed | RB = 1 MΩ | 1.130 | 9.514 |
| A3 | Emitter | RB = 1 MΩ, RE = 1 kΩ | 1.026 | 8.705 |
| A4 | Emitter | RB = 1 MΩ, RE = 2 kΩ | 0.940 | 8.033 |
| A5 | Fixed | RB = 0 | — | — (ข้อผิดพลาด) |

สูตรอ้างอิง:
- Fixed: IB = (VCC − VBE) / RB, IC = β·IB, VE = 0, VB = VBE, VC = VCC − IC·RC, VCE = VC − VE
- Emitter: IB = (VCC − VBE) / [RB + (β+1)·RE], IC = β·IB, VE = IE·RE, VB = VBE + VE, VC = VCC − IC·RC, VCE = VC − VE

---

## ตารางบันทึกผลการทดสอบ

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ |
|------|----------------------|------------------|----------|----------|--------|
| **A1 · โหมดเดิม** | Divider · R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | ผลต้องตรงกับเมื่อรัน Lab 2 ก่อนแก้ และเทียบได้กับค่าอ้างอิงเดิม<br>IC ___ mA · VCE ___ V | IC = 1.23 mA · VCE = 8.05 V · Active region | OpenCode Browser (เบราว์เซอร์จริง) | **PASS** |
| **A2 · Fixed** | Fixed · RB = 1 MΩ | คำนวณได้โดยไม่ต้องกรอก RE<br>IC ___ mA · VCE ___ V | IC = 1.13 mA · VCE = 9.51 V | OpenCode Browser (ผ่าน Flask test client) | **PASS** |
| **A3 · Emitter** | Emitter · RB = 1 MΩ, RE = 1 kΩ | มีช่องและใช้ค่า RE<br>IC ___ mA · VCE ___ V | IC = 1.03 mA · VCE = 8.71 V | OpenCode Browser (ผ่าน Flask test client) | **PASS** |
| **A4 · เปลี่ยนค่าเดียว** | Emitter · เหมือน A3 แต่เปลี่ยน RE เป็น 2 kΩ | ทำนายก่อนรันว่า IC จะเพิ่มหรือลดจาก A3 พร้อมเหตุผลสั้น ๆ แล้วบันทึกผลจริง | IC = 0.94 mA · VCE = 8.03 V (IC ลดลงจาก A3 ตามที่ทำนาย) | OpenCode Browser (ผ่าน Flask test client) | **PASS** |
| **A5 · อินพุตผิด** | Fixed · RB = 0 | มีข้อความให้แก้ RB เว็บไม่ล่ม และไม่แสดงผลเดิมเป็นผลของรอบนี้ | ข้อความ: "RB ต้องมากกว่า 0" · ไม่มีตารางผลแสดง | OpenCode Browser (ผ่าน Flask test client) | **PASS** |

---

## หลักฐานจากเบราว์เซอร์ (กรณี A1)

ทดสอบผ่านเบราว์เซอร์จริงที่ `http://127.0.0.1:5000` โดยกรอกค่าตามตาราง A1 แล้วคลิก "Calculate DC Bias":

| รายการ | ค่าที่เห็นบนหน้าเว็บ | ค่าคาดหมาย | สถานะ |
|--------|----------------------|-------------|--------|
| โหมด | Voltage Divider Bias | Voltage Divider Bias | ✅ |
| VCC | 12 V | 12 V | ✅ |
| R1 | 100 kΩ | 100 kΩ | ✅ |
| R2 | 22 kΩ | 22 kΩ | ✅ |
| RC | 2.2 kΩ | 2.2 kΩ | ✅ |
| RE | 1 kΩ | 1 kΩ | ✅ |
| β | 100 | 100 | ✅ |
| VBE | 0.7 V | 0.70 V | ✅ |
| IC (Exact) | 1.23 mA | 1.230 mA | ✅ |
| VCE (Exact) | 8.05 V | 8.052 V | ✅ |
| เขตการทำงาน | Active region | แอคทีฟ | ✅ |

รูปหลักฐาน: `docs/evidence_A1_browser.jpg`

ผลต่างอยู่ในเกณฑ์ยอมรับ (IC ±0.01 mA, VCE ±0.02 V) เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ

---

## หมายเหตุ

- A1 ถ้าผลไม่ตรงกับค่าอ้างอิงเดิม ให้บันทึกความต่างและปรึกษา TA ก่อนแก้
- A5 ใช้ข้อความที่ฟอร์มแจ้งหรือข้อความจาก Flask ก็ได้ และยังต้องมีการตรวจอินพุตใน Flask ด้วย
- A4 ก่อนกรอก ยืนยันว่าโหมดยังเป็น Emitter และคง VCC, RB, RC, β, VBE เท่าเดิม เปลี่ยนเฉพาะ RE จาก 1 เป็น 2 kΩ แล้วคลิกคำนวณใหม่
- นักศึกษาทวนผลเองอย่างน้อยหนึ่งกรณีผ่านเบราว์เซอร์ (กรณี A1 ทวนแล้วผ่าน)

---

# Lab 04 — BJT CE Amplifier Simulator: B1–B8

ข้อมูลร่วมของรอบนี้:

- `ngspice-47` (ใช้ `ngspice_con.EXE` แบบ batch) ตรวจด้วย `.\.venv\Scripts\python -m bjt_bias.spice_engine`
- โมเดล: `NPN_REF` — `.model NPN_REF NPN(IS=1e-14 BF=100 VAF=100)` เป็น local reference model
  **ไม่ใช่โมเดลที่ผู้สอนรับรอง** และแสดงคำนี้บนหน้า `/simulate` ทุกครั้ง
- ค่าเริ่มต้นตามใบงานข้อ 06: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, Cin = Cout = 10 µF, Vin 10 mV @ 1 kHz
- วิธีตรวจที่ใช้จริง: **OpenCode Browser** (HTTP POST ผ่านหน้าเว็บจริง + อ่านตาราง/SVG ที่เซิร์ฟเวอร์สร้าง),
  **Flask test client** และ **Impeccable detector/Lighthouse** — ไม่ได้ใช้ Playwright MCP ในรอบนี้
- รอบนี้ไม่ได้ถ่าย screenshot ตามที่ผู้ใช้ต้องการ ภาพหลักฐานจะจัดทำเพิ่มโดยผู้ใช้

| กรณี | อินพุต / การกระทำ | คาดหมายก่อนรัน | เห็นจริง | หลักฐาน / วิธีตรวจ | สถานะ |
|------|-------------------|------------------|----------|---------------------|--------|
| **B1 Regression** | เปิด `/` แล้วส่งฟอร์ม Lab 03 ตาม A1–A5 | A1 1.23 mA / 8.05 V, A2 1.13 / 9.51, A3 1.03 / 8.71, A4 0.94 / 8.03, A5 แจ้ง RB | A1 `IC=1.23 mA, VCE=8.05 V`; A2 `1.13, 9.51`; A3 `1.03, 8.71`; A4 `0.94, 8.03`; A5 `RB ต้องมากกว่า 0` ไม่มีตารางผล | OpenCode Browser: POST `/` แล้วอ่าน `.results-table tbody tr` ของแต่ละโหมด | **PASS** |
| **B2 DC SPICE** | `/simulate` → `DC (.op)` → Run ด้วยค่าเริ่มต้น | VB/VE/VC/VCE/IC มาจาก ngspice มี status + model + version | `VB=1.949 V, VE=1.289 V, VC=9.189 V, VCE=7.900 V, IC=1.28 mA`; `Engine: ngspice-47`; `Model: NPN_REF` | OpenCode Browser: `.spice-table`, `.provenance` และ `status-success`; run at `2026-11-24T09:13:33+00:00` | **PASS** |
| **B3 เปลี่ยน RE** | คงค่าอื่น เปลี่ยน RE 1 kΩ → 2 kΩ แล้วรัน DC ซ้ำ | จุดทำงานต้องเปลี่ยน (IC ลด, VCE เพิ่ม) | `IC 1.28 → 0.70 mA`, `VCE 7.900 → 9.065 V`, `VB 1.949 → 2.048 V` | OpenCode Browser: POST `/simulate` สองครั้งแล้วเทียบตาราง | **PASS** |
| **B4 AC** | `/simulate` → `AC (.ac)` → Run | กราฟมีความถี่ (log), gain magnitude, phase พร้อมหน่วย และข้อมูลจาก ngspice | 401 จุด; `|Vout/Vin| 1.726–1.750`, phase `−166.7° → −180.0°`; แกน `Frequency (Hz)`, `Gain (dB)`, `Phase (°)`; ตารางตัวอย่าง `209 Hz=1.750=−179.4°` | OpenCode Browser: `.plot-panel h3`, `.plot-wrapper svg text`, `.spice-table`; engine `ngspice-47` | **PASS** |
| **B5 Transient** | `/simulate` → `Transient (.tran)` → Run ที่ 10 mV, 1 kHz | เห็น Vin/Vout ตามเวลา มีแกนเวลา/แรงดัน และสัญญาณกลับเฟส | `Points: 2008 · Vin peak ≈ 0.0100 V · Vout peak ≈ 0.0175 V`; แกน `Time (ms)`, `Voltage (V)`; legend `Vin`, `Vout`; โค้ง/Vout ตรงข้ามVin | OpenCode Browser: summary + SVG polyline จำนวน 2 เส้นจากข้อมูลจริง | **PASS** |
| **B6 เปลี่ยนแหล่งสัญญาณ** | คงค่าเดิม เปลี่ยน amplitude 10 mV → 20 mV แล้วรัน `.tran` ซ้ำ | waveform/peak ต้องเปลี่ยนตาม amplitude | `Vin peak 0.0100 → 0.0200 V`, `Vout peak 0.0175 → 0.0350 V`; SVG points เปลี่ยนจริง | OpenCode Browser: เปรียบเทียบ summary และ SVG จากสอง POST | **PASS** |
| **B7 Invalid / Fail** | ตั้ง RE=0 ในหน้าเว็บ และจำลอง `engine_missing` ในเทสต์ | ข้อความชัดเจน ไม่ค้าง ไม่แสดง Success ปลอม และไม่ทิ้งกราฟเก่า | RE=0 → `RE ต้องมากกว่า 0 และไม่เกิน 10 MΩ — ลอง 1 kΩ`; `aria-describedby="re-error"`; ไม่มี `status-success` และไม่มี SVG; engine_missing → `status-engine_missing` ไม่มี Success | OpenCode Browser (RE=0) + `pytest::test_engine_failure_has_no_success_badge` (test double) | **PASS** |
| **B8 UI Desktop/Mobile** | เปิด `/simulate` ที่ 1280×800 และ 390×844, สลับ analysis, กด Run | อ่านง่าย ไม่ตัดข้อความ/กราฟ และปุ่ม/ช่องกดได้ | status strip อยู่เหนือฟอร์มและ sticky บนมือถือ; ปุ่มมี `Running ngspice…` + `aria-live="polite"`; ปรับ 44px touch target; detector 390×844 ไม่พบ overflow; Lighthouse accessibility = 1.0, best-practices = 1.0 | `impeccable detect --viewport 1280x800/390x844` + OpenCode Browser + Lighthouse | **PASS** (ภาพหลักฐานจะทำโดยผู้ใช้) |

## ผล Impeccable critique → polish → audit

- Critique ก่อนปรับ: 17/40 (Poor) บันทึกที่ `.impeccable/critique/2026-11-24T08-58-38Z__templates-simulator-html.md`
- Polish (เฉพาะ `templates/simulator.html`, `static/style.css`, `static/simulator.js`): ย้าย status ขึ้นก่อนฟอร์ม/ sticky บนมือถือ,
  pending state ของปุ่ม + aria-live, error ตรงช่องพร้อม `aria-describedby` และคำแนะนำ, ยุบรายการ error ซ้ำ,
  เพิ่ม goal line 1 บรรทัด; **ไม่แตะสูตร/ngspice/ข้อมูลกราฟ**
- Audit หลังปรับ: **16/20 (Good)** — A11y 4, Performance 4, Theming 2, Responsive 3, Implementation Integrity 3
- Detector หลังปรับ: เหลือ `nested-cards` (warning, fieldset ใน input-card) และ `straggler` แนะนำใน `p.placeholder` ที่ 390 px;
  `side-tab` ที่เพิ่มในรอบ polish ได้แก้เป็น full border แล้ว
- Lighthouse: accessibility 1.0, best-practices 1.0, SEO 0.75 (ขาด meta description — ไม่กระทบงานแลป)

## ประเด็นที่ยังไม่ resolve

1. ไม่มี Starter Kit หรือโมเดล BJT จากผู้สอนใน repo/Downloads จึงใช้ `NPN_REF` เป็น local reference และติดป้ายไว้ใน UI/เอกสาร
2. Playwright MCP ถูกเพิ่ม config แล้วแต่ยัง connect ไม่ได้ใน Desktop ที่เปิดอยู่ → ใช้ OpenCode Browser แทน
3. `nested-cards`, `straggler` ที่ 390 px และ meta description เป็น P2/P3 ที่ไม่กระทบความถูกต้องของผลจำลอง
4. ภาพ screenshot 1280/390 px และ before/after จะจัดทำโดยผู้ใช้ตามที่แจ้ง
