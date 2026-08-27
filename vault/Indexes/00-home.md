---
title: Home
tags: [moc, home]
---

# 🏠 คลังความรู้กองทุนรวมไทย

ฐานความรู้กองทุนรวมไทย สร้างจาก SEC Open Data API v2

## 📇 สารบัญ

| ดัชนี | คำอธิบาย |
|---|---|
| [[all-funds]] | รายชื่อกองทุนทั้งหมด |
| [[by-amc]] | แยกตาม บลจ. |
| [[by-policy]] | แยกตามนโยบายการลงทุน |
| [[by-risk]] | แยกตามระดับความเสี่ยง |
| [[by-management-style]] | แยกตามกลยุทธ์การบริหาร |
| [[by-tax-incentive]] | แยกตามสิทธิประโยชน์ภาษี |
| [[by-peer-group]] | แยกตามกลุ่ม AIMC (จาก factsheet) |
| [[master-funds]] | กองทุนหลักต่างประเทศ (Yahoo + FT) |
| [[by-holding]] | เริ่มจากสินทรัพย์ ดูว่ากองไหนถือ |
| [[by-lookthrough]] | ทะลุกองทุนหลักไปถึงหุ้นจริง |
| [[changelog]] | สิ่งที่เปลี่ยนในแต่ละรอบการรัน |
| [[compare-fees]] | เทียบค่าธรรมเนียมในหมวดเดียวกัน |
| [[screener]] | 🔎 คัดกรอง/เรียงกองด้วย Dataview (interactive) |
| [[../Factsheets/00-factsheets-index\|Factsheets]] | ข้อความจาก PDF |

## 📚 แนวคิดพื้นฐาน

- [[ค่าธรรมเนียมกองทุนรวม]]
- [[ระดับความเสี่ยงกองทุนรวม]]
- [[NAV และราคาซื้อขายหน่วยลงทุน]]
- [[Feeder Fund]]
- [[ค่าธรรมเนียมสองชั้นของ Feeder Fund]]
- [[การรวมชื่อสินทรัพย์]]
- [[Look-through การถือทางอ้อม]]
- [[กลยุทธ์การบริหารกองทุน]]
- [[สถิติวัดผลกองทุน]]
- [[สิทธิประโยชน์ทางภาษีของกองทุนรวม]]
- [[ชนิดหน่วยลงทุน Share Class]]

## 📊 ตัวเลขในคลังนี้

| รายการ | จำนวน |
|---|---|
| กองทุนในขอบเขต | 2,121 |
| ชนิดหน่วยลงทุน (class) | 4,663 |
| บลจ. | 22 |
| กองที่ถูกคัดออก | 222 |

### ความครบถ้วนของข้อมูล

| ชุดข้อมูล | มีข้อมูล | คิดเป็น |
|---|---|---|
| `investment_policy` | 2,121 | 100% |
| `project_fees` | 2,121 | 100% |
| `involve_parties` | 2,121 | 100% |
| `dividend_policy` | 2,120 | 100% |
| `nav` | 2,120 | 100% |
| `factsheet_urls` | 2,120 | 100% |
| `min_amounts` | 2,120 | 100% |
| `factsheet_fees` | 2,111 | 100% |
| `risk_spectrum` | 2,102 | 99% |
| `portfolio` | 2,075 | 98% |
| `statistics` | 2,069 | 98% |
| `asset_allocation` | 2,069 | 98% |
| `portfolio_asset_type` | 2,062 | 97% |
| `dealing_periods` | 2,042 | 96% |
| `performance` | 2,021 | 95% |
| `benchmarks` | 1,880 | 89% |
| `top5_holdings` | 1,875 | 88% |
| `dividend_history` | 296 | 14% |

## 🔎 ค้นหาแบบ interactive (ต้องติดตั้งปลั๊กอิน Dataview)

ทุกโน้ตกองทุนมี frontmatter ครบ จึง query ได้ทันที
คัดลอกโค้ดด้านล่างไปวางในโน้ตใหม่แล้วปรับเงื่อนไขตามต้องการ

**กองหุ้นความเสี่ยงสูง เรียงตาม บลจ.**

````
```dataview
TABLE amc AS "บลจ.", risk_spectrum AS "เสี่ยง", management_style AS "กลยุทธ์"
FROM #fund
WHERE policy = "ตราสารทุน" AND risk_spectrum >= "6"
SORT amc ASC
```
````

**กอง SSF ทั้งหมด**

````
```dataview
LIST
FROM #fund AND #tax/ssf
SORT file.name ASC
```
````

**กอง passive ที่ลงทุนต่างประเทศ**

````
```dataview
TABLE amc, policy
FROM #fund AND #passive AND #foreign-exposure
SORT amc ASC
```
````

**นับจำนวนกองต่อ บลจ.**

````
```dataview
TABLE length(rows) AS "จำนวนกอง"
FROM #fund
GROUP BY amc
SORT length(rows) DESC
```
````

> [!NOTE]
> field ที่ query ได้: `proj_id` `abbr` `amc` `policy` `risk_spectrum`
> `management_style` `retail_type` `invest_country_flag` `class_count`
> `init_date` `has_factsheet`
> tag ที่ใช้ได้: `#fund` `#active` `#passive` `#feeder` `#leveraged-inverse` `#foreign-exposure` `#restricted-investor`
> `#tax/ssf` `#tax/thai-esg` `#tax/rmf` `#policy/*` `#risk/*`

## 🛠️ เอกสารโปรเจกต์

- [API Reference (21 endpoints)](../../docs/api-reference/00-index.md)
- [Quickstart](../../docs/guides/quickstart.md)
- [Fund Taxonomy](../../docs/guides/fund-taxonomy.md)
- [Task board](../../docs/project/tasks.md)
- [Issue log](../../docs/project/issues.md)
