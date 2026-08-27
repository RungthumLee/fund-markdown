---
title: ดัชนีการเปลี่ยนแปลง
tags: [index, changelog]
---

# 📆 ดัชนีการเปลี่ยนแปลง

[[00-home|🏠 Home]] · [[all-funds|กองทุนทั้งหมด]] · [คู่มือรันประจำวัน](../../docs/guides/daily-operation.md)

แต่ละโน้ตคือส่วนต่างระหว่างการรันสองครั้งติดกัน ไม่ใช่ภาพรวมของทั้งวอลต์

| วันที่ | จำนวนการเปลี่ยนแปลง |
|---|---|
| [[../Changes/2026-08-27\|2026-08-27]] | 0 |

## ค้นด้วย Dataview

````
```dataview
TABLE changes AS "การเปลี่ยนแปลง"
FROM #changelog
SORT date DESC
```
````
