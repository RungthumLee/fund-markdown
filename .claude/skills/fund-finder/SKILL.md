---
name: fund-finder
description: หากองทุนไทยที่ตรงโจทย์ภาษาคนจากคลัง Fund-knowledge โดยแปลงเป็น faceted tag แล้วกรอง — ใช้เมื่อผู้ใช้ถาม "มีกองไหนที่... / หากองสำหรับ... / อยากได้กอง...". Finds Thai funds matching a natural-language need via the faceted tags.
---

# fund-finder

แปลงโจทย์ภาษาคน → faceted tag → รายชื่อกองที่ตรง พร้อมเหตุผล

## แปลงโจทย์เป็น tag (ตัวอย่าง)
| โจทย์ | tag |
|---|---|
| พักเงินสั้น เสี่ยงต่ำ ถอนไว | `#use/park-cash` (+ `#risk/very-low` `#liquidity/t1`) |
| ลดหย่อนภาษี | `#use/tax-saving` (`#tax/rmf` `#tax/ssf` `#tax/thai-esg`) |
| กองปันผล | `#use/income` |
| หุ้นเทค / การเงิน / พลังงาน | `#sector/technology` `#sector/financials` `#sector/energy` |
| หุ้นใหญ่ระดับโลก | `#cap/large` |
| ตราสารหนี้ระยะสั้น / high-yield | `#duration/short` `#credit/high-yield` |
| ไม่เสี่ยงค่าเงิน (ในประเทศ) | ดู frontmatter `market_countries`/`country_top` = ไทย |

## วิธีค้น
1. ดูรายการ tag ทั้งหมด: `vault/Indexes/tags.md` · ดัชนี: `by-country.md` `by-sector.md` `compare-fees.md`
2. กรองจาก frontmatter ในโน้ต `vault/Funds/*.md` (fields: `ter_retail` `perf_1y` `risk_spectrum` `nav` `fund_size` `country_top` `tags`)
   หรือ grep tag แล้วอ่าน frontmatter · เรียงตาม `ter_retail`/`perf_1y`
3. คืน 5–15 กอง: ชื่อย่อ · TER · ผลตอบแทน 1 ปี (อดีต) · ประเทศ/หมวด · เหตุผลที่ตรงโจทย์

## กรอบ (docs/project/ideas.md §0)
- คัดกรองตามคุณสมบัติที่ประกาศไว้ **ไม่ใช่การแนะนำให้ซื้อ**
- "เสี่ยงต่ำ" ≠ "ไม่มีความเสี่ยง" · ผลตอบแทน = อดีต ไม่รับประกันอนาคต
- ค่าธรรมเนียมต่ำ/ผลตอบแทนสูงในอดีต ไม่ได้แปลว่าดีกว่าเสมอ — ให้ผู้ใช้ตัดสินเอง
