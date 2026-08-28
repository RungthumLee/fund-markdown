---
title: Ideas — Skills & Factor Analysis
tags: [project, ideas, backlog]
updated: 2026-08-28
---

# 💡 Ideas — Skills ที่ใช้กับ Data + Factor Analysis

บันทึกไอเดียเพื่อพิจารณา ยังไม่ลงมือ · ที่เกี่ยวข้อง: [[STATUS|STATUS]] · [[roadmap|Roadmap]] · [[tasks|Tasks]]

---

## 1. Skills — ให้ AI ทำงานกับคลังนี้

Skill = ชุดคำสั่งสำเร็จรูปให้ AI (เช่น Claude Code) อ่าน/สังเคราะห์ข้อมูลในคลัง
รูปแบบไฟล์: `SKILL.md` (frontmatter `name` + `description` + วิธีใช้ data)

> คลังนี้มี 3 ชั้นข้อมูลให้ skill ใช้: **โน้ต markdown** (`vault/`) · **tag/Dataview** (faceted) ·
> **JSON ดิบ** (`data/processed/*.json` — funds, entities, lookthrough, master, security_meta)

| Skill | ทำอะไร | ใช้ข้อมูล | หมายเหตุ |
|---|---|---|---|
| **fund-explainer** | อธิบายกอง 1 ตัวเป็นภาษานักลงทุน (แบบที่ทำกับ A-RING) | โน้ตกอง + โน้ตกองหลัก | deterministic (อ่าน+สังเคราะห์) |
| **fund-finder** | โจทย์ภาษาคน → filter tag/Dataview → กองที่ตรง พร้อมเหตุผล | faceted tags | "พักเงินสั้น เสี่ยงต่ำ" → `#use/park-cash` |
| **fund-compare** | เทียบ 2–3 กองข้าง ๆ กัน (ค่าธรรมเนียมรวม 2 ชั้น · ประเทศ · sector · look-through overlap) | funds.json + lookthrough | |
| **portfolio-overlap** | ผู้ใช้ถือหลายกอง → คำนวณความซ้ำซ้อนจริง (กองหลักเดียวกัน / หุ้นเดียวกันผ่าน look-through) + เตือนกระจุกตัว/ค่าธรรมเนียมซ้อน | lookthrough.json + master_links | ตอบโจทย์ "ถือหลายกองแต่ซ้ำกัน" |
| **fee-audit** | แยกต้นทุนรวม (TER ไทย + OCF กองหลัก) + หากองถูกกว่าในกลุ่ม AIMC เดียวกัน | fees.py + peer_group | |
| **holding-explorer** | หุ้น/สินทรัพย์ 1 ตัว → กองไทยทุกกองที่ถือ (ตรง+ทางอ้อม) + สัดส่วนรวม | entities.json + lookthrough | ใช้ B1/B2 ที่ทำไว้ |
| **factor-exposure** | ปัจจัยบวก/ลบที่กระทบกอง (ดูข้อ 2) | holdings + sector + country + factor-map | ต้องมี factor-map ก่อน |
| **data-refresh** | รัน pipeline (`daily.py` / `fetch_sectors.py`) แล้วสรุปสิ่งที่เปลี่ยน | scripts + changelog | operational |

**หลักการร่วมของทุก skill:**
- ตอบจาก **data ในคลังเท่านั้น** อ้างอิงที่มาทุกตัวเลข (dataset/field หรือเลขหน้า) — เหมือนกติกา loop
- **ข้อมูลอ้างอิง ไม่ใช่คำแนะนำ** — ห้ามทำนาย/ชี้นำซื้อขาย
- ถ้าข้อมูลไม่มี ให้บอกว่าไม่มี ไม่เดา (ISS-009)

**ลำดับแนะนำ:** เริ่ม **fund-explainer** + **fund-finder** (ใช้ของที่มีครบแล้ว) → **portfolio-overlap** (unique, ใช้ look-through) → **factor-exposure** (หลังทำ factor-map)

---

## 2. Factor Analysis — ปัจจัยบวก/ลบที่กระทบกอง (micro + macro)

**ไอเดียตั้งต้น (จากผู้ใช้):** เพราะเรารู้ **holdings + look-through** แล้ว จึงเสนอปัจจัยที่กระทบกองได้
ทั้งระดับ micro (บริษัท/หมวด) และ macro (ประเทศ/ค่าเงิน/ดอกเบี้ย) — แต่ **ไม่รู้จะหา data จากไหน**

### แยกให้ชัดว่า "ปัจจัย" มี 2 ชนิด — คนละแหล่งข้อมูล

**(ก) Structural exposure — "กองนี้ไวต่ออะไร" (ทำได้เลย ไม่ต้องมี feed)**
เรามี sector/country/holdings อยู่แล้ว → map เข้ากับ **ตัวขับเคลื่อนมาตรฐานของแต่ละหมวด** ได้
โดยสร้าง **factor-map** (ตารางความรู้ static เขียนครั้งเดียว): `sector/theme/asset → ปัจจัยบวก/ลบที่รู้กันทั่วไป`

