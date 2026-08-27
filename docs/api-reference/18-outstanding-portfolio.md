---
title: Quarterly Fund Portfolio
operation_id: get-outstanding-port
endpoint: /v2/fund/outstanding/portfolio
dataset: out_portfolio
tags: [sec-api, fund, api-reference]
---

# การลงทุนของกองทุนรวม ณ วันทำการสุดท้ายแต่ละไตรมาส

> **Quarterly Fund Portfolio**  
> `GET /v2/fund/outstanding/portfolio`  
> Operation id: `get-outstanding-port`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลการลงทุนของกองทุนรวม ณ วันทำการสุดท้ายของไตรมาส (Fund Portfolio) โดยแสดงข้อมูลรายละเอียดสินทรัพย์และหนี้สินที่กองทุนถือครองในแต่ละไตรมาส ได้แก่ ประเภททรัพย์สิน ชื่อหลักทรัพย์ ผู้ออกหลักทรัพย์ มูลค่าตลาด และสัดส่วนการลงทุนคิดเป็นร้อยละของมูลค่าสินทรัพย์สุทธิของกองทุน (%NAV)

> [!NOTE]
> ข้อมูลเป็นข้อมูลรายไตรมาสย้อนหลัง 3 ปี โดยงวดข้อมูลล่าสุดมีระยะเวลาในการนำมาเปิดเผย (lag time) 45 วัน หลังวันทำการสุดท้ายของไตรมาสนั้น ๆ ผู้ใช้งานสามารถดึงข้อมูลงวดที่ต้องการได้ผ่านพารามิเตอร์ period_start และ period_end โดยข้อมูลแต่ละแถวจะระบุงวดข้อมูล (period ในรูปแบบ YYYYMM) และวันที่อ้างอิง (as_of_date) กำกับเพื่อระบุช่วงเวลาที่ข้อมูลนั้นมีผล

<details><summary>English description</summary>

This API provides fund portfolio as of the last business day of each quarter. The dataset presents the assets and liabilities held by the fund in each quarter, including asset categories, security names, issuers, market values, and the proportion of each holding as a percentage of the fund’s Net Asset Value (%NAV).

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/outstanding/portfolio?page_size=100
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
| `start_period` | date | no | ระบุงวดข้อมูลแรกที่ต้องการดึงข้อมูล (รูปแบบ: YYYYMM) หมายเหตุ: หากต้องการดึงข้อมูลงวดเดียว ให้ระบุ period_start และ period_end เป็นงวดเดียวกัน |
| `end_period` | date | no | ระบุงวดข้อมูลสุดท้ายที่ต้องการดึงข้อมูล (รูปแบบ: YYYYMM) หมายเหตุ: หากต้องการดึงข้อมูลงวดเดียว ให้ระบุ period_start และ period_end เป็นงวดเดียวกัน |

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
| `items[].period` | string | งวดข้อมูล (YYYYMM) |
| `items[].as_of_date` | date | ข้อมูล ณ วันที่ (YYYY-MM-DD) |
| `items[].assetliab_code` | string | รหัสประเภทสินทรัพย์หนี้สิน |
| `items[].assetliab_desc` | string | ประเภทสินทรัพย์หนี้สิน |
| `items[].issue_code` | string | ชื่อย่อหลักทรัพย์ |
| `items[].isin_code` | string | ISIN Code |
| `items[].issuer` | string | ชื่อผู้ออกหลักทรัพย์ |
| `items[].market_value` | number | มูลค่าตามราคาตลาด (บาท) ปัดเศษทศนิยม 5 ตำแหน่ง |
| `items[].percent_nav` | number | %NAV ปัดเศษทศนิยม 5 ตำแหน่ง (เนื่องจากการปัดเศษ อาจทำให้สัดส่วนรวมเกิน 100% ได้ถึง 100.20% ของ NAV) |
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
   "period": "202212",
   "as_of_date": "2022-12-30",
   "assetliab_id": "101",
   "assetliab_desc": "หุ้นสามัญ",
   "issue_code": "ADVANC",
   "isin_code": "TH0268010Z03",
   "issuer": "ADVANCED INFO SERVICE PUBLIC COMPANY LIMITED",
   "assetliab_value": 105670500,
   "percent_nav": 2.80362,
   "last_upd_date": "2023-02-21T05:00:25Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/out_portfolio.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py out_portfolio`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
