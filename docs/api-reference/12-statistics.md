---
title: Fund Statistics
operation_id: getFactsheetStatisticsinfo
endpoint: /v2/fund/factsheet/statistics
dataset: fs_statistics
tags: [sec-api, fund, api-reference]
---

# ข้อมูลเชิงสถิติของกองทุนรวม

> **Fund Statistics**  
> `GET /v2/fund/factsheet/statistics`  
> Operation id: `getFactsheetStatisticsinfo`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลสถิติสำคัญของกองทุนรวม (Fund Statistics) ในแต่ละชนิดหน่วยลงทุน (Class Fund) ตามที่บลจ.รายงานใน Fund Fact Sheet แต่ละงวดรายงาน เช่น อัตราหมุนเวียนพอร์ต (Portfolio Turnover Ratio), Maximum Drawdown, Sharpe Ratio, Beta, Alpha, Yield to Maturity เป็นต้น

> [!NOTE]
> ข้อมูลในชุดนี้เป็นข้อมูลตามช่วงเวลาที่ Fund Fact Sheet นั้น ๆ มีผล โดยแต่ละแถวจะแสดงข้อมูลตามวันที่ Fund Factsheet นั้นเริ่มมีผล (start_date) และวันที่สิ้นสุดผล (end_date) ซึ่งกองทุนหรือชนิดหน่วยลงทุนหนึ่งรายการอาจมีหลายงวดข้อมูลย้อนหลัง

<details><summary>English description</summary>

This API provides key fund statistics as reported for each fund and share class in the Fund Factsheet by Asset Management Companies (AMCs), such as Portfolio Turnover Ratio, Maximum Drawdown, Sharpe Ratio, Beta, Alpha, Yield to Maturity, etc.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/factsheet/statistics?page_size=100
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
| `start_date` | date | no | ระบุวันที่เริ่มต้นที่ factsheet มีผล (รูปแบบ: YYYY-MM-DD) ระบบจะคืนข้อมูลที่มี start_date มากกว่าหรือเท่ากับค่าที่ระบุ |
| `end_date` | date | no | ระบุวันที่สิ้นสุดที่ factsheet มีผล (รูปแบบ: YYYY-MM-DD) ระบบจะคืนข้อมูลที่มี end_date น้อยกว่าหรือเท่ากับค่าที่ระบุ |
| `latest` | boolean | no | หากต้องการเฉพาะข้อมูลจาก factsheet ที่มีผลล่าสุดเท่านั้น ให้ระบุค่า latest เป็น true และระบบจะไม่พิจารณา start_date และ end_date หากมีการส่งค่าเข้ามา |
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
| `items[].fund_class_name` | string | ชื่อย่อชนิดหน่วยลงทุน (Class Fund) หมายเหตุ: เป็น "main" ถ้าเป็นกองทุนที่ไม่ใช่ Class Fund |
| `items[].start_date` | date | วันที่เริ่มต้นที่ factsheet มีผล |
| `items[].end_date` | date | วันที่สิ้นสุดที่ factsheet มีผล หมายเหตุ: หากเป็นข้อมูลจาก factsheet ที่มีผลล่าสุด end_date จะมีค่าเป็น null |
| `items[].prospectus_type` | string | ประเภทการส่ง factsheet ของบลจ.:<br>IPO = ส่งเมื่อยื่นขอจัดตั้งกองทุน<br>Monthly = ส่งรายเดือน<br>SignificantFactsheet = ส่งเมื่อมีการเปลี่ยนแปลงข้อมูลอย่างมีนัยสำคัญ |
| `items[].portfolio_turnover_ratio` | string | อัตราส่วนหมุนเวียนการลงทุน (Portfolio Turn Over Ratio) |
| `items[].recovering_period` | string | ระยะเวลาที่ฟื้นตัว (Recovering Period) |
| `items[].portfolio_duration_period` | string | อายุเฉลี่ยของกองทุนตราสารหนี้ (Portfolio Duration) |
| `items[].maximum_drawdown` | string | อัตราผลขาดทุนสูงสุดของกองทุนรวมในระยะเวลา 5 ปีย้อนหลัง (หรือตั้งแต่จัดตั้งกองทุนกรณีที่ยังไม่ครบ 5 ปี) (Maximum Drawdown) |
| `items[].sharpe_ratio` | string | Sharpe Ratio (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `items[].beta` | string | Beta (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `items[].alpha` | string | Alpha (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `items[].fx_hedging` | string | FX Hedging |
| `items[].tracking_error` | string | Tracking Error |
| `items[].yield_to_maturity` | string | Yield to Maturity |
| `items[].last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "proj_id": "M0027_2541",
   "fund_class_name": "ABCC",
   "start_date": "2023-07-31",
   "end_date": "2023-08-30",
   "prospectus_type": "Monthly",
   "portfolio_turnover_ratio": "24.63",
   "recovering_period": "1 เดือน",
   "portfolio_duration_period": "1 เดือน 13 วัน",
   "maximum_drawdown": "-0.02",
   "sharpe_ratio": "0",
   "beta": "0",
   "alpha": "0",
   "fx_hedging": "0",
   "tracking_error": "0",
   "yield_to_maturity": "2026-01-05",
   "last_upd_date": "2023-08-28T11:15:36Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/fs_statistics.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py fs_statistics`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
