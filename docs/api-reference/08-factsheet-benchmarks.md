---
title: Fund Benchmark
operation_id: getFactsheetBenchmark
endpoint: /v2/fund/factsheet/benchmarks
dataset: fs_benchmarks
tags: [sec-api, fund, api-reference]
---

# ดัชนีชี้วัดกองทุนรวม

> **Fund Benchmark**  
> `GET /v2/fund/factsheet/benchmarks`  
> Operation id: `getFactsheetBenchmark`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลดัชนีชี้วัดของกองทุนรวมตามที่บลจ.นำส่งข้อมูลใน Fund Fact Sheet แต่ละงวดรายงาน

> [!NOTE]
> ข้อมูลในชุดนี้เป็นข้อมูลตามช่วงเวลาที่ Fund Fact Sheet นั้น ๆ มีผล โดยแต่ละแถวจะแสดงข้อมูลตามวันที่ Fund Factsheet นั้นเริ่มมีผล (start_date) และวันที่สิ้นสุดผล (end_date) ซึ่งกองทุนหรือชนิดหน่วยลงทุนหนึ่งรายการอาจมีหลายงวดข้อมูลย้อนหลัง

<details><summary>English description</summary>

This API provides information on the fund benchmark, based on the Fund Fact Sheet reported by Asset Management Companies (AMCs).

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/factsheet/benchmarks?page_size=100
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
| `proj_id` | date | no | ระบุ proj_id เพื่อดึงข้อมูลของกองทุน 1 กอง |
| `start_date` | date | no | ระบุวันที่เริ่มต้นที่ factsheet มีผล (รูปแบบ: YYYY-MM-DD) ระบบจะคืนข้อมูลที่มี start_date มากกว่าหรือเท่ากับค่าที่ระบุ |
| `end_date` | string | no | ระบุวันที่สิ้นสุดที่ factsheet มีผล (รูปแบบ: YYYY-MM-DD) ระบบจะคืนข้อมูลที่มี end_date น้อยกว่าหรือเท่ากับค่าที่ระบุ |
| `latest` | boolean | no | หากต้องการเฉพาะข้อมูลจาก factsheet ที่มีผลล่าสุดเท่านั้น ให้ระบุค่า latest เป็น true และระบบจะไม่พิจารณา start_date และ end_date หากมีการส่งค่าเข้ามา |

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
| `items[].start_date` | date | วันที่เริ่มต้นที่ factsheet มีผล |
| `items[].end_date` | date | วันที่สิ้นสุดที่ factsheet มีผล หมายเหตุ: หากเป็นข้อมูลจาก factsheet ที่มีผลล่าสุด end_date จะมีค่าเป็น null |
| `items[].prospectus_type` | string | ประเภทการส่ง factsheet ของบลจ.:<br>IPO = ส่งเมื่อยื่นขอจัดตั้งกองทุน<br>Monthly = ส่งรายเดือน<br>SignificantFactsheet = ส่งเมื่อมีการเปลี่ยนแปลงข้อมูลอย่างมีนัยสำคัญ |
| `items[].group_seq` | string | ลำดับกลุ่ม |
| `items[].benchmark` | string | ดัชนีชี้วัด (8.1) |
| `items[].remark` | string | หมายเหตุ (ถ้ามี) |
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
   "start_date": "2022-06-30",
   "end_date": "2022-07-26",
   "prospectus_type": "Monthly",
   "group_seq": 1,
   "benchmark": "ดัชนีผลตอบแทนรวมตลาดหลักทรัพย์แห่งประเทศไทย (SET TRI)",
   "benchmark_remark": "",
   "last_upd_date": "2022-07-26T07:53:25Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/fs_benchmarks.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py fs_benchmarks`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
