---
title: Monthly Fund Portfolio by Asset Type
operation_id: get-outstanding-portassettype
endpoint: /v2/fund/outstanding/portfolio-asset-type
dataset: out_port_asset_type
tags: [sec-api, fund, api-reference]
---

# สัดส่วนการลงทุนของกองทุนรวมตามประเภทสินทรัพย์ ณ วันทำการสุดท้ายของเดือน

> **Monthly Fund Portfolio by Asset Type**  
> `GET /v2/fund/outstanding/portfolio-asset-type`  
> Operation id: `get-outstanding-portassettype`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลสัดส่วนการลงทุนของกองทุนรวม ณ วันทำการสุดท้ายของเดือน โดยจำแนกตามกลุ่มสินทรัพย์และหนี้สินของกองทุน (เช่น กลุ่มเงินฝากธนาคาร กลุ่มหุ้น กลุ่มหน่วยลงทุน เป็นต้น) และแสดงมูลค่าตลาด (บาท) และสัดส่วนการลงทุนต่อมูลค่าสินทรัพย์สุทธิของกองทุน (%NAV)

> [!NOTE]
> ข้อมูลเป็นข้อมูลรายเดือนย้อนหลัง 3 ปี โดยงวดข้อมูลล่าสุดจะมีระยะเวลาในการเปิดเผย (lag time) 45 วันภายหลังวันทำการสุดท้ายของเดือน ผู้ใช้งานสามารถดึงข้อมูลงวดที่ต้องการได้ผ่านพารามิเตอร์ period_start และ period_end โดยข้อมูลแต่ละแถวจะระบุงวดข้อมูล (period ในรูปแบบ YYYYMM) กำกับเพื่อระบุช่วงเวลาที่ข้อมูลนั้นมีผล

<details><summary>English description</summary>

This API provides fund portfolio by asset type as of the last business day of each month. The dataset presents asset and liability groups held by the fund, including market values and the proportion of each group as a percentage of the fund’s Net Asset Value (%NAV).

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/outstanding/portfolio-asset-type?page_size=100
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
| `start_period` | string | no | ระบุงวดข้อมูลแรกที่ต้องการดึงข้อมูล (รูปแบบ: YYYYMM) หมายเหตุ: หากต้องการดึงข้อมูลงวดเดียว ให้ระบุ period_start และ period_end เป็นงวดเดียวกัน |
| `end_period` | string | no | ระบุงวดข้อมูลสุดท้ายที่ต้องการดึงข้อมูล (รูปแบบ: YYYYMM) หมายเหตุ: หากต้องการดึงข้อมูลงวดเดียว ให้ระบุ period_start และ period_end เป็นงวดเดียวกัน |

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
| `items[].assetliab_code` | string | รหัสประเภทการลงทุน |
| `items[].assetliab_desc` | string | ประเภทการลงทุน |
| `items[].market_value` | number | มูลค่าตลาด |
| `items[].percent_nav` | number | สัดส่วนต่อมูลค่าสินทรัพย์สุทธิ |

### ตัวอย่าง response

```json
{
 "message": "success",
 "page_size": 100,
 "next_cursor": "xxxx-xxx-xxx",
 "items": [
  {
   "proj_id": "M0000_2552",
   "period": "201101",
   "assetliab_code": "101",
   "assetliab_desc": "หุ้น (รหัส 101-102)",
   "market_value": 1296947797.6,
   "percent_nav": 91.18823
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/out_port_asset_type.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py out_port_asset_type`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
