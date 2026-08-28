---
title: Ideas — Skills & Factor Analysis
tags: [project, ideas, backlog, design]
updated: 2026-08-28
---

# 💡 Ideas — Skills ที่ใช้กับ Data + Factor Analysis

เอกสารออกแบบ (ยังไม่ลงมือทั้งหมด) · ที่เกี่ยวข้อง: [[STATUS|STATUS]] · [[roadmap|Roadmap]] · [[tasks|Tasks]] · [[decisions|Decisions]]

> เอกสารนี้มี 3 ส่วน: **(0) กรอบ "ข้อมูลอ้างอิง" — เส้นที่ห้ามข้าม** (คุมทุกอย่าง) ·
> **(1) Skills** · **(2) Factor Analysis** — ทุกส่วนต้องอยู่ใต้ส่วน (0)

> [!DONE] สถานะการทำ (2026-08-28)
> **ทำแล้ว:** Skills 6 ตัว (`.claude/skills/`) · factor-exposure เชิงโครงสร้าง (section ในโน้ตกอง, สองด้าน) ·
> **correlation วัดจริง** (A-RING +0.89 ทอง / 1AMSET50 +0.93 SET, 1,704 กอง) · NAV history (R-05) ·
> ทั้งหมดอยู่ในกรอบ §0 · ดู [[STATUS#แผนเฟส|STATUS Phases]]
> **ยังไม่ทำ:** factor-live skill (FRED ค่าปัจจุบัน) · เวอร์ชันพยากรณ์ (นอกกรอบ, §2.8) · by-category index กองหลัก

---

## 0. กรอบ "ข้อมูลอ้างอิง" — เส้นที่ห้ามข้าม (governing rules)

คลังนี้คือ **ข้อมูลอ้างอิงเพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน** ทุก skill/feature
ต้องผ่านกฎนี้ก่อนเสมอ — ตระกูลเดียวกับบทเรียน [[issues|ISS-009 / ISS-014]]
("ตัวเลขที่ดูน่าเชื่อ อันตรายกว่าไม่มีตัวเลข")

### เส้นแบ่งหลัก: **มองอดีต (ได้) vs มองอนาคต (ไม่ได้)**

| ✅ อยู่ในกรอบ (descriptive) | ❌ ข้ามเส้น (predictive / advice) |
|---|---|
| อดีต/ปัจจุบัน ที่วัดได้ ("อดีตสัมพันธ์กัน −0.82") | พยากรณ์อนาคต ("จะลง 2.5–4%") |
| exposure จากข้อมูลจริง ("ถือทอง 100%") | ความน่าจะเป็นของคำพยากรณ์ ("confidence 0.88") |
| ป้ายเชิงคุณภาพจากข้อมูล ("ไวระดับสูง") | คะแนน/ตัวเลขที่แต่งขึ้นให้ดูแม่น |
| แสดงค่าให้ผู้ใช้ตัดสินเอง | ชี้นำซื้อ/ขาย/ถือ/กระจายเสี่ยง |
| สองด้านสมมาตร (bull + bear) | เลือกข้างว่าจะไปทางไหน |
| "correlation = เคลื่อนไหวพร้อมกัน" | "correlation = สาเหตุ" (≠ causation) |

### กฎ 7 ข้อ (ผ่านทุกข้อก่อนปล่อย feature)
1. **ทุกตัวเลขมีที่มา** — dataset/field หรือเลขหน้า PDF หรือ series id
2. **ระบุช่วงเวลาที่วัดเสมอ** (สถิติ/correlation) — ไม่มี window = ห้ามแสดง
3. **ไม่พยากรณ์** ราคา/ผลตอบแทน/ทิศทางอนาคต
4. **ไม่ให้ confidence/probability กับสิ่งที่เป็นอนาคต** (ยกเว้นมาจาก backtest จริง)
5. **ไม่ชี้นำการกระทำ** (ซื้อ/ขาย/ถือ/สับเปลี่ยน/กระจายเสี่ยง)
6. **สองด้านเสมอ** — factor/ปัจจัยแสดงทั้งโอกาสและความเสี่ยง ไม่เลือกข้าง
7. **ไม่มีข้อมูล = บอกว่าไม่มี** ไม่เดา ไม่เติมให้ครบ

### ป้ายบังคับ
- ข้อมูลที่เป็นภาพอดีต: `"อดีต ณ <ช่วง> · ไม่ใช่พยากรณ์"`
- ข้อมูลสด (ดึงตอนถาม): `"ณ <เวลา> · ยังไม่ยืนยัน · ไม่บอกอนาคต"`
- ทุก factor/สถิติ: `"correlation ไม่นิ่ง · อดีตไม่รับประกันอนาคต"`

---

## 1. Skills — ให้ AI ทำงานกับคลังนี้

Skill = ชุดคำสั่งสำเร็จรูปให้ AI (เช่น Claude Code) อ่าน/สังเคราะห์ข้อมูล
รูปแบบไฟล์: `SKILL.md` (frontmatter `name` + `description` + วิธีใช้ data)

> ข้อมูล 3 ชั้นให้ skill ใช้: **โน้ต markdown** (`vault/`) · **tag/Dataview** (faceted) ·
> **JSON ดิบ** (`data/processed/*.json`: funds · entities · lookthrough · master · security_meta)

| Skill | ทำอะไร | ใช้ข้อมูล | ระดับ |
|---|---|---|---|
| **fund-explainer** | อธิบายกอง 1 ตัวเป็นภาษานักลงทุน (แบบ A-RING) | โน้ตกอง + กองหลัก | 🟢 ทำได้เลย |
| **fund-finder** | โจทย์ภาษาคน → filter tag → กองที่ตรง + เหตุผล | faceted tags | 🟢 ทำได้เลย |
| **fund-compare** | เทียบ 2–3 กอง (ค่าธรรมเนียม 2 ชั้น · ประเทศ · sector · overlap) | funds + lookthrough | 🟢 |
| **portfolio-overlap** | ถือหลายกอง → ความซ้ำซ้อนจริง (กองหลัก/หุ้นเดียวกัน) + เตือนกระจุก/ค่าธรรมเนียมซ้อน | lookthrough + master_links | 🟢 unique |
| **fee-audit** | ต้นทุนรวม (TER ไทย + OCF กองหลัก) + หากองถูกกว่าในกลุ่ม AIMC | fees.py + peer_group | 🟢 |
| **holding-explorer** | หุ้น 1 ตัว → กองไทยทุกกองที่ถือ (ตรง+ทางอ้อม) + สัดส่วนรวม | entities + lookthrough | 🟢 (ใช้ B1/B2) |
| **factor-exposure** | ปัจจัยบวก/ลบที่กระทบกอง (ดูส่วน 2) | holdings + sector + country + factor-map | 🟡 ต้องมี factor-map |
| **factor-live** | สถานะ factor ปัจจุบัน (ราคาทอง/ดอกเบี้ยวันนี้) ประกอบ factor-exposure | FRED/Yahoo (ดึงสด) | 🟠 optional, มี guardrail |
| **data-refresh** | รัน pipeline แล้วสรุปสิ่งที่เปลี่ยน | scripts + changelog | 🟢 operational |

**หลักการทุก skill:** อยู่ใต้กรอบส่วน 0 · ตอบจาก data ในคลัง · อ้างอิงที่มา · ไม่ทำนาย/ไม่ชี้นำ

**ลำดับแนะนำ:** fund-explainer + fund-finder → portfolio-overlap → factor-exposure (หลัง factor-map + R-05)

---

## 2. Factor Analysis — ปัจจัยที่กระทบกอง (micro + macro)

**ที่มาไอเดีย:** เพราะรู้ **holdings + look-through** จึงเสนอปัจจัยที่กระทบกองได้
คำถามหลักที่ต้องตอบ: (ก) หาจากไหน (ข) ใช้ factor อะไร (ค) ละเอียดแค่ไหน
(ง) กระทบมากน้อยแค่ไหน (จ) มี "โอกาส" ด้วยไหม

### 2.1 factor หามาจากไหน — 2 แหล่ง คนละบทบาท
| แหล่ง | ให้อะไร | fetch? |
|---|---|---|
| **(ก) ข้อมูลเราเอง** | **exposure** — กองไวต่อ factor ไหน "แค่ไหน" (sector/country/holdings/cap/fx/beta/vol) | ❌ มีครบ |
| **(ข) factor-map (static)** | **direction** — factor นั้นดันขึ้นหรือลง (ความรู้การเงินมาตรฐาน) | ❌ เขียนครั้งเดียว |

> จุดสำคัญ: tag ที่ทำแล้ว (`sector/*` · country · `cap/*` · `fx/*` · `conc/*` + beta/vol ใน factsheet)
> **คือ factor exposure ~80% อยู่แล้ว** — เหลือแค่เขียน factor-map ทิศทาง

**factor-map มาจากไหน:** ความรู้การเงินมาตรฐาน (ไม่ใช่ feed) — เขียนเป็นโน้ต reference:
sector sensitivity ที่รู้กันทั่วไป (Financials +ดอกเบี้ย · Utilities −ดอกเบี้ย · Energy/Materials +สินค้าโภคภัณฑ์ ·
Gold −real yield/−USD) + style factor (Fama-French: size/value/momentum/quality/low-vol)

### 2.2 ใช้ factor อะไร — taxonomy
- **Macro:** ดอกเบี้ย(จริง/นาม) · เงินเฟ้อ · USD/ค่าเงิน · วัฏจักรเศรษฐกิจ · credit spread · ราคาสินค้าโภคภัณฑ์
- **Style (Fama-French):** ขนาด(size=`cap/*`) · value/growth · momentum · quality · low-vol
- **Sector/theme:** วัฏจักรชิป · AI capex · เปลี่ยนผ่านพลังงาน · วัฏจักรอสังหา
- **โครงสร้างกอง:** hedge ค่าเงิน(`fx/*`) · กระจุกตัว(`conc/*`) · ค่าธรรมเนียม(TER = drag คงที่)

### 2.3 ความละเอียด — 3 ระดับ (แนะนำ L2)
- **L1 (หยาบ):** asset class → factor กว้าง · ทุกกอง
- **L2 (กลาง) ⭐:** sector + country → factor เฉพาะ · คุ้มสุด (เฉพาะพอ ใช้ข้อมูลที่มี ไม่ overfit)
- **L3 (ละเอียด):** holding รายตัว → factor เฉพาะบริษัท/สินค้า (A-RING → "ราคาทอง") · ใช้กับกอง single-theme

### 2.4 กระทบมากน้อยแค่ไหน — magnitude (จุดที่ต้องซื่อสัตย์สุด)
**magnitude = น้ำหนัก(ข้อมูล) × ความไว(map/beta)** — ห้ามพยากรณ์ผลตอบแทน
- **น้ำหนัก = ข้อมูลจริง** (A-RING = 100% เหมืองทอง → น้ำหนัก factor ทอง ≈ 100%)
- **ความไว** = beta ที่รายงาน + ป้ายคุณภาพ (แรง/กลาง/อ่อน) จาก map · **vol = สัญญาณรวม**
- 🚫 ห้ามใส่ตัวเลขทำนายว่าจะขึ้น/ลงกี่ % (fake precision)
- พูดได้แค่: *"100% อยู่ในหมวดที่ไวต่อราคาทอง ระดับแรง (beta 0.99, vol 50%)"*

### 2.5 โอกาส (opportunity) — factor เป็นสองด้านเสมอ
- ทุก factor มี **bull case (โอกาส) + bear case (ความเสี่ยง)** → นำเสนอสมมาตร ไม่ใช่ "ความเสี่ยง" อย่างเดียว
- โอกาสเชิงโครงสร้างที่พูดได้ (ไม่ใช่ทำนาย): กองกระจุก/ผันผวนสูง = upside แรง/downside แรง ·
  กอง hedge = ตัดทั้งโอกาส/ความเสี่ยงค่าเงิน · ค่าธรรมเนียมสูง = factor ลบคงที่
- 🚫 ห้ามใส่ "ความน่าจะเป็น" ว่า factor จะไปทางไหน (ต้อง forecast)

### 2.6 Correlation — ใช้ได้ (descriptive) แต่มี guardrail
- **realized/historical correlation = ข้อเท็จจริงอดีต** → อยู่ในกรอบ เหมือน beta/vol/ผลตอบแทนอดีต
- **เวอร์ชันวัดจริงของ factor exposure:** correlation ของ NAV กอง กับ series ของ factor (ราคาทอง/ดอกเบี้ย)
  → ดีกว่า map เชิงคุณภาพ เพราะมาจากข้อมูล
- **guardrail (บังคับ):**
  1. ระบุ **window + จำนวน observation** เสมอ (ไม่มี = ห้ามแสดง)
  2. เตือน **correlation ไม่นิ่ง · มักพุ่งเข้า 1 ตอนวิกฤต**
  3. **correlation ≠ causation**
  4. ห้ามใช้พยากรณ์/แนะนำกระจายเสี่ยง
- **ตัวบล็อกจริง = ข้อมูล ไม่ใช่หลักการ:** NAV เก็บแค่ **120 วัน** ([[decisions|DEC-002]]) → correlation สั้น/noisy
  → ต้องทำ **R-05 (surface NAV time-series) ก่อน** ถึงจะเชื่อถือได้

### 2.7 รูปแบบผลลัพธ์ (output format)
**✅ เวอร์ชันในกรอบ (descriptive):**
```json
{
  "asset": "Gold",
  "as_of": "2026-08-28",
  "factors": [{
    "factor_name": "US 10Y Real Yield",
    "category": "Macro",
    "relationship": "inverse",
    "realized_correlation": -0.82,
    "correlation_window": "120d (2026-05-01..08-28)",
    "observations": 82,
    "exposure_weight_pct": 100,
    "impact_magnitude": "High",
    "bull_case": "real yield ลง → ปัจจัยหนุน",
    "bear_case": "real yield ขึ้น → ปัจจัยกด",
    "source": "NAV series × FRED:DFII10",
    "caveat": "อดีต ไม่ใช่พยากรณ์ · correlation ไม่นิ่ง"
  }]
}
```

**❌ field ที่ห้ามใช้ (ข้ามเส้น):**
| field | ทำไมห้าม |
|---|---|
| `estimated_asset_change_pct` | พยากรณ์ราคาอนาคต |
| `confidence_score` | ความมั่นใจต่อคำพยากรณ์ = ตัวเลขปลอม (เว้นแต่มาจาก backtest จริง) |
| `time_horizon` (แบบ forward) | ระบุกรอบเวลาพยากรณ์ = มองอนาคต |
| `target_price` / `signal` / `rating` | ชี้นำการกระทำ |

**สิ่งที่ต่างจากตัวอย่างพยากรณ์ทั่วไป:** ตัด `estimated_change` + `confidence` ·
เพิ่ม window/observations/source/caveat + `bull_case`/`bear_case` (สองด้าน)

### 2.8 ถ้าจะทำเวอร์ชันพยากรณ์จริง (นอกกรอบ — ต้องเลือกอย่างตั้งใจ)
ถ้าต้องการ `estimated_change` / `confidence` จริง = **ออกจาก "ข้อมูลอ้างอิง" ไปเป็น "เครื่องมือพยากรณ์"**:
- `confidence` ซื่อสัตย์ได้ต้องมาจาก **backtest** (เก็บ error โมเดลย้อนหลัง) — เราไม่มีข้อมูลยาวพอ
- ต้องมีโมเดลชัด (regression NAV~factor) + สมมติฐาน + คำเตือน "อาจผิด"
- ต้องเปลี่ยน disclaimer จาก "ไม่ใช่คำแนะนำ" เป็น "ประมาณการเชิงสถิติ มีโอกาสพลาด"
- → ทำเป็น **skill แยกที่ติดป้ายชัด** ไม่ปนกับ reference layer

---

## 3. ลำดับพึ่งพา (dependencies)
```
R-05 (surface NAV 120 วัน)  ──►  correlation (fund↔fund, fund↔factor)
factor-map (static, เขียนครั้งเดียว)  ──►  factor-exposure skill (L2)
FRED/Yahoo (ดึงสด, optional)  ──►  factor-live skill (มี guardrail)
```
**ประตูสำคัญ = R-05** (ปูทางทั้ง correlation และ factor-measured)

## 4. Backlog เสริม
- `by-category` index ของกองหลัก (Morningstar category)
- semantic validator เพิ่ม check: country/sector coverage · cap สอดคล้อง policy
- FRED integration (ฟรี, API) สำหรับ factor series: real yield (DFII10) · USD (DTWEXBGS) · ราคาทอง/น้ำมัน
