"""
gen_master_notes.py - Write one note per foreign master fund into the vault.

Each note carries what the two external sources agree on, plus the list of Thai
feeder funds that route money into it - which is the link the SEC data alone
cannot give you from the other direction. A popular master such as SPDR Gold
Trust sits behind dozens of separate Thai funds; seeing them on one page makes
the real concentration obvious.

    python scripts/gen_master_notes.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fees  # noqa: E402
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("gen_master_notes")
PROC = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "masters"
OUT = ROOT / "vault" / "MasterFunds"
IDX = ROOT / "vault" / "Indexes"

SECTOR_TH = {
    "technology": "เทคโนโลยี", "financial_services": "การเงิน",
    "healthcare": "สุขภาพ", "consumer_cyclical": "สินค้าฟุ่มเฟือย",
    "consumer_defensive": "สินค้าจำเป็น", "communication_services": "สื่อสาร",
    "industrials": "อุตสาหกรรม", "energy": "พลังงาน",
    "basic_materials": "วัตถุดิบ", "realestate": "อสังหาริมทรัพย์",
    "utilities": "สาธารณูปโภค",
}

ASSET_TH = {
    "stockPosition": "หุ้น", "bondPosition": "ตราสารหนี้",
    "cashPosition": "เงินสด", "preferredPosition": "หุ้นบุริมสิทธิ",
    "convertiblePosition": "หุ้นกู้แปลงสภาพ", "otherPosition": "อื่น ๆ",
}

QUOTE_TH = {"ETF": "ETF (จดทะเบียนซื้อขายในตลาด)",
            "MUTUALFUND": "กองทุนรวม (ไม่ได้จดทะเบียนซื้อขาย)"}


def safe_name(text) -> str:
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s).strip(". ")
    return (s or "untitled")[:100]


def yaml_str(value) -> str:
    if value is None:
        return '""'
    return '"' + str(value).replace('"', "'").replace("\n", " ").strip() + '"'


def cell(text) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip() or "-"


def table(headers, rows) -> list[str]:
    if not rows:
        return ["_ไม่มีข้อมูล_", ""]
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]
    out.append("")
    return out


def pct(value, digits: int = 2) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):,.{digits}f}%"
    except (TypeError, ValueError):
        return str(value)


def money(value) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    for unit, div in (("ล้านล้าน", 1e12), ("พันล้าน", 1e9), ("ล้าน", 1e6)):
        if abs(v) >= div:
            return f"{v / div:,.2f} {unit}"
    return f"{v:,.0f}"


def epoch_date(value) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return "-"


def _ocf_num(ocf) -> float | None:
    """Parse an OCF string like '1.95%' into a number for the fee-stacking sum."""
    m = re.search(r"(\d+(?:\.\d+)?)", str(ocf or ""))
    return float(m.group(1)) if m else None


def render(rec: dict, entry: dict, ter_by_pid: dict[str, float] | None = None) -> str:
    ter_by_pid = ter_by_pid or {}
    y = rec.get("yahoo") or {}
    ft = rec.get("ft") or {}
    name = y.get("longName") or ft.get("name") or rec["display_name"]
    isin = rec.get("isin")

    # ongoing charge: FT is the reliable one for non-ETFs
    ocf = ft.get("ongoing_charge")
    if not ocf and y.get("netExpenseRatio") is not None:
        ocf = pct(y["netExpenseRatio"])

    o: list[str] = []
    a = o.append

    a("---")
    a(f"title: {yaml_str(name)}")
    a(f"master_key: {yaml_str(rec['key'])}")
    # omit fields we have no value for, so Dataview filters on presence
    for key, value in (("isin", isin),
                       ("quote_type", y.get("quoteType")),
                       ("category", ft.get("category") or y.get("category")),
                       ("fund_family", y.get("fundFamily")),
                       ("domicile", ft.get("domicile")),
                       ("currency", y.get("currency")),
                       ("ongoing_charge", ocf)):
        if value:
            a(f"{key}: {yaml_str(value)}")
    a(f"feeder_count: {rec['feeder_count']}")
    a(f"has_external_data: {str(bool(rec.get('has_data'))).lower()}")
    tags = ["master-fund", "external-data"]
    if y.get("quoteType") == "ETF":
        tags.append("etf")
    if not rec.get("has_data"):
        tags.append("no-external-data")
    if rec.get("search_facts") or rec.get("search_note"):
        tags.append("web-search")
    a(f"tags: [{', '.join(tags)}]")
    a("---")
    a("")

    a(f"# 🌐 {name}")
    a("")
    if isin:
        a(f"**ISIN:** `{isin}`" + (f" · **Ticker:** `{y['symbol']}`"
                                   if y.get("symbol") else ""))
    a("")
    a(f"กองทุนหลักของกองทุนไทย **{rec['feeder_count']}** กอง · "
      "[[../Indexes/master-funds|ดัชนีกองทุนหลักทั้งหมด]] · "
      "[[../Concepts/Feeder Fund|Feeder Fund คืออะไร]]")
    a("")

    facts = rec.get("search_facts") or {}
    note = rec.get("search_note")
    if not rec.get("has_data"):
        a("> [!WARNING] ไม่พบข้อมูลจากแหล่งภายนอก")
        a("> ทั้ง Yahoo Finance และ FT.com ไม่มีข้อมูลกองนี้ "
          "มักเป็นกอง private / institutional ที่ไม่ได้เสนอขายสาธารณะ")
        if facts or note:
            a("> มีเฉพาะข้อมูลจากการค้นเว็บ ซึ่งอยู่ในหัวข้อแยกด้านล่าง")
        else:
            a("> ข้อมูลด้านล่างจึงมีเฉพาะส่วนที่ได้จาก ก.ล.ต. ไทย")
        a("")

    if facts or note:
        a("## 🔎 ข้อมูลจากการค้นเว็บ (ยังไม่ยืนยัน)")
        a("")
        a("> [!CAUTION] ตัวเลขในหัวข้อนี้ยังไม่ผ่านการยืนยันกับแหล่งข้อมูลตลาด")
        a("> มาจากผลค้นเว็บ ซึ่งมักปน**ตัวเลขข้าม share class** — "
          "กองทุนหลักเป็น share class เฉพาะเจาะจงเสมอ")
        a("> จึงใช้อ่านประกอบเท่านั้น **ไม่ถูกนำไปคิดในตารางเปรียบเทียบใด ๆ**")
        a("")
        if note:
            a(note)
            a("")
        if facts:
            o.extend(table(["รายการ", "ค่าที่ค้นพบ"],
                           [[cell(k), cell(v)] for k, v in facts.items()]))
        for url in rec.get("search_sources") or []:
            a(f"- แหล่ง: {url}")
        a("")

    # ---- profile
    a("## ข้อมูลกองทุน")
    a("")
    rows = [
        ["ชื่อกองทุน", name],
        ["ISIN", f"`{isin}`" if isin else "-"],
        ["ประเภท", QUOTE_TH.get(y.get("quoteType"), y.get("quoteType"))],
        ["โครงสร้างทางกฎหมาย", ft.get("legal_structure") or y.get("legalType")],
        ["ประเทศจดทะเบียน", ft.get("domicile") or ", ".join(entry.get("countries") or [])],
        ["หมวด (Morningstar)", ft.get("category") or y.get("category")],
        ["บริษัทจัดการ", y.get("fundFamily")],
        ["ผู้จัดการกองทุน", ft.get("manager")
         + (f" (เริ่ม {ft['manager_start']})" if ft.get("manager_start") else "")
         if ft.get("manager") else None],
        ["สกุลเงิน", y.get("currency")],
        ["วันจัดตั้ง", epoch_date(y.get("fundInceptionDate"))],
        ["นโยบายปันผล", ft.get("income_treatment")],
        ["สไตล์การลงทุน", ft.get("style_stocks") or ft.get("style_bonds")],
    ]
    o.extend(table(["รายการ", "ค่า"], [r for r in rows if r[1]]))

    # ---- size and cost
    a("## ขนาดกองทุนและค่าธรรมเนียม")
    a("")
    rows = [
        ["ขนาดกองทุน (FT)", ft.get("fund_size")],
        ["ขนาดกองทุน (Yahoo)", money(y.get("totalAssets"))
         + (f" {y.get('currency')}" if y.get("totalAssets") else "")],
        ["**ค่าธรรมเนียมรวมต่อปี (OCF/TER)**", f"**{ocf}**" if ocf else None],
        ["ค่าธรรมเนียมแรกเข้า (initial charge)",
         ft.get("initial_charge") if ft.get("initial_charge") not in ("--", None) else None],
        ["Yield", pct(float(y["yield"]) * 100) if y.get("yield") else None],
    ]
    o.extend(table(["รายการ", "ค่า"], [r for r in rows if r[1] and r[1] != "-"]))
    if ocf:
        a("> [!IMPORTANT]")
        a("> ค่าธรรมเนียมนี้เป็นของ **กองทุนหลัก** ผู้ลงทุนไทยจ่าย"
          "**ซ้อนกับ**ค่าธรรมเนียมของกองไทยอีกชั้น")
        a("> ดู [[../Concepts/ค่าธรรมเนียมกองทุนรวม|ค่าธรรมเนียมกองทุนรวม]]")
        a("")

    # ---- performance
    perf = [
        ["YTD", pct(y.get("ytdReturn"))],
        ["1 ปี (FT)", ft.get("change_1y")],
        ["3 ปี (เฉลี่ยต่อปี)", pct(float(y["threeYearAverageReturn"]) * 100)
         if y.get("threeYearAverageReturn") is not None else None],
        ["5 ปี (เฉลี่ยต่อปี)", pct(float(y["fiveYearAverageReturn"]) * 100)
         if y.get("fiveYearAverageReturn") is not None else None],
        ["Beta (3 ปี)", y.get("beta3Year")],
        ["Morningstar rating", "★" * int(y["morningStarOverallRating"])
         if y.get("morningStarOverallRating") else None],
    ]
    perf = [p for p in perf if p[1] and p[1] != "-"]
    if perf:
        a("## ผลการดำเนินงาน")
        a("")
        o.extend(table(["ช่วงเวลา", "ผลตอบแทน"], perf))
        a("> ตัวเลขจากแหล่งภายนอก อาจคิดคนละสกุลเงินและคนละวันอ้างอิงกับ NAV "
          "ของกองไทย · ผลตอบแทนในอดีตไม่รับประกันอนาคต")
        a("")

    # ---- portfolio look-through
    if y.get("asset_classes"):
        a("## สัดส่วนประเภทสินทรัพย์")
        a("")
        o.extend(table(["ประเภท", "สัดส่วน"],
                       [[ASSET_TH.get(k, k), pct(v)]
                        for k, v in sorted(y["asset_classes"].items(),
                                           key=lambda x: -x[1]) if v]))
    if y.get("sector_weightings"):
        a("## สัดส่วนกลุ่มอุตสาหกรรม")
        a("")
        o.extend(table(["กลุ่มอุตสาหกรรม", "สัดส่วน"],
                       [[SECTOR_TH.get(k, k), pct(v)]
                        for k, v in sorted(y["sector_weightings"].items(),
                                           key=lambda x: -x[1]) if v]))
    if y.get("top_holdings"):
        a("## หลักทรัพย์ที่ถือมากที่สุด")
        a("")
        a("นี่คือ **look-through** ที่แท้จริง — สิ่งที่เงินของผู้ลงทุนไทยไปลงทุนจริง")
        a("")
        o.extend(table(["#", "หลักทรัพย์", "Ticker", "สัดส่วน"],
                       [[i, h["name"], f"`{h['symbol']}`", pct(h["percent"])]
                        for i, h in enumerate(y["top_holdings"], 1)]))

    if y.get("longBusinessSummary"):
        a("## คำอธิบายกองทุน (ต้นฉบับภาษาอังกฤษ)")
        a("")
        a("> " + y["longBusinessSummary"].replace("\n", " ").strip())
        a("")

    # ---- the Thai side
    a("## กองทุนไทยที่ลงทุนในกองนี้")
    a("")
    a(f"**{rec['feeder_count']} กอง** — เรียงตามสัดส่วนที่ถือ")
    a("")
    feeders = sorted(entry["feeders"],
                     key=lambda x: -(x.get("pct_nav") or 0))
    # fee stacking: the Thai fund's own TER PLUS this master's OCF is the true
    # all-in cost, because the master fee is charged inside the master's NAV on
    # top of the Thai fee. See the double-fee concept note.
    master_ocf = _ocf_num(ocf)

    def fee_cells(x: dict) -> list[str]:
        ter = ter_by_pid.get(x.get("proj_id"))
        ter_s = f"{ter:.2f}" if ter is not None else "-"
        if ter is not None and master_ocf is not None:
            combined = f"**≈ {ter + master_ocf:.2f}**"
        else:
            combined = "-"
        return [ter_s, combined]

    o.extend(table(["กองทุนไทย", "บลจ.", "เสี่ยง", "% NAV ที่ถือกองนี้",
                    "TER ไทย (%)", "รวม 2 ชั้น ≈ (%)"],
                   [[f"[[{safe_name(x.get('abbr'))}]]",
                     f"[[{safe_name(x.get('amc_th') or 'ไม่ระบุ')}]]",
                     x.get("risk_spectrum") or "-",
                     pct(x.get("pct_nav")), *fee_cells(x)] for x in feeders]))
    if master_ocf is not None:
        a(f"> **รวม 2 ชั้น** = TER ของกองไทย + OCF ของกองหลัก (**{master_ocf:.2f}%**) "
          "— ค่าธรรมเนียมที่แท้จริงที่ผู้ลงทุนไทยแบกทั้งหมด · "
          "ดู [[../Concepts/ค่าธรรมเนียมสองชั้นของ Feeder Fund|ค่าธรรมเนียมสองชั้น]]")
        a("")
    if rec["feeder_count"] > 1:
        a("> [!NOTE]")
        a(f"> กองไทยทั้ง {rec['feeder_count']} กองนี้ลงทุนในกองทุนหลัก**เดียวกัน** "
          "การถือหลายกองจึงไม่ได้กระจายความเสี่ยงอย่างที่คิด")
        a("")

    # ---- sources
    a("---")
    a("")
    a("## แหล่งข้อมูล")
    a("")
    src = []
    if y:
        src.append(f"- **Yahoo Finance** — โปรไฟล์ ผลตอบแทน sector holdings "
                   f"(symbol `{y.get('symbol', '-')}`)")
    if ft:
        src.append(f"- **FT.com** — ค่าธรรมเนียม ขนาดกองทุน domicile ผู้จัดการ "
                   f"([tearsheet]({ft.get('url')}))")
    if rec.get("isin_from_search"):
        src.append(f"- **ค้นเว็บ** — พบ ISIN `{rec['isin_from_search']}` "
                   "แล้วยืนยันตัวเลขซ้ำกับ FT/Yahoo อีกชั้น")
    elif facts or note:
        src.append("- **ค้นเว็บ** — ข้อมูลเชิงบรรยาย ยังไม่ยืนยัน (ดูหัวข้อ 🔎)")
    src.append("- **ก.ล.ต. ไทย** — รายชื่อกองทุนไทยที่ลงทุนและสัดส่วนที่ถือ")
    o.extend(src)
    a("")
    a("[[../Indexes/00-home|🏠 Home]] · "
      "[วิธีเก็บข้อมูลกองทุนหลัก](../../docs/guides/master-fund-sources.md)")
    a("")
    return "\n".join(o)


def main() -> None:
    masters = json.loads((PROC / "master_funds.json").read_text(encoding="utf-8"))
    # the retail TER of each Thai fund, for the fee-stacking column
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    ter_by_pid = {pid: fees.retail_ter(f) for pid, f in funds.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    IDX.mkdir(parents=True, exist_ok=True)
    # the generator owns this folder outright: stale notes from an earlier run
    # (before domestic masters were routed to their Thai fund note) would
    # otherwise linger as orphans
    for old in OUT.glob("*.md"):
        old.unlink()

    written, with_data, domestic, used = 0, 0, 0, {}
    rows, link_map = [], {}

    for key, entry in masters.items():
        safe = key.replace(":", "_").replace("/", "_")[:80]
        path = CACHE / f"{safe}.json"
        if not path.exists():
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))

        thai = entry.get("thai_master")
        if thai:
            note = safe_name(thai.get("abbr") or thai.get("name_th"))
            for f in entry["feeders"]:
                link_map[f["proj_id"]] = {
                    "note": note,
                    "name": thai.get("name_th") or note,
                    "isin": None, "domestic": True}
            domestic += 1
            continue

        y, ft = rec.get("yahoo") or {}, rec.get("ft") or {}
        name = y.get("longName") or ft.get("name") or rec["display_name"]
        note = safe_name(name)
        if note in used and used[note] != key:
            note = safe_name(f"{name} ({rec.get('isin') or key[-6:]})")
        used[note] = key

        (OUT / f"{note}.md").write_text(
            render(rec, entry, ter_by_pid), encoding="utf-8")
        written += 1
        if rec.get("has_data"):
            with_data += 1
        for f in entry["feeders"]:
            link_map[f["proj_id"]] = {"note": note, "name": name,
                                      "isin": rec.get("isin")}
        rows.append({
            "note": note, "name": name,
            "type": y.get("quoteType") or "-",
            "category": ft.get("category") or y.get("category") or "-",
            "ocf": ft.get("ongoing_charge")
            or (f"{y['netExpenseRatio']:.2f}%" if y.get("netExpenseRatio") else "-"),
            "count": rec["feeder_count"],
            "has_data": bool(rec.get("has_data")),
        })

    # feeder note -> master note, consumed by gen_vault.py
    (PROC / "master_links.json").write_text(
        json.dumps(link_map, ensure_ascii=False, indent=1), encoding="utf-8")

    rows.sort(key=lambda r: -r["count"])
    o = ["---", "title: กองทุนหลัก (Master Funds)", "tags: [index, master-fund]",
         "---", "", "# 🌐 กองทุนหลักของกองทุนไทย (Master Funds)", "",
         "[[00-home|🏠 Home]] · [[../Concepts/Feeder Fund|Feeder Fund]] · "
         "[[../Concepts/ค่าธรรมเนียมสองชั้นของ Feeder Fund|ค่าธรรมเนียมสองชั้น]] · "
         "[วิธีเก็บข้อมูล Yahoo + FT](../../docs/guides/master-fund-sources.md)", "",
         f"กองทุนหลัก **{len(rows):,}** กอง "
         f"(มีข้อมูลจากแหล่งภายนอก {with_data:,} กอง)", "",
         "ข้อมูลรวมจาก **Yahoo Finance** + **FT.com** เชื่อมกับข้อมูล ก.ล.ต. ไทย", "",
         "## กองหลักที่มีกองทุนไทยลงทุนมากที่สุด", "",
         "> [!IMPORTANT]",
         "> กองหลักหนึ่งกองมักมีกองไทยหลายกองป้อนเข้าไป "
         "ถ้าถือกองไทยหลายกองที่ feed เข้ากองหลักเดียวกัน",
         "> เท่ากับถือสินทรัพย์เดิมซ้ำ ไม่ได้กระจายความเสี่ยง", ""]
    def link(r: dict) -> str:
        """Alias only when the display name differs from the note name."""
        label = r["name"][:52]
        return f"[[{r['note']}]]" if label == r["note"] else                f"[[{r['note']}|{label}]]"

    o.extend(table(["กองทุนหลัก", "ประเภท", "หมวด", "OCF", "กองไทยที่ลงทุน"],
                   [[link(r), r["type"], r["category"][:34], r["ocf"], r["count"]]
                    for r in rows if r["count"] > 1]))
    o += ["## กองหลักที่มีกองไทยลงทุนกองเดียว", "",
          f"อีก {sum(1 for r in rows if r['count'] == 1):,} กอง", "",
          "<details><summary>กางรายชื่อ</summary>", ""]
    o.extend(table(["กองทุนหลัก", "ประเภท", "หมวด", "OCF"],
                   [[link(r), r["type"], r["category"][:34], r["ocf"]]
                    for r in rows if r["count"] == 1]))
    o += ["</details>", ""]
    (IDX / "master-funds.md").write_text("\n".join(o), encoding="utf-8")

    LOG.info("wrote %d master notes (%d with external data), "
             "%d feeder links, %d masters are Thai funds already in the vault",
             written, with_data, len(link_map), domestic)


if __name__ == "__main__":
    main()
