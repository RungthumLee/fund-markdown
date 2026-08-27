---
title: Handover
tags: [project, handover, summary]
updated: 2026-08-27
---

# 🤝 Handover — สรุปสิ่งที่ทำเสร็จและวิธีรับช่วงต่อ

**ที่เกี่ยวข้อง:** [[tasks|Tasks]] · [[issues|Issues]] · [[outstanding|Outstanding]] · [[roadmap|Roadmap]] · [[data-quality|Data Quality]]

---

## สิ่งที่ส่งมอบ

### 1. คู่มือ SEC Fund API ภาษาไทย
`docs/api-reference/` — **21 endpoints ครบทุกตัว** แต่ละหน้ามี
คำอธิบายไทย/อังกฤษ · ตาราง parameter · data dictionary · ตัวอย่าง response · ตัวอย่างการเรียก
สร้างอัตโนมัติจาก catalog ของ SEC ที่เก็บสำเนาไว้ที่ `_spec/fund.json`

### 2. คู่มือการใช้งานและแนวคิด
`docs/guides/` — 11 หน้า ครอบคลุม authentication, pagination,
error handling, การ join ข้อมูล, ตารางรหัสทั้งหมด, data dictionary รวม 104 field,
เกณฑ์คัดกรอง, ภาพรวม pipeline, ข้อมูล holdings และการแกะ factsheet PDF

### 3. คลังความรู้ Obsidian
`vault/` — โน้ตกองทุนพร้อม wikilink เชื่อมโยงกันทั้งหมด
เปิดด้วย Obsidian ที่โฟลเดอร์ `vault/` แล้วเริ่มที่ `Indexes/00-home.md`

### 4. Factsheet
PDF ต้นฉบับที่ `data/factsheets/` และข้อความที่แกะแล้วเป็นโน้ต markdown
ที่ `vault/Factsheets/`

### 5. Pipeline ที่รันซ้ำได้
`python run_all.py` — 10 ขั้นตอน ทุกขั้น resume ได้

### 6. เอกสารบริหารโปรเจกต์
`docs/project/` — tasks, issues, decisions, outstanding, roadmap,
data-quality, validation-report, security-notes

---

## ตัวเลขผลลัพธ์

| รายการ | จำนวน |
|---|---|
| กองทุนในขอบเขต | **2,121** |
| ชนิดหน่วยลงทุน (share class) | 4,663 |
| บลจ. | 22 |
| กองที่คัดออก | 222 (Term fund 195 · PVD 27) |
| แถวข้อมูลดิบที่ดึงมา | 743,690 |
| Factsheet PDF | 2,119 (แกะข้อความไทยได้ 100%) |
| กองที่แกะตารางจาก PDF ได้ | 1,763 |
| โน้ตใน vault | 4,286 |
| หน้าเอกสาร | 44 |

**ผลตรวจสอบ:** ลิงก์เสีย **0** · โน้ตกำพร้า **0** · ชื่อไฟล์ซ้ำ **0** · frontmatter ขาด **0**

ตัวเลขที่อัปเดตทุกครั้งที่รัน อยู่ที่ [[data-quality|Data Quality Report]]
และ `vault/Indexes/00-home.md`

### ข้อมูลที่ได้จาก Factsheet PDF ซึ่ง API ไม่มี

เพิ่มเข้ามาระหว่างทาง — sector / ประเทศ / อันดับความน่าเชื่อถือ /
ผู้จัดการกองทุน / กลุ่ม AIMC / holdings ของกองทุนหลัก (feeder look-through)
ดู [[../guides/factsheet-extraction|Factsheet Extraction]]

### พอร์ตการลงทุน

เก็บ **ครบทุกรายการ** ของงวดล่าสุด (136,077 แถว) พร้อม ISIN ผู้ออก และมูลค่า
พร้อมสถิติกระจุกตัว — ดู [[../guides/holdings-data|Holdings Data]]

---

