---
title: Daily Fund NAV Information
operation_id: getFundDailyInfoNAV
endpoint: /v2/fund/daily-info/nav
dataset: nav
tags: [sec-api, fund, api-reference]
---

# มูลค่าทรัพย์สินสุทธิ (NAV) ของกองทุนรวมรายวัน

> **Daily Fund NAV Information**  
> `GET /v2/fund/daily-info/nav`  
> Operation id: `getFundDailyInfoNAV`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลมูลค่าหน่วยลงทุน (Net Asset Value: NAV) ของกองทุนรวมในรูปแบบรายวัน โดยแสดงรายละเอียดจำนวนมูลค่าทรัพย์สินสุทธิของกองทุน (Net Asset), มูลค่าหน่วยลงทุน (NAV per unit), ราคาซื้อ–ขายปกติ และราคาซื้อ–ขายสำหรับการสับเปลี่ยนหน่วยลงทุน (Switching)

> [!NOTE]
> ผู้ใช้งานสามารถค้นหาข้อมูลเฉพาะกองทุนหรือช่วงวันที่ต้องการได้ผ่านพารามิเตอร์ proj_id, nav_date_start, และ nav_date_end

<details><summary>English description</summary>

This API provides the daily Net Asset Value (NAV) information of mutual funds. The dataset includes the fund’s net asset value, NAV per unit, selling and redemption prices, as well as switching buy/sell prices.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/daily-info/nav?page_size=100
Ocp-Apim-Subscription-Key: <SEC_SUBSCRIPTION_KEY>
Accept: application/json
```

### Path parameters

_(ไม่มี)_

### Query parameters

| Parameter | Type | Required | คำอธิบาย |
|---|---|---|---|
| `next_cursor` | string | no | ค่า cursor ล่าสุดที่ได้รับจากการตอบกลับก่อนหน้า (ใช้สำหรับโหลดข้อมูลเพิ่มเติม) |
| `page_size` | integer | no | จำนวนรายการข้อมูลต่อหน้าที่ต้องการให้ระบบส่งกลับ (ค่าเริ่มต้น 100) โดยรองรับค่าตั้งแต่ 1 ถึง 100 รายการ |
| `proj_id` | string | no | ระบุ proj_id เพื่อดึงข้อมูลของกองทุน 1 กอง |
| `start_nav_date` | date | no | ระบุวันที่เริ่มต้นของ NAV ที่ต้องการดึงข้อมูล (รูปแบบ: YYYY-MM-DD) |
| `end_nav_date` | date | no | ระบุวันที่สิ้นสุดของ NAV ที่ต้องการดึงข้อมูล (รูปแบบ: YYYY-MM-DD) |
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
| `items[].proj_id` | string | เลขที่โครงการ({Type}{ID}_YYYY) |
| `items[].nav_date` | date | วันที่ NAV (YYYY-MM-DD) |
| `items[].fund_class_name` | string | ชื่อย่อชนิดหน่วยลงทุน (Class Fund) หมายเหตุ: เป็น "main" ถ้าเป็นกองทุนที่ไม่ใช่ Class Fund |
| `items[].net_asset` | number | มูลค่าทรัพย์สินสุทธิ (บาท) |
| `items[].last_val` | number | มูลค่าหน่วยลงทุน (บาท/หน่วย) |
| `items[].unique_id` | string | รหัสอ้างอิงบริษัทจัดการที่เป็นผู้ส่งข้อมูล |
| `items[].sell_price` | number | ราคาขาย (บาท/หน่วย) |
| `items[].buy_price` | number | ราคาซื้อคืน (บาท/หน่วย) |
| `items[].sell_swap_price` | number | ราคาขายสับเปลี่ยน (บาท/หน่วย) |
| `items[].buy_swap_price` | number | ราคาซื้อคืนสับเปลี่ยน (บาท/หน่วย) |
| `items[].last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "proj_id": "M0004_2559",
   "unique_id": "C0000033452",
   "fund_class_name": "-",
   "nav_date": "2023-07-13",
   "net_asset": 248999361.26,
   "last_val": 15.0833,
   "sell_price": 15.3097,
   "buy_price": 15.0833,
   "sell_swap_price": 15.0833,
   "buy_swap_price": 15.3097,
   "last_upd_date": "2024-10-31T03:34:11Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/nav.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py nav`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
