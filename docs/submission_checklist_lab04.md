# Submission Checklist — Lab 04 (CE Amplifier Simulator, ngspice)

รายการตรวจสอบก่อนส่งงาน Lab 04 วันที่ทดสอบ: 2026-11-24

## 1. GitHub Repository URL และ Commit SHA

- [x] GitHub URL: https://github.com/preedaporn21787/Gitlab
- [x] Commit SHA: `a858a9c43216b32bed414fa4c558bc0d0d3b238d` (ตรวจด้วย `git rev-parse HEAD` บนเครื่องที่รัน Tests)
- Branch: `feature/multi-bias-types`
- หมายเหตุ: ถ้าพรีเพรสซ้ำไปก่อนเสร็จสิ้นรอบนี้ ให้บันทึก SHA จริงที่เดินงานจริงลงที่นี่

## 2. Flask App — CE SPICE (DC/AC/Transient) และ DC Bias เดิม 3 แบบ

ตรวจได้จากซอร์สโค้ดและรัน Tests ผ่านแล้วบนเครื่องนี้:

- [x] DC Bias เดิม 3 แบบ (Voltage Divider / Fixed / Emitter Single) — `/` ยังตอบคำขอเดิมถูกต้อง
  - ที่: `app.py` `/` route, `bjt_bias/validation.py` — `BIAS_TYPES = ("voltage_divider", "fixed", "emitter_single")`
- [x] CE SPICE DC `.op` — หน้า `/simulate` → Run ngspice
  - ที่: `app.py` `/simulate` route, `bjt_bias/spice_engine.py` บรรทัด `.op` (analysis="dc")
- [x] CE SPICE AC `.ac` — ดึงค่าจากไฟล์ `.raw` ที่ ngspice เขียน
  - ที่: `bjt_bias/spice_engine.py` (`.ac dec`), `bjt_bias/spice_plots.py::ac_svg()`
- [x] CE SPICE Transient `.tran` — ดึง Vin/Vout จากข้อมูลจริงเท่านั้น
  - ที่: `bjt_bias/spice_engine.py` (`.tran`), `bjt_bias/spice_plots.py::transient_svg()`
- [x] โมเดล CE คือ `NPN_REF` — `IS=1e-14 BF=100 VAF=100`
  - ตรวจด้วย: `.\.venv\Scripts\python -m bjt_bias.spice_engine`
- [x] ทดสอบผ่านทั้งหมด — `.\.venv\Scripts\python -m pytest -q` → **177 passed**

## 3. README.md — ขั้นติดตั้ง ngspice/Python Dependencies, วิธีรัน Server และ Browser

- [x] Python Dependencies — มีแล้ว
  - `.\run.ps1` หรือ `python -m venv .venv` + `.venv\Scripts\python -m pip install -r requirements.txt` (README ที่ประมาณบรรทัด 38–50)
- [x] เวอร์ชัน ngspice — มีคำสั่งเช็กและผลที่ควรเห็นบน README (บรรทัด 57–71)
  - `.\.venv\Scripts\python -m bjt_bias.spice_engine` → ต้องเห็น `executable: ...\ngspice_con.EXE` และ `version: ngspice-47`
  - [⚠️ GAP] README ยังไม่มีขั้นติดตั้ง ngspice แบบชัดเจน (ที่ดาวน์โหลด ngspice_con) นอกจากหมายเหตุ `NGSPICE_EXECUTABLE` แนะนำเพิ่มบรรทับสั้นๆ ว่า ngspice 47 จาก ngspice-47 ผลใช้ได้
- [x] วิธีรัน Server — มีแล้ว
  - `.\run.ps1` หรือ `.venv\Scripts\python app.py` → เปิด http://127.0.0.1:5000
- [x] วิธีเข้าหน้า Browser — มีแล้ว
  - `/simulate` ที่ http://127.0.0.1:5000/simulate

## 4. docs/validation.md — บันทึก B1–B8, วิธีตรวจ, ผลที่เห็นจริง, แหล่งอ้างอิง, ความคลาดเคลื่อนและข้อจำกัด

ข้อมูลนี้บันทึกไว้ที่ `docs/validation.md` ส่วน Lab 04 (บรรทับ 86–130)

- [x] บันทึก B1–B8 — ตารางมีครบถ้วน
  - คอลัมน์: กรณี / อินพุต-การกระทำ / คาดหมายก่อนรัน / เห็นจริง / หลักฐาน-วิธีตรวจ / สถานะ
