# บันทึกความร่วมมือ AI — Lab 04

1. AI สร้างหน้า `/simulate` (CE SPICE) พร้อม `bjt_bias/spice_engine.py` (netlist dc/ac/tran เรียก ngspice_con จริง, model NPN_REF) และเพิ่ม `spice_plots.py` สำหรับอ่านไฟล์ `.raw` วาดกราฟ AC/Transient จริง รวมถึงปรับ UI แถบนำทาง Lab (lab-nav) ใน `style.css`, `index.html`, `simulator.html`
2. AI แก้จุดเชื่อม divider node กับ base ของทรานซิสเตอร์ และเขียนเอกสาร `docs/validation.md` (B1–B8), `DEBUGGING_GUIDE.md` และ checklist รวมถึงปรับปรุงคำอธิบายใน README
3. นักศึกษาตรวจเองว่า `/simulate` ใหม่ไม่กระทบผล `/` เดิม, B1–B5 ผ่านทั้งหมด, และรัน `pytest` ได้ 177 passed
4. นักศึกษาตรวจตัวเลขจริงจาก ngspice ในตาราง (B2 VB=1.949 V / VE=1.289 V / VC=9.189 V / VCE=7.900 V / IC=1.28 mA; B4 401 จุด gain 1.726–1.750) และยืนยันกราฟ/ตารางแสดงข้อมูลจริงไม่ใช่ค่าจำลอง
5. นักศึกษาทดสอบกรณีผิดเงื่อนไขเอง (RE=0 → B7 error) และเช็ก version ngspice ว่าขึ้น `ngspice-47` ตามที่เอกสารระบุ
