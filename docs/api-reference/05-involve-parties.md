---
title: Fund Involve Party
operation_id: getFundRelative
endpoint: /v2/fund/general-info/involve-parties
dataset: involve_parties
tags: [sec-api, fund, api-reference]
---

# ผู้เกี่ยวข้องกับกองทุนรวม

> **Fund Involve Party**  
> `GET /v2/fund/general-info/involve-parties`  
> Operation id: `getFundRelative`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลบุคคลหรือนิติบุคคลที่เกี่ยวข้องกับกองทุนรวม ตามบทบาทหน้าที่ที่กำหนดไว้ในโครงการกองทุน เช่น ผู้ดูแลผลประโยชน์ นายทะเบียน ผู้แทนจำหน่าย ผู้สร้างสภาพคล่อง ที่ปรึกษาการลงทุน และหน่วยงานอื่นที่เกี่ยวข้อง

<details><summary>English description</summary>

This API provides information on entities related to mutual funds based on the roles defined in the fund project, such as Trustee, Registrar, Distributor, Market Maker, Participating Dealer, Investment Advisor, and other involved parties.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/general-info/involve-parties?page_size=100
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
| `entity_type` | string | no | ค้นหาประเภทบุคคล/นิติบุคคลที่เกี่ยวข้อง |

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
| `items[].entity_type` | string | ประเภทบุคคล/นิติบุคคลที่เกี่ยวข้อง (ENTITY_TYPE):<br>A = ผู้สอบบัญชี<br>U = ผู้จัดจำหน่าย<br>S = ผู้สนับสนุนการขายและรับซื้อคืน<br>R = นายทะเบียนหน่วยลงทุน<br>V = ผู้ดูแลผลประโยชน์<br>M = ที่ปรึกษาการลงทุน<br>O = ผู้รับมอบหมายงานด้านการจัดการลงทุน<br>P = ผู้ลงทุนรายใหญ่<br>K = ผู้ดูแลสภาพคล่อง<br>N = ที่ปรึกษาทางการเงิน<br>F = ผู้จัดการกองทุน |
| `items[].entity_name_th` | string | ชื่อบุคคล/นิติบุคคล (ภาษาไทย) |
| `items[].entity_name_en` | string | ชื่อบุคคล/นิติบุคคล (ภาษาอังกฤษ) |
| `items[].address` | string | ที่อยู่ |
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
   "entity_type": "R",
   "entity_name_en": "MFC ASSET MANAGEMENT PUBLIC COMPANY LIMITED ",
   "entity_name_th": "บริษัทหลักทรัพย์จัดการกองทุน เอ็มเอฟซี จำกัด (มหาชน)",
   "address": "เลขที่ 199 อาคารคอลัมน์ทาวเวอร์ ชั้น จี,ชั้น 21-23 ถนนรัชดาภิเษก ประเทศไทย 10110",
   "last_upd_date": "2025-11-19T07:22:16Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/involve_parties.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py involve_parties`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
