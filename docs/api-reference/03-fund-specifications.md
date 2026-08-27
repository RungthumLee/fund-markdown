---
title: Fund Specification
operation_id: getFundSpecification
endpoint: /v2/fund/general-info/specifications
dataset: specifications
tags: [sec-api, fund, api-reference]
---

# ประเภทกองทุนรวมตามลักษณะพิเศษ

> **Fund Specification**  
> `GET /v2/fund/general-info/specifications`  
> Operation id: `getFundSpecification`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลประเภทกองทุนรวมตามลักษณะพิเศษ (Fund Specification) ซึ่งนิยามตามประกาศสำนักงาน ก.ล.ต. สน.87/2558 ภาคผนวก 2 ในระดับชนิดหน่วยลงทุน (Class Fund)

<details><summary>English description</summary>

This API provides special characteristics of each mutual funds (Fund Specifications), as defined in SEC Notification Nor. 87/2568 Appendix 2 at the Class Fund level.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/general-info/specifications?page_size=100
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
| `proj_id` | string | no | เลขที่โครงการ ({Type}{ID}_YYYY) |
| `fund_class_name` | string | no | ชื่อชนิดหน่วยลงทุน |

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
| `items[].proj_id` | string | เลขที่โครงการ ({Type}{ID}_YYYY) |
| `items[].fund_class_name` | string | ชื่อย่อชนิดหน่วยลงทุน (Class Fund) หมายเหตุ: เป็น "main" ถ้าเป็นกองทุนที่ไม่ใช่ Class Fund |
| `items[].spec_code` | string | รหัสลักษณะพิเศษ |
| `items[].spec_desc` | string | ประเภทกองทุนตามลักษณะพิเศษ (นิยามตามประกาศ สน.87/2558 ภาคผนวก 2) |
| `items[].last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "proj_id": "M0000_2552",
   "fund_class_name": "HIDIV-AR",
   "spec_code": "CIV",
   "spec_desc": "กองทุนรวมที่มีนโยบายเปิดให้มีการลงทุนในกองทุนรวมอื่นภายใต้ บลจ. เดียวกัน (CROSS Investing Fund)",
   "last_upd_date": "2025-11-19T07:23:12Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/specifications.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py specifications`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
