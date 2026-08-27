---
title: Task Board
tags: [project, tasks, kanban]
updated: 2026-08-27
---

# ✅ Task Board

สถานะงานทั้งหมดของโปรเจกต์ Fund Knowledge Base

**ที่เกี่ยวข้อง:** [[issues|Issues]] · [[outstanding|Outstanding]] · [[decisions|Decisions]] · [[roadmap|Roadmap]]

Legend: `[x]` เสร็จ · `[~]` กำลังทำ · `[ ]` ยังไม่เริ่ม · `[!]` ติดปัญหา

---

## Phase 1 — สำรวจและทำเอกสาร API

- [x] **T-001** ค้นหา endpoint ของ SEC Open API กลุ่ม fund
  - Portal ตอบ 403 ต่อ scraper → ใช้ machine-readable mirror แทน (ดู [[issues|ISS-001]])
- [x] **T-002** ดึง spec ทั้งหมด (21 endpoints) เก็บที่ `_spec/fund.json`
- [x] **T-003** ทดสอบ API key จาก `.env.local` — ผ่าน (HTTP 200)
- [x] **T-004** เขียน `scripts/sec_client.py` (retry, key failover, pagination)
- [x] **T-005** สร้าง `docs/api-reference/` อัตโนมัติ 21 หน้า + index
- [x] **T-006** เขียนคู่มือ: quickstart, authentication, pagination, errors
- [x] **T-007** เขียนคู่มือ: fund-taxonomy, fund-identifiers, scope-and-filters, bulk-vs-per-fund

## Phase 2 — เก็บข้อมูล

- [x] **T-010** ออกแบบกลยุทธ์ bulk fetch (เร็วกว่า per-fund ~24 เท่า) → [[decisions|DEC-001]]
- [x] **T-011** เขียน `scripts/harvest.py` พร้อม checkpoint `.done`
- [x] **T-012** รัน harvest ครบ 21 dataset → `data/raw/*.jsonl` (743,690 แถว)
- [x] **T-013** กำหนดหน้าต่างเวลาสำหรับ time-series ไม่ให้ข้อมูลบวม → [[decisions|DEC-002]]

## Phase 3 — แปลงข้อมูล

- [x] **T-020** เขียน `scripts/transform.py` (streaming, join by proj_id)
- [x] **T-021** ใส่ตัวกรอง scope: Registered / ไม่ใช่ Term / ไม่ใช่ PVD
- [x] **T-022** decode field ที่เป็น Base64/HTML (`investment_policy_desc`)
- [x] **T-023** รัน transform → `data/processed/funds.json`
- [x] **T-024** ตรวจ coverage แต่ละ field → [[data-quality|Data Quality]]

## Phase 4 — Factsheet PDF

- [x] **T-030** เขียน `scripts/fetch_factsheets.py` (ดาวน์โหลดขนาน + resume)
- [x] **T-031** ดาวน์โหลด PDF ทั้งหมด → `data/factsheets/` (2,119 ไฟล์ / 32 วินาที)
- [x] **T-032** เขียน `scripts/parse_factsheets.py` (PyMuPDF → text)
- [x] **T-033** แปลง PDF → markdown → `vault/Factsheets/` (แกะข้อความไทยได้ 100%)

## Phase 5 — Obsidian Vault

- [x] **T-040** เขียน `scripts/gen_vault.py`
- [x] **T-041** สร้างโน้ตรายกองทุน `vault/Funds/`
- [x] **T-042** สร้างโน้ต บลจ. `vault/AMCs/` พร้อม backlink
- [x] **T-043** สร้าง MOC / index (ตามนโยบาย, ความเสี่ยง, บลจ., ภาษี)
- [x] **T-044** เขียนโน้ต Concepts (ค่าธรรมเนียม, NAV, feeder, risk spectrum)
- [x] **T-045** ตรวจ wikilink ที่ชี้ไปไฟล์ที่ไม่มีอยู่ → **ลิงก์เสีย 0**

## Phase 6 — ตรวจสอบและส่งมอบ