ตัวอย่างจากที่รู้กัน (ไม่ต้อง fetch อะไร):
| หมวด/ธีม | ปัจจัยบวก | ปัจจัยลบ |
|---|---|---|
| เหมืองทองคำ (A-RING) | ราคาทองขึ้น · ดอกเบี้ยแท้จริงติดลบ · USD อ่อน | ต้นทุนขุด/พลังงานสูง · ดอกเบี้ยจริงขึ้น · USD แข็ง |
| ธนาคาร | ดอกเบี้ยขาขึ้น (NIM กว้าง) · เศรษฐกิจโต | NPL/หนี้เสีย · เศรษฐกิจถดถอย |
| เทคโนโลยี/semiconductor | วัฏจักรชิปขาขึ้น · AI capex | ดอกเบี้ยสูง (กด valuation) · จีน-สหรัฐกีดกัน |
| พลังงาน | ราคาน้ำมัน/ก๊าซขึ้น · OPEC ลดกำลังผลิต | เปลี่ยนผ่านพลังงานสะอาด · อุปสงค์ชะลอ |

→ กองแต่ละตัวจะได้ "ปัจจัยที่กระทบ" **จากหมวด/ประเทศที่ถือจริง** (deterministic, อ้างอิงได้)
นี่คือเวอร์ชันที่ **ปลอดภัย + ทำได้เลย** — บอก "ไวต่ออะไร" ไม่ใช่ "จะขึ้นหรือลง"

**แหล่ง factor-map:** ความรู้การเงินมาตรฐาน (เขียนเป็นโน้ต reference คล้าย `Concepts/`)
ไม่ต้องใช้ API/feed — เขียนครั้งเดียว ปรับปรุงเมื่อรู้เพิ่ม

**(ข) Live factor context — "ตอนนี้ปัจจัยเป็นยังไง" (ต้องมี feed + ระวัง)**
ค่าปัจจุบัน (ราคาทองวันนี้ · ทิศทางดอกเบี้ย · ข่าว) = ต้องดึงจากภายนอก:
- ราคาสินค้าโภคภัณฑ์/ดัชนี/ค่าเงิน → Yahoo/FRED (ฟรี, มี API)
- ข่าว/มุมมอง → web search ตอน query (LLM skill)

> [!CAUTION] เส้นที่ **ไม่ควรข้าม**
> - live context เป็นข้อมูล**อ่อนไหวตามเวลา** — ห้ามเก็บลงโน้ตแบบถาวร (จะเก่าทันที)
> - อย่าให้กลายเป็น**คำทำนาย/ชี้นำ** — ผิดหลักคลัง (ISS-014 เตือนเรื่องตัวเลขจากผลค้นที่ดูน่าเชื่อ)
> - ถ้าทำ ให้แยกเป็น skill ที่ดึงสด ๆ ตอนถาม + ติดป้าย "ยังไม่ยืนยัน / ณ เวลานี้"

### ข้อเสนอเชิงปฏิบัติ (ผมเสริม)
1. **ทำ (ก) ก่อน** — สร้าง `vault/Concepts/factor-map.md` (หรือ `data/factor_map.json`)
   map `sector/*` + `geo/*` + `theme/*` → ปัจจัยบวก/ลบ → เจน section "⚖️ ปัจจัยที่กระทบ" ในโน้ตกอง
   จาก sector/country ที่กองถือจริง · **deterministic ไม่ต้อง feed**
2. **(ข) เป็น optional เฟสหลัง** — skill `factor-live` ที่ดึงราคาทอง/ดอกเบี้ยจาก FRED/Yahoo ตอนถาม
   ประกอบกับ (ก) แต่ **ไม่เขียนกลับลงคลัง**
3. แหล่งฟรีที่ใช้ได้จริง: **FRED** (ดอกเบี้ย/เงินเฟ้อ/ราคาสินค้าโภคภัณฑ์ — มี API ฟรี) · **Yahoo** (ราคาสินทรัพย์ — มีอยู่แล้วใน pipeline)

**สรุปคำตอบเรื่อง "หา data จากไหน":**
ส่วนที่เป็น **"ไวต่อปัจจัยอะไร" ไม่ต้องหา data จากที่ไหนเลย** — เรารู้ holdings/sector/country แล้ว
เหลือแค่เขียน **factor-map (ความรู้ static)** ครั้งเดียว · ส่วน **ค่าปัจจุบัน**ค่อยดึงสดจาก FRED/Yahoo ตอนถาม (optional)

---

## 3. ไอเดียเสริมอื่น ๆ (backlog)
- `by-category` index ของกองหลัก (Morningstar category) — ให้ vertical กองหลัก browse ได้
- master holdings แสดง sector ต่อหุ้น (จาก `security_meta`)
- semantic validator เพิ่ม check ชั้นใหม่ (country/sector coverage, cap สอดคล้อง policy)
