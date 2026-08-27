---
title: Quickstart
tags: [guide, sec-api, getting-started]
---

# 🚀 Quickstart — เริ่มใช้งาน SEC Fund API

คู่มือเริ่มต้นสำหรับดึงข้อมูลกองทุนรวมไทยจาก SEC Open Data API v2

**ที่เกี่ยวข้อง:** [[authentication|Authentication]] · [[pagination|Pagination]] · [[rate-limits-and-errors|Errors]] · [[../api-reference/00-index|API Reference]]

---

## 1. เตรียม API Key

สมัครและ subscribe ที่ [SEC Open Data Developer Portal](https://secopendata.sec.or.th/sec-open-apis)
แล้วนำ key มาใส่ใน `.env.local` ที่ root ของโปรเจกต์:

```ini
SEC_SUBSCRIPTION_KEY=<primary key 32 ตัวอักษร>
SEC_secondary_key=<secondary key>
```

> [!IMPORTANT]
> `.env.local` **ห้าม commit** ขึ้น git — ดู [[../project/security-notes|Security Notes]]

---

## 2. เรียก API ครั้งแรก

```bash
curl "https://api.sec.or.th/v2/fund/general-info/amcs?page_size=5" \
  -H "Ocp-Apim-Subscription-Key: $SEC_SUBSCRIPTION_KEY"
```

ผลลัพธ์:

```json
{
  "message": "success",
  "page_size": 5,
  "next_cursor": "MnxFMTBBQzI3YkQvUXNQ...",
  "items": [
    {
      "unique_id": "C0000033452",
      "comp_name_en": "EASTSPRING ASSET MANAGEMENT (THAILAND) COMPANY LIMITED",
      "comp_name_th": "บริษัทหลักทรัพย์จัดการกองทุน อีสท์สปริง (ประเทศไทย) จำกัด",
      "last_upd_date": "2026-08-27T07:42:19.577"
    }
  ]
}
```

ทุก response มีโครงเดียวกัน: `message` · `page_size` · `next_cursor` · `items[]`

---

## 3. ใช้ผ่าน Python client ของโปรเจกต์นี้

```python
import sys; sys.path.insert(0, "scripts")
from sec_client import SECClient, EP

client = SECClient()                       # อ่าน key จาก .env.local อัตโนมัติ

# ดึงทีละหน้า
data = client.get(EP["profiles"], {"fund_status": "Registered", "page_size": 100})

# ดึงทั้งหมด (วน cursor ให้อัตโนมัติ)
for fund in client.paginate(EP["profiles"], {"fund_status": "Registered"}):
    print(fund["proj_abbr_name"], fund["proj_name_th"])
```

`SECClient` จัดการให้แล้ว: retry + exponential backoff, สลับไป secondary key เมื่อ 401/403,
หน่วงเวลาระหว่าง request และ log ลง `logs/sec_client.log`

---

## 4. ดึงข้อมูลทั้งชุด (bulk harvest)

```bash
python scripts/harvest.py              # ดึงครบทุก dataset
python scripts/harvest.py fs_fees      # ดึงเฉพาะบางชุด
python scripts/harvest.py --force nav  # บังคับดึงใหม่
```

ผลลัพธ์เก็บที่ `data/raw/<dataset>.jsonl` (1 record ต่อ 1 บรรทัด) พร้อมไฟล์ `.done`
เพื่อให้รันซ้ำแล้ว **ข้าม dataset ที่เสร็จแล้ว**

> [!TIP]
> เกือบทุก endpoint เรียกได้โดย **ไม่ต้องใส่ `proj_id`** ซึ่งจะคืนข้อมูลทั้งตลาด
> วิธีนี้เร็วกว่าการยิงทีละกอง 2,300 ครั้งอย่างมาก — ดู [[bulk-vs-per-fund|Bulk vs Per-fund]]

---

## 5. สร้าง Obsidian vault

```bash
python scripts/transform.py       # แปลง raw → data/processed/funds.json
python scripts/gen_vault.py       # สร้าง vault/ (markdown + wikilinks)
python scripts/fetch_factsheets.py  # โหลด PDF factsheet
python scripts/parse_factsheets.py  # อ่าน PDF → markdown
```

ดู [[pipeline|ภาพรวม Pipeline ทั้งหมด]]

---

## ลำดับการเรียนรู้ที่แนะนำ

1. [[authentication|Authentication]] — key ทำงานยังไง
2. [[pagination|Pagination]] — cursor-based ไม่ใช่ offset
3. [[fund-identifiers|Fund Identifiers]] — `proj_id` vs `regis_id` vs `fund_class_name`
4. [[fund-taxonomy|Fund Taxonomy]] — ประเภทกองทุน / การกรอง Term fund และ PVD
5. [[../api-reference/00-index|API Reference ทั้ง 21 endpoints]]