- [x] **T-050** เขียน `scripts/validate_vault.py`
- [x] **T-051** เขียน `run_all.py` รันทั้ง pipeline ในคำสั่งเดียว
- [x] **T-052** เขียน `.gitignore` (กัน `.env.local` และ `data/raw/`)
- [x] **T-053** เขียน `README.md` ที่ root
- [x] **T-054** รายงานสรุปผลลัพธ์ → [[handover|Handover]]

## Phase 7 — ข้อมูลเพิ่มเติมจาก Factsheet (เพิ่มระหว่างทาง)

- [x] **T-060** เขียน `scripts/factsheet_sections.py` แกะตารางจาก layout ของ PDF
- [x] **T-061** แยกตารางของ **กองทุนหลัก** ออกจากกองไทย (feeder look-through)
- [x] **T-062** กู้ตารางที่ถูกกลืนรวมกัน ด้วยการจับจุดที่น้ำหนักกระโดดกลับขึ้น
- [x] **T-063** แกะ sector / country / credit rating / ผู้จัดการกองทุน / กลุ่ม AIMC
- [x] **T-064** ยกเลิกการจำกัด holdings 30 อันดับ → เก็บครบทุกรายการ
- [x] **T-065** คำนวณสถิติกระจุกตัว (`top10_pct_nav`, `issuer_count`)
- [x] **T-066** ตัดแถวสรุปรหัส 903 ออกจาก holdings → [[issues|ISS-007]]
- [x] **T-067** เพิ่มดัชนี `by-peer-group` และ `compare-fees`
- [x] **T-068** สร้างโน้ตหมวดนโยบาย (`gen_policy_notes.py`)
- [x] **T-069** เขียนคู่มือ [[../guides/holdings-data|Holdings Data]] และ
  [[../guides/factsheet-extraction|Factsheet Extraction]]

## Phase 8 — กองทุนหลักต่างประเทศ (Master Funds)

- [x] **T-070** ตรวจความเป็นไปได้ — พบว่า `out_portfolio` มี **ISIN ของกองหลัก** อยู่แล้ว
  จึงไม่ต้องเดาจากชื่อ (773/999 feeder มี ISIN ชี้ชัด)
- [x] **T-071** ทดสอบ yfinance บน ISIN จริง 45 ตัว → **hit rate 91%**
  รวมถึง UCITS SICAV ลักเซมเบิร์ก (ไม่ได้จำกัดแค่ ETF)
- [x] **T-072** เขียน `scripts/resolve_masters.py` → 618 กองหลักที่ไม่ซ้ำ
- [x] **T-073** เขียน `scripts/ft_scraper.py` อ่าน tearsheet จาก markets.ft.com
- [x] **T-074** เขียน `scripts/fetch_masters.py` (Yahoo + FT, cache ต่อกอง, resume ได้)
- [x] **T-075** ดึงข้อมูลครบ 618 กอง → **507 กองมีข้อมูล (82%)**
- [x] **T-076** เขียน `scripts/gen_master_notes.py` → `vault/MasterFunds/` 591 โน้ต
- [x] **T-077** ลิงก์สองทาง: โน้ตกองไทย ↔ โน้ตกองหลัก (996 ลิงก์)
- [x] **T-078** ตรวจพบกองหลัก 27 กองเป็น **กองทุนไทย** เอง → ลิงก์ไปโน้ตเดิม ไม่สร้าง stub
- [x] **T-079** ทิ้งค่า `expense ratio = 0.0` ของ Yahoo (หมายถึงไม่มีข้อมูล ไม่ใช่ฟรี)
- [x] **T-080** เขียนโน้ต [[../../vault/Concepts/ค่าธรรมเนียมสองชั้นของ Feeder Fund|ค่าธรรมเนียมสองชั้น]]
- [x] **T-081** เขียนคู่มือ [[../guides/master-fund-sources|Master Fund Sources]]

---

## Phase 9 — Semantic validation + ยกระดับ KB (รอบพัฒนา 2026-08-27)

