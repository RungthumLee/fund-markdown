---
title: Pipeline Overview
tags: [guide, architecture, pipeline]
---

# 🔄 Pipeline — ภาพรวมทั้งระบบ

**ที่เกี่ยวข้อง:** [[quickstart|Quickstart]] · [[bulk-vs-per-fund|Bulk vs Per-fund]] · [[scope-and-filters|Scope & Filters]] · [[../project/tasks|Tasks]]

---

## ภาพรวม

```
                 ┌──────────────────────┐
                 │   SEC Open API v2    │
                 │  api.sec.or.th       │
                 └──────────┬───────────┘
                            │  21 endpoints, cursor pagination
                            ▼
   ┌────────────────────────────────────────────────┐
   │ 1. harvest.py            data/raw/*.jsonl      │
   │    bulk fetch + checkpoint (.done)             │
   └────────────────────────┬───────────────────────┘
                            ▼
   ┌────────────────────────────────────────────────┐
   │ 2. transform.py          data/processed/*.json │
   │    streaming join by proj_id                   │
   │    scope filter · decode base64/HTML           │
   └───────────┬────────────────────────┬───────────┘
               │                        │
               ▼                        ▼
   ┌────────────────────────┐  ┌────────────────────────┐
   │ 3. fetch_factsheets.py │  │ 5. gen_vault.py        │
   │    data/factsheets/    │  │    vault/Funds/        │
   │    *.pdf (8 threads)   │  │    vault/AMCs/         │
   └───────────┬────────────┘  │    vault/Indexes/      │
               ▼               └───────────┬────────────┘
   ┌────────────────────────┐              │
   │ 4. parse_factsheets.py │──────────────┤
   │    vault/Factsheets/   │              │
   │    *.md  (PyMuPDF)     │              │
   └────────────────────────┘              ▼
                              ┌────────────────────────┐
                              │ 6. validate_vault.py   │
                              │    validation-report   │
                              └────────────────────────┘
```

---

## รันทั้งหมดในคำสั่งเดียว

```bash
python run_all.py                    # รันครบทุกขั้น (ข้ามที่ทำแล้ว)
python run_all.py --smoke            # รันทดสอบขนาดเล็ก
python run_all.py --from vault       # เริ่มจากขั้นที่กำหนด
python run_all.py --skip factsheets  # ข้ามขั้นที่ไม่ต้องการ
```

---

## แต่ละขั้นทำอะไร

### 1. `harvest.py` — เก็บข้อมูลดิบ

ดึงทั้ง 21 dataset โดยไม่ระบุ `proj_id` (bulk) → `data/raw/<name>.jsonl`
มีไฟล์ `.done` เก็บจำนวนแถว ทำให้รันซ้ำแล้วข้าม dataset ที่เสร็จแล้ว

**Resume:** อัตโนมัติ · **Force:** `python scripts/harvest.py --force <dataset>`

### 2. `transform.py` — รวมและกรอง

- อ่าน JSONL แบบ streaming (ไฟล์ raw ใหญ่ระดับหลายร้อย MB)
- index ทุก dataset ด้วย `proj_id`
- ใช้เกณฑ์ [[scope-and-filters|Scope filter]]: Registered · ไม่ใช่ Term · ไม่ใช่ PVD
- `clean_text()` decode Base64 → strip HTML → ตัดที่ 4,000 ตัวอักษร
- เลือกงวดล่าสุดด้วย `latest_by()`

**Output:** `funds.json` · `amcs.json` · `excluded.json` · `stats.json`

### 3. `fetch_factsheets.py` — โหลด PDF

ThreadPool 8 เส้น ดาวน์โหลดจาก `pdf_factsheet` URL
ตรวจว่าเป็น PDF จริง (magic bytes `%PDF`) ก่อนบันทึก
บันทึกผลทุกไฟล์ลง `_manifest.json` พร้อมสถานะ

**Resume:** ไฟล์ที่มีแล้วข้าม · **Retry:** `--retry` ลองเฉพาะที่พลาด

### 4. `parse_factsheets.py` — แกะข้อความ

PyMuPDF อ่านทีละหน้า → tidy whitespace → เขียนเป็นโน้ต markdown
พร้อม **แกะตารางที่มีโครงสร้าง** ออกมาเป็น markdown table —
กลุ่มอุตสาหกรรม ประเทศ อันดับความน่าเชื่อถือ ผู้จัดการกองทุน
และ holdings ของกองทุนหลัก (ข้อมูลที่ API ไม่มี)
ผลเก็บที่ `data/processed/factsheet_sections.json` เพื่อให้ `gen_vault.py` นำไปใช้ต่อ
ดู [[factsheet-extraction|Factsheet Extraction]]

### 5. `gen_vault.py` — สร้างโน้ต

- `vault/Funds/<ABBR>.md` — 12 หัวข้อต่อกอง
- `vault/AMCs/<ชื่อ บลจ.>.md` — พร้อมสรุปสัดส่วนกองทุน
- `vault/Indexes/` — home, all-funds, by-amc, by-policy, by-risk,
  by-management-style, by-tax-incentive, by-peer-group, compare-fees
- `vault/Concepts/` — โน้ตแนวคิด + โน้ตหมวดนโยบาย (`gen_policy_notes.py`)
- ทุกโน้ตมี YAML frontmatter (Dataview query ได้) และ wikilink ระหว่างโน้ต

### 6. `validate_vault.py` — ตรวจสอบ

ลิงก์เสีย · โน้ตกำพร้า · frontmatter ที่ขาด · ชื่อซ้ำ · หัวข้อที่หายไป
→ `docs/project/validation-report.md`

---

## เวลาที่ใช้โดยประมาณ

| ขั้น | เวลา |
|---|---|
| harvest | ~40–60 นาที (ครั้งแรก) |
| transform | ~2–5 นาที |
| fetch_factsheets | ~15–30 นาที |
| parse_factsheets | ~5–10 นาที |
| gen_vault | ~1–2 นาที |
| validate | < 1 นาที |

รันซ้ำ (ทุกอย่าง cached) ใช้เวลาไม่กี่นาที

---

## การอัปเดตข้อมูล

```bash
# อัปเดตรายเดือน (factsheet ออกรายเดือน)
rm data/raw/*.done
python run_all.py
```

หรืออัปเดตเฉพาะบางส่วน:

```bash
python scripts/harvest.py --force nav fs_fees
python scripts/transform.py
python scripts/gen_vault.py
```
