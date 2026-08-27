---
title: Data Dictionary
tags: [guide, reference, data-model]
---

# 📖 Data Dictionary — พจนานุกรมข้อมูลรวม

รวมทุก field จากทั้ง 21 endpoint (104 field ไม่ซ้ำ) พร้อมระบุว่าปรากฏใน dataset ใดบ้าง

**ที่เกี่ยวข้อง:** [[fund-identifiers|Fund Identifiers]] · [[fund-taxonomy|Fund Taxonomy]] · [[../api-reference/00-index|API Reference]]

---

## โครงสร้าง response ที่ทุก endpoint ใช้ร่วมกัน

| Field | Type | คำอธิบาย |
|---|---|---|
| `message` | string | ข้อความสถานะของการเรียก API |
| `page_size` | number | จำนวนรายการที่ส่งกลับต่อครั้ง |
| `next_cursor` | string | cursor สำหรับหน้าถัดไป (ว่าง = หมดแล้ว) |
| `items` | array&lt;object&gt; | รายการข้อมูลหลัก |

> ดู [[pagination|Pagination]] สำหรับวิธีวน cursor

---

## Field ที่มีชุดรหัสกำหนดไว้ (enum)

field เหล่านี้รับเฉพาะค่าที่กำหนด — ดูตารางเต็มที่ [[fund-taxonomy|Fund Taxonomy]]

- `entity_type` — ปรากฏใน: `involve_parties`
- `fee_type_desc` — ปรากฏใน: `fs_fees`, `mutual_fund_fees`
- `fund_status` — ปรากฏใน: `profiles`
- `invest_country_flag` — ปรากฏใน: `profiles`
- `management_style` — ปรากฏใน: `profiles`
- `proj_retail_type` — ปรากฏใน: `profiles`
- `prospectus_type` — ปรากฏใน: `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5`, `fs_urls`

---

## Field ทั้งหมด (เรียงตามตัวอักษร)