งาน 3 ก้อนที่ตกลงกันไว้: (1) semantic validator (2) Dataview + ตารางเทียบค่าธรรมเนียม
(3) ทำ changelog ให้รันต่อเนื่อง — พร้อม git + push ขึ้น GitHub

### 9.1 Semantic validator — ก้อนที่ 1
- [x] **T-090** เขียน `scripts/validate_semantics.py` — ตรวจ "ข้อมูลสมเหตุสมผล"
  ไม่ใช่แค่ลิงก์ครบ เขียนรายงานที่ [[semantic-report|Semantic Report]]
- [x] **T-091** check S1 (🔴) หลักทรัพย์ไทยผูกตัวตนผิดบริษัท → เจอ Mapletree/MINT
  ([[issues|ISS-035]]) · exit 1 เมื่อเกิน `S1_BUDGET`
- [x] **T-092** check S2 (🟡) benchmark ขัดพื้นที่ลงทุน → เจอ 1AMSET50, ONE-TCMSSF
  ([[issues|ISS-036]]) · calibrate flag ภูมิศาสตร์ + ตัด benchmark เงินฝากออกจากสัญญาณ
- [x] **T-093** check S5/S6/S7 (🟢) ผลรวม asset allocation / NAV ค้าง / holding เกิน 150%
- [x] **T-094** แก้ regex `\bsSET\b` (กัน "aSSETs" ชน) + ตัด benchmark เงินฝากออกจากสัญญาณ → S2 เหลือ 2 ของจริง
- [x] **T-095** แก้ต้นเหตุ Mapletree/MINT ใน `normalize_entities.py` (issuer-th) → **S1 = 0** ([[issues|ISS-035]])
  - แยก S8 สำหรับ ISIN ที่ต้นทางกรอกผิด ([[issues|ISS-035b]]) · ตั้ง `S1_BUDGET = 0`
  - regenerate vault ครบ → validate_vault: ลิงก์เสีย/orphan/case-clash = 0
- [x] **T-096** เพิ่ม stage `semantics` ใน `run_all.py` และ `daily.py` (non-blocking เหมือน validate)

### 9.2 Dataview + ตารางเทียบค่าธรรมเนียม — ก้อนที่ 2 ([[roadmap|R-01]] · [[roadmap|R-02]])
- [x] **T-097** เพิ่ม field ตัวเลขใน frontmatter (`ter_retail`, `perf_1y`, `nav`, `fund_size`)
  + สร้างหน้า [[../../vault/Indexes/screener|🔎 screener]] รวม Dataview query พร้อมใช้ 6 แบบ + ลิงก์จาก home
- [x] **T-098** `compare-fees` เทียบ retail TER รายหมวดอยู่แล้ว (มีมาก่อนรอบนี้ ใช้ `scripts/fees.py`) — ยืนยันทำงาน

### 9.3 Changelog ต่อเนื่อง — ก้อนที่ 3 ([[roadmap|R-07]])
- [x] **T-099** ยืนยัน `gen_changelog.py` ทำงานครบ + wired ใน `daily.py` + ทดสอบรันจริง (diff = 0 ตามคาด)
- [~] **T-100** ลงทะเบียน scheduled task — **ผู้ใช้รันเอง 1 บรรทัด** (คำสั่งอยู่ใน `run-daily.cmd`):
  ```
  schtasks /Create /TN "FundKnowledge Daily" /SC DAILY /ST 07:30 /TR "d:\Website\Fund-knowledge\run-daily.cmd" /RL LIMITED /F
  ```

### 9.4 Git + GitHub ([[roadmap|R-03]] · [[outstanding|OUT-009]])
- [~] **T-101** `git init` + ตรวจ `.gitignore` กัน `.env.local` และ `data/raw/`
- [~] **T-102** push ขึ้น `github.com/RungthumLee/fund-markdown`

> [!IMPORTANT] ก่อน commit/push ต้องยืนยันว่า `.env.local` (มี API key + DB_*) ถูก ignore จริง
> ดู [[security-notes|Security Notes]]

---

## งานที่เสนอไว้สำหรับรอบถัดไป

ดู [[roadmap|Roadmap]] และ [[outstanding|Outstanding items]]
