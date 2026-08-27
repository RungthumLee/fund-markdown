---
title: OpenFIGI
tags: [guide, data-quality, holdings, identifiers]
updated: 2026-08-27
---

# 🏷️ OpenFIGI — ผูกสินทรัพย์กับรหัสสากลของ Bloomberg

**ที่เกี่ยวข้อง:** [[entity-normalization|Entity Normalization]] ·
[[lookthrough|Look-through]] · [[../project/decisions|Decisions]] ·
[[../project/issues|Issues]]

สคริปต์: [`fetch_figi.py`](../../scripts/fetch_figi.py)

---

## ทำไมเลือก OpenFIGI

ทดสอบสามเจ้าด้วย ISIN จริงจากข้อมูลของเรา ไม่ใช่อ่านจากเอกสารอย่างเดียว

| | Finnhub | Financial Modeling Prep | **OpenFIGI** |
|---|---|---|---|
| เรียกได้โดยไม่สมัคร | ❌ HTTP 401 | ❌ HTTP 401 | ✅ ได้ (10 job/request) |
| มี key | 60/นาที · personal เท่านั้น | **250 ครั้ง/วัน** | **100 job/request** |
| ข้อมูลต่างประเทศ | **ต้องเสียเงิน** | จำกัด | ฟรีทั้งหมด |
| ทดสอบกับ ISIN ของเรา | ทำไม่ได้ | ทำไม่ได้ | **8/8** |
| เวลาต่อ 1 รอบ (3,357 รายการ) | — | **~13 วัน** | **91 วินาที** |

**Finnhub** ระบุเองว่า ISIN ต้องมี entitlement และ international coverage
อยู่ในแผนเสียเงิน — ISIN ของเราเป็นไทย 1,597 รายการ บวก LU/IE/SG/VN/MY/JP
**FMP** 250 ครั้ง/วัน คือ 13 วันต่อหนึ่งรอบ และการแสดงข้อมูลต่อสาธารณะ
ต้องมี licensing agreement แยก

---

## ผลที่ได้จริง

| | |
|---|---|
| ส่งไปถาม | 3,357 |
| **ผูกได้** | **3,026 (90%)** |
| ได้ ticker | 3,026 |
| ได้ `shareClassFIGI` | 1,921 |
| **ชื่อดีกว่าของเดิม** | **238 รายการ** |
| **ประเภทไม่ตรงกับที่ บลจ. ยื่น** | **70 รายการ** |

หาไม่เจอ 331 รายการ ซึ่ง **260 เป็นตั๋วเงิน** (ตั๋วแลกเงิน/ตั๋วสัญญาใช้เงินไทย)
ที่ไม่มีรหัสสากลจริง ๆ

### ตัวอย่างชื่อที่ดีขึ้น

| เดิม | จาก OpenFIGI |
|---|---|
| `BLACKROC` | ISHARES 1-3 YEAR TREASURY BOND |
| `IE00B3YCGJ38GB` | INVESCO S&P 500 ACC |
| `FFGSYAU_LX_USD` | FIDELITY-GL SH DN INC-YA USD |
| `KT-WTAI` | KTAM WLD TECHNLGY ARTFC INTL |

---

## สิ่งที่มีค่ากว่าชื่อ: `securityType`

[[../project/issues|ISS-029]] คือปัญหาที่ บลจ. คนละรายใส่ `assetliab_id`
ไม่ตรงกันสำหรับหลักทรัพย์เดียวกัน OpenFIGI เป็นบุคคลที่สามที่เป็นกลาง

**70 รายการที่ไม่ตรงกัน** ส่วนใหญ่คือ REIT ที่ถูกยื่นเป็นกองทุนหรือหุ้น

| เรายื่นเป็น | Bloomberg บอกว่า | จำนวน |
|---|---|---|
| หน่วยลงทุน | REIT | 37 |
| หุ้น | REIT | 15 |
| หุ้น | ETP | 15 |

> [!NOTE] ไม่แก้ `kind` ให้อัตโนมัติ
> `kind` เป็นส่วนหนึ่งของ `entity_id` การเปลี่ยนจะทำให้ทุกลิงก์ในวอลต์พัง
> จึงเก็บเป็น `figi_type` แล้ว**ขึ้นคำเตือนในโน้ต**เมื่อไม่ตรงกัน
> ให้ผู้อ่านเห็นทั้งสองฝั่ง

---

## กฎสองข้อที่มีเพราะไม่มีแล้วได้คำตอบผิด

### 1. ห้ามค้น ticker โดยไม่ระบุตลาด

