---
title: Fund Identifiers
tags: [guide, sec-api, data-model, keys]
---

# 🔑 Fund Identifiers — คีย์ต่าง ๆ และวิธี join ข้อมูล

เข้าใจเรื่องนี้ก่อน มิฉะนั้นจะ join ข้อมูลผิดทั้งระบบ

**ที่เกี่ยวข้อง:** [[fund-taxonomy|Fund Taxonomy]] · [[data-dictionary|Data Dictionary]] · [[pipeline|Pipeline]]

---

## คีย์หลักทั้ง 4 ตัว

| Field | ระดับ | ตัวอย่าง | คำอธิบาย |
|---|---|---|---|
| `unique_id` | บลจ. | `C0000000021` | รหัสบริษัทจัดการกองทุน (AMC) |
| `proj_id` | **โครงการ** | `M0001_2558` | เลขที่โครงการ — **คีย์หลักในการ join ทุก API** |
| `regis_id` | กองทุน | `MF0013_2558` | เลขที่จดทะเบียนกองทุน |
| `fund_class_name` | ชนิดหน่วยลงทุน | `main`, `K-FIXED-A` | share class ภายในโครงการเดียวกัน |

รูปแบบ `proj_id`: `{Type}{ID}_{ปี พ.ศ.}` เช่น `M0001_2558` = โครงการลำดับ 0001 ปี 2558

---

## ความสัมพันธ์

```
AMC (unique_id)
 └── Project / กองทุน (proj_id)          ← 1 บลจ. มีหลายโครงการ
      ├── Share class (fund_class_name)   ← 1 โครงการมีได้หลาย class
      │     "main" = ไม่มี multi-class
      └── regis_id                        ← เลขจดทะเบียน 1:1 กับ proj_id
```

**ตัวเลขจริงในโปรเจกต์นี้:** 30 บลจ. → 2,343 โครงการ (Registered) → 4,892 share class

---

## ⚠️ กับดักที่ต้องระวัง

> [!WARNING]
> **1. `proj_id` ไม่ unique ใน response**
> API หลายตัวคืนข้อมูล **1 แถวต่อ share class** ไม่ใช่ต่อโครงการ
> เช่น `profiles` คืน 4,892 แถว จาก 2,343 โครงการ
> ต้อง group by `proj_id` เอง หรือ join ด้วย `(proj_id, fund_class_name)`

> [!WARNING]
> **2. บาง API ไม่มี `fund_class_name`**
> `risk-spectrum`, `top5-holdings`, `asset-allocation`, `benchmarks`, `ipos`
> เป็นข้อมูล**ระดับโครงการ** — join ด้วย `proj_id` อย่างเดียว
> ส่วน `fees`, `performance`, `statistics`, `dividend-policy`, `nav`
> เป็นข้อมูล**ระดับ class** — ต้อง join ด้วย `(proj_id, fund_class_name)`

> [!WARNING]
> **3. `dividend-history` ใช้ `class_abbr_name` ไม่ใช่ `fund_class_name`**
> ชื่อ field ต่างกัน และค่าก็เป็นชื่อย่อ ไม่ตรงกับ `fund_class_name` เสมอไป

> [!WARNING]
> **4. หลาย record ต่อ 1 กอง เพราะเป็นข้อมูลตามงวด**
> API กลุ่ม factsheet มี `start_date` / `end_date` — 1 กองมีหลายงวดย้อนหลัง
> ใช้ `latest=true` เพื่อเอาเฉพาะงวดล่าสุด (โปรเจกต์นี้ใช้วิธีนี้)

---

## ตารางสรุประดับข้อมูลของแต่ละ endpoint

| Dataset | ระดับ | คีย์ join |
|---|---|---|
| `amcs` | บลจ. | `unique_id` |
| `profiles` | class | `proj_id` + `fund_class_name` |
| `specifications` | class | `proj_id` + `fund_class_name` |
| `mutual_fund_fees` | class | `proj_id` + `fund_class_name` |
| `involve_parties` | โครงการ | `proj_id` |
| `fs_urls` | class | `proj_id` + `fund_class_name` |
| `fs_ipos` | โครงการ | `proj_id` |
| `fs_benchmarks` | โครงการ | `proj_id` |
| `fs_min_amounts` | class | `proj_id` + `fund_class_name` |
| `fs_periods` | class | `proj_id` + `fund_class_name` |
| `fs_risk` | โครงการ | `proj_id` |
| `fs_statistics` | class | `proj_id` + `fund_class_name` |
| `fs_dividend` | class | `proj_id` + `fund_class_name` |
| `fs_fees` | class | `proj_id` + `fund_class_name` |
| `fs_performance` | class | `proj_id` + `fund_class_name` |
| `fs_asset_alloc` | โครงการ | `proj_id` |
| `fs_top5` | โครงการ | `proj_id` |
| `out_portfolio` | โครงการ | `proj_id` + `period` |
| `out_port_asset_type` | โครงการ | `proj_id` + `period` |
| `nav` | class | `proj_id` + `fund_class_name` + `nav_date` |
| `dividend_history` | class | `proj_id` + `class_abbr_name` |

---

## ตัวระบุอื่น ๆ

| Field | คำอธิบาย |
|---|---|
| `proj_abbr_name` | ชื่อย่อกองทุน เช่น `K-FIXED` — ที่คนทั่วไปใช้เรียก **แต่ไม่การันตี unique** |
| `fund_class_isin_code` | ISIN ของ share class (มาตรฐานสากล) |
| `isin_code` | ISIN ของหลักทรัพย์ในพอร์ต (คนละความหมาย!) |

> [!TIP]
> ใน vault ที่ generate ออกมา ใช้ `proj_abbr_name` เป็นชื่อไฟล์เพื่อให้อ่านง่าย
> แต่เก็บ `proj_id` ไว้ใน frontmatter เสมอเพื่อความถูกต้อง
> กรณีชื่อย่อชนกัน จะเติม suffix จาก `proj_id`
