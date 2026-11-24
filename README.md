# Gitlab

ใช้สำหรับเรียนแลป Compro ไฟฟ้า

## แล็บ BJT Common-Emitter DC Bias (ENG29 2121) — Lab 03

แอป Flask สำหรับคำนวณจุดทำงานกระแสตรง (Q-point) ของทรานซิสเตอร์ BJT ชนิด NPN
รองรับวงจรไบแอส 3 แบบ ได้แก่ Voltage Divider Bias, Fixed Bias และ Emitter Bias (แหล่งจ่ายเดียว)
คอนฟิกูเรชันคอมมอน-อีมิเตอร์

**อินพุต 7 ค่า:** VCC, RC, β, VBE (ร่วมทุกโหมด) พร้อมอินพุตเฉพาะโหมด:
- Voltage Divider: R1, R2, RE
- Fixed Bias: RB
- Emitter Bias: RB, RE

**เอาต์พุต:** I_B, I_C, I_E (mA) และ V_B, V_C, V_E, V_CE (V) พร้อมการจำแนกเขต
การทำงาน (คัตออฟ / แอคทีฟ / อิ่มตัว) และการตรวจสอบความถูกต้องของข้อมูลนำเข้า

ผลลัพธ์ถูกตรวจสอบไขว้กับวิธีวิเคราะห์อิสระ (nodal analysis สำหรับ Divider, KVL แยกต่างหากสำหรับ Fixed และ Emitter) อย่างเป็นอิสระ

### ส่งงาน Lab 03

- **GitHub URL:** https://github.com/preedaporn21787/Gitlab
- **Commit SHA:** `9331ee6`
- **Branch:** `feature/multi-bias-types`
- **ไฟล์สรุปงาน:** `LAB03_SUMMARY.md` (มีตารางทดสอบ A1–A5 ครบถ้วน)

### ส่วนที่ AI ช่วยพัฒนา

- เพิ่มฟังก์ชัน `solve_fixed_bias()` และ `solve_emitter_bias_single_supply()` ใน `bjt_bias/engineering.py` พร้อมวิธีตรวจอิสระ
- เพิ่มการตรวจค่าและแปลงหน่วยต่อโหมดใน `bjt_bias/validation.py`
- วาดวงจร SVG และกราฟโหลดไลน์สำหรับทุกโหมดใน `bjt_bias/plotting.py`
- ปรับ `templates/index.html` ให้เลือกโหมดและแสดงเฉพาะช่องที่ใช้
- แก้บั๊ก validation ที่บังคับกรอก RE แม้เลือกโหมด Fixed Bias

### วิธีใช้งาน

วิธีที่สั้นที่สุด (สคริปต์จะสร้าง `.venv` และติดตั้ง dependencies ให้เองถ้ายังไม่มี):

```powershell
.\run.ps1
```

หรือทำเองทีละขั้น:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

> ต้องใช้ `.\.venv\Scripts\python` เท่านั้น ถ้าพิมพ์ `python app.py` เฉย ๆ จะได้
> `ModuleNotFoundError: No module named 'flask'` เพราะ Flask ติดตั้งไว้ใน venv