```
TICKER=MTRE (ไม่ระบุ exchCode) → MAK-TUTUN AD RESEN   ← บริษัทมาซิโดเนีย
```

ของเราคือ **Muangthai Real Estate** — ตอบผิดแบบมั่นใจ
สคริปต์จึงใช้ TICKER **เฉพาะเมื่อ alias มีรหัสตลาดติดมาด้วย**
เช่น `FRT VN`, `SPXS LN`, `2330 TT` เท่านั้น

### 2. ชื่อจาก OpenFIGI ใช้เฉพาะเมื่อชื่อเดิมเป็นรหัส

Bloomberg ใช้ชื่อย่อ

| ก.ล.ต. (ชื่อจดทะเบียน) | OpenFIGI |
|---|---|
| KASIKORNBANK PUBLIC COMPANY LIMITED | KASIKORNBANK PCL |
| Capital Group New Perspective Fund | CAPITAL GP NEW PERS-BUSD |

ถ้าแทนที่หมดจะแย่ลง — ใช้กติกาเดียวกับตอน Yahoo คือแทนที่**เฉพาะเมื่อ
ชื่อเดิมได้คะแนนต่ำกว่า `REAL_NAME_SCORE`**

---

## หนึ่ง ISIN ได้หลาย listing

NVIDIA คืนมา **247 รายการ** (ทุกตลาดทั่วโลก) และ SPDR Gold คืนตลาดเยอรมัน
มาเป็นอันดับแรก — **หยิบตัวแรกไม่ได้**

| ฟิลด์ | วิธีเลือก |
|---|---|
| `name`, `securityType`, `marketSector` | **โหวตเสียงข้างมาก** — ทั้ง 247 listing ของ NVIDIA ตรงกันหมด |
| `ticker`, `exchCode` | listing ของ**ตลาดบ้านเกิด** ตาม `HOME_EXCHANGE` แล้วค่อย fall back ไป composite |

เลือก ticker ตามตลาดบ้านเกิดเพราะ ticker ต่างกันตามตลาดจริง ๆ —
SPDR Gold คือ `GLD` ที่นิวยอร์ก แต่ `GQ9` ที่แฟรงก์เฟิร์ต

---

## ลำดับใน pipeline

```
entities  →  figi  →  entities (รอบถัดไปได้ชื่อและประเภทจาก FIGI)
```

`fetch_figi.py` อ่าน `entities.json` เพื่อรู้ว่าต้องถามอะไร
`normalize_entities.py` จึงอ่าน `figi.json` **ของรอบก่อน**
หลักทรัพย์ที่เพิ่งโผล่จะได้ข้อมูลในรอบถัดไป — ISIN ไม่เปลี่ยน
ความล่าช้าหนึ่งรอบจึงกระทบเฉพาะรายการใหม่จริง ๆ

ใน `run_all.py` (สร้างใหม่จากศูนย์) มี stage `entities2` รันซ้ำให้เลย

---

## สิ่งที่ OpenFIGI **ไม่** ให้

- **ไม่คืน ISIN** — map ISIN → FIGI ได้ แต่ไม่ใช่ทางกลับ
  จึงหา ISIN ให้สินทรัพย์ที่ไม่มีไม่ได้
- **ไม่มีราคา ไม่มี AUM ไม่มีค่าธรรมเนียม** — เป็นระบบรหัสอย่างเดียว
  ส่วนนั้นยังต้องพึ่ง Yahoo + FT ([[master-fund-sources|Master Funds]])
- **ตั๋วเงินไทยไม่มีในระบบ** — 260 รายการ

> [!TIP] `shareClassFIGI` ใช้แทน ISIN ได้ในบางกรณี
> เป็นรหัสระดับ share class ที่ listing ทุกตลาดของหลักทรัพย์เดียวกันใช้ร่วมกัน
> 1,921 entity มีค่านี้ ใช้เป็นกุญแจรวมเพิ่มได้เมื่อ ISIN หาย

---

## ปรับแต่ง

| ค่า | ความหมาย |
|---|---|
| `BATCH_WITH_KEY = 100` | ขีดจำกัดจริงของ API เมื่อมี key (ไม่มี key = 10) |
| `DELAY_WITH_KEY = 0.4` | เผื่อจากเพดาน 25 request/6 วินาที |
| `HOME_EXCHANGE` | ประเทศของ ISIN → รหัสตลาด ใช้เลือก ticker |
| `TICKER_WITH_EX` | รูปแบบ alias ที่ยอมให้ค้นด้วย ticker |