## เริ่มต้นใช้งานใน 3 ขั้นตอน

```bash
# 1. เปิด vault
#    Obsidian -> Open folder as vault -> เลือกโฟลเดอร์ vault/
#    เริ่มที่ Indexes/00-home.md

# 2. อ่านคู่มือ API
#    docs/api-reference/00-index.md

# 3. อัปเดตข้อมูลรอบใหม่ (factsheet ออกรายเดือน)
rm data/raw/*.done && python run_all.py
```

---

## รอบพัฒนา 2026-08-27 — สถานะปัจจุบัน

กำลังทำ 3 ก้อน (สถานะรายตัวที่ [[tasks|Phase 9]]):

| ก้อน | สถานะ |
|---|---|
| 1. Semantic validator (`validate_semantics.py`) | ✅ เขียนเสร็จ + รันได้ · เหลือ re-run ยืนยันเลข (T-094), แก้ต้นเหตุ Mapletree (T-095), เพิ่ม stage ใน pipeline (T-096) |
| 2. Dataview + เทียบค่าธรรมเนียม ([[roadmap|R-01]]/[[roadmap|R-02]]) | ⏳ ยังไม่เริ่ม |
| 3. Changelog ต่อเนื่อง ([[roadmap|R-07]]) | ✅ โค้ดพร้อม + wired ใน `daily.py` · ⏳ เหลือลงทะเบียน scheduler |
| 4. Git + push GitHub ([[roadmap|R-03]]) | ⏳ ยังไม่เริ่ม — ปลายทาง `github.com/RungthumLee/fund-markdown` |

> [!WARNING] ก่อน push: ยืนยันว่า `.env.local` (API key + `DB_*` + Ollama) ถูก `.gitignore` จริง
> และ `data/raw/` (~1 GB) ไม่ถูก stage — ดู [[security-notes|Security Notes]]

**ผลตรวจ semantic รอบแรก:** 🔴 S1 = 3 (Mapletree/MINT 377 กอง — [[issues|ISS-035]]) ·
🟡 S2 = benchmark ต้นทางผิด ([[issues|ISS-036]]) · 🟢 S5/S6/S7 = ช่องว่างข้อมูลต้นทาง
รายงานเต็มที่ [[semantic-report|Semantic Report]]

## สิ่งที่ควรทำต่อ (เรียงตามความคุ้มค่า)

1. **[[tasks|T-095]]** แก้ต้นเหตุ Mapletree/MINT ใน `normalize_entities.py` → validator เขียว
2. **[[roadmap|R-01]]** เพิ่ม Dataview query ในโน้ต index — frontmatter พร้อมแล้ว ใช้แรงน้อยมาก
3. **[[roadmap|R-02]]** โน้ตเปรียบเทียบค่าธรรมเนียมรายหมวด — ตอบคำถามที่คนถามบ่อยที่สุด
4. **[[outstanding|OUT-001]]** ปรับวิธีตรวจจับ RMF ให้แม่นกว่าการดูชื่อกอง

---

## สิ่งที่ต้องรู้ก่อนแก้โค้ด

> [!IMPORTANT]
> **1. ไฟล์ raw ใหญ่มาก (~1 GB)**
> `profiles.jsonl` และ `mutual_fund_fees.jsonl` ไฟล์ละหลายร้อย MB
> อ่านแบบ streaming เสมอ — ห้าม `json.load()` ทั้งไฟล์

> [!IMPORTANT]
> **2. `proj_id` ไม่ unique ในทุก response**
> ข้อมูลบางชุดเป็นระดับ share class ต้อง join ด้วย `(proj_id, fund_class_name)`
> ตารางเต็มอยู่ที่ [[../guides/fund-identifiers|Fund Identifiers]]

