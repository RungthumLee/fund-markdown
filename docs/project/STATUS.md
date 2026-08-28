---
title: STATUS — คิวงานและบันทึกลูป
tags: [project, status, loop]
updated: 2026-08-28
---

# 🔁 STATUS — คิวงาน (G→D→I→V→R→S)

โครงลูป: **G**oal → **D**ecide → **I**mplement → **V**erify → **R**ecord → **S**top
ที่เกี่ยวข้อง: [[tasks|Tasks]] · [[issues|Issues]] · [[decisions|Decisions]]

## กติกาแต่ละขั้น
| ขั้น | ทำอะไร | เงื่อนไขผ่าน |
|---|---|---|
| G | เลือกงานถัดไป 1 ชิ้นจากคิว | เล็กพอจบใน 1 รอบ (3–8 ไฟล์) |
| D | ตอบ 5 คำถามก่อนแตะไฟล์ | ตัดสินใจไม่ได้ → โหวต 3 agent แล้วบันทึก |
| I | เขียน markdown | ทุกตัวเลขมีแหล่งอ้างอิง (dataset/field หรือเลขหน้า PDF) |
| V | ตรวจ 2 ชั้น | broken_links=0 + ข้อเท็จจริงถูก |
| R | บันทึกลง docs | ทำทุกรอบ แม้รอบที่ไม่มีปัญหา |
| S | ถึงเป้า หรือต้องให้คนตัดสิน | — |

## 5 คำถามของ D
1. เป้าหมาย + เกณฑ์ "เสร็จ" ของงานนี้คืออะไร?
2. แหล่งข้อมูล/provenance ของทุกตัวเลข — มีจริงและเชื่อถือได้ไหม?
3. แตะไฟล์ไหนบ้าง (3–8)?
4. ตรวจผ่านยังไง (broken_links=0 + ข้อเท็จจริงถูก)?
5. มีทางแยกที่ต้องตัดสินใจไหม? ถ้ามี → โหวต 3 agent

---

## 🗂️ แผนเฟส (autonomous — เริ่ม 2026-08-28)

