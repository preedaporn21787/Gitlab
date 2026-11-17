# สรุปงาน Lab 03 — BJT DC Bias Web App (เพิ่ม Fixed Bias และ Emitter Bias)

## ข้อมูลโครงการ

| รายการ | รายละเอียด |
|--------|-------------|
| วิชา | ENG29 2121 — Computer Programming for Electrical Engineers |
| แล็บ | Lab 03 · BJT DC Bias และการตรวจผลผ่านเบราว์เซอร์ |
| ภาษา | Python + Flask + Jinja2 |
| Repository | https://github.com/preedaporn21787/Gitlab |
| Branch | `feature/multi-bias-types` |
| Commit ล่าสุด | `6e05e4f` |
| สถานะทดสอบ | ผ่านทั้งหมด 148 เคส |

## สิ่งที่เพิ่มเข้ามา (จาก Lab 02)

| ส่วน | รายละเอียด |
|------|-------------|
| `bjt_bias/engineering.py` | เพิ่ม `solve_fixed_bias()` และ `solve_emitter_bias_single_supply()` พร้อมวิธีตรวจอิสระ (`solve_fixed_bias_check`, `solve_emitter_bias_single_supply_check`) และ `analyze()` ที่เลือกฟังก์ชันตาม `bias_type` |
| `bjt_bias/validation.py` | ตรวจค่าต่อโหมด (RB สำหรับ fixed/emitter, R1/R2 สำหรับ divider) แปลงหน่วย kΩ → Ω |
| `bjt_bias/plotting.py` | วาดวงจร SVG และกราฟโหลดไลน์สำหรับทั้งสามโหมด |
| `templates/index.html` | เลือกโหมดวงจร แสดงเฉพาะช่องที่เกี่ยวข้อง ตารางผล Exact / Approx. |
| `app.py` | ใช้ `if/elif` เลือกฟังก์ชันคำนวณตามโหมดที่ส่งจากฟอร์ม |

## ตารางทดสอบยอมรับ A1–A5

เงื่อนไขร่วม: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V  
เกณฑ์: IC ต่างไม่เกิน ±0.01 mA, VCE ต่างไม่เกิน ±0.02 V เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ

| กรณี | โหมด | ค่าที่กรอก | IC คาดหมาย (mA) | VCE คาดหมาย (V) | IC จริง (mA) | VCE จริง (V) | วิธีตรวจ | สถานะ |
|------|------|-----------|-------------------|-------------------|--------------|--------------|----------|--------|
| A1 | Voltage Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.230 | 8.052 | 1.23 | 8.05 | เบราว์เซอร์จริง (OpenCode Browser) | PASS |
| A2 | Fixed | RB = 1 MΩ | 1.130 | 9.514 | 1.13 | 9.51 | Flask test client | PASS |
| A3 | Emitter | RB = 1 MΩ, RE = 1 kΩ | 1.026 | 8.705 | 1.03 | 8.71 | Flask test client | PASS |
| A4 | Emitter | RB = 1 MΩ, RE = 2 kΩ | 0.940 | 8.033 | 0.94 | 8.03 | Flask test client | PASS |
| A5 | Fixed | RB = 0 | — | — | — | — | Flask test client | PASS (ข้อผิดพลาด RB ต้องมากกว่า 0) |

หมายเหตุ A4: IC ลดลงจาก A3 (1.026 → 0.940 mA) ตามที่ทำนาย เพราะ RE มากขึ้น ทำให้ IB และ IC ลดลง

หมายเหตุ A5: กรอก RB = 0 แล้วเว็บแสดงข้อความ "RB ต้องมากกว่า 0" ไม่ล่ม และไม่แสดงผลเก่าแทน

## ค่าคาดหมายที่คำนวณด้วยมือ (อิสระจากโปรแกรม)

### A2 Fixed Bias (RB = 1 MΩ)
- IB = (VCC − VBE) / RB = (12 − 0.7) / 1,000,000 = 11.3 µA
- IC = β·IB = 100 × 11.3 µA = 1.13 mA
- VE = 0 V, VB = VBE = 0.7 V
- VC = VCC − IC·RC = 12 − 1.13×2.2 = 9.514 V
- VCE = VC − VE = 9.514 V

### A3 Emitter Bias (RB = 1 MΩ, RE = 1 kΩ)
- IB = (VCC − VBE) / [RB + (β+1)RE] = 11.3 / [1,000,000 + 101×1,000] = 10.26 µA
- IC = 100 × 10.26 µA = 1.026 mA
- VE = IE·RE = 101×10.26 µA × 1,000 = 1.036 V
- VB = VBE + VE = 1.736 V
- VC = 12 − 1.026×2.2 = 9.742 V
- VCE = VC − VE = 8.705 V

## การแก้ไขระหว่างทดสอบ

พบบั๊ก: โหมด Fixed Bias validation ยังบังคับกรอกช่อง RE ทั้งที่เทมเพลตซ่อนช่องนี้ไว้ ทำให้ส่งฟอร์มแล้วไม่แสดงผล

แก้ไขใน `bjt_bias/validation.py`:
- ข้ามการ validate RE เมื่อ `bias_type = fixed`
- กำหนดค่า default `re = 0.0` สำหรับ fixed bias

หลังแก้ไข ชุดทดสอบเดิม 148 เคสยังผ่านครบ

## การส่งงาน

- GitHub URL: https://github.com/preedaporn21787/Gitlab
- Commit SHA: `6e05e4f`
- Branch: `feature/multi-bias-types`
- วิธีรัน: `.\run.ps1` หรือ `python -m flask --app app run` แล้วเปิด `http://127.0.0.1:5000`

## บทบาท MCP

OpenCode เป็น MCP Client, Playwright MCP เป็น MCP Server ที่ควบคุมเบราว์เซอร์ เบราว์เซอร์ส่งฟอร์มไป Flask ผ่าน HTTP ส่วน OpenCode คุยกับ Playwright ผ่าน MCP Flask ทำงานเหมือนเดิม ไม่ต้องลง Playwright ใน requirements.txt
