---
title: NAV Continuity Report
tags: [project, data-quality, nav, generated]
updated: 2026-08-28
---

# NAV Continuity - ความต่อเนื่องของ NAV รายชนิดหน่วยลงทุน

> สร้างอัตโนมัติโดย `scripts/check_nav_continuity.py` จาก `data/raw/nav.jsonl` - **อย่าแก้ด้วยมือ**

ที่เกี่ยวข้อง: [[data-quality|Data Quality]] · [[issues|Issues]] · [[../../vault/Concepts/การเปลี่ยนชื่อกองทุนกับ NAV|แนวคิด: เปลี่ยนชื่อกับ NAV]]

## 1. ความถี่ในการประกาศ NAV

ไม่ใช่ทุกกองประกาศ NAV ทุกวันทำการ - ถ้าไม่แยกออกก่อน กองที่ประกาศรายเดือน จะดูเหมือน 'ข้อมูลขาด' ทั้งที่เป็นเรื่องปกติของกองนั้น

| ความถี่ | จำนวน class-series (ในขอบเขต) |
|---|---|
| รายวัน | 3,466 |
| รายสัปดาห์ | 14 |
| รายเดือน | 37 |

## 2. ช่องว่างของกองที่ประกาศรายวัน

- series รายวันทั้งหมด **3,466**
- มีช่องว่างเกิน 10 วันอย่างน้อย 1 ครั้ง: **2,646** (76%)
- ช่องว่างที่มีป้ายชื่ออื่นของกองเดียวกันครอบคลุมอยู่ (= เปลี่ยนป้าย ไม่ใช่ข้อมูลหาย): **299** ครั้ง

### ช่วงที่หายพร้อมกันทั้งตลาด

ช่องว่างเดียวกันโผล่ในหลายร้อยกองพร้อมกัน = **ข้อมูลต้นทางขาด** ไม่ใช่เรื่องของกองใดกองหนึ่ง

| ข้อมูลล่าสุดก่อนหาย | กลับมามีข้อมูล | จำนวน series ที่กระทบ |
|---|---|---|
| 2024-10-31 | 2024-11-15 | 1,022 |
| 2024-10-31 | 2024-11-14 | 850 |
| 2024-10-31 | 2024-11-13 | 281 |
| 2024-10-30 | 2024-11-14 | 184 |
| 2024-02-08 | 2024-02-20 | 79 |
| 2026-02-13 | 2026-02-24 | 61 |

### ช่องว่างที่ยาวที่สุด 15 อันดับ

| กอง | ชนิด | หายตั้งแต่ | กลับมา | วัน | มีป้ายอื่นครอบคลุม |
|---|---|---|---|---|---|
| [[../../vault/Funds/PRINCIPAL DPLUS\|PRINCIPAL DPLUS]] | `PRINCIPAL DPLUS-X` | 2024-09-03 | 2026-05-28 | 632 | ใช่ |
| [[../../vault/Funds/ASP-NCLR\|ASP-NCLR]] | `main` | 2024-10-31 | 2026-06-11 | 588 | ใช่ |
| [[../../vault/Funds/ASP-NCLRRMF\|ASP-NCLRRMF]] | `main` | 2024-10-31 | 2026-06-11 | 588 | ใช่ |
| [[../../vault/Funds/ASP-BIC\|ASP-BIC]] | `main` | 2024-10-31 | 2026-04-23 | 539 | ใช่ |
| [[../../vault/Funds/B-TOPTEN\|B-TOPTEN]] | `main` | 2024-10-31 | 2025-12-30 | 425 | ไม่ |
| [[../../vault/Funds/B-MIXED75\|B-MIXED75]] | `main` | 2024-10-31 | 2025-12-30 | 425 | ไม่ |
| [[../../vault/Funds/BCAP-MSCITH\|BCAP-MSCITH]] | `main` | 2024-10-31 | 2025-12-30 | 425 | ใช่ |
| [[../../vault/Funds/B-BASICPLUS\|B-BASICPLUS]] | `main` | 2024-10-31 | 2025-12-30 | 425 | ไม่ |
| [[../../vault/Funds/B-EQUITY\|B-EQUITY]] | `main` | 2024-10-31 | 2025-12-30 | 425 | ไม่ |
| [[../../vault/Funds/PMIX\|PMIX]] | `main` | 2024-10-31 | 2025-12-29 | 424 | ไม่ |
| [[../../vault/Funds/TLEQ-SELECT\|TLEQ-SELECT]] | `main` | 2024-10-31 | 2025-12-29 | 424 | ไม่ |
| [[../../vault/Funds/TLDIVFOCUS\|TLDIVFOCUS]] | `main` | 2024-10-31 | 2025-12-29 | 424 | ไม่ |
| [[../../vault/Funds/ABMIX70\|ABMIX70]] | `main` | 2024-10-31 | 2025-12-25 | 420 | ใช่ |
| [[../../vault/Funds/ABTOPP\|ABTOPP]] | `main` | 2024-10-31 | 2025-12-25 | 420 | ใช่ |
| [[../../vault/Funds/K-SFIXED\|K-SFIXED]] | `main` | 2024-10-31 | 2025-12-24 | 419 | ไม่ |

