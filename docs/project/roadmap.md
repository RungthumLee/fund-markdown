---
title: Roadmap
tags: [project, roadmap, planning]
updated: 2026-08-27
---

# 🗺️ Roadmap

ทิศทางถัดไปของคลังความรู้นี้ เรียงตามความคุ้มค่า (ผลลัพธ์ต่อแรงที่ลง)

**ที่เกี่ยวข้อง:** [[tasks|Tasks]] · [[outstanding|Outstanding]] · [[decisions|Decisions]]

---

> [!NOTE] ความคืบหน้ารอบ 2026-08-27
> เริ่มพัฒนา 3 ก้อน: **semantic validator (ทำแล้ว)** · Dataview + เทียบค่าธรรมเนียม (R-01/R-02, ค้าง) ·
> changelog ต่อเนื่อง (R-07 มีโค้ดแล้ว เหลือ scheduler) — สถานะรายตัวที่ [[tasks|Phase 9]]

---

## ✅ ทำแล้วรอบนี้

### R-00 · Semantic validator — ตรวจว่าข้อมูล "สมเหตุสมผล" ไม่ใช่แค่ลิงก์ครบ
`scripts/validate_semantics.py` — เสริม `validate_vault.py` ที่ตรวจแต่โครงสร้าง
จับได้ทันทีที่รันครั้งแรก: ตัวตน Mapletree/MINT ผิดใน 377 กอง ([[issues|ISS-035]])
และ benchmark ที่ต้นทาง SEC ผิด ([[issues|ISS-036]])
รายงานที่ [[semantic-report|Semantic Report]]
**เหลือ:** แก้ต้นเหตุ Mapletree ใน `normalize_entities.py` + เพิ่ม stage ใน pipeline

---

## ทำได้เลย — คุ้มค่าสูง แรงน้อย

### R-01 · เพิ่ม Dataview query ในโน้ต index
_สถานะ: ค้าง (Phase 9.2)_
ทุกโน้ตมี frontmatter ครบแล้ว (`policy`, `risk_spectrum`, `management_style`, …)
เพิ่ม query ในโน้ต index จะได้ตารางเรียง/กรองแบบ interactive ทันที

```dataview
TABLE risk_spectrum, policy, amc
FROM #fund
WHERE policy = "ตราสารทุน" AND risk_spectrum >= 6
SORT amc ASC
```

### R-02 · โน้ตเปรียบเทียบค่าธรรมเนียมรายหมวด
ดึงจาก `funds.json` โดยตรง สร้างตารางเรียงตาม TER ในแต่ละ `policy_desc`
ตอบคำถามที่คนถามบ่อยที่สุด: "กองหมวดนี้ กองไหนถูกที่สุด"

### R-03 · ตั้ง git repository และ commit
`.gitignore` พร้อมแล้ว — ดู [[outstanding|OUT-009]]

---

## รอบถัดไป — คุ้มค่าปานกลาง

### R-04 · OCR สำหรับ factsheet ที่เป็นภาพสแกน
Tesseract + `tha.traineddata` กับไฟล์ที่ `thai_text_ok: false`
ดู [[outstanding|OUT-003]]

### R-05 · ดึงข้อมูลย้อนหลังให้ลึกขึ้น
NAV 3–5 ปี เพื่อคำนวณผลตอบแทน/ความผันผวนเองได้
ต้องประเมินขนาดข้อมูลก่อน — ดู [[outstanding|OUT-004]]

### R-06 · Parse โครงสร้างจาก factsheet PDF
ตอนนี้เก็บเป็น plain text ต่อหน้า
ถ้าแกะตารางออกมาได้จะเทียบกับข้อมูล API เพื่อตรวจสอบความถูกต้องได้

### R-07 · แจ้งเตือนการเปลี่ยนแปลง — ✅ มีโค้ดแล้ว
`scripts/gen_changelog.py` เทียบ snapshot รอบนี้กับรอบก่อน (กองใหม่/เลิก/
ค่าธรรมเนียม/ความเสี่ยง/พอร์ต/NAV) เขียนโน้ตที่ `vault/Changes/` และ wired ใน
`daily.py` แล้ว — **เหลือแค่ลงทะเบียน scheduler ให้รันจริง (R-10 · Phase 9.3)**

---

### R-11 · ดึง factsheet/KIID จากเว็บ บลจ. ของกองทุนหลักโดยตรง
ตอนนี้ข้อมูลกองหลักมาจาก Yahoo + FT ซึ่งครอบคลุม ~90%
การเข้าเว็บ บลจ. ต้นทางแล้วโหลดเอกสารจะได้ข้อมูลครบและเป็นทางการที่สุด
โดยเฉพาะกอง private/institutional ที่ทั้งสองแหล่งไม่มี
ต้องเขียน adapter แยกต่อ บลจ. (BlackRock / JPMorgan / PIMCO / Fidelity
มีโครงสร้างเว็บคนละแบบ) — ดู [[../guides/master-fund-sources|Master Funds]]

**คืบหน้า:** ทำการค้นเว็บไปแล้วเป็นขั้นกลาง (ดู [[../guides/web-search-enrichment|Web Search Enrichment]])
เหลือ **62 กอง** ที่ยังไม่มีข้อมูล ซึ่งเกือบทั้งหมดเป็นกอง private credit / BDC feeder
และกองเฮดจ์ฟันด์ Cayman ที่ไม่มีเอกสารสาธารณะเลย — R-11 จะช่วยได้เฉพาะกอง
ที่ บลจ. เผยแพร่ factsheet จริง ไม่ใช่ทั้ง 62 กอง

### R-12 · เตือนเมื่อพอร์ตซ้อนทับกันที่กองทุนหลัก
ข้อมูลพร้อมแล้ว — ถ้าผู้ใช้ถือกองไทยหลายกองที่ feed เข้ากองหลักเดียวกัน
ควรคำนวณและเตือนว่าสัดส่วนที่แท้จริงกระจุกแค่ไหน

---

## ระยะยาว

### R-08 · เก็บลงฐานข้อมูล
`.env.local` มี `DB_*` ตั้งไว้แล้วแต่ยังไม่ได้ใช้
ถ้าต้อง query ซับซ้อนหรือทำ time series การใส่ PostgreSQL จะคุ้ม
markdown เหมาะกับการอ่าน ไม่เหมาะกับการ aggregate

### R-09 · เชื่อมกับ Local LLM
`.env.local` มี `OLLAMA_BASE_URL` และ `OLLAMA_MODEL` เตรียมไว้แล้ว
ใช้สรุปนโยบายการลงทุน หรือทำ RAG ถามตอบข้าม 2,300 กอง

### R-10 · อัตโนมัติรายเดือน
factsheet ออกรายเดือน — ตั้ง scheduled task รัน `run_all.py` ทุกต้นเดือน
แล้วสร้างรายงานสรุปการเปลี่ยนแปลง

---

## สิ่งที่ตั้งใจ **ไม่** ทำ

| ไม่ทำ | เหตุผล |
|---|---|
| ให้คำแนะนำการลงทุน | คลังนี้เป็นข้อมูลอ้างอิง ไม่ใช่คำแนะนำ |
| ทำนายผลตอบแทน | ข้อมูลย้อนหลังไม่ทำนายอนาคต |
| เก็บ Term fund / PVD | อยู่นอกขอบเขตที่กำหนด — ดู [[../guides/scope-and-filters\|Scope]] |
| Scrape เว็บ SEC | มี API อย่างเป็นทางการอยู่แล้ว และ portal มี bot protection |
