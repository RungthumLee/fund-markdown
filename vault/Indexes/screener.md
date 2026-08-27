---
title: เครื่องมือคัดกรองกองทุน
tags: [index, screener]
---

# 🔎 เครื่องมือคัดกรองกองทุน (Dataview)

[[00-home|🏠 Home]] · [[compare-fees|เทียบค่าธรรมเนียม]] · [[all-funds|ทั้งหมด]]

> [!INFO] ตารางในหน้านี้ทำงานเมื่อเปิดใน **Obsidian ที่ติดตั้งปลั๊กอิน [Dataview](https://github.com/blacksmithgu/obsidian-dataview)** เท่านั้น
> ทุกโน้ตกองทุนมี field พร้อมกรอง: `ter_retail` (ค่าธรรมเนียมรวมของชนิดที่รายย่อยซื้อได้), `perf_1y`, `risk_spectrum`, `nav`, `fund_size`, `top10_pct_nav`, `policy`, `amc`

> [!WARNING] `ter_retail` และ `perf_1y` เป็นข้อมูลย้อนหลัง — ค่าธรรมเนียมต่ำ/ผลตอบแทนสูงในอดีต **ไม่รับประกันอนาคต** และควรเทียบภายในหมวดเดียวกัน

> แก้เงื่อนไขเองได้: เปลี่ยน `policy`, ปรับ `LIMIT`, หรือ `SORT ... DESC/ASC`

### ค่าธรรมเนียมรวมต่ำสุด — กองหุ้นไทย

เฉพาะชนิดที่ผู้ลงทุนรายย่อยซื้อได้จริง

```dataview
TABLE ter_retail AS "TER %", perf_1y AS "1y %", risk_spectrum AS "เสี่ยง", amc AS "บลจ."
FROM #fund
WHERE policy = "ตราสารทุน" AND ter_retail
SORT ter_retail ASC
LIMIT 25
```

### ผลตอบแทน 1 ปีสูงสุด (ทุกหมวด)

เรียงตามผลตอบแทนของกองเอง ไม่ใช่ตัวชี้วัด

```dataview
TABLE perf_1y AS "1y %", ter_retail AS "TER %", policy AS "นโยบาย", risk_spectrum AS "เสี่ยง"
FROM #fund
WHERE perf_1y
SORT perf_1y DESC
LIMIT 25
```

### ความเสี่ยงต่ำ (ระดับ ≤ 3)

กองความเสี่ยงต่ำ เรียงจากค่าธรรมเนียมถูกสุด

```dataview
TABLE risk_spectrum AS "เสี่ยง", ter_retail AS "TER %", policy AS "นโยบาย", amc AS "บลจ."
FROM #fund
WHERE risk_spectrum <= 3
SORT risk_spectrum ASC, ter_retail ASC
LIMIT 30
```

### กองขนาดใหญ่สุด

ขนาดกอง (มูลค่าทรัพย์สินสุทธิล่าสุด) หน่วยบาท

```dataview
TABLE fund_size AS "ขนาด (บาท)", ter_retail AS "TER %", policy AS "นโยบาย"
FROM #fund
WHERE fund_size
SORT fund_size DESC
LIMIT 25
```

### พอร์ตกระจุกตัวสูงสุด

น้ำหนัก 10 อันดับแรกต่อ NAV — ยิ่งสูงยิ่งกระจุก

```dataview
TABLE top10_pct_nav AS "Top10 %NAV", holdings_count AS "จำนวนที่ถือ", policy AS "นโยบาย"
FROM #fund
WHERE top10_pct_nav
SORT top10_pct_nav DESC
LIMIT 25
```

### นับกองทุนแยกตามนโยบาย

ภาพรวมว่ามีกี่กองในแต่ละหมวด

```dataview
TABLE length(rows) AS "จำนวนกอง", round(average(rows.ter_retail), 3) AS "TER เฉลี่ย %"
FROM #fund
GROUP BY policy AS "นโยบาย"
SORT length(rows) DESC
```
