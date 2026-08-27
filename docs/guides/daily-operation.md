---
title: รันประจำวัน (Daily Operation)
tags: [guide, ops, pipeline]
updated: 2026-08-27
---

# 🔁 รันประจำวัน

**ที่เกี่ยวข้อง:** [[../project/handover|Handover]] · [[../project/roadmap|Roadmap]] ·
[[../project/issues|Issues]] · [[../../vault/Indexes/changelog|ดัชนีการเปลี่ยนแปลง]]

สคริปต์: [`daily.py`](../../daily.py) · [`scripts/gen_changelog.py`](../../scripts/gen_changelog.py)

---

## คำสั่ง

```bash
python daily.py                # รันประจำวัน
python daily.py --dry-run      # ดูแผนโดยไม่แตะอะไร
python daily.py --full         # ไม่สนอายุข้อมูล ดึงใหม่ทั้งหมด
python daily.py --no-network   # สร้างใหม่จากข้อมูลที่ cache ไว้
python daily.py --only vault   # รันเฉพาะ stage เดียว
python daily.py --skip validate
```

`run_all.py` ยังอยู่ ใช้ตอน**สร้างใหม่จากศูนย์** ส่วน `daily.py` ใช้ตอนรันซ้ำ

---

## ทำไมต้องมีสองตัว

`run_all.py` ทำงานบนสมมติฐานว่ายังไม่มีอะไรอยู่เลย ซึ่งผิดสำหรับงานที่รันทุกเช้า
ด้วยเหตุผลสองข้อ

**1. `.done` checkpoint จะทำให้ไม่เกิดอะไรขึ้นเลย**
`harvest.py` ข้าม dataset ที่เคยดึงสำเร็จแล้วเสมอ รันครั้งที่สองจึงไม่ดึงอะไรใหม่
โหมดรายวันจึงถาม dataset แต่ละตัวแทนว่า**เลยรอบของตัวเองหรือยัง**

**2. ของที่มีค่าคือ "ส่วนต่าง" ไม่ใช่ "โน้ตที่สร้างใหม่"**
ไม่มีใครอ่านโน้ต 7,000 ฉบับที่ถูกเขียนทับ สิ่งที่ผู้ถือหน่วยอยากรู้คือ
ค่าธรรมเนียมกองตัวเองขึ้นไหม ถูกปรับระดับความเสี่ยงหรือเปล่า พอร์ตงวดใหม่มาหรือยัง

---

## รอบการอัปเดตของแต่ละ dataset

กำหนดไว้ที่ `harvest.MAX_AGE_HOURS`

| dataset | รอบ | เหตุผล |
|---|---|---|
| `nav` | 20 ชม. | เคลื่อนไหวทุกวันทำการ |
| `profiles` | 24 ชม. | กองใหม่ / เปลี่ยนสถานะ |
| `fs_urls` | 24 ชม. | URL ใหม่คือสัญญาณว่ามี factsheet ฉบับใหม่ |
| `out_portfolio`, `out_port_asset_type` | 7 วัน | เผยแพร่รายไตรมาส และมี lag |
| `fs_performance`, `fs_statistics`, `dividend_history`, `fs_dividend` | 7 วัน | อัปเดตรายเดือน–ไตรมาส |
| ที่เหลือ (ค่าธรรมเนียม benchmark คู่สัญญา ฯลฯ) | 14 วัน | เปลี่ยนเมื่อแก้หนังสือชี้ชวนเท่านั้น |

> [!NOTE]
> ถ้าดึงทั้ง 21 dataset ทุกวันจะใช้เวลา ~40 นาทีและ ~2,000 API call
> เพื่อไปพบว่าข้อมูลส่วนใหญ่ไม่ได้ขยับ

---

## การข้าม stage ที่อินพุตไม่เปลี่ยน

แต่ละ stage ประกาศไฟล์ที่ตัวเองอ่าน `daily.py` เก็บ **fingerprint**
(path + ขนาด + mtime) ของไฟล์เหล่านั้นไว้ใน `data/state/daily.json`
ถ้ารอบถัดไป fingerprint เท่าเดิม → ข้าม

ไม่ใช้ hash เนื้อไฟล์เพราะไฟล์ raw รวมกันหลายร้อย MB
การ hash จะแพงกว่า stage ที่พยายามจะข้าม และไฟล์เหล่านี้ถูกเขียนทับทั้งไฟล์เสมอ
ไม่เคยถูกแก้บางส่วน

`harvest` · `changelog` · `validate` รันทุกครั้งเสมอ

### เวลาที่ใช้จริง

| สถานการณ์ | เวลา |
|---|---|
| วันที่ไม่มีอะไรเปลี่ยน | **~10 วินาที** |
| วันที่ NAV เปลี่ยน (สร้างโน้ตใหม่) | ~40 วินาที |
| `--full` สร้างใหม่หมด | ~40–45 นาที |

---

## กับดักที่เจอตอนออกแบบ

