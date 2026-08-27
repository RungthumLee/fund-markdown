---
title: Fund Dividend History
operation_id: getFundDailyInfoDividendHistory
endpoint: /v2/fund/daily-info/dividend-history
dataset: dividend_history
tags: [sec-api, fund, api-reference]
---

# ประวัติการจ่ายเงินปันผลของกองทุนรวม

> **Fund Dividend History**  
> `GET /v2/fund/daily-info/dividend-history`  
> Operation id: `getFundDailyInfoDividendHistory`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลประวัติการจ่ายเงินปันผลของกองทุนรวม โดยแสดงข้อมูลวันที่ปิดสมุดทะเบียน (Book Close Date), วันที่จ่ายเงินปันผล (Dividend Date) และจำนวนเงินปันผลต่อหน่วย (Dividend Value)

> [!NOTE]
> ผลลัพธ์มีเฉพาะข้อมูลที่มีวันที่ปิดสมุดทะเบียน และวันที่จ่ายเงินปันผลครบถ้วนเท่านั้น

<details><summary>English description</summary>

This API provides the dividend news history of mutual funds, including the book close date, dividend payment date, and dividend value per unit.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/daily-info/dividend-history?page_size=100
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
| `items[].unique_id` | string | รหัสอ้างอิงบริษัทจัดการที่เป็นผู้ส่งข้อมูล |
| `items[].proj_id` | string | เลขที่โครงการ({Type}{ID}_YYYY) |
| `items[].class_abbr_name` | string | ชื่อกองทุน |
| `items[].book_close_date` | date | วันที่ปิดสมุดทะเบียน (YYYY-MM-DD) |
| `items[].dividend_date` | date | วันที่จ่ายเงินปันผล (YYYY-MM-DD) |
| `items[].dividend_value` | number | เงินปันผลต่อหน่วย (บาท) |
| `items[].last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "proj_id": "M2530_0002",
   "unique_id": "C0000000023",
   "class_abbr_name": "-",
   "book_close_date": "2005-01-14T12:00:00Z",
   "dividend_date": "2005-01-26T12:00:00Z",
   "dividend_value": 2.43,
   "last_upd_date": "2018-07-04T04:07:54Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/dividend_history.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py dividend_history`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
