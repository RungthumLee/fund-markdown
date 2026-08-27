---
title: Bulk vs Per-fund fetching
tags: [guide, performance, architecture]
---

# ⚡ Bulk vs Per-fund — ทำไมถึงเลือกดึงแบบ bulk

**ที่เกี่ยวข้อง:** [[pagination|Pagination]] · [[pipeline|Pipeline]] · [[../project/decisions|Decision log #1]]

---

## ปัญหา

มีกองทุนที่ต้องเก็บ ~2,300 โครงการ × 21 endpoints
ถ้ายิงแบบ per-fund (ส่ง `proj_id` ทีละกอง) = **~48,000 requests**

## การค้นพบสำคัญ

query parameter `proj_id` ของ SEC API v2 เป็น **optional ทุก endpoint**
ถ้าไม่ใส่ = คืนข้อมูล **ทั้งตลาด** แล้ววน cursor เอา

## เปรียบเทียบ

| | Per-fund | **Bulk (ที่เลือกใช้)** |
|---|---|---|
| จำนวน request | ~48,000 | ~2,000 |
| เวลาโดยประมาณ | ~16 ชั่วโมง | ~40 นาที |
| ความเสี่ยงโดน rate limit | สูง | ต่ำ |
| ความซับซ้อนของ retry | ต้องจำว่ากองไหนพลาด | checkpoint ต่อ dataset พอ |
| ข้อเสีย | — | ต้องกรอง/จัดกลุ่มเองในเครื่อง + ไฟล์ใหญ่ |

**ผลลัพธ์: เร็วขึ้นประมาณ 24 เท่า**

## วิธี implement

1. `harvest.py` ดึงแต่ละ endpoint เป็น stream เดียว → `data/raw/<dataset>.jsonl`
2. `transform.py` อ่าน JSONL ทั้งหมด แล้ว index เป็น `dict[proj_id] -> rows`
3. กรองด้วยเกณฑ์ [[scope-and-filters|Scope & Filters]] ในหน่วยความจำ
4. `gen_vault.py` เขียน markdown ต่อ 1 กอง

## ข้อควรระวัง

> [!WARNING]
> ไฟล์ raw บางตัวใหญ่มาก เพราะมี field ที่เป็นข้อความยาว/HTML/Base64
> - `profiles.jsonl` ≈ 172 MB (จาก `investment_policy_desc`)
> - `mutual_fund_fees.jsonl` ≈ 200 MB+ (จาก `fee_other_desc`)
>
> `transform.py` จึงต้องอ่านแบบ **streaming ทีละบรรทัด** และตัด/ย่อ field เหล่านี้
> ห้าม `json.load()` ทั้งไฟล์เข้า memory

> [!NOTE]
> `data/raw/` ควรอยู่ใน `.gitignore` — สร้างใหม่ได้จาก API เสมอ