## 3. การเปลี่ยนชื่อที่ตรวจพบจากป้าย class

ต้นทางไม่เก็บประวัติชื่อ (`profiles` มีชื่อเดียวต่อโครงการ) - ร่องรอยเดียวคือป้าย `fund_class_name` ในชุดข้อมูล NAV

พบการส่งไม้ที่เข้าเกณฑ์ (ไม่เคยรายงานวันเดียวกัน · ห่างไม่เกิน 7 วัน · NAV ต่างไม่เกิน 5%): **358** คู่

| กอง | ป้ายเดิม | ป้ายใหม่ | เริ่มใช้ | NAV ขยับ |
|---|---|---|---|---|
| [[../../vault/Funds/ASP-INDIA\|ASP-INDIA]] | `main` | `ASP-INDIA-A` | 2024-11-21 | -0.44% |
| [[../../vault/Funds/ASP-S&P500\|ASP-S&P500]] | `main` | `ASP-S&P500-A` | 2024-11-21 | +0.40% |
| [[../../vault/Funds/ASP-THDEQ\|ASP-THDEQ]] | `ASP-LTF-A` | `ASP-THDEQ-A` | 2025-12-30 | +0.54% |
| [[../../vault/Funds/ASP-THDEQ\|ASP-THDEQ]] | `ASP-LTF-A` | `ASP-THDEQ-T` | 2025-12-30 | +0.54% |
| [[../../vault/Funds/ASP-THDEQ\|ASP-THDEQ]] | `ASP-LTF-T` | `ASP-THDEQ-A` | 2025-12-30 | +0.54% |
| [[../../vault/Funds/ASP-THDEQ\|ASP-THDEQ]] | `ASP-LTF-T` | `ASP-THDEQ-T` | 2025-12-30 | +0.54% |
| [[../../vault/Funds/ASP-THGEQ\|ASP-THGEQ]] | `ASP-GLTF-A` | `ASP-THGEQ-T` | 2025-12-30 | +0.53% |
| [[../../vault/Funds/ASP-THGEQ\|ASP-THGEQ]] | `ASP-GLTF-A` | `ASP-THGEQ-A` | 2025-12-30 | +0.53% |
| [[../../vault/Funds/ASP-THGEQ\|ASP-THGEQ]] | `ASP-GLTF-T` | `ASP-THGEQ-T` | 2025-12-30 | +0.53% |
| [[../../vault/Funds/ASP-THGEQ\|ASP-THGEQ]] | `ASP-GLTF-T` | `ASP-THGEQ-A` | 2025-12-30 | +0.53% |
| [[../../vault/Funds/ASP-THSME\|ASP-THSME]] | `ASP-SMELTF-A` | `ASP-THSME-T` | 2025-12-30 | +0.35% |
| [[../../vault/Funds/ASP-THSME\|ASP-THSME]] | `ASP-SMELTF-A` | `ASP-THSME-A` | 2025-12-30 | +0.35% |
| [[../../vault/Funds/ASP-THSME\|ASP-THSME]] | `ASP-SMELTF-T` | `ASP-THSME-T` | 2025-12-30 | +0.35% |
| [[../../vault/Funds/ASP-THSME\|ASP-THSME]] | `ASP-SMELTF-T` | `ASP-THSME-A` | 2025-12-30 | +0.35% |
| [[../../vault/Funds/ASP-USSMALL\|ASP-USSMALL]] | `main` | `ASP-USSMALL-A` | 2024-11-20 | +0.29% |
| [[../../vault/Funds/ES-AALF\|ES-AALF]] | `main` | `ES-AALF-A` | 2025-06-05 | +0.16% |
| [[../../vault/Funds/ES-AAMF\|ES-AAMF]] | `main` | `ES-AAMF-A` | 2025-06-05 | +0.07% |
| [[../../vault/Funds/ES-AASF\|ES-AASF]] | `main` | `ES-AASF-A` | 2025-06-05 | -0.02% |
| [[../../vault/Funds/ES-CHINAA\|ES-CHINAA]] | `main` | `ES-CHINAA-A` | 2025-06-04 | +0.52% |
| [[../../vault/Funds/ES-GAINCOME\|ES-GAINCOME]] | `main` | `ES-GAINCOME-RI` | 2024-07-01 | +0.02% |
| [[../../vault/Funds/ES-GDIV-UH\|ES-GDIV-UH]] | `main` | `ES-GDIV-UH-A` | 2025-03-13 | +0.02% |
| [[../../vault/Funds/ES-GDIV-UH\|ES-GDIV-UH]] | `main` | `ES-GDIV-UH-S` | 2025-03-18 | +2.80% |
| [[../../vault/Funds/ES-GINCOME\|ES-GINCOME]] | `main` | `ES-GINCOME-R` | 2025-11-24 | +0.11% |
| [[../../vault/Funds/ES-JPNAE\|ES-JPNAE]] | `main` | `ES-JPNAE-A` | 2025-06-04 | -0.59% |
| [[../../vault/Funds/ES-NDQPIN\|ES-NDQPIN]] | `main` | `ES-NDQPIN-R` | 2025-04-30 | -0.57% |
| [[../../vault/Funds/ES-NDQPIN-UH\|ES-NDQPIN-UH]] | `main` | `ES-NDQPIN-UH-R` | 2025-04-30 | -0.47% |
| [[../../vault/Funds/FP APREIT\|FP APREIT]] | `KWI APREIT-A` | `FP APREIT-A` | 2025-09-01 | +0.95% |
| [[../../vault/Funds/FP APREIT\|FP APREIT]] | `KWI APREIT-A` | `FP APREIT-R` | 2025-09-01 | +0.94% |
| [[../../vault/Funds/FP APREIT\|FP APREIT]] | `KWI APREIT-R` | `FP APREIT-A` | 2025-09-01 | +0.96% |
| [[../../vault/Funds/FP APREIT\|FP APREIT]] | `KWI APREIT-R` | `FP APREIT-R` | 2025-09-01 | +0.95% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ` | `FP EQ` | 2025-08-29 | -0.92% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ` | `FP EQ SSF` | 2025-08-29 | -0.87% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ` | `FP LTF` | 2025-08-29 | +0.37% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ SSF` | `FP EQ` | 2025-08-29 | -0.98% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ SSF` | `FP EQ SSF` | 2025-08-29 | -0.92% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI EQ SSF` | `FP LTF` | 2025-08-29 | +0.32% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI LTF` | `FP EQ` | 2025-08-29 | -2.20% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI LTF` | `FP EQ SSF` | 2025-08-29 | -2.15% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `KWI LTF` | `FP LTF` | 2025-08-29 | -0.92% |
| [[../../vault/Funds/FP LARGE\|FP LARGE]] | `FP EQ` | `FP LARGEA` | 2025-12-29 | -0.77% |

_แสดง 40 คู่แรกจาก 358_ · `nav_history.py` ต่อ series ให้อัตโนมัติตามเกณฑ์เดียวกันนี้
