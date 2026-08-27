"""
gen_vault.py - Render data/processed/funds.json into an Obsidian vault.

Produces one note per fund and per AMC, a set of index / MOC notes, and concept
notes explaining the domain terms. Every note is cross-linked with [[wikilinks]]
and carries YAML frontmatter so Dataview queries work.

    python scripts/gen_vault.py
    python scripts/gen_vault.py --limit 50
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fees  # noqa: E402
import tagging  # noqa: E402
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("gen_vault")
PROC = ROOT / "data" / "processed"

# entity id -> note filename, filled in by main() from entity_links.json.
# Empty when normalize_entities/gen_entity_notes have not run yet; the holdings
# table then falls back to plain text instead of dangling links.
ENTITY_LINKS: dict[str, str] = {}

# proj_id -> resolved look-through record, from lookthrough.json
LOOKTHROUGH: dict[str, dict] = {}
VAULT = ROOT / "vault"

RETAIL_TYPE = {
    "R": "ผู้ลงทุนทั่วไป", "X": "สถาบัน + รายใหญ่พิเศษ (UI)",
    "V": "กองทุนสำรองเลี้ยงชีพ (PVD)", "B": "ผู้มีเงินลงทุนสูง (HNW)",
    "A": "ผู้ลงทุนที่มิใช่รายย่อย (AI)", "H": "มิใช่รายย่อย + เงินลงทุนสูง",
    "N": "ผู้ลงทุนสถาบัน (II)", "G": "กองทุนพิเศษตอบสนองนโยบายภาครัฐ",
    "F": "กองทุนเสริมสภาพคล่องตลาดตราสารหนี้",
}

MGMT_STYLE = {
    "AM": "Active management", "AN": "Feeder — กองหลัก active",
    "PM": "Passive / index tracking", "PN": "Feeder — กองหลัก passive",
    "IM": "Inverse management", "IN": "Feeder — กองหลัก inverse",
    "LM": "Leveraged management", "LN": "Feeder — กองหลัก leveraged",
    "BH": "Buy-and-hold", "SM": "Enhanced index", "OT": "อื่น ๆ",
}

COUNTRY_FLAG = {
    "1": "เน้นลงทุนต่างประเทศ", "2": "ลงทุนต่างประเทศบางส่วน",
    "3": "ไม่มีความเสี่ยงต่างประเทศ", "4": "มีความเสี่ยงทั้งในและต่างประเทศ",
}

ENTITY_TYPE = {
    "A": "ผู้สอบบัญชี", "U": "ผู้จัดจำหน่าย", "S": "ผู้สนับสนุนการขายและรับซื้อคืน",
    "R": "นายทะเบียนหน่วยลงทุน", "V": "ผู้ดูแลผลประโยชน์", "M": "ที่ปรึกษาการลงทุน",
    "O": "ผู้รับมอบหมายงานจัดการลงทุน", "P": "ผู้ลงทุนรายใหญ่",
    "K": "ผู้ดูแลสภาพคล่อง", "N": "ที่ปรึกษาทางการเงิน", "F": "ผู้จัดการกองทุน",
}

RISK_BUCKET = {
    "1": "1 — ตลาดเงินในประเทศ", "2": "2 — ตลาดเงินต่างประเทศบางส่วน",
    "3": "3 — พันธบัตรรัฐบาล", "4": "4 — ตราสารหนี้ทั่วไป", "5": "5 — ผสม",
    "6": "6 — ตราสารทุน", "7": "7 — หมวดอุตสาหกรรม", "8": "8 — สินทรัพย์ทางเลือก",
    "8+": "8+ — สินทรัพย์ทางเลือกที่กระจุกตัว",
}

DEALING_LABEL = {
    "fund_class_name": "Class", "start_date": "มีผลตั้งแต่", "end_date": "ถึง",
    "minimum_sub_ipo": "ซื้อขั้นต่ำ (IPO)", "minimum_sub_ipo_cur": "สกุล (IPO)",
    "minimum_sub": "ซื้อขั้นต่ำ", "minimum_sub_cur": "สกุล",
    "minimum_sub_unit": "ซื้อขั้นต่ำ (หน่วย)",
    "minimum_redempt": "ขายคืนขั้นต่ำ", "minimum_redempt_cur": "สกุล (ขายคืน)",
    "minimum_redempt_unit": "ขายคืนขั้นต่ำ (หน่วย)",
    "lowbal_val": "ยอดคงเหลือขั้นต่ำ", "lowbal_val_cur": "สกุล (คงเหลือ)",
    "lowbal_unit": "ยอดคงเหลือขั้นต่ำ (หน่วย)",
    "type": "ประเภทรายการ", "period": "ช่วงเวลาทำรายการ",
    "redemp_period_oth": "รายละเอียดเพิ่มเติม",
    "settlement_period": "ระยะเวลารับเงิน",
}

DEALING_TYPE = {"subscription": "การซื้อ (subscription)",
                "redemption": "การขายคืน (redemption)"}

# performance periods, shortest first, then calendar years newest first
PERIOD_ORDER = ["3 months", "6 months", "year to date", "1 year", "3 years",
                "5 years", "10 years", "inception date",
                "2025", "2024", "2023", "2022", "2021", "2020", "2019"]

PERIOD_LABEL = {
    "3 months": "3 เดือน", "6 months": "6 เดือน", "year to date": "YTD",
    "1 year": "1 ปี", "3 years": "3 ปี", "5 years": "5 ปี",
    "10 years": "10 ปี", "inception date": "ตั้งแต่จัดตั้ง",
}

# fund return first, then what it should be judged against
PERF_TYPE_ORDER = ["ผลตอบแทนกองทุนรวม", "ผลตอบแทนตัวชี้วัด",
                   "ค่าเฉลี่ยในกลุ่มเดียวกัน", "ความผันผวนของกองทุนรวม",
                   "ความผันผวนของตัวชี้วัด"]

POLICY_SLUG = {
    "ตราสารทุน": "equity", "ผสม": "mixed", "ตราสารหนี้": "fixed-income",
    "ทรัพย์สินทางเลือก": "alternative", "อื่น ๆ": "other",
}


# ------------------------------------------------------------------ utils

def safe_name(text) -> str:
    """Obsidian-safe filename: strip characters that break links or Windows paths."""
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s).strip(". ")
    return s or "untitled"


def yaml_str(value) -> str:
    if value is None:
        return '""'
    s = str(value).replace('"', "'").replace("\n", " ").strip()
    return f'"{s}"'


def fmt(value, unit: str = "", digits: int = 4) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, (int, float)):
        s = f"{value:,.{digits}f}".rstrip("0").rstrip(".")
        return f"{s}{unit}"
    return str(value)


def pct(value) -> str:
    return "-" if value is None else f"{value:,.2f}%"


def cell(text) -> str:
    t = str(text or "").replace("|", "\\|").replace("\n", " ").strip()
    return t or "-"


def fund_perf_1y(f: dict):
    """1-year return of the fund itself (not the benchmark or peer average)."""
    for p in f.get("performance") or []:
        if (str(p.get("period")) == "1 year"
                and str(p.get("type")) == "ผลตอบแทนกองทุนรวม"
                and p.get("value") is not None):
            return p["value"]
    return None


def fund_latest_nav(f: dict):
    """The most recent NAV row, or None. Used for a sortable frontmatter field."""
    rows = [r for r in f.get("nav") or [] if r.get("date")]
    return max(rows, key=lambda r: r["date"]) if rows else None


def table(headers: list[str], rows: list[list]) -> list[str]:
    if not rows:
        return ["_ไม่มีข้อมูล_", ""]
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(cell(c) for c in r) + " |")
    out.append("")
    return out


# ------------------------------------------------------------- fund note

def fund_tags(f: dict) -> list[str]:
    """Faceted, investor-language tags. The deterministic taxonomy lives in
    scripts/tagging.py; here we add the two orthogonal audience flags and the
    `fund` tag the Dataview screener queries with (`FROM #fund`)."""
    tags = ["fund", "sec-data"]
    tags += tagging.investor_tags(f)
    if f.get("retail_type") in ("A", "B", "H", "N", "X"):
        tags.append("audience/restricted")
    if f.get("retail_type") == "G":
        tags.append("audience/government")
    return tags


def render_fund(f: dict, has_factsheet: bool) -> str:
    abbr = f.get("abbr") or f["proj_id"]
    amc = safe_name(f.get("amc_th") or "ไม่ระบุ")
    risk = str(f.get("risk_spectrum") or "")

    o: list[str] = []
    a = o.append

    # ---- frontmatter
    a("---")
    a(f"title: {yaml_str(abbr)}")
    a(f"proj_id: {f['proj_id']}")
    a(f"regis_id: {yaml_str(f.get('regis_id'))}")
    a(f"abbr: {yaml_str(abbr)}")
    a(f"name_th: {yaml_str(f.get('name_th'))}")
    a(f"name_en: {yaml_str(f.get('name_en'))}")
    a(f"amc: {yaml_str(f.get('amc_th'))}")
    a(f"amc_id: {yaml_str(f.get('amc_id'))}")
    a(f"policy: {yaml_str(f.get('policy'))}")
    a(f"risk_spectrum: {yaml_str(risk) if risk else 'null'}")
    a(f"management_style: {yaml_str(f.get('management_style'))}")
    a(f"retail_type: {yaml_str(f.get('retail_type'))}")
    a(f"invest_country_flag: {yaml_str(f.get('invest_country_flag'))}")
    a(f"init_date: {yaml_str(f.get('init_date'))}")
    a(f"regis_date: {yaml_str(f.get('regis_date'))}")
    a(f"class_count: {f.get('class_count', 1)}")
    a(f"has_factsheet: {str(has_factsheet).lower()}")
    # numeric fields for Dataview: let a reader sort/filter funds by the retail
    # fee, one-year return, latest NAV and fund size without opening each note.
    # ter_retail is the cheapest class an individual can actually buy (fees.py),
    # never the unreachable institutional minimum.
    _ter = fees.retail_ter(f)
    if _ter is not None:
        a(f"ter_retail: {_ter}")
    _p1y = fund_perf_1y(f)
    if _p1y is not None:
        a(f"perf_1y: {_p1y}")
    _nav = fund_latest_nav(f)
    if _nav:
        a(f"nav: {_nav.get('nav_per_unit')}")
        a(f"nav_date: {yaml_str(_nav.get('date'))}")
        if _nav.get("net_asset") is not None:
            a(f"fund_size: {_nav.get('net_asset')}")
    if f.get("portfolio"):
        a(f"holdings_count: {f['portfolio']['total_rows']}")
        a(f"top10_pct_nav: {f['portfolio'].get('top10_pct_nav') or 0}")
    _fs = f.get("factsheet_sections") or {}
    if f.get("_master"):
        a(f"master_fund: {yaml_str(f['_master']['name'])}")
        if f["_master"].get("isin"):
            a(f"master_isin: {yaml_str(f['_master']['isin'])}")
    if _fs.get("peer_group"):
        a(f"peer_group: {yaml_str(_fs['peer_group'])}")
    if _fs.get("managers"):
        a("fund_managers: [" + ", ".join(yaml_str(n) for n in _fs["managers"]) + "]")
    a(f"tags: [{', '.join(fund_tags(f))}]")
    a("---")
    a("")

    # ---- header
    a(f"# {abbr}")
    a("")
    a(f"**{f.get('name_th') or '-'}**  ")
    if f.get("name_en"):
        a(f"_{f['name_en']}_")
    a("")
    a(f"บลจ. [[{amc}]] · นโยบาย [[{safe_name(f.get('policy') or 'อื่น ๆ')}]]"
      + (f" · ความเสี่ยงระดับ **{risk}**" if risk else ""))
    a("")

    nav_line = ""
    if f.get("nav"):
        n0 = f["nav"][0]
        nav_line = f"NAV {fmt(n0.get('nav_per_unit'))} ({n0.get('date')})"
    a("> [!abstract] สรุปย่อ")
    a(f"> - **รหัสโครงการ:** `{f['proj_id']}`")
    a(f"> - **ประเภท:** {f.get('policy') or '-'} · "
      f"{MGMT_STYLE.get(f.get('management_style'), f.get('management_style') or '-')}")
    a(f"> - **ผู้ลงทุน:** {RETAIL_TYPE.get(f.get('retail_type'), '-')}")
    a(f"> - **ต่างประเทศ:** {COUNTRY_FLAG.get(f.get('invest_country_flag'), '-')}")
    a(f"> - **จัดตั้ง:** {f.get('init_date') or '-'} · "
      f"**จดทะเบียน:** {f.get('regis_date') or '-'}")
    a(f"> - **ชนิดหน่วยลงทุน:** {f.get('class_count', 1)} class")
    if nav_line:
        a(f"> - **{nav_line}**")
    a("")

    # ---- 1. general
    a("## 1. ข้อมูลทั่วไป")
    a("")
    o.extend(table(["รายการ", "ค่า"], [
        ["เลขที่โครงการ (proj_id)", f"`{f['proj_id']}`"],
        ["เลขที่จดทะเบียน (regis_id)", f.get("regis_id")],
        ["ชื่อย่อ", abbr],
        ["ชื่อไทย", f.get("name_th")],
        ["ชื่ออังกฤษ", f.get("name_en")],
        ["บลจ.", f"[[{amc}]]"],
        ["สถานะ", f.get("status")],
        ["วันจัดตั้ง", f.get("init_date")],
        ["วันจดทะเบียน", f.get("regis_date")],
        ["ประเภทตามนโยบาย", f.get("policy")],
        ["กลยุทธ์บริหาร",
         f"{f.get('management_style') or '-'} — "
         f"{MGMT_STYLE.get(f.get('management_style'), '-')}"],
        ["ลักษณะโครงการ",
         f"{f.get('retail_type') or '-'} — "
         f"{RETAIL_TYPE.get(f.get('retail_type'), '-')}"],
        ["ความเสี่ยงต่างประเทศ", COUNTRY_FLAG.get(f.get("invest_country_flag"), "-")],
    ]))

    master = f.get("_master")
    if f.get("feeder_master") or master:
        a("### กองทุนหลัก (Feeder Fund)")
        a("")
        a(f"- **กองทุนหลัก:** {f.get('feeder_master') or master['name']}")
        a(f"- **ประเทศ:** {f.get('feeder_country') or '-'}")
        if master:
            if master.get("isin"):
                a(f"- **ISIN กองทุนหลัก:** `{master['isin']}`")
            a(f"- 🌐 **โน้ตกองทุนหลัก:** [[{master['note']}]] — "
              "ค่าธรรมเนียม ขนาดกองทุน sector และหลักทรัพย์ที่ถือจริง")
        a("")
        a("ดูแนวคิดที่ [[Feeder Fund]]")
        a("")

    if f.get("fx_policy"):
        a("### นโยบายป้องกันความเสี่ยงอัตราแลกเปลี่ยน")
        a("")
        a(f["fx_policy"])
        a("")

    # ---- 2. share classes
    a("## 2. ชนิดหน่วยลงทุน (Share Class)")
    a("")
    o.extend(table(["Class", "ISIN", "สิทธิประโยชน์ภาษี", "รายละเอียด"],
                   [[c["name"], c.get("isin"), c.get("tax_incentive") or "-",
                     (c.get("detail") or c.get("description") or "")[:200]]
                    for c in f.get("classes") or []]))

    # ---- 3. investment policy
    a("## 3. นโยบายการลงทุน")
    a("")
    a(f.get("investment_policy") or "_ไม่มีข้อมูลจาก API_")
    a("")
    if f.get("specifications"):
        a("### ลักษณะเฉพาะของโครงการ")
        a("")
        for code, desc in f["specifications"]:
            a(f"- `{code}` {desc}")
        a("")

    # ---- 4. risk
    a("## 4. ความเสี่ยง")
    a("")
    if risk:
        a(f"**ระดับความเสี่ยง: {risk} / 8** — {RISK_BUCKET.get(risk, '')}")
        a("")
        if f.get("risk_desc"):
            a(f"> {f['risk_desc']}")
            a("")
    else:
        a("_ไม่มีข้อมูลระดับความเสี่ยงจาก API_")
        a("")
    a("อ่านเพิ่ม: [[ระดับความเสี่ยงกองทุนรวม]]")
    a("")

    if f.get("statistics"):
        a("### สถิติเชิงปริมาณ")
        a("")
        o.extend(table(
            ["Class", "Sharpe", "Alpha", "Beta", "Max Drawdown",
             "Tracking Error", "Turnover", "FX Hedging"],
            [[s["class"], fmt(s.get("sharpe"), digits=4),
              fmt(s.get("alpha"), digits=4), fmt(s.get("beta"), digits=4),
              pct(s.get("max_drawdown")), fmt(s.get("tracking_error"), digits=4),
              fmt(s.get("turnover"), digits=4), s.get("fx_hedging")]
             for s in f["statistics"]]))
        a("อ่านเพิ่ม: [[สถิติวัดผลกองทุน]]")
        a("")

    # ---- 5. fees
    a("## 5. ค่าธรรมเนียม")
    a("")
    a("ดูคำอธิบายแต่ละประเภทที่ [[ค่าธรรมเนียมกองทุนรวม]]")
    a("")
    # Fees belong to a share class, not to the fund. Collapsing them hides that
    # PRINCIPAL GOPP charges 0.01% to a group class and 2.19% to the retail one.
    rows = fees.fee_rows(f)
    if rows:
        a("### สรุปต่อชนิดหน่วยลงทุน (Share Class)")
        a("")
        spread = fees.ter_spread(f)
        retail = fees.retail_ter(f)
        if spread and spread[1] - spread[0] > 0.01:
            a(f"> [!IMPORTANT] ค่าธรรมเนียมของกองนี้ต่างกันตามชนิดหน่วยลงทุน "
              f"**{spread[0]:.2f}% – {spread[1]:.2f}%**")
            if retail is not None:
                a(f"> อัตราที่ผู้ลงทุนรายย่อยซื้อได้ถูกที่สุดคือ **{retail:.2f}%**")
            if fees.restricted_cheapest(f):
                a("> ชนิดที่ถูกที่สุดเป็น**ชนิดที่รายย่อยซื้อไม่ได้** "
                  "(สถาบัน/กลุ่มบุคคล) จึงไม่ถูกนำไปใช้จัดอันดับ")
            a("")
        if any(fees.is_suspect(r) for r in rows):
            a("> [!WARNING] ⚠️ บางชนิดรายงาน **ค่าธรรมเนียมรวมที่เก็บจริง "
              "ต่ำกว่าค่าธรรมเนียมการจัดการที่เก็บจริง** ซึ่งเป็นไปไม่ได้")
            a("> ตัวเลขเหล่านั้นไม่ถูกนำไปเทียบกับกองอื่น")
            a("")
        if any(fees.is_incomplete(r) for r in rows):
            a("> [!NOTE] ℹ️ บางชนิดรายงานค่าธรรมเนียมรวมไว้ "
              "แต่**ไม่ได้รายงานค่าธรรมเนียมการจัดการที่เก็บจริง**")
            a("> อาจเป็นเพราะยกเว้นค่าธรรมเนียมจริง หรือรายงานไม่เต็มรอบปี "
              "— ข้อมูลจาก ก.ล.ต. แยกสองกรณีนี้ไม่ได้")
            a("> ตัวเลขยังถูกนำไปเทียบ แต่ควรอ่านคู่กับคอลัมน์เพดาน")
            a("")

        headers = ["ชนิดหน่วยลงทุน", "ซื้อได้โดย", "รวม: เก็บจริง (%)",
                   "รวม: เพดาน (%)", "จัดการ: เก็บจริง (%)",
                   "ขาย (%)", "รับซื้อคืน (%)"]
        body = []
        for r in rows:
            flag = (" ⚠️" if fees.is_suspect(r)
                    else " ℹ️" if fees.is_incomplete(r) else "")
            audience = (f"{fees.AUDIENCE_ICON[r['audience']]} "
                        f"{fees.AUDIENCE_LABEL[r['audience']]}")
            total = fees.charged(r, "total")
            body.append([
                f"`{r['name']}`" + (f"<br><sub>{r['detail']}</sub>"
                                    if r.get("detail") else ""),
                audience,
                (fmt(total) + flag) if total is not None else "—",
                fmt(fees.ceiling(r, "total")),
                fmt(fees.charged(r, "management")),
                fmt(fees.charged(r, "front")),
                fmt(fees.charged(r, "back")),
            ])
        o.extend(table(headers, body))
        a("**เก็บจริง** = อัตราที่เรียกเก็บในรอบที่รายงาน · "
          "**เพดาน** = อัตราสูงสุดที่หนังสือชี้ชวนอนุญาต — "
          "สองค่านี้เทียบกันข้ามกองไม่ได้")
        a("")
        a("อธิบายชนิดหน่วยลงทุนที่ [[ชนิดหน่วยลงทุน Share Class]] · "
          "[[../Indexes/compare-fees|เทียบกับกองอื่นในหมวดเดียวกัน]]")
        a("")

    a("### ตาม Factsheet ล่าสุด (ทุกแถวที่รายงาน)")
    a("")
    o.extend(table(["Class", "ประเภท", "เพดาน (%)", "เก็บจริง (%)"],
                   [[x["class"], x["type"], fmt(x.get("rate")), fmt(x.get("actual"))]
                    for x in f.get("factsheet_fees") or []]))
    a("### ตามหนังสือชี้ชวน (เพดานตามโครงการ)")
    a("")
    o.extend(table(["Class", "ประเภท", "อัตรา", "หน่วย"],
                   [[x["class"], x["type"], fmt(x.get("rate")), x.get("unit")]
                    for x in f.get("project_fees") or []]))

    # ---- 6. performance
    a("## 6. ผลการดำเนินงาน")
    a("")
    perf = f.get("performance") or []
    if perf:
        # The API returns one flat row per (class, metric, period). Pivot it so
        # a fund's return sits next to its benchmark and peer average for the
        # same period - that comparison is the entire point of the numbers.
        by_class = defaultdict(lambda: defaultdict(dict))
        for p in perf:
            by_class[p["class"]][p.get("type")][p.get("period")] = p.get("value")

        for cls, metrics in sorted(by_class.items()):
            a(f"### Class `{cls}`")
            a("")
            periods = [p for p in PERIOD_ORDER
                       if any(p in m for m in metrics.values())]
            periods += sorted({p for m in metrics.values() for p in m
                               if p not in PERIOD_ORDER})
            if not periods:
                continue
            headers = ["รายการ"] + [PERIOD_LABEL.get(p, p) for p in periods]
            rows = []
            for metric in PERF_TYPE_ORDER:
                if metric not in metrics:
                    continue
                rows.append([metric] + [fmt(metrics[metric].get(p), digits=2)
                                        for p in periods])
            for metric in sorted(set(metrics) - set(PERF_TYPE_ORDER)):
                rows.append([metric] + [fmt(metrics[metric].get(p), digits=2)
                                        for p in periods])
            o.extend(table(headers, rows))
        a("> ตัวเลขเป็น % ต่อปี · เทียบ **ผลตอบแทนกองทุนรวม** กับ "
          "**ผลตอบแทนตัวชี้วัด** และ **ค่าเฉลี่ยในกลุ่มเดียวกัน** เสมอ  ")
        a("> ดู [[สถิติวัดผลกองทุน]] · ผลตอบแทนในอดีตไม่รับประกันอนาคต")
        a("")
    else:
        a("_ไม่มีข้อมูลผลการดำเนินงานจาก API_")
        a("")
    if f.get("benchmarks"):
        a("### ดัชนีชี้วัด (Benchmark)")
        a("")
        o.extend(table(["#", "ดัชนีชี้วัด", "หมายเหตุ"],
                       [[b.get("seq"), b["name"], (b.get("remark") or "")[:300]]
                        for b in f["benchmarks"]]))

    # ---- 7. portfolio
    a("## 7. พอร์ตการลงทุน")
    a("")
    if f.get("asset_allocation"):
        a("### การจัดสรรสินทรัพย์ (จาก Factsheet)")
        a("")
        o.extend(table(["สินทรัพย์", "สัดส่วน (%)"],
                       [[x["name"], fmt(x.get("ratio"))]
                        for x in f["asset_allocation"]]))
    if f.get("top5_holdings"):
        a("### 5 อันดับแรกที่ลงทุน")
        a("")
        o.extend(table(["#", "หลักทรัพย์", "สัดส่วน (%)"],
                       [[x.get("seq"), x["name"], fmt(x.get("ratio"))]
                        for x in f["top5_holdings"]]))
    pat = f.get("portfolio_asset_type")
    if pat:
        a(f"### สัดส่วนตามประเภทสินทรัพย์ (งวด {pat['period']})")
        a("")
        o.extend(table(["รหัส", "ประเภทสินทรัพย์", "มูลค่าตลาด", "% NAV"],
                       [[x.get("code"), x["name"], fmt(x.get("market_value"), digits=0),
                         fmt(x.get("percent_nav"))] for x in pat["items"][:25]]))
    pf = f.get("portfolio")
    if pf:
        a(f"### รายการลงทุนรายตัวทั้งหมด (งวด {pf['period']} · ณ {pf.get('as_of') or '-'})")
        a("")
        a(f"- จำนวนรายการที่ถือ: **{pf['total_rows']:,}** รายการ "
          f"จากผู้ออก {pf.get('issuer_count', 0):,} ราย")
        if pf.get("net_asset_value"):
            a(f"- มูลค่าทรัพย์สินสุทธิของกองทุน: "
              f"**{fmt(pf['net_asset_value'], digits=0)}** บาท")
        a(f"- น้ำหนัก 10 อันดับแรกรวม: **{fmt(pf.get('top10_pct_nav'), digits=2)}% ของ NAV**"
          + (f" (คิดเป็น {pf['top10_share_of_port']}% ของพอร์ต)"
             if pf.get("top10_share_of_port") is not None else ""))
        a("")
        if (pf.get("top10_pct_nav") or 0) > 100:
            a("> [!NOTE]")
            a("> น้ำหนักรวมเกิน 100% ของ NAV ได้ตามปกติ เพราะตารางนี้แสดง"
              "**ฐานะขั้นต้น** (หน่วยลงทุนกองหลัก + เงินฝาก) ")
            a("> ซึ่งถูกหักกลบด้วยรายการหนี้สินที่มีค่าติดลบในตารางเดียวกัน "
              "ไม่ใช่การใช้ leverage")
            a("")
        # the raw `name` is whatever the AMC's system exported - a ticker, a
        # SEDOL, sometimes the ISIN. Show the resolved entity instead, linked
        # to its note, and keep the raw string beside it so nothing is hidden.
        def security(x: dict) -> str:
            note = ENTITY_LINKS.get(x.get("entity") or "")
            label = x.get("entity_name") or x.get("name") or "-"
            raw = (x.get("name") or "").strip()
            # table() escapes the pipe through cell(); pre-escaping it here
            # produced a double backslash that Obsidian will not resolve
            cell_text = (f"[[../Entities/{note}|{label}]]" if note
                         else str(label))
            if raw and raw.upper() != str(label).upper():
                cell_text += f" <br><sub>`{raw}`</sub>"
            return cell_text

        rows = [[i, security(x), (x.get("issuer") or "")[:40],
                 (x.get("type") or "")[:35], x.get("isin") or "-",
                 fmt(x.get("value"), digits=0), fmt(x.get("percent_nav"))]
                for i, x in enumerate(pf["items"], 1)]
        headers = ["#", "หลักทรัพย์", "ผู้ออก", "ประเภท", "ISIN", "มูลค่า", "% NAV"]
        # long tables are collapsed so the note stays readable when opened
        if len(rows) > 25:
            o.extend(table(headers, rows[:25]))
            a(f"<details><summary>ดูอีก {len(rows) - 25:,} รายการที่เหลือ</summary>")
            a("")
            o.extend(table(headers, rows[25:]))
            a("</details>")
            a("")
        else:
            o.extend(table(headers, rows))
    # A feeder's own filing says "99% units of the master" and stops there.
    # Multiplying through the master's disclosed holdings answers the question
    # the filing cannot: which shares is this money actually in?
    lt = LOOKTHROUGH.get(f.get("proj_id") or "")
    if lt:
        a("### 🔭 ทะลุกองทุนหลัก (Look-through)")
        a("")
        a(f"กองนี้ถือ **{lt['master_name']}** อยู่ **{lt['stake_pct']:.2f}%** ของ NAV "
          "ตารางด้านล่างคูณต่อด้วยสัดส่วนที่กองทุนหลักถือหลักทรัพย์แต่ละตัว")
        a("")
        if lt.get("stake_capped"):
            a(f"> [!WARNING] พอร์ตที่ยื่นกับ ก.ล.ต. ระบุสัดส่วนไว้ "
              f"**{lt['stake_filed_pct']:.2f}%** ซึ่งเกิน 100% ของ NAV")
            a("> การคำนวณด้านล่างจำกัดไว้ที่ 100% เพราะเงินทั้งหมดของกอง "
              "มีได้มากที่สุดคือ 100% ถ้าไม่ใช้ leverage")
            a("")
        a("> [!CAUTION] ตัวเลขนี้เป็น **ขั้นต่ำ** ไม่ใช่สัดส่วนที่แท้จริง")
        a("> ใช้เฉพาะหลักทรัพย์ **10 อันดับแรก** ที่กองทุนหลักเปิดเผย "
          f"รวมกันได้เพียง **{lt['covered_pct']:.2f}%** จาก {lt['stake_pct']:.2f}% "
          "ที่กองถืออยู่")
        a("> ส่วนที่เหลืออยู่ในหลักทรัพย์ที่ไม่ได้เปิดเผยรายตัว "
          "และวันอ้างอิงของสองฝั่งไม่ตรงกัน")
        a("> อ่าน [[Look-through การถือทางอ้อม|ข้อจำกัดฉบับเต็ม]] ก่อนใช้ตัดสินใจ")
        a("")
        rows = []
        for i, e in enumerate(lt["exposures"], 1):
            note = ENTITY_LINKS.get(e.get("entity") or "")
            label = (f"[[../Entities/{note}|{e['name']}]]" if note
                     else e["name"])
            rows.append([i, label, e.get("symbol") or "-",
                         fmt(e["pct_of_master"]), fmt(e["pct_of_fund"])])
        o.extend(table(["#", "หลักทรัพย์", "Symbol",
                        "% ของกองทุนหลัก", "~% ของกองนี้"], rows))
        a("[[../Indexes/by-lookthrough|ดัชนีการถือทางอ้อมทั้งหมด]] · "
          "[[ค่าธรรมเนียมสองชั้นของ Feeder Fund]]")
        a("")

    if not any([f.get("asset_allocation"), f.get("top5_holdings"), pat, pf]):
        a("_ไม่มีข้อมูลพอร์ตการลงทุนจาก API_")
        a("")

    # ---- breakdowns that only exist in the factsheet PDF ----------------
    fs = f.get("factsheet_sections") or {}
    fs_blocks = [
        ("sectors", "การจัดสรรการลงทุนในกลุ่มอุตสาหกรรม", "กลุ่มอุตสาหกรรม"),
        ("countries", "การจัดสรรการลงทุนในต่างประเทศ", "ประเทศ / ภูมิภาค"),
        ("credit_ratings", "การจัดสรรตามอันดับความน่าเชื่อถือ", "อันดับ"),
    ]
    rendered_fs = False
    for key, heading, col in fs_blocks:
        for suffix, note in (("", ""), ("_master", " (ของกองทุนหลัก)")):
            rows = fs.get(key + suffix)
            if not rows:
                continue
            if not rendered_fs:
                a("### ข้อมูลเพิ่มเติมจาก Factsheet")
                a("")
                a("ส่วนนี้ไม่มีใน API — แกะจากตารางใน Factsheet PDF")
                a("")
                rendered_fs = True
            a(f"**{heading}{note}**")
            a("")
            o.extend(table([col, "% NAV"],
                           [[r["name"], fmt(r["percent"], digits=2)] for r in rows]))
    if fs.get("top_holdings_master"):
        if not rendered_fs:
            a("### ข้อมูลเพิ่มเติมจาก Factsheet")
            a("")
            rendered_fs = True
        a("**ทรัพย์สินที่ลงทุนสูงสุดของกองทุนหลัก (look-through)**")
        a("")
        o.extend(table(["ทรัพย์สิน", "% NAV"],
                       [[r["name"], fmt(r["percent"], digits=2)]
                        for r in fs["top_holdings_master"]]))
    if rendered_fs:
        a(f"> รายละเอียดทั้งหมดดูที่ [[Factsheet - {safe_name(abbr)}]]")
        a("")

    # ---- 8. NAV
    a("## 8. NAV")
    a("")
    if f.get("nav"):
        o.extend(table(["Class", "วันที่", "NAV/หน่วย", "ราคาขาย", "ราคารับซื้อคืน",
                        "มูลค่าทรัพย์สินสุทธิ"],
                       [[n["class"], n["date"], fmt(n.get("nav_per_unit")),
                         fmt(n.get("sell")), fmt(n.get("buy")),
                         fmt(n.get("net_asset"), digits=0)] for n in f["nav"]]))
        a("อ่านเพิ่ม: [[NAV และราคาซื้อขายหน่วยลงทุน]]")
    else:
        a("_ไม่มีข้อมูล NAV ในช่วง 120 วันที่ผ่านมา_")
    a("")

    # ---- 9. dividend
    a("## 9. เงินปันผล")
    a("")
    if f.get("dividend_policy"):
        o.extend(table(["Class", "นโยบายปันผล"],
                       [[d["class"], d.get("policy")]
                        for d in f["dividend_policy"]]))
    if f.get("dividend_history"):
        a("### ประวัติการจ่ายปันผล (20 ครั้งล่าสุด)")
        a("")
        o.extend(table(["Class", "วันปิดสมุด", "วันจ่าย", "บาท/หน่วย"],
                       [[d.get("class"), d.get("book_close"), d.get("pay_date"),
                         fmt(d.get("value"))] for d in f["dividend_history"]]))
    if not f.get("dividend_policy") and not f.get("dividend_history"):
        a("_ไม่มีข้อมูลเงินปันผล_")
        a("")

    # ---- 10. dealing
    a("## 10. การซื้อขายหน่วยลงทุน")
    a("")
    def dealing_table(rows: list[dict], drop: set) -> list[str]:
        """Thai headers, and hide columns where every row is empty."""
        keys = [k for k in (rows[0] or {}) if k not in drop]
        keys = [k for k in keys
                if any(r.get(k) not in (None, "", "-") for r in rows)]
        return table([DEALING_LABEL.get(k, k) for k in keys],
                     [[DEALING_TYPE.get(str(r.get(k)), r.get(k)) for k in keys]
                      for r in rows])

    if f.get("min_amounts"):
        a("### ยอดซื้อขายขั้นต่ำ")
        a("")
        o.extend(dealing_table(f["min_amounts"], {"proj_id", "end_date"}))
    if f.get("dealing_periods"):
        a("### ช่วงเวลาซื้อขายและการชำระเงิน")
        a("")
        o.extend(dealing_table(f["dealing_periods"], {"proj_id", "end_date"}))
    if not f.get("min_amounts") and not f.get("dealing_periods"):
        a("_ไม่มีข้อมูลเงื่อนไขการซื้อขาย_")
        a("")

    # ---- 11. parties
    a("## 11. บุคคลที่เกี่ยวข้อง")
    a("")
    if fs.get("managers"):
        a("### ผู้จัดการกองทุน (จาก Factsheet)")
        a("")
        for name in fs["managers"]:
            a(f"- {name}")
        a("")
    o.extend(table(["บทบาท", "ชื่อ"],
                   [[ENTITY_TYPE.get(p["type"], p["type"]), p.get("name_th")
                     or p.get("name_en")] for p in f.get("involve_parties") or []]))

    # ---- 12. factsheet
    a("## 12. Factsheet")
    a("")
    if has_factsheet:
        a(f"📄 ข้อความที่แกะจาก PDF: [[Factsheet - {safe_name(abbr)}]]")
        a("")
    for u in f.get("factsheet_urls") or []:
        label = f"class `{u['class']}`" + (f" (ณ {u['as_of']})" if u.get("as_of") else "")
        if u.get("pdf"):
            a(f"- {label} — [PDF]({u['pdf']})")
        elif u.get("amc_url"):
            a(f"- {label} — [หน้าเว็บ บลจ.]({u['amc_url']})")
    if not f.get("factsheet_urls"):
        a("_ไม่มีลิงก์ factsheet จาก API_")
    a("")

    # ---- footer
    a("---")
    a("")
    a("## ดูเพิ่ม")
    a("")
    a(f"- กองอื่นของ [[{amc}]]")
    a(f"- กองประเภทเดียวกัน: [[{safe_name(f.get('policy') or 'อื่น ๆ')}]]")
    if risk:
        a(f"- ความเสี่ยงระดับเดียวกัน: [[by-risk|กองความเสี่ยงระดับ {risk}]]")
    if f.get("_master"):
        a(f"- กองทุนหลักที่ลงทุนจริง: [[{f['_master']['note']}]]")
    a("- [[00-home|🏠 Home]] · [[all-funds|รายชื่อกองทุนทั้งหมด]]")
    a("")
    a(f"> ข้อมูลจาก SEC Open API · อัปเดตล่าสุด `{f.get('last_upd_date') or '-'}`")
    a("")
    return "\n".join(o)


# -------------------------------------------------------------- AMC note

def render_amc(amc: dict, funds: list[dict]) -> str:
    name = amc.get("name_th") or amc.get("unique_id")
    o: list[str] = []
    a = o.append
    a("---")
    a(f"title: {yaml_str(name)}")
    a(f"unique_id: {yaml_str(amc.get('unique_id'))}")
    a(f"name_en: {yaml_str(amc.get('name_en'))}")
    a(f"fund_count: {len(funds)}")
    a("tags: [amc, sec-data]")
    a("---")
    a("")
    a(f"# 🏢 {name}")
    a("")
    if amc.get("name_en"):
        a(f"_{amc['name_en']}_")
        a("")
    a(f"**รหัสบริษัท:** `{amc.get('unique_id')}` · "
      f"**จำนวนกองทุนในขอบเขต:** {len(funds)}")
    a("")
    a("[[00-home|🏠 Home]] · [[by-amc|บลจ. ทั้งหมด]]")
    a("")

    by_policy = defaultdict(int)
    by_risk = defaultdict(int)
    for f in funds:
        by_policy[f.get("policy") or "ไม่ระบุ"] += 1
        by_risk[str(f.get("risk_spectrum") or "-")] += 1

    a("## สัดส่วนกองทุน")
    a("")
    o.extend(table(["ประเภทนโยบาย", "จำนวน"],
                   sorted(by_policy.items(), key=lambda x: -x[1])))
    o.extend(table(["ระดับความเสี่ยง", "จำนวน"], sorted(by_risk.items())))

    a("## รายชื่อกองทุน")
    a("")
    o.extend(table(["ชื่อย่อ", "ชื่อกองทุน", "นโยบาย", "ความเสี่ยง", "Class"],
                   [[f"[[{safe_name(f.get('abbr') or f['proj_id'])}]]",
                     f.get("name_th"), f.get("policy"),
                     f.get("risk_spectrum") or "-", f.get("class_count")]
                    for f in sorted(funds, key=lambda x: str(x.get("abbr") or ""))]))
    return "\n".join(o)


# ----------------------------------------------------------- index notes

def render_index(title: str, desc: str, groups: dict[str, list[dict]],
                 tag: str, note_links: dict[str, str] | None = None) -> str:
    o = ["---", f"title: {yaml_str(title)}", f"tags: [index, {tag}]", "---", "",
         f"# {title}", "", desc, "", "[[00-home|🏠 Home]]", "",
         f"**รวม {sum(len(v) for v in groups.values()):,} กองทุน "
         f"ใน {len(groups)} กลุ่ม**", ""]
    for key in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        rows = groups[key]
        heading = (note_links or {}).get(key, key)
        o.append(f"## {heading} ({len(rows)})")
        o.append("")
        o.extend(table(["ชื่อย่อ", "ชื่อกองทุน", "บลจ.", "ความเสี่ยง"],
                       [[f"[[{safe_name(f.get('abbr') or f['proj_id'])}]]",
                         f.get("name_th"),
                         f"[[{safe_name(f.get('amc_th') or 'ไม่ระบุ')}]]",
                         f.get("risk_spectrum") or "-"]
                        for f in sorted(rows, key=lambda x: str(x.get("abbr") or ""))]))
    return "\n".join(o)


# faceted tag browser: top-level facet -> (Thai heading, one-line note)
FACET_LABEL = {
    "asset": ("สินทรัพย์", "ประเภทสินทรัพย์หลักที่กองลงทุน"),
    "use": ("การใช้งาน", "กองนี้เหมาะกับโจทย์แบบไหน"),
    "risk": ("ความเสี่ยง (ภาษาคน)", "แปลระดับ 1–8 เป็นคำที่เข้าใจง่าย"),
    "geo": ("ภูมิภาค", "พื้นที่ลงทุนหลัก (อ่านจากชื่อกอง)"),
    "theme": ("ธีม/หมวด", "ธีมการลงทุน (อ่านจากชื่อกอง — ยังเป็น best-effort)"),
    "style": ("กลยุทธ์บริหาร", "active / passive / ปันผล ฯลฯ"),
    "struct": ("โครงสร้าง", "ลงตรง / feeder"),
    "conc": ("การกระจุกตัว", "จำนวนหลักทรัพย์ที่ถือ (เฉพาะกองหุ้น)"),
    "fx": ("การป้องกันค่าเงิน", "hedge เต็ม/บางส่วน/ไม่ hedge/ตามดุลยพินิจ"),
    "liquidity": ("สภาพคล่อง", "ได้เงินคืนกี่วันทำการหลังขาย"),
    "tax": ("สิทธิภาษี", "RMF / SSF / Thai ESG"),
    "compliance": ("ข้อกำหนดพิเศษ", "ESG / ชารีอะห์ / trigger"),
    "audience": ("กลุ่มผู้ลงทุน", "ข้อจำกัดผู้ซื้อ"),
}


def render_tag_index(scoped: list[dict]) -> str:
    """The faceted tag overview - every tag with its fund count, grouped by
    facet, plus ready-made Dataview queries for the questions people ask."""
    counts: Counter = Counter()
    for f in scoped:
        counts.update(tagging.investor_tags(f))

    by_facet: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for tag, n in counts.items():
        by_facet[tag.split("/")[0]].append((tag, n))

    o = ["---", "title: แท็กทั้งหมด", "tags: [index, tags]", "---", "",
         "# 🏷️ แท็กกองทุน (faceted)", "",
         "[[00-home|🏠 Home]] · [[screener|🔎 Screener]] · [[all-funds|ทั้งหมด]]", "",
         "> [!INFO] แต่ละกองติดแท็กหลายมิติแบบ deterministic (อ่านจากข้อมูล ก.ล.ต.)",
         "> **คลิกแท็ก** เพื่อดูทุกกองที่ติดแท็กนั้น หรือใช้ Dataview ด้านล่าง",
         "> ธีม/ภูมิภาคอ่านจากชื่อกอง จึงเป็น best-effort (LLM จะช่วยขัดในเฟสถัดไป)",
         ""]
    for facet in FACET_LABEL:
        rows = by_facet.get(facet)
        if not rows:
            continue
        title, note = FACET_LABEL[facet]
        o += [f"## {title} · `{facet}`", "", f"_{note}_", ""]
        for tag, n in sorted(rows, key=lambda kv: (-kv[1], kv[0])):
            o.append(f"- #{tag} · **{n}**")
        o.append("")

    # ready-made intent queries - the whole point of the tag layer
    def dv(title, note, query):
        return [f"### {title}", "", note, "", "```dataview", *query, "```", ""]

    o += ["---", "", "## 🔎 คำถามยอดฮิต (Dataview)", "",
          "> ต้องเปิดใน Obsidian ที่ติดตั้งปลั๊กอิน Dataview", ""]
    o += dv("พักเงินระยะสั้น เสี่ยงต่ำ ถอนไว",
            "กองตลาดเงิน/ตราสารหนี้สั้น เรียงตามผลตอบแทน 1 ปี",
            ['TABLE ter_retail AS "TER %", perf_1y AS "1y %", '
             'risk_spectrum AS "เสี่ยง"',
             'FROM #use/park-cash', 'WHERE perf_1y',
             'SORT perf_1y DESC', 'LIMIT 20'])
    o += dv("หุ้นจีน + เทคโนโลยี",
            "กองที่ติดทั้งภูมิภาคจีนและธีมเทคโนโลยี",
            ['TABLE perf_1y AS "1y %", ter_retail AS "TER %", '
             'nav AS "NAV", amc AS "บลจ."',
             'FROM #geo/china AND #theme/technology',
             'SORT perf_1y DESC'])
    o += dv("กองปันผล เสี่ยงปานกลาง",
            "กองที่จ่ายปันผล ความเสี่ยงไม่สูงเกินไป",
            ['TABLE perf_1y AS "1y %", ter_retail AS "TER %", policy AS "นโยบาย"',
             'FROM #use/income', 'WHERE risk_spectrum <= 5',
             'SORT perf_1y DESC', 'LIMIT 20'])
    o += dv("ลดหย่อนภาษี (RMF/SSF/ThaiESG) ค่าธรรมเนียมต่ำ",
            "กองประหยัดภาษี เรียงจากค่าธรรมเนียมถูกสุด",
            ['TABLE ter_retail AS "TER %", perf_1y AS "1y %", policy AS "นโยบาย"',
             'FROM #use/tax-saving', 'WHERE ter_retail',
             'SORT ter_retail ASC', 'LIMIT 25'])
    return "\n".join(o)


# ------------------------------------------------------------------ main

def main() -> None:
    argv = sys.argv[1:]
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    amcs = json.loads((PROC / "amcs.json").read_text(encoding="utf-8"))
    stats = json.loads((PROC / "stats.json").read_text(encoding="utf-8"))

    lt_path = PROC / "lookthrough.json"
    if lt_path.exists():
        LOOKTHROUGH.update(
            json.loads(lt_path.read_text(encoding="utf-8")).get("funds", {}))
        LOG.info("look-through resolved for %d feeder funds", len(LOOKTHROUGH))

    ent_path = PROC / "entity_links.json"
    if ent_path.exists():
        ENTITY_LINKS.update(json.loads(ent_path.read_text(encoding="utf-8")))
        LOG.info("entity notes available for %d holdings", len(ENTITY_LINKS))

    links_path = PROC / "master_links.json"
    master_links = json.loads(links_path.read_text(encoding="utf-8"))         if links_path.exists() else {}
    if master_links:
        LOG.info("master fund links available for %d funds", len(master_links))

    sections_path = PROC / "factsheet_sections.json"
    fs_sections = json.loads(sections_path.read_text(encoding="utf-8"))         if sections_path.exists() else {}
    LOG.info("factsheet sections available for %d funds", len(fs_sections))

    manifest_path = ROOT / "data" / "factsheets" / "_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) \
        if manifest_path.exists() else {}
    have_fs = {p for p, r in manifest.items()
               if r.get("status") in ("ok", "cached")}

    for sub in ("Funds", "AMCs", "Indexes", "Concepts"):
        (VAULT / sub).mkdir(parents=True, exist_ok=True)

    items = list(funds.items())
    if limit:
        items = items[:limit]

    # ---- fund notes, resolving duplicate abbreviations ------------------
    used: dict[str, str] = {}
    written = 0
    for pid, f in items:
        base = safe_name(f.get("abbr") or pid)
        name = base
        if name in used and used[name] != pid:
            name = f"{base} ({pid})"
        used[name] = pid
        f["_note"] = name
        f["factsheet_sections"] = fs_sections.get(pid) or {}
        f["_master"] = master_links.get(pid)
        (VAULT / "Funds" / f"{name}.md").write_text(
            render_fund(f, pid in have_fs), encoding="utf-8")
        written += 1
    LOG.info("wrote %d fund notes", written)

    scoped = [f for _, f in items]

    # ---- AMC notes -----------------------------------------------------
    by_amc = defaultdict(list)
    for f in scoped:
        by_amc[f.get("amc_id")].append(f)
    for amc_id, group in by_amc.items():
        amc = amcs.get(amc_id) or {"unique_id": amc_id,
                                   "name_th": group[0].get("amc_th"),
                                   "name_en": group[0].get("amc_en")}
        (VAULT / "AMCs" / f"{safe_name(amc.get('name_th') or amc_id)}.md").write_text(
            render_amc(amc, group), encoding="utf-8")
    LOG.info("wrote %d AMC notes", len(by_amc))

    # ---- indexes -------------------------------------------------------
    idx = VAULT / "Indexes"

    g_policy = defaultdict(list)
    for f in scoped:
        g_policy[f.get("policy") or "ไม่ระบุ"].append(f)
    (idx / "by-policy.md").write_text(render_index(
        "📊 กองทุนแยกตามนโยบายการลงทุน",
        "จัดกลุ่มตาม `policy_desc` — ดูความหมายที่ "
        "[Fund Taxonomy](../../docs/guides/fund-taxonomy.md)",
        g_policy, "policy"), encoding="utf-8")

    g_risk = defaultdict(list)
    for f in scoped:
        g_risk[str(f.get("risk_spectrum") or "ไม่ระบุ")].append(f)
    (idx / "by-risk.md").write_text(render_index(
        "⚠️ กองทุนแยกตามระดับความเสี่ยง",
        "ระดับ 1 (เสี่ยงต่ำสุด) ถึง 8 (เสี่ยงสูงสุด) — "
        "ดู [[ระดับความเสี่ยงกองทุนรวม]]",
        g_risk, "risk",
        {k: RISK_BUCKET.get(k, k) for k in g_risk}), encoding="utf-8")

    g_style = defaultdict(list)
    for f in scoped:
        g_style[f.get("management_style") or "ไม่ระบุ"].append(f)
    (idx / "by-management-style.md").write_text(render_index(
        "🎯 กองทุนแยกตามกลยุทธ์การบริหาร",
        "Active / Passive / Feeder / Leveraged — ดู [[กลยุทธ์การบริหารกองทุน]]",
        g_style, "style",
        {k: f"`{k}` — {MGMT_STYLE.get(k, k)}" for k in g_style}), encoding="utf-8")

    g_tax = defaultdict(list)
    for f in scoped:
        taxes = {c.get("tax_incentive") for c in f.get("classes") or []}
        taxes = {t for t in taxes if t}
        for t in (taxes or {"ไม่มีสิทธิประโยชน์พิเศษ"}):
            g_tax[t].append(f)
    (idx / "by-tax-incentive.md").write_text(render_index(
        "🧾 กองทุนแยกตามสิทธิประโยชน์ทางภาษี",
        "SSF / Thai ESG — ดู [[สิทธิประโยชน์ทางภาษีของกองทุนรวม]]",
        g_tax, "tax"), encoding="utf-8")

    # AIMC peer group — only available from the factsheet PDF, and the
    # grouping Thai investors actually compare funds within
    g_peer = defaultdict(list)
    for f in scoped:
        peer = ((f.get("factsheet_sections") or {}).get("peer_group") or "").strip()
        if peer:
            g_peer[peer[:80]].append(f)
    if g_peer:
        (idx / "by-peer-group.md").write_text(render_index(
            "🏷️ กองทุนแยกตามกลุ่ม AIMC",
            "กลุ่มกองทุนตามการจัดของสมาคมบริษัทจัดการลงทุน (AIMC) "
            "แกะจาก Factsheet PDF — ข้อมูลนี้ไม่มีใน API\n\n"
            "การเทียบผลตอบแทนควรเทียบภายในกลุ่มเดียวกันเท่านั้น · "
            "ดู [วิธีแกะข้อมูล](../../docs/guides/factsheet-extraction.md)",
            g_peer, "peer-group"), encoding="utf-8")

    # ---- comparison index: cheapest / best-performing per policy ---------
    def ter_of(f: dict):
        """The cheapest total expense an individual can actually be charged.

        Deliberately NOT the minimum across all share classes. 42 funds price
        a group or institutional class far below their retail one - PRINCIPAL
        GOPP charges 0.01% there and 2.19% to a retail buyer - and ranking on
        the unreachable number puts those funds at the top of a cheapest-first
        table they do not belong in. See scripts/fees.py.
        """
        return fees.retail_ter(f)

    def perf_1y(f: dict):
        """1-year return of the fund itself (not the benchmark or peer average)."""
        for p in f.get("performance") or []:
            if (str(p.get("period")) == "1 year"
                    and str(p.get("type")) == "ผลตอบแทนกองทุนรวม"
                    and p.get("value") is not None):
                return p["value"]
        return None

    o = ["---", "title: เปรียบเทียบกองทุน", "tags: [index, compare]", "---", "",
         "# ⚖️ เปรียบเทียบกองทุนในหมวดเดียวกัน", "", "[[00-home|🏠 Home]]", "",
         "เทียบเฉพาะกองที่อยู่ในหมวดนโยบายเดียวกันเท่านั้น "
         "การเทียบข้ามหมวดไม่มีความหมาย", "",
         "> [!WARNING]",
         "> - **TER** = `Total Fee and Expense` ของ**ชนิดหน่วยลงทุนที่ถูกที่สุด "
         "ซึ่งผู้ลงทุนรายย่อยซื้อได้จริง**",
         "> - ชนิดสำหรับผู้ลงทุนสถาบัน/กลุ่มบุคคล **ไม่ถูกนำมาจัดอันดับ** "
         "เพราะบุคคลทั่วไปซื้อไม่ได้ — ดู [[ชนิดหน่วยลงทุน Share Class]]",
         "> - ตัวเลขที่รายงานต่ำกว่าค่าธรรมเนียมการจัดการ (เป็นไปไม่ได้) "
         "ถูกตัดออกจากการเทียบ",
         "> - กองที่ไม่ได้รายงานจะไม่ปรากฏในตาราง",
         "> - ℹ️ = ชนิดนั้นรายงานค่าธรรมเนียมรวมไว้ "
         "แต่ไม่ได้รายงานค่าธรรมเนียมการจัดการที่เก็บจริง "
         "(215 กอง) — อาจยกเว้นจริงหรือรายงานไม่เต็มรอบ",
         "> - **ผลตอบแทน 1 ปี** เป็นข้อมูลย้อนหลัง **ไม่ได้ทำนายอนาคต**",
         "> - ค่าธรรมเนียมต่ำไม่ได้แปลว่าดีกว่าเสมอไป — ดู "
         "[[ค่าธรรมเนียมกองทุนรวม]] และ [[สถิติวัดผลกองทุน]]", ""]

    for policy in sorted(g_policy, key=lambda k: -len(g_policy[k])):
        rows = g_policy[policy]
        with_ter = sorted([(ter_of(f), f) for f in rows if ter_of(f) is not None],
                          key=lambda x: x[0])
        if not with_ter:
            continue
        o.append(f"## {policy} ({len(with_ter)} กองที่รายงาน TER "
                 f"จาก {len(rows)} กอง)")
        o.append("")
        o.append("### ค่าธรรมเนียมรวมต่ำสุด 15 อันดับ (เฉพาะชนิดที่รายย่อยซื้อได้)")
        o.append("")
        def ter_cell(f: dict, ter) -> str:
            """Mark a TER whose class filed no charged management fee."""
            flag = " ℹ️" if any(
                fees.is_incomplete(r) and fees.charged(r, "total") == ter
                for r in fees.fee_rows(f)) else ""
            return fmt(ter, digits=4) + flag

        o.extend(table(["#", "กองทุน", "บลจ.", "TER (%)", "เสี่ยง", "ผลตอบแทน 1 ปี (%)"],
                       [[i, f"[[{f['_note']}|{f.get('abbr')}]]",
                         f"[[{safe_name(f.get('amc_th') or 'ไม่ระบุ')}]]",
                         ter_cell(f, ter), f.get("risk_spectrum") or "-",
                         fmt(perf_1y(f), digits=2)]
                        for i, (ter, f) in enumerate(with_ter[:15], 1)]))
        o.append("### ค่าธรรมเนียมรวมสูงสุด 5 อันดับ")
        o.append("")
        o.extend(table(["กองทุน", "บลจ.", "TER (%)", "เสี่ยง"],
                       [[f"[[{f['_note']}|{f.get('abbr')}]]",
                         f"[[{safe_name(f.get('amc_th') or 'ไม่ระบุ')}]]",
                         fmt(ter, digits=4), f.get("risk_spectrum") or "-"]
                        for ter, f in reversed(with_ter[-5:])]))
    (idx / "compare-fees.md").write_text("\n".join(o), encoding="utf-8")

    # ---- screener: interactive Dataview queries over the frontmatter --------
    # R-01. Every fund note now carries ter_retail / perf_1y / nav / fund_size /
    # top10_pct_nav in its frontmatter, so these queries sort and filter all
    # 2,000+ funds live inside Obsidian - no regeneration needed to re-rank.
    def dv(title: str, note: str, query: list[str]) -> list[str]:
        return [f"### {title}", "", note, "", "```dataview", *query, "```", ""]

    o = ["---", "title: เครื่องมือคัดกรองกองทุน", "tags: [index, screener]",
         "---", "", "# 🔎 เครื่องมือคัดกรองกองทุน (Dataview)", "",
         "[[00-home|🏠 Home]] · [[compare-fees|เทียบค่าธรรมเนียม]] · [[all-funds|ทั้งหมด]]", "",
         "> [!INFO] ตารางในหน้านี้ทำงานเมื่อเปิดใน **Obsidian ที่ติดตั้งปลั๊กอิน "
         "[Dataview](https://github.com/blacksmithgu/obsidian-dataview)** เท่านั้น",
         "> ทุกโน้ตกองทุนมี field พร้อมกรอง: `ter_retail` (ค่าธรรมเนียมรวมของชนิดที่รายย่อยซื้อได้), "
         "`perf_1y`, `risk_spectrum`, `nav`, `fund_size`, `top10_pct_nav`, `policy`, `amc`",
         "",
         "> [!WARNING] `ter_retail` และ `perf_1y` เป็นข้อมูลย้อนหลัง — ค่าธรรมเนียมต่ำ/"
         "ผลตอบแทนสูงในอดีต **ไม่รับประกันอนาคต** และควรเทียบภายในหมวดเดียวกัน", "",
         "> แก้เงื่อนไขเองได้: เปลี่ยน `policy`, ปรับ `LIMIT`, หรือ `SORT ... DESC/ASC`", ""]

    o += dv("ค่าธรรมเนียมรวมต่ำสุด — กองหุ้นไทย",
            "เฉพาะชนิดที่ผู้ลงทุนรายย่อยซื้อได้จริง",
            ['TABLE ter_retail AS "TER %", perf_1y AS "1y %", '
             'risk_spectrum AS "เสี่ยง", amc AS "บลจ."',
             'FROM #fund', 'WHERE policy = "ตราสารทุน" AND ter_retail',
             'SORT ter_retail ASC', 'LIMIT 25'])
    o += dv("ผลตอบแทน 1 ปีสูงสุด (ทุกหมวด)",
            "เรียงตามผลตอบแทนของกองเอง ไม่ใช่ตัวชี้วัด",
            ['TABLE perf_1y AS "1y %", ter_retail AS "TER %", '
             'policy AS "นโยบาย", risk_spectrum AS "เสี่ยง"',
             'FROM #fund', 'WHERE perf_1y', 'SORT perf_1y DESC', 'LIMIT 25'])
    o += dv("ความเสี่ยงต่ำ (ระดับ ≤ 3)",
            "กองความเสี่ยงต่ำ เรียงจากค่าธรรมเนียมถูกสุด",
            ['TABLE risk_spectrum AS "เสี่ยง", ter_retail AS "TER %", '
             'policy AS "นโยบาย", amc AS "บลจ."',
             'FROM #fund', 'WHERE risk_spectrum <= 3',
             'SORT risk_spectrum ASC, ter_retail ASC', 'LIMIT 30'])
    o += dv("กองขนาดใหญ่สุด",
            "ขนาดกอง (มูลค่าทรัพย์สินสุทธิล่าสุด) หน่วยบาท",
            ['TABLE fund_size AS "ขนาด (บาท)", ter_retail AS "TER %", '
             'policy AS "นโยบาย"',
             'FROM #fund', 'WHERE fund_size', 'SORT fund_size DESC', 'LIMIT 25'])
    o += dv("พอร์ตกระจุกตัวสูงสุด",
            "น้ำหนัก 10 อันดับแรกต่อ NAV — ยิ่งสูงยิ่งกระจุก",
            ['TABLE top10_pct_nav AS "Top10 %NAV", '
             'holdings_count AS "จำนวนที่ถือ", policy AS "นโยบาย"',
             'FROM #fund', 'WHERE top10_pct_nav',
             'SORT top10_pct_nav DESC', 'LIMIT 25'])
    o += dv("นับกองทุนแยกตามนโยบาย",
            "ภาพรวมว่ามีกี่กองในแต่ละหมวด",
            ['TABLE length(rows) AS "จำนวนกอง", '
             'round(average(rows.ter_retail), 3) AS "TER เฉลี่ย %"',
             'FROM #fund', 'GROUP BY policy AS "นโยบาย"',
             'SORT length(rows) DESC'])
    (idx / "screener.md").write_text("\n".join(o), encoding="utf-8")

    # faceted tag browser + intent queries
    (idx / "tags.md").write_text(render_tag_index(scoped), encoding="utf-8")

    # by AMC index
    o = ["---", "title: บลจ. ทั้งหมด", "tags: [index, amc]", "---", "",
         "# 🏢 บริษัทจัดการกองทุน (บลจ.)", "", "[[00-home|🏠 Home]]", "",
         f"**{len(by_amc)} บลจ. ที่มีกองทุนในขอบเขต**", ""]
    o.extend(table(["บลจ.", "ชื่ออังกฤษ", "จำนวนกองทุน"],
                   [[f"[[{safe_name((amcs.get(k) or {}).get('name_th') or (g[0].get('amc_th')))}]]",
                     (amcs.get(k) or {}).get("name_en") or g[0].get("amc_en"), len(g)]
                    for k, g in sorted(by_amc.items(), key=lambda x: -len(x[1]))]))
    (idx / "by-amc.md").write_text("\n".join(o), encoding="utf-8")

    # all funds
    o = ["---", "title: รายชื่อกองทุนทั้งหมด", "tags: [index, all]", "---", "",
         "# 📇 รายชื่อกองทุนทั้งหมด", "", "[[00-home|🏠 Home]]", "",
         f"**{len(scoped):,} กองทุน** (Registered · ไม่ใช่ Term fund · ไม่ใช่ PVD)", "",
         "เกณฑ์คัดกรอง: [Scope & Filters](../../docs/guides/scope-and-filters.md)", ""]
    o.extend(table(["ชื่อย่อ", "ชื่อกองทุน", "บลจ.", "นโยบาย", "เสี่ยง", "Class"],
                   [[f"[[{f['_note']}|{f.get('abbr')}]]", f.get("name_th"),
                     f"[[{safe_name(f.get('amc_th') or 'ไม่ระบุ')}]]",
                     f.get("policy"), f.get("risk_spectrum") or "-",
                     f.get("class_count")]
                    for f in sorted(scoped, key=lambda x: str(x.get("abbr") or ""))]))
    (idx / "all-funds.md").write_text("\n".join(o), encoding="utf-8")

    # home / MOC
    cov = stats.get("coverage", {})
    o = ["---", "title: Home", "tags: [moc, home]", "---", "",
         "# 🏠 คลังความรู้กองทุนรวมไทย", "",
         "ฐานความรู้กองทุนรวมไทย สร้างจาก SEC Open Data API v2", "",
         "## 📇 สารบัญ", "",
         "| ดัชนี | คำอธิบาย |", "|---|---|",
         "| [[all-funds]] | รายชื่อกองทุนทั้งหมด |",
         "| [[by-amc]] | แยกตาม บลจ. |",
         "| [[by-policy]] | แยกตามนโยบายการลงทุน |",
         "| [[by-risk]] | แยกตามระดับความเสี่ยง |",
         "| [[by-management-style]] | แยกตามกลยุทธ์การบริหาร |",
         "| [[by-tax-incentive]] | แยกตามสิทธิประโยชน์ภาษี |",
         "| [[by-peer-group]] | แยกตามกลุ่ม AIMC (จาก factsheet) |",
         "| [[master-funds]] | กองทุนหลักต่างประเทศ (Yahoo + FT) |",
         "| [[by-holding]] | เริ่มจากสินทรัพย์ ดูว่ากองไหนถือ |",
         "| [[by-lookthrough]] | ทะลุกองทุนหลักไปถึงหุ้นจริง |",
         "| [[changelog]] | สิ่งที่เปลี่ยนในแต่ละรอบการรัน |",
         "| [[compare-fees]] | เทียบค่าธรรมเนียมในหมวดเดียวกัน |",
         "| [[screener]] | 🔎 คัดกรอง/เรียงกองด้วย Dataview (interactive) |",
         "| [[tags]] | 🏷️ แท็ก faceted + คำถามยอดฮิต (พักเงิน/จีน AI/ปันผล) |",
         "| [[../Factsheets/00-factsheets-index\\|Factsheets]] | ข้อความจาก PDF |",
         "", "## 📚 แนวคิดพื้นฐาน", "",
         "- [[ค่าธรรมเนียมกองทุนรวม]]",
         "- [[ระดับความเสี่ยงกองทุนรวม]]",
         "- [[NAV และราคาซื้อขายหน่วยลงทุน]]",
         "- [[Feeder Fund]]",
         "- [[ค่าธรรมเนียมสองชั้นของ Feeder Fund]]",
         "- [[การรวมชื่อสินทรัพย์]]",
         "- [[Look-through การถือทางอ้อม]]",
         "- [[กลยุทธ์การบริหารกองทุน]]",
         "- [[สถิติวัดผลกองทุน]]",
         "- [[สิทธิประโยชน์ทางภาษีของกองทุนรวม]]",
         "- [[ชนิดหน่วยลงทุน Share Class]]",
         "", "## 📊 ตัวเลขในคลังนี้", "",
         "| รายการ | จำนวน |", "|---|---|",
         f"| กองทุนในขอบเขต | {stats.get('funds_in_scope', 0):,} |",
         f"| ชนิดหน่วยลงทุน (class) | {stats.get('share_classes', 0):,} |",
         f"| บลจ. | {len(by_amc)} |",
         f"| กองที่ถูกคัดออก | {stats.get('excluded_total', 0):,} |",
         "", "### ความครบถ้วนของข้อมูล", "",
         "| ชุดข้อมูล | มีข้อมูล | คิดเป็น |", "|---|---|---|"]
    total = max(stats.get("funds_in_scope", 1), 1)
    for k, v in sorted(cov.items(), key=lambda x: -x[1]):
        o.append(f"| `{k}` | {v:,} | {v / total * 100:.0f}% |")
    o += ["", "## 🔎 ค้นหาแบบ interactive (ต้องติดตั้งปลั๊กอิน Dataview)", "",
          "ทุกโน้ตกองทุนมี frontmatter ครบ จึง query ได้ทันที",
          "คัดลอกโค้ดด้านล่างไปวางในโน้ตใหม่แล้วปรับเงื่อนไขตามต้องการ", "",
          "**กองหุ้นความเสี่ยงสูง เรียงตาม บลจ.**", "", "````",
          "```dataview", "TABLE amc AS \"บลจ.\", risk_spectrum AS \"เสี่ยง\", "
          "management_style AS \"กลยุทธ์\"",
          "FROM #fund", "WHERE policy = \"ตราสารทุน\" AND risk_spectrum >= \"6\"",
          "SORT amc ASC", "```", "````", "",
          "**กอง SSF ทั้งหมด**", "", "````", "```dataview",
          "LIST", "FROM #fund AND #tax/ssf", "SORT file.name ASC", "```", "````", "",
          "**กอง passive ที่ลงทุนต่างประเทศ**", "", "````", "```dataview",
          "TABLE amc, policy", "FROM #fund AND #passive AND #foreign-exposure",
          "SORT amc ASC", "```", "````", "",
          "**นับจำนวนกองต่อ บลจ.**", "", "````", "```dataview",
          "TABLE length(rows) AS \"จำนวนกอง\"", "FROM #fund", "GROUP BY amc",
          "SORT length(rows) DESC", "```", "````", "",
          "> [!NOTE]",
          "> field ที่ query ได้: `proj_id` `abbr` `amc` `policy` `risk_spectrum`",
          "> `management_style` `retail_type` `invest_country_flag` `class_count`",
          "> `init_date` `has_factsheet`",
          "> tag ที่ใช้ได้: `#fund` `#active` `#passive` `#feeder` "
          "`#leveraged-inverse` `#foreign-exposure` `#restricted-investor`",
          "> `#tax/ssf` `#tax/thai-esg` `#tax/rmf` `#policy/*` `#risk/*`", "",
          "## 🛠️ เอกสารโปรเจกต์", "",
          "- [API Reference (21 endpoints)](../../docs/api-reference/00-index.md)",
          "- [Quickstart](../../docs/guides/quickstart.md)",
          "- [Fund Taxonomy](../../docs/guides/fund-taxonomy.md)",
          "- [Task board](../../docs/project/tasks.md)",
          "- [Issue log](../../docs/project/issues.md)", ""]
    (idx / "00-home.md").write_text("\n".join(o), encoding="utf-8")

    LOG.info("vault generated: %d funds, %d AMCs, indexes + home",
             written, len(by_amc))


if __name__ == "__main__":
    main()