ทำตามลำดับ ทุกเฟส commit + broken=0 · อยู่ในกรอบ [[ideas#0. กรอบ|ข้อมูลอ้างอิง]] (สองด้าน · ไม่ทำนาย)

- [x] **P1 · Factor foundation** ✅ — `factor_map.json` (static) + `factors.py` + section "⚖️ ปัจจัยที่กระทบ" ในโน้ตกอง (สองด้าน, ไม่ทำนาย)
- [x] **P2 · Skills** ✅ — `.claude/skills/*` : fund-explainer · fund-finder · portfolio-overlap · fee-audit · holding-explorer
- [x] **P3 · R-05 NAV time-series** ✅ — surface NAV 120 วัน ในโน้ตกอง (ประตูสู่ correlation)
- [x] **P5 · Correlation (fund↔factor)** ✅ — factor series (Yahoo) + realized correlation + block ในโน้ต (descriptive+caveat)
- [x] **P4** ✅ เสริมสรุปภาษาคนให้มี **ประเทศ + กลุ่มอุตสาหกรรม** (A-RING: เน้นกลุ่มวัสดุ/โลหะ · แคนาดา)
- [x] **P8 · ความต่อเนื่องของ NAV + การเปลี่ยนชื่อกอง** ✅ — ต่อ series ให้ 116 กอง · กันผลตอบแทนคร่อมช่องว่าง · รายงาน [[nav-continuity|NAV Continuity]]
- [x] **P7 · Backfill NAV 5 ปี + holding 12 ไตรมาส** ✅ — 3.3 ล้านแถว NAV · correlation median n 53 → **1,050**
- [x] **P6 · Probe ต้นทาง + เก็บงานค้าง** ✅ — `probe_history.py` (NAV/portfolio reach + rate limit) · OUT-001 RMF · sync เอกสาร

## 🤝 Handoff — สำหรับ Session ถัดไป (2026-08-28)

### สถานะปัจจุบัน (ทำเสร็จแล้ว)
คลังกองทุนไทย 2,121 กอง · โน้ต markdown 8,079 · broken_links=0 · push GitHub ครบ
- **ชั้นข้อมูล:** ประเทศ (look-through) · sector (factsheet+Yahoo) · cap · duration/credit · fx/conc — เป็น faceted tag
- **ชั้นสังเคราะห์:** สรุปภาษาคน · ค่าธรรมเนียม 2 ชั้น (feeder) · **factor exposure (สองด้าน)** · **correlation วัดจริง** (A-RING↔ทอง +0.89) · NAV history ~120 วัน
- **Skills 6 ตัว** ที่ `.claude/skills/` · **ออกแบบ+กรอบ** ที่ [[ideas]] (§0 = เส้นห้ามข้าม)

### งานถัดไป (เรียงตามคุ้มค่า) — ดูรายละเอียด [[ideas#5]]
> ✅ **ทำแล้ว 2026-08-28:** probe ต้นทาง (§5.5) · **backfill NAV 5 ปี + holding 12 ไตรมาส** (P7)
> ข้อมูลพร้อมสำหรับงานที่ต้องใช้ประวัติยาวแล้ว

1. **Rolling correlation** — correlation เคลื่อนที่ (เช่น หน้าต่าง 1 ปี ขยับทีละเดือน)
   → ตอบ "นิ่งหรือดริฟต์" ด้วย**ตัวเลข** แทนการเตือนลอย ๆ · ข้อมูลพร้อม (median 1,050 วัน)
2. **Crisis correlation** — correlation เฉพาะช่วงตลาดตก → ทำให้คำเตือน "พุ่งเข้า 1 ตอนวิกฤต"
   เป็นตัวเลขที่วัดได้ · ต้องนิยาม "ช่วงวิกฤต" จากข้อมูล ไม่ใช่เลือกเอง
3. **Fund-to-fund correlation** — เสริม skill `portfolio-overlap`:
   ซ้ำซ้อนที่วัดจากการเคลื่อนไหวจริง ไม่ใช่แค่ถือหุ้นตัวเดียวกัน
4. **Style drift / tag ที่ทน** — ใช้ holding 12 ไตรมาสที่ backfill มาแล้ว
   (`data/raw/out_portfolio.jsonl` มีครบ · ตอนนี้ `transform` ใช้แค่งวดล่าสุด)
5. **[[tasks|T-100]]** ลงทะเบียน `schtasks` — ผู้ใช้รันเอง 1 บรรทัด (agent ถูก policy บล็อก)

### วิธีทำงาน (สำคัญ)
- **ทุกอย่างอยู่ใต้กรอบ [[ideas#0. กรอบ|§0]]:** descriptive · สองด้าน · ไม่ทำนาย · ไม่มี `estimated_change`/`confidence` · ทุกตัวเลขมีที่มา+ช่วงเวลา · ไม่มีข้อมูล=บอกไม่มี
- **ตัดสินใจสำคัญจริง → โหวต 3 agent + บันทึก** (เรื่องเล็กตัดสินเอง) · ดู DEC-L01 เป็นตัวอย่าง
- **ทุกรอบ:** V (broken_links=0 + fact-check) → R (บันทึก STATUS) → commit+push
- **ข้อมูล fetch (nav_history/factor_series/correlations/security_meta) อยู่ใน `data/` (gitignore)** — commit เฉพาะโน้ตที่ regenerate · Yahoo ดึงได้บนเครื่องนี้ (yfinance ไม่ติด 429)

### แผนที่ไฟล์ (ที่ทำรอบนี้)
```
scripts/geography.py      ประเทศจาก ISIN/symbol
scripts/tagging.py        faceted tag + plain_summary (asset/risk/sector/cap/fx/duration/credit/use)
scripts/securities.py     sector/cap จาก Yahoo (dormant ถ้าไม่ fetch)
scripts/factors.py        factor exposure (อ่าน factor_map.json)  · factor_map.json (ความรู้ static)
scripts/nav_history.py    NAV ~120 วัน + สถิติ (R-05)
scripts/fetch_factor_series.py + correlations.py   correlation NAV↔factor
scripts/fetch_sectors.py  ดึง sector/mcap ต่อหลักทรัพย์ (รันบนเครื่อง)
gen_vault.py / gen_master_notes.py / gen_entity_notes.py  เจนโน้ต (เรียกทุกโมดูลข้างบน)
```
รัน pipeline: `python daily.py` (มี navhist/factorseries/correlations wired แล้ว)

---

## คิวงาน

- [x] **A1** ประเทศจากหลักทรัพย์ (ISIN/exchange) → rollup ขึ้นกอง → ดัชนี by-country ✅ Round 1
- [x] **B1** หลักทรัพย์เป็น knowledge node — เพิ่ม **ประเทศ** (ticker/exchange/ownership มีอยู่แล้ว) ✅ Round 2
- [x] **A2** sector facet — factsheet (R4) + **Yahoo per-holding เปิดใช้จริงแล้ว** (R7/R8, 1,170 หลักทรัพย์) ✅
- [x] **A3-market-cap** facet `cap/*` จาก Yahoo market-cap ✅ (R7/R8) · _currency ไม่มีในต้นทาง (R6)_
- [~] **A3** ช่องว่างอื่น: **duration/credit ทำแล้ว** (Round 3) · currency=ยังไม่ parse · market-cap=ต้องแหล่งนอก

---

## บันทึกการตัดสินใจ (Decision log)

_บันทึกผลโหวต 3 agent ต่อทางแยกที่ตัดสินเองไม่ได้ (เฉพาะเรื่องสำคัญจริง)_

### DEC-L01 (A1) — จัดการ ISIN ที่เป็น "ที่จดทะเบียนกอง" (LU/IE/KY ~680 entity)
**ปัญหา:** feeder 983 กองถือ master ที่จดทะเบียน LU/IE/KY — ISIN→ประเทศตรง ๆ จะได้
"ลักเซมเบิร์ก" แทนตลาดจริง (เช่นจีน) กระทบความถูกต้องของชั้น geo ทั้งชั้น

**ผลโหวต: เอกฉันท์ 3/3 → Option 3 (dual field)**
- `domicile_country` = ISIN prefix ตรง ๆ เสมอ (provenance anchor, deterministic)
- `market_country` = ตลาดจริง — feeder ใช้ look-through, หุ้นตรงใช้ ISIN ตัวเอง
- rollup "% ประเทศ" ของกองใช้ **market_country** เท่านั้น

**ข้อควรระวังร่วม (ทั้ง 3 agent):** look-through ทะลุได้แค่บางส่วน (บาง master
`covered_pct` ~38%) → **ต้องแสดง "% ที่ทะลุได้ / ส่วนที่เหลือ" ชัดเจน** ไม่งั้น % ประเทศ
จะรวมไม่ถึง 100 และทำให้เข้าใจผิดว่าครบ

**เหตุที่ต้องโหวต:** เป็นทางแยกที่กำหนดความถูกต้องของ A1/A2/B1 ทั้งหมด ไม่ใช่เรื่องเล็ก

---

## บันทึกรอบ (Round log)

_หนึ่งบรรทัดต่อรอบ: งาน · ผล V · ไฟล์ที่แตะ_

- **P8 · NAV ต่อเนื่องไหม + กองเปลี่ยนชื่อ** (คำถามผู้ใช้) — V ผ่าน (broken=0 · orphan=0 · S1=0) ·
  **คำตอบ 1:** ไม่ต่อเนื่องทั้งหมด — series รายวัน **2,646/3,466 มีช่องว่าง >10 วัน** ·
  สาเหตุใหญ่คือ **ต้นทางขาดทั้งตลาด 1–12 พ.ย. 2024** (เรียก API ตรง ๆ ได้ 21 แถวทั้งช่วง
  เทียบกับช่วงข้างเคียงที่เต็ม) กระทบ ~1,500 series · อีก 51 series เป็นกองที่ประกาศ
  **รายเดือน/รายสัปดาห์** ซึ่งปกติ ไม่ใช่ข้อมูลขาด · และมีกองที่หายจริงยาว ๆ เช่น B-EQUITY 425 วัน ·
  **คำตอบ 2:** ต้นทาง**ไม่เก็บประวัติชื่อ** (`profiles` มีชื่อเดียวต่อโครงการ ครบ 4,892 แถว = 0 กรณี)
  ร่องรอยเดียวคือ `fund_class_name` ในชุด NAV → พบการส่งไม้ **358 คู่** (ASP-POWER→ASP-NCLR ·
  ASP-BRIC→ASP-BIC · ASP-LTF→ASP-THDEQ) **NAV ต่อเนื่องจริง แต่ป้ายเปลี่ยน** ·
  **แก้:** [[issues|ISS-041]] กันคำนวณผลตอบแทนคร่อมช่องว่าง (`MAX_GAP_DAYS=7`) ·
  [[issues|ISS-042]] `stitch_lineage` ต่อป้ายเดิม 3 เงื่อนไข (ไม่เคยรายงานวันเดียวกัน · ≤7 วัน · NAV ≤5%)
  → ต่อให้ **116 กอง** (ASP-NCLR 841 → 1,218 วัน) · เงื่อนไข "ไม่เคยรายงานวันเดียวกัน" คือตัวกัน
  ไม่ให้ 1AMSET50-RA/-RU (ต่างกัน <1%) ถูกต่อผิด ·
  ไฟล์: `nav_history.py` `correlations.py` `gen_vault.py` `check_nav_continuity.py`(ใหม่) `run_all.py`
  `vault/Concepts/การเปลี่ยนชื่อกองทุนกับ NAV.md`(ใหม่) `gen_data_quality.py`

- **P7 · Backfill ข้อมูลย้อนหลัง (T-106)** — V ผ่าน (broken=0 · orphan=0 · S1=0) ·
  `harvest.py` `NAV_YEARS=5` + `PORT_QUARTERS_BACK=12` และเปลี่ยนเป็น **ดึงแบบแบ่ง slice**
  (ปีละไฟล์/ไตรมาสละไฟล์ ลง `.parts/` มี `.done` ของตัวเอง → หลุดกลางทางรันต่อได้) ·
  ผลจริง: **NAV 3,300,111 แถว / 873 MB ใน 2 ชม. 14 นาที** · **portfolio 763,302 แถว / 251 MB ใน 31 นาที** ·
  **rate limit ของจริง:** 4 workers → เจอ 429 ใน 3 นาที · เรียงต่อกัน → 429 = 0 (แก้ [[outstanding|OUT-002]] ที่ burst test บอกว่าไม่มีเพดาน) ·
  `fetch_factor_series` 8 เดือน → 5 ปี (ไม่งั้น correlation ถูกคอขวดที่ฝั่ง factor) ·
  `nav_history` เก็บ series เต็ม + สถิติ **1Y/3Y/5Y** (แสดงเฉพาะช่วงที่กองอายุถึง ≥80%) ·
  **ผลลัพธ์ที่วัดได้:** correlation median n **53 → 1,050** (SE ~0.12 → ~0.03) · 1AMSET50↔SET +0.93(n=53) → **+0.97(n=1,167)** ·
  A-RING↔ทอง +0.89(n=78) → **+0.82(n=170)** · กองที่มี correlation 1,704 → **1,883** · กองในขอบเขตที่มีสถิติ 5 ปี **1,442** ·
  เจอบั๊กที่โผล่เพราะข้อมูลยาวขึ้น 2 ตัว: [[issues|ISS-039]] (NAV สรุปย่อเป็นของ class ที่ตายแล้ว) ·
  [[issues|ISS-040]] (รัน `transform` แล้วไม่รัน pipeline ต่อ → ลิงก์หลักทรัพย์หาย 2,027 orphan) ·
  ไฟล์: `harvest.py` `nav_history.py` `fetch_factor_series.py` `gen_vault.py` + เอกสาร

- **P6 · Probe ต้นทาง + เก็บงานค้าง** — V ผ่าน (broken=0 · orphan=0 · S1=0 · `#tax/rmf` 341→**377** กอง) ·
  `probe_history.py` วัดจริง 463 call: **NAV ย้อนถึงวันจัดตั้ง** (K-FIXED 1995–2026 = 32 ปี · ปีก่อนจัดตั้ง 0 แถว) ·
  **portfolio เพดาน 202309 = 12 ไตรมาส** (กอง 32 ปี/24 ปี ได้งวดแรกเท่ากัน → retention ของ API ไม่ใช่อายุกอง) ·
  **ไม่เจอ 429 เลย** ถึง 73 req/s (8 threads) — ยิงเรียงถูกจำกัดด้วย latency ~80 ms ·
  **OUT-001 แก้:** RMF อ่านจากชื่อจดทะเบียน "เพื่อการเลี้ยงชีพ" แทนชื่อย่อ (ยืนยัน `fund_class_tax_incentive_type`
  มีแค่ SSF 398 / Thai ESG 44 ไม่มี RMF) → superset ของวิธีเดิม เพิ่ม M-VALUE/SCBRMS&P500/SCB2576 ·
  **[[issues|ISS-038]] แก้:** ตารางปัจจัยสลับลำดับเองทุกรอบ (set iteration + hash seed) → `sorted()` + tiebreaker
  ทำให้ regenerate ได้ผลเท่าเดิมทุกครั้ง (พิสูจน์ด้วยการรัน 2 ครั้งติด) ·
  sync `handover.md` ให้ชี้ STATUS เป็นแหล่งจริง · ไฟล์: `probe_history.py`(ใหม่) `tagging.py` `factors.py`
  `gen_data_quality.py` `handover.md` `outstanding.md` `decisions.md` `ideas.md` `issues.md` `tasks.md` `STATUS.md`

- **P5 · Correlation fund↔factor** — V ผ่าน (broken=0 · **A-RING +0.89 ทองคำ / −0.60 USD** · 1AMSET50 **+0.93 SET** — วัดจริง) · `fetch_factor_series.py` (7 series Yahoo) + `correlations.py` (Pearson, lag 0/1 กัน timezone, |r|≥0.4, ≥30 obs) → 1,704 กอง · block "📊 เคลื่อนไหวสัมพันธ์กับอะไร" + caveat แรง · wired · **ปิด loop factor-measured** · ไฟล์: `fetch_factor_series.py` `correlations.py` `gen_vault.py` `run_all.py` `daily.py`

- **P4 · สรุปภาษาคน + ประเทศ/กลุ่ม** — V ผ่าน (broken=0) · plain_summary เพิ่ม 'เน้นกลุ่ม<sector>' + 'ลงทุนต่างประเทศ (<ประเทศ>)' · ไฟล์: `tagging.py` `gen_vault.py`

- **P3 · R-05 NAV time-series** — V ผ่าน (broken=0 · A-RING: ret +22% / vol 51.8% คำนวณเอง ตรง factsheet · sparkline) · `nav_history.py` อ่าน raw/nav.jsonl → series ~80 วันทำการ + สถิติ window (descriptive, caveat อดีต) · section 8 · wired ใน run_all/daily · **ประตูสู่ correlation พร้อมแล้ว** · ไฟล์: `nav_history.py` `gen_vault.py` `run_all.py` `daily.py`

- **P1 · Factor foundation** — V ผ่าน (broken=0 · S1=0 · A-RING→ราคาโลหะ/จีน/เฟด สองด้าน) · `factor_map.json`(static, ความรู้) + `factors.py` + section "⚖️ ปัจจัยที่กระทบ (สองด้าน)" ในโน้ตกอง · descriptive ไม่ทำนาย ตามกรอบ ideas §0 · ไฟล์: `factor_map.json` `factors.py` `gen_vault.py`

- **B2-R1 · Fee stacking ในโน้ตกองหลัก** — V ผ่าน (broken=0 · LHHEALTH 2.16%+1.14%=≈3.30% · KT-US 1.54%+0.92%=≈2.46% ·
  กองที่ไม่มี TER → "-" ไม่ปลอม) · เพิ่มคอลัมน์ TER ไทย + รวม 2 ชั้น (TER ไทย + OCF กองหลัก) ในตารางกองไทยที่ feed ·
  ไม่ต้องโหวต · ไฟล์: `gen_master_notes.py` (import fees + ter_by_pid + fee_cells)
- **B2-R2 · ลิงก์ holdings กองหลัก → โน้ต entity** — V ผ่าน (broken=0 · NVIDIA→[[NVIDIA Corp]] · +คอลัมน์ตลาด) ·
  symbol→entity (look-through) → entity_links → note · กองหลักกลายเป็น hub ในกราฟ (คลิกหุ้น → เห็นกองไทยที่ถือทั้งหมด) ·
  ระวัง ISS-024 (pipe ธรรมดา ให้ cell() escape) · ไฟล์: `gen_master_notes.py` (+geography, sym_to_note)
- **B2-R3 · sector ต่อหุ้นใน holdings กองหลัก** — V ผ่าน (broken=0 · NVIDIA→เทคโนโลยี · Alphabet→สื่อสาร ตาม GICS) ·
  ตาราง holdings ครบ: name(ลิงก์)/ticker/ตลาด/กลุ่ม/สัดส่วน (กลุ่มจาก `security_meta`, no-op ถ้ายังไม่ fetch) ·
  ไฟล์: `gen_master_notes.py` (+securities) · **B2 refinement เสร็จ**

- **R1 · A1 ประเทศจากหลักทรัพย์** — V ผ่าน (broken=0 · orphan=0 · ISIN/symbol→ประเทศถูกทุกตัวที่สุ่ม) ·
  ตัดสินใจ DEC-L01 (โหวต 3/3 dual field) · 1750/2121 กองมีประเทศ พร้อม covered% เปิดเผยส่วนที่ทะลุไม่ได้ ·
  ไฟล์: `geography.py`(ใหม่) · `gen_vault.py` (§7 + frontmatter + by-country index + home) · `STATUS.md` · `tasks.md`
- **R2 · B1 ประเทศในโน้ตหลักทรัพย์** — V ผ่าน (broken=0 · Tencent: ตลาด ฮ่องกง/จดทะเบียน เคย์แมน ✓ · NVIDIA สหรัฐ ✓) ·
  เพิ่ม `domicile_country`/`market_country`/`country` (domicile=ISIN, market=Bloomberg alias/symbol) ·
  ครอบคลุม 764/2960 equity (เฉพาะที่มี ISIN/Bloomberg code — ไม่เดา) · ไม่ต้องโหวต (ใช้ DEC-L01) ·
  ไฟล์: `geography.py` (+Bloomberg map) · `gen_entity_notes.py` · `STATUS.md`
  _ค้าง: หุ้น look-through ต่างประเทศที่ไม่มี ISIN (~2,200) ยังไม่มีประเทศ — เสริมได้ด้วยการ join symbol จาก lookthrough ภายหลัง_
- **R3 · A3 bond facets (duration/credit)** — V ผ่าน (broken=0 · K-FIXED → duration/medium + credit/investment-grade) ·
  parse duration ข้อความไทย "3 ปี 6 เดือน"→3.5 ปี · credit จาก factsheet (IG 147 · รัฐ 42 · HY 13) · duration (สั้น 118/กลาง 75/ยาว 30) ·
  ไม่ต้องโหวต · ไฟล์: `tagging.py` · `gen_vault.py` (facet label) · `STATUS.md`
  _ค้าง A3: currency (ต้อง parse factsheet เพิ่ม) · market-cap large/mid/small (ต้องแหล่งนอก เช่น Yahoo ซึ่งตอน 429)_
- **R4 · A2 sector facet (จาก factsheet)** — V ผ่าน (broken=0 · by-sector: การเงิน 155/เทค 129/พลังงาน 87 · 1AMSET50→financials) ·
  map ชื่อ sector ไทย(SET)+อังกฤษ(GICS) → canonical 10 กลุ่ม · tag `sector/*` 435 กอง + ดัชนี by-sector ·
  ไม่ต้องโหวต (map ตรงไปตรงมา) · ไฟล์: `tagging.py` · `gen_vault.py` (facet + index + home) · `STATUS.md`

---

- **R5 · B1 coverage (join lookthrough symbol)** — V ผ่าน (broken=0 · โน้ต entity มีประเทศ **2,838/3,136 = 90%** จากเดิม ~764) ·
  ประเทศจาก symbol ใน look-through (VIETCAP→เวียดนาม ✓) · แก้ false positive "KBANK-F→US" (bare→US เฉพาะ A-Z ล้วน ไม่มีขีด) ·
  ไม่ต้องโหวต · ไฟล์: `geography.py` (แก้ market_of_symbol) · `gen_entity_notes.py` (LT_SYMBOL fallback)
- **R8 · เปิดใช้ Yahoo sector/market-cap จริง** — รัน `fetch_sectors.py` บนเครื่องนี้ (yfinance ไม่ติด 429) →
  **1,170 หลักทรัพย์** (ok 1,165 · none 93) · V ผ่าน (broken=0 · NVIDIA→Technology/Semiconductors/$5.5T ·
  TCHTECH→cap/large+sector/communication) · `cap/large` 615 กอง ·
  _ข้อมูล fetch อยู่ใน `data/` (gitignore) — commit เฉพาะโน้ตที่ regenerate แล้ว_
- **R6 · A3 currency (สืบแล้วไม่ทำ)** — ตรวจ factsheet: ไม่มีตารางสัดส่วนสกุลเงินที่มีโครงสร้าง
  (1,831 matches เป็น glossary; "USD 60%" กระจัดกระจาย) → **ตั้งใจไม่ parse** เพื่อเลี่ยงข้อมูลปลอม (ISS-009) ·
  มิติค่าเงินจริง = FX Hedging % (ทำเป็น fx tag แล้ว) · ไม่มีไฟล์โค้ดเปลี่ยน (บันทึกอย่างเดียวตามกติกา R)

---

## 🛑 STOP — สรุปสถานะลูป (R1–R5)

ทำเสร็จแบบ deterministic ครบทุกส่วนที่ทำได้ในสภาพแวดล้อมนี้:
- ✅ **A1** ประเทศตลาดต่อกอง (จากหลักทรัพย์ + look-through) + by-country
- ✅ **B1** ประเทศบนโน้ตหลักทรัพย์ (market/domicile)
- ✅ **A3** bond duration/credit facets
- ✅ **A2** sector facet + by-sector (จาก factsheet)

**สถานะล่าสุด:**
- **A2 Yahoo per-holding sector + A3 market-cap** — ✅ **เปิดใช้จริงแล้ว (R7+R8)** — รัน `fetch_sectors.py`
  บนเครื่องนี้ได้ (yfinance จัดการ cookie/crumb แทน curl ที่โดน 429) ดึงได้ **1,170 หลักทรัพย์** ·
  tag `cap/large` 615 กอง · `sector/*` เสริมกองต่างประเทศ · โน้ตหุ้นขึ้นกลุ่ม/อุตสาหกรรม/ขนาด (NVIDIA → Technology/Semiconductors/$5.5T)
- **A3 currency exposure** — 🔴 **ตรวจแล้วไม่มีในต้นทาง** (R6): factsheet ไม่มีตารางสัดส่วนสกุลเงิน
  มีแค่ glossary + การเอ่ยกระจัดกระจาย → parse แล้วจะไม่น่าเชื่อถือ **จึงตั้งใจไม่ทำ** (หลักเดียวกับ ISS-009)
  มิติค่าเงินที่ source มีจริง = **FX Hedging %** ซึ่งทำเป็น `fx/*` tag แล้ว
- ~~**B1 coverage**~~ ✅ แก้แล้ว R5 (90%)

---

## ▶️ วิธีเปิดใช้ sector/market-cap จาก Yahoo (A2/A3 — รันบนเครื่องคุณ)

โค้ดพร้อมแล้ว (R7) และ **หลับอยู่จนกว่าจะรัน** — ถ้ายังไม่มีข้อมูล วอลต์ไม่เปลี่ยน

```bash
python scripts/fetch_sectors.py      # ดึง sector/industry/market-cap ต่อหลักทรัพย์ (resume ได้)
python scripts/gen_vault.py          # กลายเป็น tag cap/* + sector/* (เสริมกองต่างประเทศ)
python scripts/gen_entity_notes.py   # โน้ตหุ้นขึ้น กลุ่ม/อุตสาหกรรม/ขนาด
```

- ใช้ `yfinance` (เหมือน `fetch_masters.py`) · cache ต่อ symbol ที่ `data/sectors/` · รอบแรกช้า
- ผลลง `data/processed/security_meta.json` → `scripts/securities.py` แปลงเป็น tag
- ทดสอบด้วยข้อมูลปลอมแล้ว: TCHTECH → `cap/large` + `sector/consumer` · โน้ต Tencent ขึ้น กลุ่ม/อุตสาหกรรม/ขนาด · broken=0
- ถ้าไม่รัน: ทุกอย่าง no-op (ยืนยันแล้ว) ไม่กระทบของเดิม