- [x] วิธีตรวจ (วิธีจริง) — บันทึกไว้แล้ว: OpenCode Browser (รันผ่านหน้าเว็บจริง + อ่าน SVG/ตาราง), Flask test client, และ Impeccable detector/Lighthouse
- [x] ผลที่เห็นจริง — จากตารางที่ถ่ายจาก Browser (เช่น B2: VB=1.949 V, VE=1.289 V, VC=9.189 V, VCE=7.900 V, IC=1.28 mA; B4: 401 จุด, gain 1.726–1.750, phase −166.7°→−180.0°; ทั้งหมดเป็นข้อมูลจริงจาก ngspice)
- [⚠️ GAP] แหล่งอ้างอิง — มีเฉพาะโมเดลที่ใช้ (`NPN_REF`, `IS=1e-14 BF=100 VAF=100`) ที่ README/validation.md บอกว่าเป็น local reference ไม่ใช่โมเดลที่ผู้สอนรับรอง (ถ้าต้องอ้างกับสูตรหรือค่าอ้างอิงภายนอก แนะนำบันทึกเพิ่ม)
- [⚠️ GAP] ความคลาดเคลื่อนและข้อจำกัด — มีเป็น "ประเด็นที่ยังไม่ resolve" (ท้ายไฟล์) กับหมายเหตุ B8 บอกข้อจำกัด P2/P3 แต่ไม่มีส่วนแยกชัดเจนว่า "คลาดเคลื่อน/ข้อจำกัด" (เช่น เหตุผลที่ค่าบน UI ไม่ได้เทียบกับสูตรอ้างอิงภายนอก หรือข้อจำกัดของ NPN_REF) — แนะนำเพิ่มส่วนนี้ถ้าต้องการครบถ้วน

## 5. ภาพหน้าจากก่อน/หลัง UI หรือบันทึกการปรับด้วย Impeccable + Screenshot กราฟจาก Browser จริง

ชื่อไฟล์ที่สงวนไว้ (ดู `docs/captures/README.md`):

- [ ] `simulate-desktop-1280-before.png` / `simulate-desktop-1280-after.png` — /simulate ที่ 1280×800
- [ ] `simulate-mobile-390-before.png` / `simulate-mobile-390-after.png` — /simulate ที่ 390×844
- [ ] `simulate-dc-success.png` — ผล DC (B2/B3)
- [ ] `simulate-ac-bode.png` — ผล AC (B4)
- [ ] `simulate-transient-10mV.png` / `simulate-transient-20mV.png` — Transient 10 mV และ 20 mV (B5/B6)
- [ ] `simulate-invalid-re.png` — RE=0 ข้อผิดพลาด (B7)

> บันทึกความอยู่ร่วมกับการปรับด้วย Impeccable ลงที่นี่เมื่อมีภาพพร้อม (ก่อน/หลัง UI และกราฟจาก Browser จริง ตามชื่อไฟล์ข้างบน)

สถานะ: **รอผู้ใช้ถ่าย/เตรียมไว้ก่อนส่ง** — ถ่ายจาก http://127.0.0.1:5000/simulate ผ่าน OpenCode Browser ได้ก่อนหรือหลังการปรับแต่งยังคงอยู่

## 6. บันทึก 3–5 บรรทับ — AI สร้าง/แก้ส่วนใด + นักศึกษาตรวจอะไรเอง

1. AI สร้างหน้า `/simulate` (CE SPICE) บน Flask ใหม่ + `bjt_bias/spice_engine.py` (netlist dc/ac/tran, ngspice_con จริง, model NPN_REF) — ผู้ใช้เช็กเองว่า `/simulate` ใหม่ยังไม่รบกวนผลของ `/` และ B1–B5 ผ่านทั้งสอง
2. AI เพิ่มการอ่านผลจากไฟล์ `.raw` ของ ngspice และวาดกราฟ SVG จริงสำหรับ AC/Transient (`spice_plots.py`) — นักศึกษาเช็กว่ากราฟ/ตารางแสดงข้อมูลจริงจาก ngspice อย่างเป็นอิสระได้หรือไม่ (B4/B5/B6)
3. AI เพิ่ม UI บน `templates/simulator.html` + `static/simulator.js`/`style.css` + บันทึกคำอธิบายการปรับด้วย Impeccable ลง validation.md — นักศึกษาเช็กเองที่ screenshot ก่อน/หลัง (ภาพในไฟล์ของทีมงาน) ตรงประโยชน์ตามตาราง B8
4. AI เขียน `docs/validation.md` ข้อ B1–B8 (จากข้อมูลที่ถ่ายจาก Browser) — นักศึกษาเช็กข้อมูลที่บันทึกจริงในตาราง (เช่น ตัวเลข B2–B6) และตรวจเองกรณีไม่เข้าเกณฑ์

---

## สรุปสถานะโดยรวม

- ✅ ตรวจพร้อมส่งหรือรอบส่งครั้งต่อไป
- ⚠️ ต้องการการจัดเตรียมแต่ยังไม่ส่ง: ภาพหน้าจากก่อน/หลัง UI (ข้อ 5) + ส่วน GAP ของ README/validation.md (ข้อ 3–4) ถ้าต้องการครบถ้วน