| Field | Type | ปรากฏใน dataset | คำอธิบาย |
|---|---|---|---|
| `actual_value` | float | `fs_fees` | อัตราที่จ่ายจริง |
| `address` | string | `involve_parties` | ที่อยู่ |
| `alpha` | string | `fs_statistics` | Alpha (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `amc_url_factsheet` | string | `fs_urls` | ลิงก์ไปยังเอกสาร Fund Factsheet บนเว็บไซต์ของบริษัทหลักทรัพย์จัดการกองทุน (AMC) |
| `as_of_date` | date | `fs_urls`, `out_portfolio` | วันที่อ้างอิงข้อมูลในเอกสาร Fund Factsheet (As of date) |
| `asset_name` | string | `fs_asset_alloc`, `fs_top5` | ประเภททรัพย์สินที่ลงทุน |
| `asset_ratio` | float | `fs_asset_alloc`, `fs_top5` | สัดส่วน (%NAV) ที่ลงทุนในประเภททรัพย์สินนั้น |
| `asset_seq` | number | `fs_asset_alloc`, `fs_top5` | ลำดับรายการ |
| `assetliab_code` | string | `out_port_asset_type`, `out_portfolio` | รหัสประเภทสินทรัพย์หนี้สิน |
| `assetliab_desc` | string | `out_port_asset_type`, `out_portfolio` | ประเภทสินทรัพย์หนี้สิน |
| `benchmark` | string | `fs_benchmarks` | ดัชนีชี้วัด (8.1) |
| `beta` | string | `fs_statistics` | Beta (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `book_close_date` | date | `dividend_history` | วันที่ปิดสมุดทะเบียน (YYYY-MM-DD) |
| `buy_price` | number | `nav` | ราคาซื้อคืน (บาท/หน่วย) |
| `buy_swap_price` | number | `nav` | ราคาซื้อคืนสับเปลี่ยน (บาท/หน่วย) |
| `cancel_date` | date | `profiles` | วันที่ยกเลิกกองทุนรวม |
| `class_abbr_name` | string | `dividend_history` | ชื่อกองทุน |
| `comp_name_en` | string | `amcs`, `profiles` | ชื่อบริษัทหลักทรัพย์จัดการกองทุนภาษาอังกฤษ |
| `comp_name_th` | string | `amcs`, `profiles` | ชื่อบริษัทหลักทรัพย์จัดการกองทุนภาษาไทย |
| `dividend_date` | date | `dividend_history` | วันที่จ่ายเงินปันผล (YYYY-MM-DD) |
| `dividend_policy` | string | `fs_dividend` | นโยบายการจ่ายเงินปันผล |
| `dividend_value` | number | `dividend_history` | เงินปันผลต่อหน่วย (บาท) |
| `end_date` | date | `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5` | วันที่สิ้นสุดที่ factsheet มีผล หมายเหตุ: หากเป็นข้อมูลจาก factsheet ที่มีผลล่าสุด end_date จะมีค่าเป็น null |
| `entity_name_en` | string | `involve_parties` | ชื่อบุคคล/นิติบุคคล (ภาษาอังกฤษ) |
| `entity_name_th` | string | `involve_parties` | ชื่อบุคคล/นิติบุคคล (ภาษาไทย) |
| `entity_type` | string | `involve_parties` | ประเภทบุคคล/นิติบุคคลที่เกี่ยวข้อง (ENTITY_TYPE): _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `exchange_rate_protection_policy` | string | `profiles` | นโยบายป้องกันความเสี่ยงจากอัตราแลกเปลี่ยน |
| `fee_other_desc` | string | `fs_fees`, `mutual_fund_fees` | หมายเหตุเพิ่มเติม (ถ้ามี) |
| `fee_type_desc` | string | `fs_fees`, `mutual_fund_fees` | ประเภทค่าธรรมเนียม: _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `feederfund_country` | string | `profiles` | ประเทศที่จดทะเบียนของกองทุนหลัก |
| `feederfund_master_fund` | string | `profiles` | ชื่อกองทุนหลัก (Master Fund) |
| `first_sell_end_date` | string | `fs_ipos` | วันสิ้นสุด IPO |
| `first_sell_start_date` | string | `fs_ipos` | วันเริ่ม IPO |
| `fund_class_description` | string | `profiles` | คำอธิบายชนิดหน่วยลงทุนเพิ่มเติม (ถ้ามี) |
| `fund_class_detail` | string | `profiles` | ชื่อชนิดหน่วยลงทุน |
| `fund_class_isin_code` | string | `profiles` | ISIN Code ของชนิดหน่วยลงทุน |
| `fund_class_name` | string | `fs_dividend`, `fs_fees`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_statistics`, `fs_urls`, `mutual_fund_fees`, `nav`, `profiles`, `specifications` | ชื่อย่อชนิดหน่วยลงทุน (Class Fund) หมายเหตุ: เป็น "main" ถ้าเป็นกองทุนที่ไม่ใช่ Class Fund |
| `fund_class_tax_incentive_type` | string | `profiles` | สิทธิประโยชน์ทางภาษี (SSF, Thai ESG) |
| `fund_status` | string | `profiles` | สถานะกองทุนรวม: _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `fx_hedging` | string | `fs_statistics` | FX Hedging |
| `group_seq` | string | `fs_benchmarks` | ลำดับกลุ่ม |
| `init_date` | date | `profiles` | วันที่จัดตั้งกองทุนรวม |
| `invest_country_flag` | string | `profiles` | ความเสี่ยงการลงทุนในต่างประเทศ: _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `investment_policy_desc` | string | `profiles` | นโยบายการลงทุน (ข้อมูลเป็นข้อความยาว อาจอยู่ในรูป HTML หรือ String ที่ Encode ด้วย Base64) |
| `isin_code` | string | `out_portfolio` | ISIN Code |
| `issue_code` | string | `out_portfolio` | ชื่อย่อหลักทรัพย์ |
| `issuer` | string | `out_portfolio` | ชื่อผู้ออกหลักทรัพย์ |
| `last_upd_date` | datetime | `amcs`, `dividend_history`, `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5`, `fs_urls`, `involve_parties`, `mutual_fund_fees`, `nav`, `out_portfolio`, `profiles`, `specifications` | วันที่และเวลาที่มีการแก้ไขข้อมูลล่าสุด |
| `last_val` | number | `nav` | มูลค่าหน่วยลงทุน (บาท/หน่วย) |
| `lowbal_unit` | string | `fs_min_amounts` | จำนวนหน่วยคงเหลือขั้นต่ำ |
| `lowbal_val` | float | `fs_min_amounts` | มูลค่าคงเหลือขั้นต่ำ |
| `lowbal_val_cur` | string | `fs_min_amounts` | หน่วย มูลค่าคงเหลือขั้นต่ำ |
| `management_style` | string | `profiles` | กลยุทธ์การบริหารจัดการกองทุน (Management Style): _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `market_value` | number | `out_port_asset_type`, `out_portfolio` | มูลค่าตามราคาตลาด (บาท) ปัดเศษทศนิยม 5 ตำแหน่ง |
| `maximum_drawdown` | string | `fs_statistics` | อัตราผลขาดทุนสูงสุดของกองทุนรวมในระยะเวลา 5 ปีย้อนหลัง (หรือตั้งแต่จัดตั้งกองทุนกรณีที่ยังไม่ครบ 5 ปี) (Maximum Drawdown) |
| `minimum_redempt` | float | `fs_min_amounts` | มูลค่าขั้นต่ำของการสั่งขายคืน (9.5.6) |
| `minimum_redempt_cur` | string | `fs_min_amounts` | หน่วย (มูลค่าขั้นต่ำของการสั่งขายคืน) (9.5.6) |
| `minimum_redempt_unit` | string | `fs_min_amounts` | จำนวนหน่วยลงทุนขั้นต่ำของการสั่งขายคืน (9.5.6) |
| `minimum_sub` | float | `fs_min_amounts` | มูลค่าขั้นต่ำของการสั่งซื้อครั้งถัดไป (9.5.4) |
| `minimum_sub_cur` | string | `fs_min_amounts` | หน่วย มูลค่าขั้นต่ำของการสั่งซื้อครั้งถัดไป (9.5.4) |
| `minimum_sub_ipo` | float | `fs_min_amounts` | มูลค่าขั้นต่ำของการสั่งซื้อครั้งแรก (9.5.3) |
| `minimum_sub_ipo_cur` | string | `fs_min_amounts` | หน่วย มูลค่าขั้นต่ำของการสั่งซื้อครั้งแรก (9.5.3) |
| `minimum_sub_unit` | string | `fs_min_amounts` | จำนวนหน่วยลงทุนขั้นต่ำของการสั่งซื้อครั้งถัดไป (9.5.4) |
| `nav_date` | date | `nav` | วันที่ NAV (YYYY-MM-DD) |
| `net_asset` | number | `nav` | มูลค่าทรัพย์สินสุทธิ (บาท) |
| `pdf_factsheet` | string | `fs_urls` | ลิงก์ไฟล์ PDF ของ Fund Factsheet ที่จัดเก็บโดย ก.ล.ต. |
| `percent_nav` | number | `out_port_asset_type`, `out_portfolio` | %NAV ปัดเศษทศนิยม 5 ตำแหน่ง (เนื่องจากการปัดเศษ อาจทำให้สัดส่วนรวมเกิน 100% ได้ถึง 100.20% ของ NAV) |
| `performance_type_desc` | string | `fs_performance` | คำอธิบายประเภทผลตอบแทน |
| `performance_value` | string | `fs_performance` | ผลการดำเนินงานย้อนหลังของกองทุน (8.3) |
| `period` | string | `fs_periods`, `out_port_asset_type`, `out_portfolio` | ระยะเวลาขายและรับซื้อคืน |
| `policy_desc` | string | `profiles` | ประเภทกองทุนตามนโยบายกองทุน |
| `portfolio_duration_period` | string | `fs_statistics` | อายุเฉลี่ยของกองทุนตราสารหนี้ (Portfolio Duration) |
| `portfolio_turnover_ratio` | string | `fs_statistics` | อัตราส่วนหมุนเวียนการลงทุน (Portfolio Turn Over Ratio) |
| `proj_abbr_name` | string | `profiles` | ชื่อย่อโครงการจัดการกองทุนรวม |
| `proj_id` | string | `dividend_history`, `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5`, `fs_urls`, `involve_parties`, `mutual_fund_fees`, `nav`, `out_port_asset_type`, `out_portfolio`, `profiles`, `specifications` | เลขที่โครงการกองทุนรวม ({Type}{ID}_YYYY) เช่น M0000_2552 |
| `proj_name_en` | string | `profiles` | ชื่อโครงการจัดการกองทุนรวม (อังกฤษ) |
| `proj_name_th` | string | `profiles` | ชื่อโครงการจัดการกองทุนรวม (ไทย) |
| `proj_retail_type` | string | `profiles` | ลักษณะโครงการ: _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `proj_term_day` | string | `profiles` | อายุโครงการ (วัน) |
| `proj_term_flag` | string | `profiles` | อายุโครงการ (Y = กำหนด N = ไม่กำหนด) |
| `proj_term_month` | string | `profiles` | อายุโครงการ (เดือน) |
| `proj_term_year` | string | `profiles` | อายุโครงการ (ปี) |
| `prospectus_type` | string | `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5`, `fs_urls` | ประเภทการส่ง factsheet ของบลจ.: _(ดู [[fund-taxonomy\|Taxonomy]])_ |
| `rate` | string | `fs_fees`, `mutual_fund_fees` | อัตราตามโครงการ |
| `rate_unit` | string | `mutual_fund_fees` | หน่วยของอัตราตามโครงการ |
| `recovering_period` | string | `fs_statistics` | ระยะเวลาที่ฟื้นตัว (Recovering Period) |
| `redemp_period_oth` | string | `fs_periods` | คำอธิบายการขายและรับซื้อคืน (กรณีที่ period มีค่าเป็น อื่น ๆ) |
| `reference_period` | string | `fs_performance` | หมุดเวลาและปีย้อนหลัง |
| `regis_date` | date | `profiles` | วันที่จดทะเบียนกองทุนรวม |
| `regis_id` | string | `profiles` | เลขที่จดทะเบียนกองทุน |
| `remark` | string | `fs_benchmarks` | หมายเหตุ (ถ้ามี) |
| `risk_spectrum` | string | `fs_risk` | ระดับความเสี่ยงของกองทุนรวม (RS1–RS8 และ RS81) |
| `risk_spectrum_desc` | string | `fs_risk` | รายละเอียดความเสี่ยงของกองทุนรวม |
| `sell_price` | number | `nav` | ราคาขาย (บาท/หน่วย) |
| `sell_swap_price` | number | `nav` | ราคาขายสับเปลี่ยน (บาท/หน่วย) |
| `settlement_period` | string | `fs_periods` | ระยะเวลาการรับเงินค่าขายคืน |
| `sharpe_ratio` | string | `fs_statistics` | Sharpe Ratio (หมายเหตุ : เฉพาะกองตราสารทุน) |
| `spec_code` | string | `specifications` | รหัสลักษณะพิเศษ |
| `spec_desc` | string | `specifications` | ประเภทกองทุนตามลักษณะพิเศษ (นิยามตามประกาศ สน.87/2558 ภาคผนวก 2) |
| `start_date` | date | `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5` | วันที่เริ่มต้นที่ factsheet มีผล |
| `tracking_error` | string | `fs_statistics` | Tracking Error |
| `type` | string | `fs_periods` | ประเภทขายและรับซื้อคืน ได้แก่ subscription และ redemption |
| `unique_id` | string | `amcs`, `dividend_history`, `nav`, `profiles` | รหัสอ้างอิงบริษัทจัดการที่เป็นผู้ส่งข้อมูล |
| `yield_to_maturity` | string | `fs_statistics` | Yield to Maturity |

---

## Field ที่ปรากฏในหลาย dataset (คีย์สำหรับ join)

| Field | จำนวน dataset |
|---|---|
| `last_upd_date` | 20 |
| `proj_id` | 20 |
| `prospectus_type` | 12 |
| `fund_class_name` | 11 |
| `start_date` | 11 |
| `end_date` | 11 |
| `unique_id` | 4 |
| `period` | 3 |
| `comp_name_th` | 2 |
| `comp_name_en` | 2 |
| `fee_type_desc` | 2 |
| `rate` | 2 |
| `fee_other_desc` | 2 |
| `as_of_date` | 2 |
| `asset_seq` | 2 |

> วิธี join ที่ถูกต้องอยู่ที่ [[fund-identifiers|Fund Identifiers]]