เปิด [http://127.0.0.1:5000](http://127.0.0.1:5000) *(ใช้ได้เฉพาะบนเครื่องที่รัน Flask server เท่านั้น)*

### ตรวจสอบเวอร์ชัน ngspice (Lab 04 Setup)

ใช้คำสั่งนี้จากโฟลเดอร์โปรเจกต์ — มันเลือก **console build** ให้เองและมี timeout จึงไม่ค้าง:

```powershell
.\.venv\Scripts\python -m bjt_bias.spice_engine
```

ผลที่ควรเห็นคือ `executable: ...\ngspice_con.EXE` และ `version: ngspice-47`

> **ทำไมพิมพ์ `ngspice -v` แล้วไม่ขึ้น:** ไฟล์ `ngspice.exe` ในแพ็กเกจ 47 เป็น GUI build
> ที่ไม่พิมพ์ข้อความเวอร์ชันลงคอนโซลและจะค้างรอ input ให้ใช้ `ngspice_con -v` แทน
> (หรือ `ngspice_con --version`) นอกจากนี้ terminal ที่เปิดก่อนติดตั้งจะยังไม่เห็น
> user PATH ให้เปิด terminal ใหม่ หรือรันคำสั่งด้านบนซึ่งมี fallback path อยู่แล้ว
> ถ้าติดตั้งตำแหน่งอื่นให้ตั้ง `NGSPICE_EXECUTABLE` ชี้ไปที่ `ngspice_con.exe`

### Lab 04 — CE Amplifier Simulator (ต่อจาก Lab 03)

เปิด [http://127.0.0.1:5000/simulate](http://127.0.0.1:5000/simulate) หลังรัน Flask ตามวิธีด้านบน

- `/` คือหน้า DC Bias เดิมของ Lab 03 (ไม่เปลี่ยนผลลัพธ์)
- `/simulate` คือหน้าใหม่สำหรับจำลอง CE voltage-divider ด้วย ngspice จริง
- เลือก analysis ได้ทีละอัน: `DC (.op)`, `AC (.ac)` หรือ `Transient (.tran)` แล้วกด **Run ngspice**
- ค่าเริ่มต้นตามใบงาน: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ,
  RL 10 kΩ, Cin = Cout = 10 µF, แหล่งสัญญาณ 10 mV @ 1 kHz
- ผล DC แสดง VB/VE/VC/VCE/IC พร้อมหน่วย; ผล AC/transient วาด SVG จากข้อมูลจริง
  ที่อ่านจากไฟล์ `.raw` ไม่ใช่กราฟจำลอง
- หน้าแสดง engine version, ชื่อโมเดล, เวลาที่รัน และที่มาของค่าอย่างชัดเจน
- โมเดลที่ใช้คือ `NPN_REF` (`IS=1e-14 BF=100 VAF=100`) ซึ่งเป็น **local reference model**
  ไม่ใช่โมเดลที่ผู้สอนรับรอง

#### ติดตั้งเครื่องมือที่ใช้พัฒนา/ตรวจ UI

```powershell
# Node portable + npx (ใช้สำหรับ Impeccable)
$env:Path = "C:\Users\b6809393\AppData\Local\Programs\node-v26.13.1-win-x64;$env:Path"
npx impeccable install --yes --providers=opencode --scope=project

# ตรวจ UI แบบ code-level (ไม่ต้องถ่ายภาพ)
.\.opencode\skills\impeccable\scripts\impeccable.cmd detect --json --viewport 1280x800 http://127.0.0.1:5000/simulate
.\.opencode\skills\impeccable\scripts\impeccable.cmd detect --json --viewport 390x844 http://127.0.0.1:5000/simulate
```

มี `opencode.json` ที่ root สำหรับ Playwright MCP ตามตัวอย่าง Lab 03 อย่างไรก็ตาม
รอบนี้ยังเชื่อม MCP ไม่ได้ใน Desktop ที่เปิดอยู่ จึงใช้ **OpenCode Browser** เป็นวิธีเก็บ
หลักฐาน B1–B8 แทน และไม่ได้อ้างว่าใช้ Playwright MCP

### การรันเทสต์

```powershell
.\.venv\Scripts\python -m pytest -q
```

ผลการทดสอบล่าสุด: ผ่านทั้งหมด **173 เคส** (Lab 03 เดิม 148 เคส + Lab 04 เพิ่ม 25 เคส)

```powershell
.\.venv\Scripts\python -m pytest -q
# 173 passed
```

### บทบาทของ MCP (Model Context Protocol)

Lab 03 ตั้งใจใช้ **OpenCode เป็น MCP Client** และ **Playwright MCP เป็น MCP Server**
ตามตัวอย่างในใบงาน:

- OpenCode ส่งคำสั่งผ่าน MCP ให้ Playwright MCP เปิด URL, กรอกฟอร์ม, อ่านหน้าเว็บ
- เบราว์เซอร์ส่งคำขอ HTTP ไปยัง Flask (รันที่พอร์ต 5000) แล้วแสดงผลลัพธ์
- Playwright MCP ส่ง snapshot จากหน้าเว็บกลับ OpenCode เพื่อเทียบกับค่าคาดหมาย
- Flask ยังทำงานเหมือนเดิม ไม่ต้องลง Playwright ใน `requirements.txt`

สำหรับรอบ Lab 04 นี้ มีการเพิ่ม `opencode.json` เพื่อรองรับ Playwright MCP แต่ในการตรวจจริง
ใช้ **OpenCode Browser** และ Flask test client เท่านั้น ทำให้ตาราง B1–B8 ระบุวิธีตรวจตามที่เกิดขึ้นจริง

### ตารางทดสอบยอมรับ A1–A5 และ B1–B8

ดูรายละเอียดครบถ้วนในไฟล์ `LAB03_SUMMARY.md`

| กรณี | โหมด | สถานะ |
|------|------|--------|
| A1 | Voltage Divider (R1=100k, R2=22k, RE=1k) | PASS |
| A2 | Fixed (RB=1M) | PASS |
| A3 | Emitter (RB=1M, RE=1k) | PASS |
| A4 | Emitter (RB=1M, RE=2k) | PASS |
| A5 | Fixed (RB=0, ข้อผิดพลาด) | PASS |

ดูรายละเอียด B1–B8 (input, ผลที่เห็น, วิธีตรวจ, หมายเหตุโมเดล) ได้ใน `docs/validation.md`

| กรณี | สิ่งที่ตรวจ | สถานะ |
|------|-------------|--------|
| B1 | Lab 03 A1–A5 ยังตรงเดิม | PASS |
| B2 | DC `.op` ด้วย ngspice-47 | PASS |
| B3 | เปลี่ยน RE 1k → 2k แล้วผลเปลี่ยน | PASS |
| B4 | AC `.ac` มี gain/phase/แกนความถี่จริง | PASS |
| B5 | Transient `.tran` ที่ 10 mV | PASS |
| B6 | เปลี่ยน amplitude → waveform เปลี่ยน | PASS |
| B7 | RE=0 / engine_missing ไม่มี Success ปลอม | PASS |
| B8 | ตรวจเร็นเดอร์ 1280 px และ 390 px | PASS* |

\* ผู้ใช้จะเป็นคนจัดทำภาพหลักฐานส่งเอง รอบนี้ไม่ได้ถ่าย screenshot

