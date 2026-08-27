---
title: แท็กทั้งหมด
tags: [index, tags]
---

# 🏷️ แท็กกองทุน (faceted)

[[00-home|🏠 Home]] · [[screener|🔎 Screener]] · [[all-funds|ทั้งหมด]]

> [!INFO] แต่ละกองติดแท็กหลายมิติแบบ deterministic (อ่านจากข้อมูล ก.ล.ต.)
> **คลิกแท็ก** เพื่อดูทุกกองที่ติดแท็กนั้น หรือใช้ Dataview ด้านล่าง
> ธีม/ภูมิภาคอ่านจากชื่อกอง จึงเป็น best-effort (LLM จะช่วยขัดในเฟสถัดไป)

## สินทรัพย์ · `asset`

_ประเภทสินทรัพย์หลักที่กองลงทุน_

- #asset/equity · **1235**
- #asset/mixed · **450**
- #asset/fixed-income · **303**
- #asset/alternative · **95**
- #asset/fixed-income/short-term · **69**
- #asset/fixed-income/money-market · **51**
- #asset/real-estate · **41**
- #asset/commodity/gold · **40**
- #asset/other · **38**
- #asset/commodity/oil · **9**

## การใช้งาน · `use`

_กองนี้เหมาะกับโจทย์แบบไหน_

- #use/accumulate · **913**
- #use/tax-saving · **664**
- #use/thematic · **476**
- #use/income · **308**
- #use/park-cash · **48**

## ความเสี่ยง (ภาษาคน) · `risk`

_แปลระดับ 1–8 เป็นคำที่เข้าใจง่าย_

- #risk/high · **1168**
- #risk/moderate · **537**
- #risk/very-high · **326**
- #risk/low · **39**
- #risk/very-low · **32**

## ภูมิภาค · `geo`

_พื้นที่ลงทุนหลัก (อ่านจากชื่อกอง)_

- #geo/thailand · **520**
- #geo/world · **432**
- #geo/china · **113**
- #geo/us · **111**
- #geo/asia-pacific · **54**
- #geo/japan · **44**
- #geo/europe · **35**
- #geo/vietnam · **35**
- #geo/india · **28**
- #geo/emerging-markets · **20**
- #geo/korea · **6**
- #geo/taiwan · **2**

## ธีม/หมวด · `theme`

_ธีมการลงทุน (อ่านจากชื่อกอง — ยังเป็น best-effort)_

- #theme/sustainability · **114**
- #theme/technology · **89**
- #theme/real-estate · **57**
- #theme/technology/ai-robotics · **49**
- #theme/metals-mining/gold · **46**
- #theme/healthcare · **42**
- #theme/energy · **25**
- #theme/infrastructure · **21**
- #theme/technology/semiconductor · **18**
- #theme/financials · **11**
- #theme/consumer · **5**

## กลยุทธ์บริหาร · `style`

_active / passive / ปันผล ฯลฯ_

- #style/active · **1366**
- #style/passive · **346**
- #style/dividend · **308**
- #style/enhanced-index · **77**
- #style/buy-hold · **13**
- #style/inverse · **2**
- #style/leveraged · **1**

## โครงสร้าง · `struct`

_ลงตรง / feeder_

- #struct/direct · **1122**
- #struct/feeder · **999**

## การกระจุกตัว · `conc`

_จำนวนหลักทรัพย์ที่ถือ (เฉพาะกองหุ้น)_

- #conc/concentrated · **425**
- #conc/focused · **310**
- #conc/ultra-concentrated · **124**
- #conc/ultra-concentrated/ten-stock · **67**
- #conc/total-market · **43**

## การป้องกันค่าเงิน · `fx`

_hedge เต็ม/บางส่วน/ไม่ hedge/ตามดุลยพินิจ_

- #fx/partially-hedged · **549**
- #fx/fully-hedged · **510**
- #fx/discretionary · **472**
- #fx/unhedged · **70**

## สภาพคล่อง · `liquidity`

_ได้เงินคืนกี่วันทำการหลังขาย_

- #liquidity/t5 · **527**
- #liquidity/t4 · **491**
- #liquidity/t3 · **438**
- #liquidity/t2 · **410**
- #liquidity/t1 · **106**
- #liquidity/t6 · **60**
- #liquidity/t7 · **3**
- #liquidity/t8 · **1**

## สิทธิภาษี · `tax`

_RMF / SSF / Thai ESG_

- #tax/rmf · **341**
- #tax/ssf · **299**
- #tax/thai-esg · **24**

## ข้อกำหนดพิเศษ · `compliance`

_ESG / ชารีอะห์ / trigger_

- #compliance/sri-fund · **24**
- #compliance/trigger-fund · **17**
- #compliance/sharia · **7**

---

## 🔎 คำถามยอดฮิต (Dataview)

> ต้องเปิดใน Obsidian ที่ติดตั้งปลั๊กอิน Dataview

### พักเงินระยะสั้น เสี่ยงต่ำ ถอนไว

กองตลาดเงิน/ตราสารหนี้สั้น เรียงตามผลตอบแทน 1 ปี

```dataview
TABLE ter_retail AS "TER %", perf_1y AS "1y %", risk_spectrum AS "เสี่ยง"
FROM #use/park-cash
WHERE perf_1y
SORT perf_1y DESC
LIMIT 20
```

### หุ้นจีน + เทคโนโลยี

กองที่ติดทั้งภูมิภาคจีนและธีมเทคโนโลยี

```dataview
TABLE perf_1y AS "1y %", ter_retail AS "TER %", nav AS "NAV", amc AS "บลจ."
FROM #geo/china AND #theme/technology
SORT perf_1y DESC
```

### กองปันผล เสี่ยงปานกลาง

กองที่จ่ายปันผล ความเสี่ยงไม่สูงเกินไป

```dataview
TABLE perf_1y AS "1y %", ter_retail AS "TER %", policy AS "นโยบาย"
FROM #use/income
WHERE risk_spectrum <= 5
SORT perf_1y DESC
LIMIT 20
```

### ลดหย่อนภาษี (RMF/SSF/ThaiESG) ค่าธรรมเนียมต่ำ

กองประหยัดภาษี เรียงจากค่าธรรมเนียมถูกสุด

```dataview
TABLE ter_retail AS "TER %", perf_1y AS "1y %", policy AS "นโยบาย"
FROM #use/tax-saving
WHERE ter_retail
SORT ter_retail ASC
LIMIT 25
```
