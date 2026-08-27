---
title: Fund Factsheet URL and PDF File
operation_id: getFactsheetUrl
endpoint: /v2/fund/factsheet/urls
dataset: fs_urls
tags: [sec-api, fund, api-reference]
---

# URL และ ไฟล์ pdf ของ Fund Fact Sheet

> **Fund Factsheet URL and PDF File**  
> `GET /v2/fund/factsheet/urls`  
> Operation id: `getFactsheetUrl`

[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Errors]]

## คำอธิบาย

ข้อมูลลิงก์ดาวน์โหลดไฟล์ PDF ของ Fund Fact Sheet (pdf_factsheet) รวมไปถึง URL สำหรับเข้าถึง Factsheet จากเว็บไซต์ของบลจ. (amc_url_factsheet) ซึ่งเป็นไฟล์ PDF และลิงก์ที่บลจ.จัดส่งให้สำนักงานโดยตรงในระดับชนิดหน่วยลงทุน (Class Fund) สำหรับกองทุนที่มีหลายชนิดหน่วยลงทุน (Class Fund) บลจ.จะจัดส่งไฟล์ PDF เพียงไฟล์เดียวให้สำนักงาน โดยภายในไฟล์ดังกล่าวได้รวบรวมข้อมูลของทุกชนิดหน่วยลงทุนไว้ ซึ่งสำนักงาน ก.ล.ต.นำไฟล์ PDF นี้มาให้บริการต่อผ่าน API โดยไม่มีการแยกไฟล์หรือปรับแก้ไขเนื้อหาเพิ่มเติม

> [!NOTE]
> ข้อมูลในชุดนี้เป็นข้อมูลตามช่วงเวลา โดยแต่ละแถวจะแสดงข้อมูล Fund Factsheet ณ วันที่ใดวันที่หนึ่ง (as_of_date) ซึ่งกองทุนหรือชนิดหน่วยลงทุนหนึ่งรายการอาจมีหลายงวดข้อมูลย้อนหลัง

<details><summary>English description</summary>

This API provides download links for Fund Fact Sheet PDF files (pdf_factsheet) and includes URLs to the fact sheets published on the AMCs' official websites (amc_url_factsheet), which are submitted by Asset Management Companies (AMCs) to the SEC Thailand. For funds with multiple share classes (Class Funds), the AMC was required to submit a single PDF file that consolidates the fund factsheet information for all share classes into one document, which the SEC provides through the API without any modification.

</details>

## Request

```http
GET https://api.sec.or.th/v2/fund/factsheet/urls?page_size=100
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
| `items[].proj_id` | string | เลขที่โครงการกองทุนรวม ({Type}{ID}_YYYY) เช่น M0000_2552 |
| `items[].fund_class_name` | string | ชื่อย่อชนิดหน่วยลงทุน (Class Fund) หมายเหตุ: เป็น "main" ถ้าเป็นกองทุนที่ไม่ใช่ Class Fund |
| `items[].prospectus_type` | string | รูปแบบหรือความถี่ของเอกสารชี้ชวน / factsheet ที่จัดทำ เช่น Monthly (รายเดือน) |
| `items[].amc_url_factsheet` | string | ลิงก์ไปยังเอกสาร Fund Factsheet บนเว็บไซต์ของบริษัทหลักทรัพย์จัดการกองทุน (AMC) |
| `items[].pdf_factsheet` | string | ลิงก์ไฟล์ PDF ของ Fund Factsheet ที่จัดเก็บโดย ก.ล.ต. |
| `items[].as_of_date` | date | วันที่อ้างอิงข้อมูลในเอกสาร Fund Factsheet (As of date) |
| `items[].last_upd_date` | datetime | วันที่และเวลาที่มีการแก้ไขข้อมูลล่าสุด |

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
   "prospectus_type": "Monthly",
   "amc_url_factsheet": "https://documents.mfcfund.com/Website/FundFiles/Q&A/QA_HIDIV-AR.pdf",
   "pdf_factsheet": "https://secdocumentstorage.blob.core.windows.net/fundfactsheet/M0000_2552.pdf",
   "as_of_date": "2025-09-30",
   "last_upd_date": "2025-10-31T03:32:17Z"
  }
 ]
}
```

## การใช้งานในโปรเจกต์นี้

- Dataset: `data/raw/fs_urls.jsonl`
- ดึงข้อมูล: `python scripts/harvest.py fs_urls`
- Client: `scripts/sec_client.py` → `SECClient.paginate()`
- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]
