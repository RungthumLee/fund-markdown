"""
gen_policy_notes.py - Create the policy notes that every fund note links to.

Each fund note links to [[<policy_desc>]] ("ตราสารทุน", "ผสม", ...). These are
hub notes: what the category means, what to look at when judging a fund in it,
and the live roster of funds that belong to it.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("gen_policy_notes")
PROC = ROOT / "data" / "processed"
OUT = ROOT / "vault" / "Concepts"
OUT.mkdir(parents=True, exist_ok=True)

# policy -> (english, what it invests in, what to judge it on)
POLICY_INFO = {
    "ตราสารทุน": (
        "Equity fund",
        "ลงทุนในหุ้นเป็นหลัก (โดยทั่วไปไม่น้อยกว่า 80% ของ NAV)",
        ["**Alpha** — ผู้จัดการสร้างผลตอบแทนเหนือดัชนีได้จริงหรือไม่",
         "**Maximum Drawdown** — เคยขาดทุนหนักสุดเท่าไร",
         "**การกระจุกตัว** — 10 อันดับแรกรวมกันกี่ % ของ NAV",
         "**กลุ่มอุตสาหกรรม** — กระจุกในหมวดเดียวหรือไม่ (ดูตารางจาก factsheet)"],
    ),
    "ตราสารหนี้": (
        "Fixed income fund",
        "ลงทุนในพันธบัตรรัฐบาล หุ้นกู้ ตั๋วเงิน และเงินฝาก",
        ["**Duration** — ยิ่งยาวยิ่งไวต่อการเปลี่ยนแปลงดอกเบี้ย",
         "**อันดับความน่าเชื่อถือ** — สัดส่วน Investment Grade vs Non-IG",
         "**จำนวนผู้ออกตราสาร** — กระจายความเสี่ยงเครดิตดีแค่ไหน",
         "**TER** — ค่าธรรมเนียมกินผลตอบแทนสัดส่วนสูงกว่ากองหุ้นมาก"],
    ),
    "ผสม": (
        "Mixed / Allocation fund",
        "ผสมระหว่างหุ้นกับตราสารหนี้ ตามสัดส่วนที่นโยบายกำหนด",
        ["**สัดส่วนหุ้นจริง** — ดูตารางการจัดสรรสินทรัพย์ ไม่ใช่แค่ชื่อกอง",
         "**Sharpe Ratio** — ผลตอบแทนคุ้มความเสี่ยงหรือไม่",
         "**กลุ่ม AIMC** — Conservative / Moderate / Aggressive Allocation",
         "**Beta** — ขยับตามตลาดหุ้นมากน้อยแค่ไหน"],
    ),
    "ทรัพย์สินทางเลือก": (
        "Alternative assets fund",
        "ทองคำ น้ำมัน สินค้าโภคภัณฑ์ อสังหาริมทรัพย์ REIT และโครงสร้างพื้นฐาน",
        ["**สินทรัพย์อ้างอิงที่แท้จริง** — ลงทุนตรง หรือผ่านอนุพันธ์/ETF",
         "**นโยบายป้องกันความเสี่ยงอัตราแลกเปลี่ยน**",
         "**ความผันผวน** — กลุ่มนี้อยู่ระดับความเสี่ยง 8 เป็นส่วนใหญ่",
         "**สภาพคล่อง** — เงื่อนไขการรับซื้อคืนอาจจำกัดกว่ากองทั่วไป"],
    ),
    "อื่น ๆ": (
        "Other",
        "กองที่ไม่เข้าเกณฑ์หมวดหลัก เช่น กองที่มีโครงสร้างเฉพาะ",
        ["**อ่านนโยบายการลงทุนเต็ม** — หมวดนี้ไม่มีลักษณะร่วมที่ชัดเจน",
         "**ลักษณะเฉพาะของโครงการ** ในโน้ตกองทุน"],
    ),
}

FALLBACK = ("Other", "ไม่ระบุประเภทชัดเจน",
            ["อ่านนโยบายการลงทุนในโน้ตกองทุนโดยตรง"])


def safe_name(text) -> str:
    import re
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", str(text or "")).strip()
    return re.sub(r"\s+", " ", s).strip(". ") or "untitled"


def main() -> None:
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))

    by_policy = defaultdict(list)
    for f in funds.values():
        by_policy[f.get("policy") or "อื่น ๆ"].append(f)

    written = 0
    for policy, rows in by_policy.items():
        en, what, judge = POLICY_INFO.get(policy, FALLBACK)

        risks = defaultdict(int)
        styles = defaultdict(int)
        for f in rows:
            risks[str(f.get("risk_spectrum") or "ไม่ระบุ")] += 1
            styles[f.get("management_style") or "ไม่ระบุ"] += 1

        o = ["---", f"title: {policy}",
             f"tags: [concept, policy, policy-hub]",
             f"fund_count: {len(rows)}", "---", "",
             f"# 📊 {policy}", "", f"**{en}**", "", what, "",
             "[[00-home|🏠 Home]] · [[../Indexes/by-policy|ดัชนีตามนโยบาย]] · "
             "[[../Indexes/compare-fees|เทียบค่าธรรมเนียม]]", "",
             f"มีกองทุนในหมวดนี้ **{len(rows):,}** กอง", "",
             "## ดูอะไรเวลาประเมินกองในหมวดนี้", ""]
        o += [f"- {j}" for j in judge]
        o += ["", "## การกระจายตัวในหมวดนี้", "",
              "### ตามระดับความเสี่ยง", "",
              "| ระดับ | จำนวน |", "|---|---|"]
        o += [f"| {k} | {v:,} |" for k, v in sorted(risks.items())]
        o += ["", "### ตามกลยุทธ์การบริหาร", "", "| กลยุทธ์ | จำนวน |", "|---|---|"]
        o += [f"| `{k}` | {v:,} |"
              for k, v in sorted(styles.items(), key=lambda x: -x[1])]
        o += ["", "> ความหมายของรหัสดูที่ [[กลยุทธ์การบริหารกองทุน]]", "",
              "## แนวคิดที่เกี่ยวข้อง", "",
              "- [[ค่าธรรมเนียมกองทุนรวม]]",
              "- [[ระดับความเสี่ยงกองทุนรวม]]",
              "- [[สถิติวัดผลกองทุน]]",
              "- [[ชนิดหน่วยลงทุน Share Class]]", "",
              "## รายชื่อกองทุนในหมวดนี้", "",
              f"ดูรายชื่อทั้ง {len(rows):,} กองพร้อมตารางเทียบที่ "
              "[[../Indexes/by-policy|ดัชนีตามนโยบายการลงทุน]]", "",
              "กองที่มีขนาดพอร์ตกระจุกตัวสูงสุด 15 อันดับในหมวดนี้:", "",
              "| กองทุน | บลจ. | เสี่ยง | 10 อันดับแรก (% NAV) |", "|---|---|---|---|"]

        top = sorted(
            [f for f in rows if (f.get("portfolio") or {}).get("top10_pct_nav")],
            key=lambda f: -(f["portfolio"]["top10_pct_nav"] or 0))[:15]
        for f in top:
            o.append(f"| [[{safe_name(f.get('abbr'))}]] | "
                     f"[[{safe_name(f.get('amc_th') or 'ไม่ระบุ')}]] | "
                     f"{f.get('risk_spectrum') or '-'} | "
                     f"{f['portfolio']['top10_pct_nav']:,.1f} |")
        if not top:
            o.append("| _ไม่มีข้อมูลพอร์ต_ | | | |")
        o.append("")

        (OUT / f"{safe_name(policy)}.md").write_text("\n".join(o), encoding="utf-8")
        written += 1

    LOG.info("wrote %d policy notes: %s", written,
             ", ".join(sorted(by_policy, key=lambda k: -len(by_policy[k]))))


if __name__ == "__main__":
    main()
