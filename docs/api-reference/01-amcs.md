---
title: Asset Management Company : AMC
operation_id: getAmcList
endpoint: /v2/fund/general-info/amcs
dataset: amcs
tags: [sec-api, fund, api-reference]
---

# รายชื่อบริษัทจัดการกองทุนรวม (บลจ.)

> **Asset Management Company : AMC**  
> `GET /v2/fund/general-info/amcs`  
> Operation id: `getAmcList`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลรายชื่อบริษัทจัดการกองทุนรวม (บลจ.) ที่อยู่ภายใต้การกำกับดูแลของสำนักงานก.ล.ต.

> [!NOTE]
> สามารถนำรหัสบริษัทหลักทรัพย์จัดการกองทุน (unique_id) ไปใช้ร่วมกับ Fund API ข้ออื่น เช่น ข้อ 02. กองทุนรวมภายใต้การบริหารจัดการของบลจ.และลักษณะทั่วไปของแต่ละกองทุน เพื่อค้นหากองทุนที่บลจ.นั้น ๆ บริหารดูแล

<details><summary>English description</summary>

This API provides a list of Asset Management Companies (AMCs) under supervision of the SEC Thailand.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/general-info/amcs?page_size=100
Ocp-Apim-Subscription-Key: <SEC_SUBSCRIPTION_KEY>
Accept: application/json
```

### Path parameters

_(ไม่มี)_

### Query parameters

| Parameter | Type | Required | คำอธิบาย |
|---|---|---|---|
| `next_cursor` | string | no | ค่า cursor ล่าสุดที่ได้รับจาก response ก่อนหน้า (ใช้สำหรับโหลดข้อมูลเพิ่มเติม) |
| `page_size` | integer | no | จำนวนรายการข้อมูลต่อหน้าที่ต้องการให้ระบบส่งกลับ (ค่าเริ่มต้น 100) โดยรองรับค่าตั้งแต่ 1 ถึง 100 รายการ |

## Response

- Status: `200`
- Content-Type: `application/json`

### Data dictionary

| Field | Type | คำอธิบาย |
|---|---|---|
| `message` | string | ข้อความสถานะของการเรียก API |
| `page_size` | number | จำนวนรายการที่ส่งกลับต่อครั้ง |
| `next_cursor` | string | ค่า cursor ที่ได้รับจาก Response ล่าสุด (กรณีที่ค่า next_cursor = "" หมายถึงระบบส่งข้อมูลให้ครบทั้งหมดแล้ว ไม่มีหน้าถัดไป) |
| `items` | array<object> | รายการข้อมูลหลักที่ส่งกลับมา |
| `items[].unique_id` | string | รหัสบริษัทหลักทรัพย์จัดการกองทุน |
| `items[].comp_name_th` | string | ชื่อบริษัทหลักทรัพย์จัดการกองทุนภาษาไทย |
| `items[].comp_name_en` | string | ชื่อบริษัทหลักทรัพย์จัดการกองทุนภาษาอังกฤษ |
| `items[].last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "unique_id": "C0000000021",
   "comp_name_en": "KASIKORN ASSET MANAGEMENT COMPANY LIMITED",
   "comp_name_th": "บริษัทหลักทรัพย์จัดการกองทุน กสิกรไทย จำกัด",
   "last_upd_date": "2025-11-19T07:13:01Z"
  },
  {
   "unique_id": "C0000000023",
   "comp_name_en": "MFC ASSET MANAGEMENT PUBLIC COMPANY LIMITED ",
   "comp_name_th": "บริษัทหลักทรัพย์จัดการกองทุน เอ็มเอฟซี จำกัด (มหาชน)",
   "last_upd_date": "2025-11-19T07:13:01Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/amcs.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py amcs`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
