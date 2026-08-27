---
title: Mutual Fund Fee and Total Fee
operation_id: getMutualfundFee
endpoint: /v2/fund/general-info/mutual-fund-fees
dataset: mutual_fund_fees
tags: [sec-api, fund, api-reference]
---

# ค่าธรรมเนียมที่เรียกเก็บจากกองทุนรวม และค่าธรรมเนียมทั้งหมด

> **Mutual Fund Fee and Total Fee**  
> `GET /v2/fund/general-info/mutual-fund-fees`  
> Operation id: `getMutualfundFee`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลรายละเอียดค่าธรรมเนียมที่เรียกเก็บจากกองทุนรวมในระดับชนิดหน่วยลงทุน (Class Fund) แยกตามประเภทค่าธรรมเนียม เช่น ค่าธรรมเนียมการจัดการ (Management Fee), ค่าธรรมเนียมผู้ดูแลผลประโยชน์ (Trustee Fee), ค่าธรรมเนียมนายทะเบียนหน่วยลงทุน (Registrar Fee) รวมถึงค่าธรรมเนียมทั้งหมด (Total Fee) ตามที่ระบุไว้ในโครงการของกองทุน

<details><summary>English description</summary>

This API provides detailed information on mutual fund fees at the share class level (Class Fund), broken down by fee type such as management fee, trustee fee, registrar fee, distributor fee, and total fees as specified in the fund project documentation.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/general-info/mutual-fund-fees?page_size=100
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
| `items[].fee_type_desc` | string | ประเภทค่าธรรมเนียม ได้แก่ Distributor Fee, Investment Advisor Fee, Management Fee, Other Fee, Registrar Fee, Total Fee และ Trustee Fee |
| `items[].rate` | string | อัตราตามโครงการ |
| `items[].rate_unit` | string | หน่วยของอัตราตามโครงการ |
| `items[].fee_other_desc` | string | หมายเหตุเพิ่มเติม (ถ้ามี) |
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
   "fee_type_desc": "ค่าธรรมเนียมการจัดการ (Management Fee)",
   "rate": 2.14,
   "rate_unit": "ต่อปี ของมูลค่าทรัพย์สินสุทธิของกองทุนรวม",
   "fee_other_desc": "(1) ค่าธรรมเนียมการจัดตั้งกองทุน ในอัตราไม่เกินร้อยละ 1.07 ต่อปีของมูลค่าทรัพย์สินสุทธิของกองทุน ณ วันจดทะเบียนกองทรัพย์สิน...",
   "last_upd_date": "2025-11-19T07:13:41Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/mutual_fund_fees.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py mutual_fund_fees`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
