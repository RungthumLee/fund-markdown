---
title: Pagination
tags: [guide, sec-api, pagination]
---

# 📄 Pagination (cursor-based)

**ที่เกี่ยวข้อง:** [[quickstart|Quickstart]] · [[bulk-vs-per-fund|Bulk vs Per-fund]] · [[../api-reference/00-index|API Reference]]

---

## หลักการ

SEC API v2 ใช้ **cursor-based pagination** ไม่ใช่ offset/page number

| Parameter | ชนิด | ค่า |
|---|---|---|
| `page_size` | integer | 1–100 (default 100) |
| `next_cursor` | string | ค่า opaque (base64) จาก response ก่อนหน้า |

Response ทุกชุดคืน:

```json
{ "message": "success", "page_size": 100, "next_cursor": "...", "items": [ ... ] }
```

**เงื่อนไขจบ:** `next_cursor` เป็น `""` (empty string) → ไม่มีหน้าถัดไปแล้ว

> [!WARNING]
> อย่าเช็คแค่ `len(items) < page_size` เพื่อตัดสินว่าจบ — บางหน้าอาจคืนน้อยกว่า
> `page_size` แต่ยังมีหน้าถัดไป ให้ยึด `next_cursor` เป็นหลักเสมอ

## ตัวอย่าง loop

```python
def paginate(path, params):
    params = dict(params); params["page_size"] = 100
    cursor = None
    while True:
        if cursor:
            params["next_cursor"] = cursor
        data = client.get(path, params)
        yield from data.get("items") or []
        cursor = data.get("next_cursor") or ""
        if not cursor:
            return
```

ดู implementation จริงที่ `scripts/sec_client.py` → `SECClient.paginate()`

## ประสิทธิภาพที่วัดได้จริง

| | ค่าที่วัดได้ |
|---|---|
| เวลาต่อ 1 request (page_size=100) | ~1.1–1.3 วินาที |
| throughput | ~80 rows/วินาที |
| 4,892 rows (profiles) | 49 calls, 62 วินาที |
| 13,465 rows (specifications) | 135 calls, 55 วินาที |

**ประมาณการ:** dataset ขนาด 100,000 แถว ≈ 1,000 calls ≈ 20 นาที

## เคล็ดลับ

- ใช้ `page_size=100` เสมอ — ไม่มีเหตุผลให้ใช้น้อยกว่านี้ในงาน bulk
- cursor เป็น **opaque** อย่าพยายาม decode หรือสร้างเอง
- cursor ผูกกับ query params ชุดเดิม — ถ้าเปลี่ยน filter ต้องเริ่ม cursor ใหม่
- เขียนผลลง **JSONL แบบ streaming** ไม่ต้องเก็บทั้งหมดใน memory