> [!IMPORTANT]
> **3. อย่าแก้ไฟล์ที่สร้างอัตโนมัติด้วยมือ**
> `docs/api-reference/*`, `docs/guides/data-dictionary.md`,
> `docs/project/data-quality.md`, `docs/project/validation-report.md`,
> และทุกอย่างใน `vault/Funds/`, `vault/AMCs/`, `vault/Indexes/`, `vault/Factsheets/`
> จะถูกเขียนทับ — แก้ที่สคริปต์แทน
>
> ไฟล์ที่**เขียนด้วยมือ**และปลอดภัย: `vault/Concepts/*`, `docs/guides/*`
> (ยกเว้น data-dictionary), `docs/project/*` (ยกเว้น 2 ไฟล์ข้างต้น)

> [!IMPORTANT]
> **4. `.env.local` ห้าม commit**
> อยู่ใน `.gitignore` แล้ว ตรวจก่อน push ทุกครั้ง — [[security-notes|Security Notes]]

---

## ปัญหาที่เจอระหว่างทางและแก้แล้ว

สรุปสั้น ๆ — รายละเอียดที่ [[issues|Issue Log]]

| # | ปัญหา | วิธีแก้ |
|---|---|---|
| ISS-001 | Portal ตอบ 403 ต่อ script | ใช้ machine-readable mirror ของ catalog |
| ISS-002 | ภาษาไทยพังเมื่อ pipe ผ่าน shell บน Windows | เขียนไฟล์ด้วย Python `encoding="utf-8"` โดยตรง |
| ISS-003 | ไฟล์ raw ใหญ่ผิดคาด (HTML/Base64 ฝังอยู่) | streaming read + `clean_text()` decode และตัดความยาว |
| ISS-004 | heredoc ใน Git Bash พังกับ backslash | เขียนไฟล์ที่มี escape ซับซ้อนด้วย editor |
| ISS-005 | ไม่รู้เพดาน rate limit | หน่วง 0.12 วินาที + exponential backoff |
| ISS-006 | `mutual_fund_fees` ดึงช้า | ยอมรับได้ — checkpoint กันดึงซ้ำ |

---

## การตัดสินใจสำคัญ

| # | ตัดสินใจ | ทำไม |
|---|---|---|
| DEC-001 | bulk fetch ไม่ใช่ per-fund | เร็วกว่า ~24 เท่า (48,000 → ~2,000 requests) |
| DEC-002 | จำกัดหน้าต่างเวลา time-series | โจทย์คือภาพปัจจุบัน ไม่ใช่คลังย้อนหลัง |
| DEC-003 | กรอง scope ที่ระดับโครงการ | `proj_term_flag` / `proj_retail_type` เป็นคุณสมบัติของโครงการ |
| DEC-004 | เก็บกองจำกัดผู้ลงทุนไว้ ติด tag | โจทย์ให้ตัดแค่ Term fund กับ PVD |
| DEC-005 | ตั้งชื่อไฟล์ด้วยชื่อย่อกองทุน | ชื่อย่อ `K-FIXED` อ่านรู้เรื่องกว่ารหัส `M0123_2560` |
| DEC-006 | PDF แยกจาก vault, markdown อยู่ใน vault | Obsidian ทำงานเร็ว และค้นหาข้อความได้ |

รายละเอียดที่ [[decisions|Decision Log]]

---

## ข้อจำกัดที่ต้องรู้

ทั้งหมดบันทึกไว้ที่ [[data-quality|Data Quality §5]] — สรุปที่สำคัญที่สุด:

- ข้อมูลเป็นภาพ ณ **งวด factsheet ล่าสุด** ไม่ใช่เรียลไทม์
- NAV ย้อนหลังเก็บแค่ 120 วัน
- พอร์ตรายตัวแสดง **ครบทุกรายการ** ของงวดล่าสุด แต่เป็นข้อมูล**รายไตรมาส** จึงล้าหลัง NAV
- RMF ตรวจจับจากชื่อกองทุน (heuristic)
- ข้อความยาวถูกตัดที่ 4,000 อักขระ

> [!NOTE]
> คลังนี้เป็น**ข้อมูลอ้างอิงเพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน**
