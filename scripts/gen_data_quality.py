"""
gen_data_quality.py - Build docs/project/data-quality.md from actual run output.

Everything in the generated page is measured, not hand-written: coverage per
dataset, what the scope filter dropped, factsheet download outcomes, and the
known caveats that the numbers themselves cannot express.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "docs" / "project" / "data-quality.md"

FIELD_LABEL = {
    "risk_spectrum": "ระดับความเสี่ยง",
    "investment_policy": "นโยบายการลงทุน",
    "benchmarks": "ดัชนีชี้วัด",
    "factsheet_fees": "ค่าธรรมเนียม (factsheet)",
    "project_fees": "ค่าธรรมเนียม (โครงการ)",
    "performance": "ผลการดำเนินงาน",
    "statistics": "สถิติเชิงปริมาณ",
    "asset_allocation": "การจัดสรรสินทรัพย์",
    "top5_holdings": "5 อันดับแรกที่ลงทุน",
    "dividend_policy": "นโยบายปันผล",
    "dividend_history": "ประวัติปันผล",
    "nav": "NAV ล่าสุด",
    "involve_parties": "บุคคลที่เกี่ยวข้อง",
    "factsheet_urls": "ลิงก์ factsheet",
    "portfolio": "พอร์ตรายตัว",
    "portfolio_asset_type": "พอร์ตตามประเภทสินทรัพย์",
    "min_amounts": "ยอดซื้อขายขั้นต่ำ",
    "dealing_periods": "ช่วงเวลาซื้อขาย",
}

REASON_LABEL = {
    "term-fund": "Term Fund (`proj_term_flag = Y`)",
    "pvd": "PVD (`proj_retail_type = V`)",
    "not-registered": "ไม่ได้อยู่ในสถานะ Registered",
}


def load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def bar(ratio: float, width: int = 20) -> str:
    filled = round(ratio * width)
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    stats = load(PROC / "stats.json", {})
    excluded = load(PROC / "excluded.json", {})
    manifest = load(ROOT / "data" / "factsheets" / "_manifest.json", {})
    harvest = load(RAW / "_harvest_summary.json", {})
    funds = load(PROC / "funds.json", {})

    total = max(stats.get("funds_in_scope", 0), 1)
    cov = stats.get("coverage", {})

    o = ["---", "title: Data Quality", "tags: [project, data-quality, qa]",
         "---", "", "# 📊 Data Quality Report", "",
         "สร้างอัตโนมัติโดย `scripts/gen_data_quality.py` จากผลการรันจริง", "",
         "[[tasks|Tasks]] · [[issues|Issues]] · [[outstanding|Outstanding]] · "
         "[[validation-report|Validation Report]]", "", "---", "",
         "## 1. ขอบเขตข้อมูล", "", "| รายการ | จำนวน |", "|---|---|",
         f"| กองทุนในขอบเขต | **{stats.get('funds_in_scope', 0):,}** |",
         f"| ชนิดหน่วยลงทุน (share class) | {stats.get('share_classes', 0):,} |",
         f"| บลจ. ที่มีกองทุน | {stats.get('amcs_with_funds', 0)} |",
         f"| กองที่ถูกคัดออก | {stats.get('excluded_total', 0):,} |", "",
         "เกณฑ์คัดกรอง: [[../guides/scope-and-filters|Scope & Filters]]", "",
         "### กองที่ถูกคัดออก แยกตามเหตุผล", "",
         "| เหตุผล | จำนวน |", "|---|---|"]

    for reason, n in sorted(stats.get("excluded_by_reason", {}).items(),
                            key=lambda x: -x[1]):
        o.append(f"| {REASON_LABEL.get(reason, reason)} | {n:,} |")
    o += ["", "รายการเต็มอยู่ที่ `data/processed/excluded.json` "
          "(ตรวจสอบย้อนหลังได้ทุกกอง)", ""]

    # sample of excluded funds
    if excluded:
        o += ["<details><summary>ตัวอย่างกองที่ถูกคัดออก (20 รายการแรก)</summary>", "",
              "| ชื่อย่อ | ชื่อกองทุน | เหตุผล |", "|---|---|---|"]
        for e in list(excluded.values())[:20]:
            name = str(e.get("proj_name_th") or "")[:60]
            o.append(f"| {e.get('proj_abbr_name') or '-'} | {name} | "
                     f"`{e.get('reason')}` |")
        o += ["", "</details>", ""]

    # ---- 2. coverage ----------------------------------------------------
    o += ["---", "", "## 2. ความครบถ้วนของข้อมูล (coverage)", "",
          f"สัดส่วนกองทุนที่มีข้อมูลในแต่ละหมวด จากทั้งหมด {total:,} กอง", "",
          "| หมวดข้อมูล | มีข้อมูล | % | |", "|---|---|---|---|"]
    for key, n in sorted(cov.items(), key=lambda x: -x[1]):
        ratio = n / total
        o.append(f"| {FIELD_LABEL.get(key, key)} | {n:,} | {ratio * 100:.0f}% | "
                 f"`{bar(ratio)}` |")
    o.append("")

    low = [(k, n) for k, n in cov.items() if n / total < 0.9]
    if low:
        o += ["### หมวดที่ coverage ต่ำกว่า 90%", ""]
        for key, n in sorted(low, key=lambda x: x[1]):
            o.append(f"- **{FIELD_LABEL.get(key, key)}** — "
                     f"{n:,}/{total:,} ({n / total * 100:.0f}%) "
                     f"→ ขาด {total - n:,} กอง")
        o += ["", "> [!NOTE]",
              "> coverage ที่ไม่ถึง 100% ส่วนใหญ่**ไม่ใช่ข้อผิดพลาด** — "
              "เป็นเพราะ บลจ. ไม่ได้รายงานข้อมูลนั้นสำหรับกองนั้น",
              "> เช่น กองที่ตั้งไม่ถึง 1 ปีจะไม่มีสถิติผลตอบแทน "
              "และกองตราสารหนี้ไม่ต้องรายงาน Alpha/Beta", ""]

    # ---- 3. harvest -----------------------------------------------------
    if harvest:
        o += ["---", "", "## 3. ปริมาณข้อมูลดิบที่ดึงมา", "",
              "| Dataset | จำนวนแถว |", "|---|---|"]
        for name, n in harvest.items():
            o.append(f"| `{name}` | {n:,} |" if isinstance(n, int)
                     else f"| `{name}` | ⚠️ {n} |")
        o.append("")

    # ---- 4. factsheets --------------------------------------------------
    if manifest:
        counts = Counter(r.get("status", "?") for r in manifest.values())
        ok = counts.get("ok", 0) + counts.get("cached", 0)
        o += ["---", "", "## 4. ผลการดาวน์โหลด Factsheet", "",
              "| สถานะ | จำนวน | ความหมาย |", "|---|---|---|"]
        meaning = {
            "ok": "ดาวน์โหลดสำเร็จ", "cached": "มีไฟล์อยู่แล้ว",
            "no-url": "API ไม่ได้ให้ลิงก์ PDF",
            "not-pdf": "ลิงก์ไม่ได้ชี้ไปไฟล์ PDF (มักเป็นหน้าเว็บ)",
            "too-small": "ไฟล์เล็กผิดปกติ น่าจะเป็นหน้า error",
            "error": "เชื่อมต่อไม่สำเร็จหลังลองซ้ำ", "crash": "ข้อผิดพลาดที่ไม่คาดคิด",
        }
        for status, n in counts.most_common():
            label = meaning.get(status, "HTTP error" if status.startswith("http-")
                                else status)
            o.append(f"| `{status}` | {n:,} | {label} |")
        o += ["", f"**สำเร็จ {ok:,} จาก {len(manifest):,} "
              f"({ok / max(len(manifest), 1) * 100:.0f}%)**", ""]

    # ---- 5. known caveats ----------------------------------------------
    o += ["---", "", "## 5. ข้อจำกัดที่ต้องรู้ก่อนใช้ข้อมูล", "",
          "> [!WARNING] ข้อจำกัดเหล่านี้เป็นเรื่องของ**แหล่งข้อมูล** ไม่ใช่ bug", "",
          "### 5.1 ข้อมูลเป็นภาพ ณ งวด factsheet ล่าสุด ไม่ใช่เรียลไทม์",
          "ค่าธรรมเนียม สถิติ ผลการดำเนินงาน พอร์ต — ทั้งหมดมาจาก factsheet "
          "งวดล่าสุดที่ บลจ. ส่ง (โดยทั่วไปคือสิ้นเดือนก่อนหน้า)", "",
          "### 5.2 NAV ย้อนหลังจำกัด 120 วัน",
          "โน้ตแสดง NAV ล่าสุดเท่านั้น — ดู [[decisions|DEC-002]]", "",
          "### 5.3 พอร์ตรายตัวแสดงเพียง 30 อันดับแรก",
          "กองตราสารหนี้บางกองถือหลักทรัพย์หลายร้อยรายการ "
          "ข้อมูลเต็มอยู่ใน `data/raw/out_portfolio.jsonl`", "",
          "### 5.4 RMF ตรวจจับจากชื่อกองทุน (ชื่อจดทะเบียน)",
          "API ไม่มี flag สำหรับ RMF (`fund_class_tax_incentive_type` มีแค่ "
          "SSF/Thai ESG) — ใช้ชื่อตามกฎหมาย \"เพื่อการเลี้ยงชีพ\" ซึ่งกอง RMF "
          "ต้องใช้ ไม่ใช่ชื่อย่อ — ดู [[outstanding|OUT-001]]", "",
          "### 5.5 รหัสความเสี่ยงมีค่าที่ไม่เป็นมาตรฐาน",
          "API คืนค่า `RS8+` และ `RS81` นอกเหนือจาก `RS1`–`RS8` "
          "โปรเจกต์นี้รวมทั้งสองค่าเป็นระดับ `8+` "
          "และเก็บค่าดิบไว้ที่ field `risk_spectrum_raw`", "",
          "### 5.6 ข้อความยาวถูกตัดที่ 4,000 อักขระ",
          "`investment_policy_desc` บางกองยาวมาก — ข้อความเต็มอยู่ใน "
          "`data/raw/profiles.jsonl`", "",
          "### 5.7 ตัวเลขที่แกะจาก PDF เชื่อถือได้น้อยกว่า API",
          "ค่าใน frontmatter ของโน้ต Factsheet (`nav_per_unit_pdf` ฯลฯ) "
          "มาจาก regex บนข้อความ PDF — ใช้เป็นตัวอ้างอิงคร่าว ๆ เท่านั้น", ""]

    # multi-class stat, computed rather than asserted
    if funds:
        multi = sum(1 for f in funds.values() if f.get("class_count", 1) > 1)
        o += ["---", "", "## 6. ข้อสังเกตจากข้อมูล", "",
              f"- กองที่มีหลาย share class: **{multi:,}** จาก {len(funds):,} "
              f"({multi / max(len(funds), 1) * 100:.0f}%) — "
              "ตัวเลขระดับ class ต้องอ่านแยกตาม class เสมอ "
              "ดู [[../../vault/Concepts/ชนิดหน่วยลงทุน Share Class|Share Class]]"]
        no_risk = sum(1 for f in funds.values() if not f.get("risk_spectrum"))
        if no_risk:
            o.append(f"- กองที่ไม่มีระดับความเสี่ยงจาก API: **{no_risk:,}** กอง")
        no_fs = sum(1 for f in funds.values() if not f.get("factsheet_urls"))
        if no_fs:
            o.append(f"- กองที่ไม่มีลิงก์ factsheet: **{no_fs:,}** กอง")
        o.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(o), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
