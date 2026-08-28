---
title: แท็กทั้งหมด
tags: [index, tags]
---

# 🏷️ แท็กกองทุน (faceted)

[[00-home|🏠 Home]] · [[screener|🔎 Screener]] · [[all-funds|ทั้งหมด]]

> [!INFO] แต่ละกองติดแท็กหลายมิติแบบ deterministic (อ่านจากข้อมูล ก.ล.ต.)
> **คลิกแท็ก** เพื่อดูทุกกองที่ติดแท็กนั้น หรือใช้ Dataview ด้านล่าง
> อยากได้กลุ่มตามธีม/ภูมิภาค (จีน · เทคโนโลยี · สุขภาพ) ดูที่ [[by-peer-group|กลุ่ม AIMC]] ซึ่งเป็นการจัดกลุ่มจริงจาก factsheet

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

- #use/accumulate · **1195**
- #use/tax-saving · **664**
- #use/income · **308**
- #use/park-cash · **48**

## ความเสี่ยง (ภาษาคน) · `risk`

_แปลระดับ 1–8 เป็นคำที่เข้าใจง่าย_

- #risk/high · **1168**
- #risk/moderate · **537**
- #risk/very-high · **326**
- #risk/low · **39**
- #risk/very-low · **32**

## กลุ่มอุตสาหกรรม · `sector`

_กลุ่มหลักในพอร์ต (จากการจัดสรร sector ใน factsheet)_

- #sector/financials · **155**
- #sector/technology · **135**
- #sector/energy · **90**
- #sector/industrials · **20**
- #sector/consumer · **18**
- #sector/healthcare · **16**
- #sector/real-estate · **12**
- #sector/utilities · **5**

## อายุเฉลี่ยตราสารหนี้ · `duration`

_สั้น <1.5ปี / กลาง 1.5–5 / ยาว >5 (จาก duration)_

- #duration/short · **118**
- #duration/medium · **75**
- #duration/long · **30**

## คุณภาพเครดิต · `credit`

_investment-grade / high-yield / พันธบัตรรัฐ (จาก factsheet)_

- #credit/investment-grade · **147**
- #credit/government · **42**
- #credit/high-yield · **13**

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
