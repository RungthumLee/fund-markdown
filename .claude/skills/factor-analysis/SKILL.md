---
name: factor-analysis
description: อธิบายปัจจัยที่กระทบกองทุนไทย — ทั้งเชิงโครงสร้าง (ไวต่ออะไร สองด้าน) และ correlation ที่วัดจริงจาก NAV ย้อนหลัง. Use when a user asks what drives a fund / what affects it / what it moves with / its sensitivity / factor exposure. Strictly descriptive, never a forecast.
---

# factor-analysis

อธิบาย "กองนี้ไวต่อปัจจัยอะไร" 2 มุม — **เชิงโครงสร้าง** (จาก holdings) + **วัดจริง** (correlation)

## ข้อมูลที่อ่าน
1. โน้ตกอง `vault/Funds/<ABBR>.md` → 2 section:
   - **⚖️ ปัจจัยที่กระทบกอง (สองด้าน)** — จาก sector/ประเทศ/โครงสร้าง (qualitative, มี ▲ขึ้น/▼ลง)
   - **📊 เคลื่อนไหวสัมพันธ์กับอะไร (correlation อดีต)** — วัดจาก NAV รายวัน × ปัจจัย (ทอง/น้ำมัน/ดอกเบี้ย/USD/SET/EM)
2. เสริม (ถ้าต้องละเอียด): `data/processed/correlations.json` · `factor_map.json` · `factors.py`

## รูปแบบคำตอบ
- **ไวต่ออะไร (เชิงโครงสร้าง):** ปัจจัยหลัก + **ทั้งสองด้าน** (ขึ้น=โอกาส · ลง=ความเสี่ยง)
- **จริง ๆ เคลื่อนไหวกับอะไร:** correlation ที่วัดได้ + ทิศทาง + ช่วงเวลา + จำนวนวัน
- เทียบสองมุม: ถ้า map บอก "ไวต่อทอง" และ correlation ยืนยัน +0.89 → สอดคล้อง

## กรอบ (บังคับ — docs/project/ideas.md §0, §2.6)
- **ไม่พยากรณ์** ราคา/ผลตอบแทน/ทิศทาง · ไม่มี "จะขึ้น/ลงกี่ %" · ไม่มี confidence
- **สองด้านเสมอ** — ไม่เลือกข้างว่าปัจจัยจะไปทางไหน
- correlation = **อดีตช่วงสั้น** · ไม่ใช่สาเหตุ (correlation ≠ causation) · **ไม่นิ่ง** (พุ่งเข้า 1 ตอนวิกฤต) → ระบุ caveat เสมอ
- ทุกตัวเลขบอกช่วงเวลา + ที่มา
- ห้าม field: `estimated_change` · `confidence_score` · `target` · `signal` (ดูตาราง ideas §2.7)
