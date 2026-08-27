---
title: SEC Fund API Reference
tags: [sec-api, index]
---

# 📚 SEC Open API — Fund (v2) Reference

คู่มืออ้างอิง API ทั้ง **21 endpoints** ของกลุ่ม `fund` จาก SEC Open Data Developer Portal

| | |
|---|---|
| Base URL | `https://api.sec.or.th` |
| Auth header | `Ocp-Apim-Subscription-Key` |
| Pagination | `page_size` (1–100) + `next_cursor` |
| Portal | https://secopendata.sec.or.th/sec-open-apis |

**อ่านก่อนเริ่ม →** [[../guides/quickstart|Quickstart]] · [[../guides/authentication|Authentication]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Rate limits & Errors]]

## General Info

| # | Endpoint | Method | Path | Dataset |
|---|---|---|---|---|
| 01 | [[01-amcs\|รายชื่อบริษัทจัดการกองทุนรวม (บลจ.)]] | `GET` | `/v2/fund/general-info/amcs` | `amcs` |
| 02 | [[02-fund-profiles\|กองทุนรวมภายใต้การบริหารจัดการของบลจ.และลักษณะทั่วไปของแต่ละกองทุน]] | `GET` | `/v2/fund/general-info/profiles` | `profiles` |
| 03 | [[03-fund-specifications\|ประเภทกองทุนรวมตามลักษณะพิเศษ]] | `GET` | `/v2/fund/general-info/specifications` | `specifications` |
| 04 | [[04-mutual-fund-fees\|ค่าธรรมเนียมที่เรียกเก็บจากกองทุนรวม และค่าธรรมเนียมทั้งหมด]] | `GET` | `/v2/fund/general-info/mutual-fund-fees` | `mutual_fund_fees` |
| 05 | [[05-involve-parties\|ผู้เกี่ยวข้องกับกองทุนรวม]] | `GET` | `/v2/fund/general-info/involve-parties` | `involve_parties` |

## Factsheet

| # | Endpoint | Method | Path | Dataset |
|---|---|---|---|---|
| 06 | [[06-factsheet-urls\|URL และ ไฟล์ pdf ของ Fund Fact Sheet]] | `GET` | `/v2/fund/factsheet/urls` | `fs_urls` |
| 07 | [[07-factsheet-ipos\|การเสนอขายกองทุนรวม]] | `GET` | `/v2/fund/factsheet/ipos` | `fs_ipos` |
| 08 | [[08-factsheet-benchmarks\|ดัชนีชี้วัดกองทุนรวม]] | `GET` | `/v2/fund/factsheet/benchmarks` | `fs_benchmarks` |
| 09 | [[09-subscription-redemption-minimums\|มูลค่าและจำนวนหน่วยลงทุนขั้นต่ำในการสั่งซื้อ สั่งขายคืน หรือคงเหลือของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/subscription-redemption-minimums` | `fs_min_amounts` |
| 10 | [[10-subscription-redemption-periods\|ระยะเวลาขายและรับซื้อคืนของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/subscription-redemption-periods` | `fs_periods` |
| 11 | [[11-risk-spectrum\|ระดับความเสี่ยงของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/risk-spectrum` | `fs_risk` |
| 12 | [[12-statistics\|ข้อมูลเชิงสถิติของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/statistics` | `fs_statistics` |
| 13 | [[13-dividend-policy\|นโยบายการจ่ายเงินปันผลของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/dividend-policy` | `fs_dividend` |
| 14 | [[14-factsheet-fees\|ค่าธรรมเนียมของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/fees` | `fs_fees` |
| 15 | [[15-performance\|ผลการดำเนินงานย้อนหลังของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/performance` | `fs_performance` |
| 16 | [[16-asset-allocation\|สัดส่วนประเภททรัพย์สินที่ลงทุนของกองทุนรวม]] | `GET` | `/v2/fund/factsheet/asset-allocation` | `fs_asset_alloc` |
| 17 | [[17-top5-holdings\|ทรัพย์สินที่ลงทุน 5 อันดับแรก]] | `GET` | `/v2/fund/factsheet/top5-holdings` | `fs_top5` |

## Outstanding

| # | Endpoint | Method | Path | Dataset |
|---|---|---|---|---|
| 18 | [[18-outstanding-portfolio\|การลงทุนของกองทุนรวม ณ วันทำการสุดท้ายแต่ละไตรมาส]] | `GET` | `/v2/fund/outstanding/portfolio` | `out_portfolio` |
| 19 | [[19-outstanding-portfolio-asset-type\|สัดส่วนการลงทุนของกองทุนรวมตามประเภทสินทรัพย์ ณ วันทำการสุดท้ายของเดือน]] | `GET` | `/v2/fund/outstanding/portfolio-asset-type` | `out_port_asset_type` |

## Daily Info

| # | Endpoint | Method | Path | Dataset |
|---|---|---|---|---|
| 20 | [[20-daily-nav\|มูลค่าทรัพย์สินสุทธิ (NAV) ของกองทุนรวมรายวัน]] | `GET` | `/v2/fund/daily-info/nav` | `nav` |
| 21 | [[21-dividend-history\|ประวัติการจ่ายเงินปันผลของกองทุนรวม]] | `GET` | `/v2/fund/daily-info/dividend-history` | `dividend_history` |