**stage `entities` เขียนทับ `funds.json` ที่ตัวเองอ่าน**
ทำให้ mtime เปลี่ยนทุกรอบ และทุก stage ถัดไปถูกสร้างใหม่ทั้งที่ไม่มีอะไรขยับ
แก้โดยให้เขียนกลับ**เฉพาะเมื่อเนื้อหาต่างจริง**

หลักทั่วไป: stage ที่อ่านและเขียนไฟล์เดียวกันต้องเทียบเนื้อหาก่อนเขียนเสมอ

---

## ผลลัพธ์ของแต่ละรอบ

| ที่ไหน | อะไร |
|---|---|
| `vault/Changes/<วันที่>.md` | ส่วนต่างของรอบนั้น |
| `vault/Indexes/changelog.md` | ดัชนีย้อนหลัง 120 รอบ |
| `data/state/snapshot.json` | snapshot ล่าสุด |
| `data/state/snapshot-<วันที่>.json` | snapshot ก่อนหน้า เก็บไว้ตรวจย้อนหลัง |
| `data/state/daily.json` | fingerprint + ประวัติ 60 รอบล่าสุด |
| `data/logs/daily-<วันที่>.log` | log ต่อท้ายทุกรอบ |

### สิ่งที่ changelog จับ

| ฟิลด์ | ทำไมถึงสำคัญ |
|---|---|
| กองเข้า/ออกจากขอบเขต | เปิดกองใหม่ หรือปิดกอง |
| `ter` | ค่าธรรมเนียมที่เก็บจริง — ขึ้นคือจ่ายเพิ่มโดยตรง |
| `front` / `back` | ค่าธรรมเนียมขาย/รับซื้อคืน |
| `risk_spectrum` | ปรับระดับความเสี่ยงมีผลต่อว่าใครถือได้ |
| `policy` | เปลี่ยนนโยบายการลงทุน |
| `master` | feeder เปลี่ยนกองทุนหลัก |
| `port_period` | พอร์ตงวดใหม่ถูกเผยแพร่ |
| สินทรัพย์ใหม่ | entity ที่เพิ่งปรากฏและมีกองถือ ≥2 กอง |

การเปลี่ยนค่าธรรมเนียมต่ำกว่า `TER_EPSILON = 0.001` ถือเป็นการปัดเศษ ไม่รายงาน

---

## ตั้งเวลาอัตโนมัติ (Windows)

ไฟล์ [`run-daily.cmd`](../../run-daily.cmd) เตรียมไว้แล้ว
ลงทะเบียนกับ Task Scheduler

```powershell
schtasks /Create /TN "FundKnowledge Daily" /SC DAILY /ST 07:30 ^
  /TR "d:\Website\Fund-knowledge\run-daily.cmd" /RL LIMITED /F
```

ตรวจสถานะ / รันทันที / ลบ

```powershell
schtasks /Query  /TN "FundKnowledge Daily" /V /FO LIST
schtasks /Run    /TN "FundKnowledge Daily"
schtasks /Delete /TN "FundKnowledge Daily" /F
```

> [!IMPORTANT] เวลาที่ควรรัน
> ก.ล.ต. อัปเดต NAV ของวันทำการก่อนหน้าในช่วงเช้า
> **07:30–08:00** จึงเป็นเวลาที่ปลอดภัย ถ้ารันเที่ยงคืนจะได้ NAV ของสองวันก่อน

`run-daily.cmd` คืนค่า exit code ของ `daily.py` ตรง ๆ
Task Scheduler จึงขึ้นสถานะล้มเหลวได้เองเมื่อมี stage พัง

---

## เมื่อมีอะไรผิดพลาด

| อาการ | ตรวจที่ |
|---|---|
| stage พัง | `data/logs/daily-<วันที่>.log` แล้วรัน `python daily.py --only <stage>` ดูข้อความเต็ม |
| ข้อมูลดูเก่า | `python daily.py --full` เพื่อข้ามการเช็คอายุ |
| ลิงก์เสียหลังเพิ่มฟีเจอร์ | `docs/project/validation-report.md` |
| อยากรู้ว่าเมื่อวานเปลี่ยนอะไร | `vault/Changes/<วันที่>.md` |
| สงสัยผลของ diff | เทียบ `data/state/snapshot-<วันที่>.json` กับ `snapshot.json` |

`validate` ที่ขึ้น `warnings` **ไม่หยุด** pipeline เพราะข้อมูลถูกเขียนไปแล้ว
และ stage ถัดไปไม่ได้พึ่งพามัน แต่จะทำให้ exit code เป็น 1

---

## ส่วนที่ยังต้องมีคนอยู่ในลูป

[`search_masters.py`](../../scripts/search_masters.py) **ไม่ได้อยู่ใน `daily.py`**
เพราะขั้นตอนค้นเว็บต้องมีคนหรือ agent อยู่ตรงกลาง
ดู [[web-search-enrichment|Web Search Enrichment]]

รันเมื่อมีกองทุนหลักใหม่ที่ Yahoo/FT ไม่มีข้อมูล — ตรวจได้ด้วย

```bash
python scripts/search_masters.py queue
```
