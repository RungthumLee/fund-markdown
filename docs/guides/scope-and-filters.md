---
title: Scope & Filters
tags: [guide, scope, decisions]
---

# 🎯 ขอบเขตข้อมูล และเกณฑ์การคัดกรอง

เอกสารนี้บันทึก **เกณฑ์ที่ใช้ตัดสินว่ากองไหนเข้า vault** และเหตุผล
ถ้าจะเปลี่ยนขอบเขต ให้แก้ที่ `scripts/transform.py` → `is_in_scope()` และอัปเดตหน้านี้

**ที่เกี่ยวข้อง:** [[fund-taxonomy|Fund Taxonomy]] · [[pipeline|Pipeline]] · [[../project/decisions|Decision log]]

---

## โจทย์

> "เก็บข้อมูลกองทุนที่ยังมีอยู่ ยกเว้น Term fund, PVD"

แปลเป็นเกณฑ์ที่ทำงานได้:

| เงื่อนไข | Field | ค่าที่รับ | เหตุผล |
|---|---|---|---|
| ยังมีอยู่ | `fund_status` | `Registered` | จดทะเบียนแล้วและยังไม่เลิก — สถานะอื่นคือ IPO (ยังไม่ตั้ง), Expired/Canceled/Liquidated (จบแล้ว) |
| ไม่ใช่ Term fund | `proj_term_flag` | ≠ `Y` | `Y` = กำหนดอายุโครงการ = Term Fund |
| ไม่ใช่ PVD | `proj_retail_type` | ≠ `V` | `V` = กองทุนรวมเพื่อผู้ลงทุนที่เป็นกองทุนสำรองเลี้ยงชีพ |

การกรองทำที่ระดับ **โครงการ (`proj_id`)** ไม่ใช่ระดับ share class —
ถ้า class ใดใน proj_id เข้าเกณฑ์ Term/PVD จะตัดทั้งโครงการ (ดู [[../project/decisions|Decision log #3]])

---

## การ implement

```python
def is_in_scope(classes: list[dict]) -> tuple[bool, str]:
    """classes = ทุก share class ของ proj_id เดียวกัน"""
    if not any(c.get("fund_status") == "Registered" for c in classes):
        return False, "not-registered"
    if any(c.get("proj_term_flag") == "Y" for c in classes):
        return False, "term-fund"
    if any(c.get("proj_retail_type") == "V" for c in classes):
        return False, "pvd"
    return True, "in-scope"
```

ทุกกองที่ถูกตัดออกจะถูกบันทึกไว้ใน `data/processed/excluded.json`
พร้อมเหตุผล — ตรวจสอบย้อนหลังได้ ดู [[../project/data-quality|Data Quality]]

---

## สิ่งที่ **ไม่ได้** ตัดออก (โดยตั้งใจ)

| ประเภท | เหตุผลที่เก็บไว้ |
|---|---|
| กอง `X` / `A` / `B` / `H` / `N` (AI/HNW/II/UI) | ยังเป็นกองทุนรวมเปิดที่ยังมีอยู่ ไม่ใช่ Term/PVD — ติด tag `#restricted-investor` ให้กรองต่อได้ |
| กอง `G` (นโยบายภาครัฐ) | เช่นเดียวกัน — ติด tag `#government-policy` |
| ETF / Leveraged / Inverse | เป็น open-end ไม่ใช่ Term fund |
| Feeder fund | เช่นเดียวกัน |
| SSF / RMF / Thai ESG | เป็น open-end มีสิทธิประโยชน์ภาษี ไม่ใช่ Term |
| Trigger fund | ไม่มี flag แยกใน API — ส่วนใหญ่จะถูกจับได้จาก `proj_term_flag=Y` อยู่แล้ว |

---

## ขอบเขตข้อมูลย้อนหลัง (time series)

เพื่อไม่ให้ dataset บวมจนใช้งานไม่ได้ ข้อมูลรายวัน/รายงวดถูกจำกัดหน้าต่างเวลา
กำหนดที่ `scripts/harvest.py`:

| Dataset | หน้าต่าง | ตัวแปร |
|---|---|---|
| `nav` | 120 วันล่าสุด | `NAV_DAYS` |
| `out_port_asset_type` | 4 เดือนล่าสุด | `PORT_MONTHS_BACK` |
| `out_portfolio` | 2 ไตรมาสล่าสุด | `PORT_QUARTERS_BACK` |
| `dividend_history` | ทั้งหมด | — |
| factsheet ทุกตัว | งวดล่าสุด (`latest=true`) | — |

ถ้าต้องการย้อนหลังมากกว่านี้ ให้แก้ค่าคงที่แล้วรัน `python scripts/harvest.py --force <dataset>`
