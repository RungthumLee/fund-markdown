---
title: Rate limits & Error handling
tags: [guide, sec-api, errors, reliability]
---

# ⚠️ Rate limits & Error handling

**ที่เกี่ยวข้อง:** [[authentication|Authentication]] · [[pagination|Pagination]] · [[../project/issues|Issues]]

---

## HTTP status ที่พบ

| Status | ความหมาย | วิธีจัดการใน `SECClient` |
|---|---|---|
| `200` | สำเร็จ | คืน JSON |
| `204` | ไม่มีข้อมูล | คืน `{"items": [], "next_cursor": ""}` — ไม่ถือเป็น error |
| `400` | parameter ผิดรูปแบบ | raise ทันที (แก้โค้ด ไม่ใช่ retry) |
| `401` / `403` | key ผิด / หมดสิทธิ์ / ยังไม่ subscribe | สลับไป secondary key แล้วลองใหม่ |
| `404` | ไม่พบ resource | คืน empty result — ไม่ raise |
| `429` | ยิงถี่เกินไป | exponential backoff แล้ว retry |
| `5xx` | ฝั่ง SEC ล่ม/ timeout | exponential backoff แล้ว retry |

## Retry policy ที่ใช้

```
max_retries = 5
delay       = 1s -> 2s -> 4s -> 8s -> 16s  (cap ที่ 60s)
rate_delay  = 0.12s หน่วงระหว่างทุก request
timeout     = 60s
```

ครอบคลุมทั้ง `requests.RequestException` (network/timeout) และ `json.JSONDecodeError`
(กรณี SEC คืน HTML error page แทน JSON)

## Rate limit ที่สังเกตได้

SEC ไม่ประกาศตัวเลข quota อย่างเป็นทางการใน portal
จากการทดสอบจริงในโปรเจกต์นี้:

- ยิงต่อเนื่องด้วยหน่วง `0.12s` (~8 req/s) **ไม่เจอ 429** ตลอดการ harvest
- ยังไม่พบ header `X-RateLimit-*` ในการตอบกลับ
- แนะนำให้คงหน่วงไว้ที่ 0.1–0.2s เพื่อความปลอดภัย

> [!NOTE]
> ถ้าเจอ 429 บ่อย ให้เพิ่ม `rate_delay` ตอนสร้าง client:
> `SECClient(rate_delay=0.5)`

## หลักการ resilience ของ pipeline

1. **Checkpoint ต่อ dataset** — ไฟล์ `.done` ทำให้รันซ้ำแล้วข้ามของที่เสร็จ
2. **Streaming write** — เขียน JSONL ทีละบรรทัด งานที่ทำไปแล้วไม่หาย
3. **ไม่ล้มทั้งงานเพราะ dataset เดียว** — `harvest.py` จับ exception ต่อ dataset
   บันทึกลง `_harvest_summary.json` แล้วไปต่อ
4. **Log ทุกอย่าง** — `logs/*.log` เก็บทั้ง console และไฟล์

## ปัญหาที่เจอจริง

ดูบันทึกทั้งหมดที่ [[../project/issues|Issues log]]
