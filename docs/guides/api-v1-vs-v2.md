---
title: API v1 vs v2
tags: [guide, sec-api, migration]
---

# 🔀 SEC Fund API — v1 vs v2

**ที่เกี่ยวข้อง:** [[authentication|Authentication]] · [[../api-reference/00-index|API Reference]]

---

## ไทม์ไลน์การย้าย

| วันที่ | เหตุการณ์ |
|---|---|
| 12 ม.ค. 2026 | Developer Portal ใหม่เปิดใช้งาน (`secopendata.sec.or.th`) |
| 30 มิ.ย. 2026 | Portal เดิม (`api-portal.sec.or.th`) **ปิดบริการ** |

> [!IMPORTANT]
> เอกสารและโค้ดในโปรเจกต์นี้ใช้ **v2 ทั้งหมด**
> ถ้าเจอตัวอย่างโค้ดเก่าบนอินเทอร์เน็ตที่ใช้ path แบบ `/FundFactsheet/...`
> นั่นคือ v1 ซึ่งเลิกใช้แล้ว

---

## ความต่างเชิงโครงสร้าง

| | v1 (เดิม) | **v2 (ปัจจุบัน)** |
|---|---|---|
| Path | `/FundFactsheet/fund/{proj_id}/policy` | `/v2/fund/general-info/profiles` |
| การระบุกอง | `proj_id` อยู่ใน **path** (บังคับ) | `proj_id` เป็น **query param** (ไม่บังคับ) |
| ดึงทั้งตลาด | ทำไม่ได้ — ต้องวนทีละกอง | **ทำได้** — ไม่ใส่ `proj_id` |
| Pagination | ไม่มี | `page_size` + `next_cursor` |
| Response | array ตรง ๆ | `{message, page_size, next_cursor, items[]}` |
| การกรองงวด | ไม่มี | `start_date` / `end_date` / `latest` |
| Auth | `Ocp-Apim-Subscription-Key` | เหมือนเดิม |
| Host | `api.sec.or.th` | เหมือนเดิม |

---

## ผลกระทบที่สำคัญที่สุด

การที่ v2 ทำให้ `proj_id` เป็น optional คือเหตุผลที่โปรเจกต์นี้เลือก
[[bulk-vs-per-fund|กลยุทธ์ bulk fetch]] ซึ่งเร็วกว่าแบบ v1 ประมาณ **24 เท่า**

```
v1 style:  GET /FundFactsheet/fund/M0001_2558/policy   × 2,300 กอง
v2 style:  GET /v2/fund/general-info/profiles?page_size=100  × 49 หน้า
```

---

## แผนที่ endpoint คร่าว ๆ

| v1 (แนวคิด) | v2 |
|---|---|
| `/FundFactsheet/fund` | `/v2/fund/general-info/profiles` |
| `/FundFactsheet/fund/{id}/policy` | `/v2/fund/general-info/profiles` (field `investment_policy_desc`) |
| `/FundFactsheet/fund/{id}/FundFee` | `/v2/fund/factsheet/fees` |
| `/FundFactsheet/fund/{id}/performance` | `/v2/fund/factsheet/performance` |
| `/FundFactsheet/fund/{id}/risk_spectrum` | `/v2/fund/factsheet/risk-spectrum` |
| `/FundDailyInfo/{id}/dailynav` | `/v2/fund/daily-info/nav` |
| `/FundFactsheet/fund/amc` | `/v2/fund/general-info/amcs` |

> [!NOTE]
> ตารางนี้เป็นการเทียบเชิงแนวคิด ชื่อ field ใน response ก็เปลี่ยนไปด้วย
> อย่าคาดหวังว่าโค้ด v1 จะย้ายมา v2 ได้โดยเปลี่ยนแค่ URL
> catalog ฉบับเต็มของ v2 อยู่ที่ [[../api-reference/00-index|API Reference]]

---

## หมายเหตุเรื่อง Portal

หน้า catalog ของ portal ใหม่มี **bot protection** — เรียกด้วย script จะได้ `403`
(ดู [[../project/issues|ISS-001]])
โปรเจกต์นี้จึงเก็บสำเนา catalog ไว้ที่ `_spec/fund.json` เพื่อให้สร้างเอกสารซ้ำได้
ตัว **API เอง ไม่ได้ถูกบล็อก** — เรียกได้ปกติด้วย subscription key
