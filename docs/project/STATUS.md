---
title: STATUS — คิวงานและบันทึกลูป
tags: [project, status, loop]
updated: 2026-08-28
---

# 🔁 STATUS — คิวงาน (G→D→I→V→R→S)

โครงลูป: **G**oal → **D**ecide → **I**mplement → **V**erify → **R**ecord → **S**top
ที่เกี่ยวข้อง: [[tasks|Tasks]] · [[issues|Issues]] · [[decisions|Decisions]]

## กติกาแต่ละขั้น
| ขั้น | ทำอะไร | เงื่อนไขผ่าน |
|---|---|---|
| G | เลือกงานถัดไป 1 ชิ้นจากคิว | เล็กพอจบใน 1 รอบ (3–8 ไฟล์) |
| D | ตอบ 5 คำถามก่อนแตะไฟล์ | ตัดสินใจไม่ได้ → โหวต 3 agent แล้วบันทึก |
| I | เขียน markdown | ทุกตัวเลขมีแหล่งอ้างอิง (dataset/field หรือเลขหน้า PDF) |
| V | ตรวจ 2 ชั้น | broken_links=0 + ข้อเท็จจริงถูก |
| R | บันทึกลง docs | ทำทุกรอบ แม้รอบที่ไม่มีปัญหา |
| S | ถึงเป้า หรือต้องให้คนตัดสิน | — |

## 5 คำถามของ D
1. เป้าหมาย + เกณฑ์ "เสร็จ" ของงานนี้คืออะไร?
2. แหล่งข้อมูล/provenance ของทุกตัวเลข — มีจริงและเชื่อถือได้ไหม?
3. แตะไฟล์ไหนบ้าง (3–8)?
4. ตรวจผ่านยังไง (broken_links=0 + ข้อเท็จจริงถูก)?
5. มีทางแยกที่ต้องตัดสินใจไหม? ถ้ามี → โหวต 3 agent

---

## คิวงาน

- [x] **A1** ประเทศจากหลักทรัพย์ (ISIN/exchange) → rollup ขึ้นกอง → ดัชนี by-country ✅ Round 1
- [x] **B1** หลักทรัพย์เป็น knowledge node — เพิ่ม **ประเทศ** (ticker/exchange/ownership มีอยู่แล้ว) ✅ Round 2
- [x] **A2** sector facet + by-sector index จาก **factsheet allocation** (deterministic) ✅ Round 4
  · _Yahoo per-holding version รอ network (429 ในนี้) — ให้ผู้ใช้รันบนเครื่องตัวเอง_
- [~] **A3** ช่องว่างอื่น: **duration/credit ทำแล้ว** (Round 3) · currency=ยังไม่ parse · market-cap=ต้องแหล่งนอก

---

## บันทึกการตัดสินใจ (Decision log)

_บันทึกผลโหวต 3 agent ต่อทางแยกที่ตัดสินเองไม่ได้ (เฉพาะเรื่องสำคัญจริง)_

### DEC-L01 (A1) — จัดการ ISIN ที่เป็น "ที่จดทะเบียนกอง" (LU/IE/KY ~680 entity)
**ปัญหา:** feeder 983 กองถือ master ที่จดทะเบียน LU/IE/KY — ISIN→ประเทศตรง ๆ จะได้
"ลักเซมเบิร์ก" แทนตลาดจริง (เช่นจีน) กระทบความถูกต้องของชั้น geo ทั้งชั้น

**ผลโหวต: เอกฉันท์ 3/3 → Option 3 (dual field)**
- `domicile_country` = ISIN prefix ตรง ๆ เสมอ (provenance anchor, deterministic)
- `market_country` = ตลาดจริง — feeder ใช้ look-through, หุ้นตรงใช้ ISIN ตัวเอง
- rollup "% ประเทศ" ของกองใช้ **market_country** เท่านั้น

**ข้อควรระวังร่วม (ทั้ง 3 agent):** look-through ทะลุได้แค่บางส่วน (บาง master
`covered_pct` ~38%) → **ต้องแสดง "% ที่ทะลุได้ / ส่วนที่เหลือ" ชัดเจน** ไม่งั้น % ประเทศ
จะรวมไม่ถึง 100 และทำให้เข้าใจผิดว่าครบ

**เหตุที่ต้องโหวต:** เป็นทางแยกที่กำหนดความถูกต้องของ A1/A2/B1 ทั้งหมด ไม่ใช่เรื่องเล็ก

