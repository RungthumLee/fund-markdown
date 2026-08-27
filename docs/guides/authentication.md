---
title: Authentication
tags: [guide, sec-api, auth]
---

# 🔑 Authentication

**ที่เกี่ยวข้อง:** [[quickstart|Quickstart]] · [[rate-limits-and-errors|Errors]] · [[../project/security-notes|Security Notes]]

---

## รูปแบบ

SEC Open API ใช้ **Azure API Management (APIM)** subscription key ส่งผ่าน HTTP header:

```http
Ocp-Apim-Subscription-Key: <32-hex-characters>
```

- ไม่ใช่ OAuth / Bearer token — ไม่มี expiry ในตัว
- ส่งเป็น header เท่านั้น (ไม่รองรับ query string ในเวอร์ชัน v2)
- 1 subscription มี **2 keys** (primary + secondary) เพื่อให้หมุนเวียนคีย์ได้โดยไม่ downtime

## Key ในโปรเจกต์นี้

| ตัวแปรใน `.env.local` | บทบาท |
|---|---|
| `SEC_SUBSCRIPTION_KEY` | primary — ใช้เป็นค่าเริ่มต้น |
| `SEC_secondary_key` | secondary — `SECClient` จะสลับมาใช้อัตโนมัติเมื่อเจอ 401/403 |

`scripts/sec_client.py` อ่านไฟล์เอง ไม่ต้องพึ่ง `python-dotenv`:

```python
ENV = load_env()                       # parse .env.local
PRIMARY_KEY   = ENV.get("SEC_SUBSCRIPTION_KEY", "")
SECONDARY_KEY = ENV.get("SEC_secondary_key", "")
```

## การ failover

```
GET -> 401/403  ->  _rotate_key()  ->  ยิงซ้ำด้วย secondary
                     ยังไม่ผ่าน     ->  raise RuntimeError("Auth failed")
```

## ข้อควรระวัง

> [!WARNING]
> - **ห้าม** hardcode key ลงในสคริปต์หรือ notebook
> - **ห้าม** commit `.env.local` — ใส่ใน `.gitignore` เสมอ
> - **ห้าม** ใส่ key ลงใน markdown ที่ generate ออกมา (ทุกสคริปต์ในโปรเจกต์นี้ไม่เขียน key ลงไฟล์ output)
> - เอกสารและ log ในโปรเจกต์นี้ mask key ทั้งหมด

## Portal migration

| | |
|---|---|
| Portal เดิม | `https://api-portal.sec.or.th` — ปิดบริการ **30 มิ.ย. 2026** |
| Portal ใหม่ | `https://secopendata.sec.or.th/sec-open-apis` — เปิดใช้ **12 ม.ค. 2026** |
| API host | `https://api.sec.or.th` (เหมือนเดิม) |

API v1 เดิม (`/FundFactsheet/...`) ถูกแทนที่ด้วย v2 (`/v2/fund/...`)
ดู [[api-v1-vs-v2|เทียบ v1 กับ v2]]