---

## บันทึกรอบ (Round log)

_หนึ่งบรรทัดต่อรอบ: งาน · ผล V · ไฟล์ที่แตะ_

- **R1 · A1 ประเทศจากหลักทรัพย์** — V ผ่าน (broken=0 · orphan=0 · ISIN/symbol→ประเทศถูกทุกตัวที่สุ่ม) ·
  ตัดสินใจ DEC-L01 (โหวต 3/3 dual field) · 1750/2121 กองมีประเทศ พร้อม covered% เปิดเผยส่วนที่ทะลุไม่ได้ ·
  ไฟล์: `geography.py`(ใหม่) · `gen_vault.py` (§7 + frontmatter + by-country index + home) · `STATUS.md` · `tasks.md`
- **R2 · B1 ประเทศในโน้ตหลักทรัพย์** — V ผ่าน (broken=0 · Tencent: ตลาด ฮ่องกง/จดทะเบียน เคย์แมน ✓ · NVIDIA สหรัฐ ✓) ·
  เพิ่ม `domicile_country`/`market_country`/`country` (domicile=ISIN, market=Bloomberg alias/symbol) ·
  ครอบคลุม 764/2960 equity (เฉพาะที่มี ISIN/Bloomberg code — ไม่เดา) · ไม่ต้องโหวต (ใช้ DEC-L01) ·
  ไฟล์: `geography.py` (+Bloomberg map) · `gen_entity_notes.py` · `STATUS.md`
  _ค้าง: หุ้น look-through ต่างประเทศที่ไม่มี ISIN (~2,200) ยังไม่มีประเทศ — เสริมได้ด้วยการ join symbol จาก lookthrough ภายหลัง_
- **R3 · A3 bond facets (duration/credit)** — V ผ่าน (broken=0 · K-FIXED → duration/medium + credit/investment-grade) ·
  parse duration ข้อความไทย "3 ปี 6 เดือน"→3.5 ปี · credit จาก factsheet (IG 147 · รัฐ 42 · HY 13) · duration (สั้น 118/กลาง 75/ยาว 30) ·
  ไม่ต้องโหวต · ไฟล์: `tagging.py` · `gen_vault.py` (facet label) · `STATUS.md`
  _ค้าง A3: currency (ต้อง parse factsheet เพิ่ม) · market-cap large/mid/small (ต้องแหล่งนอก เช่น Yahoo ซึ่งตอน 429)_
- **R4 · A2 sector facet (จาก factsheet)** — V ผ่าน (broken=0 · by-sector: การเงิน 155/เทค 129/พลังงาน 87 · 1AMSET50→financials) ·
  map ชื่อ sector ไทย(SET)+อังกฤษ(GICS) → canonical 10 กลุ่ม · tag `sector/*` 435 กอง + ดัชนี by-sector ·
  ไม่ต้องโหวต (map ตรงไปตรงมา) · ไฟล์: `tagging.py` · `gen_vault.py` (facet + index + home) · `STATUS.md`

---

## 🛑 STOP — สรุปสถานะลูป (R1–R4)

ทำเสร็จแบบ deterministic ครบทุกส่วนที่ทำได้ในสภาพแวดล้อมนี้:
- ✅ **A1** ประเทศตลาดต่อกอง (จากหลักทรัพย์ + look-through) + by-country
- ✅ **B1** ประเทศบนโน้ตหลักทรัพย์ (market/domicile)
- ✅ **A3** bond duration/credit facets
- ✅ **A2** sector facet + by-sector (จาก factsheet)

**ต้องให้คน/สภาพแวดล้อมตัดสิน (หยุดตามเกณฑ์ S):**
- **A2 Yahoo per-holding sector** — Yahoo คืน **429** ในนี้ · ต้องรัน fetch บนเครื่องผู้ใช้ (pipeline `fetch_masters` มีอยู่แล้ว)
- **A3 currency exposure** — ต้องขยาย `factsheet_sections.py` ให้ parse ตารางสกุลเงิน (งาน parsing ก้อนใหม่)
- **A3 market-cap (large/mid/small)** — ต้องแหล่งข้อมูลภายนอก (Yahoo, 429)
- **B1 coverage** — หุ้น look-through ต่างประเทศ ~2,200 ตัวที่ไม่มี ISIN ยังไม่มีประเทศ
