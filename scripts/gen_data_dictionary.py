"""
gen_data_dictionary.py - Build docs/guides/data-dictionary.md from the catalog.

Merges the per-endpoint data dictionaries in _spec/fund.json into one
alphabetical field reference, noting which datasets each field appears in.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "_spec" / "fund.json"
OUT = ROOT / "docs" / "guides" / "data-dictionary.md"

DATASET = {
    "getAmcList": "amcs", "getFundProfile": "profiles",
    "getFundSpecification": "specifications", "getMutualfundFee": "mutual_fund_fees",
    "getFundRelative": "involve_parties", "getFactsheetUrl": "fs_urls",
    "getFactsheetIPO": "fs_ipos", "getFactsheetBenchmark": "fs_benchmarks",
    "getFactsheetRedemptionInvestment": "fs_min_amounts",
    "getFactsheetRedemption": "fs_periods", "getFactsheetRiskSpectrum": "fs_risk",
    "getFactsheetStatisticsinfo": "fs_statistics",
    "getFactsheetDividend": "fs_dividend", "getFactsheetFee": "fs_fees",
    "getFactsheetPerformance": "fs_performance",
    "getFactsheetAssetAllocation": "fs_asset_alloc",
    "getFactsheetTop5Holding": "fs_top5", "get-outstanding-port": "out_portfolio",
    "get-outstanding-portassettype": "out_port_asset_type",
    "getFundDailyInfoNAV": "nav", "getFundDailyInfoDividendHistory": "dividend_history",
}

# envelope fields present on every response — documented once, not per field
ENVELOPE = {"message", "page_size", "next_cursor", "items"}


def cell(text) -> str:
    t = str(text or "").strip().replace("|", "\\|")
    t = re.sub(r"\r\n?", "\n", t).replace("\n", "<br>")
    return t or "-"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    fields: dict[str, dict] = {}
    where: defaultdict[str, set] = defaultdict(set)

    for api in spec["apiLists"]:
        ds = DATASET.get(api.get("id"))
        if not ds:
            continue
        for f in (api.get("responses") or {}).get("dataDictionary") or []:
            name = str(f.get("fieldName", "")).replace("items[].", "")
            if not name or name in ENVELOPE:
                continue
            where[name].add(ds)
            desc = (f.get("description") or {})
            th = desc.get("th") or desc.get("en") or ""
            # keep the richest description seen for a field
            if name not in fields or len(th) > len(fields[name]["desc"]):
                fields[name] = {"type": f.get("type", ""), "desc": th}

    enum_fields = {n for n, v in fields.items() if "=" in v["desc"] and "\n" in v["desc"]}

    out = ["---", "title: Data Dictionary", "tags: [guide, reference, data-model]",
           "---", "",
           "# 📖 Data Dictionary — พจนานุกรมข้อมูลรวม",
           "",
           f"รวมทุก field จากทั้ง 21 endpoint ({len(fields)} field ไม่ซ้ำ) "
           "พร้อมระบุว่าปรากฏใน dataset ใดบ้าง", "",
           "**ที่เกี่ยวข้อง:** [[fund-identifiers|Fund Identifiers]] · "
           "[[fund-taxonomy|Fund Taxonomy]] · "
           "[[../api-reference/00-index|API Reference]]", "",
           "---", "", "## โครงสร้าง response ที่ทุก endpoint ใช้ร่วมกัน", "",
           "| Field | Type | คำอธิบาย |", "|---|---|---|",
           "| `message` | string | ข้อความสถานะของการเรียก API |",
           "| `page_size` | number | จำนวนรายการที่ส่งกลับต่อครั้ง |",
           "| `next_cursor` | string | cursor สำหรับหน้าถัดไป (ว่าง = หมดแล้ว) |",
           "| `items` | array&lt;object&gt; | รายการข้อมูลหลัก |", "",
           "> ดู [[pagination|Pagination]] สำหรับวิธีวน cursor", "",
           "---", "",
           "## Field ที่มีชุดรหัสกำหนดไว้ (enum)", "",
           "field เหล่านี้รับเฉพาะค่าที่กำหนด — ดูตารางเต็มที่ "
           "[[fund-taxonomy|Fund Taxonomy]]", ""]

    for name in sorted(enum_fields):
        out.append(f"- `{name}` — ปรากฏใน: "
                   + ", ".join(f"`{d}`" for d in sorted(where[name])))
    out += ["", "---", "", "## Field ทั้งหมด (เรียงตามตัวอักษร)", "",
            "| Field | Type | ปรากฏใน dataset | คำอธิบาย |", "|---|---|---|---|"]

    for name in sorted(fields):
        f = fields[name]
        ds_list = ", ".join(f"`{d}`" for d in sorted(where[name]))
        desc = f["desc"]
        if name in enum_fields:
            desc = desc.split("\n")[0] + " _(ดู [[fund-taxonomy|Taxonomy]])_"
        out.append(f"| `{name}` | {f['type']} | {ds_list} | {cell(desc)} |")

    out += ["", "---", "",
            "## Field ที่ปรากฏในหลาย dataset (คีย์สำหรับ join)", "",
            "| Field | จำนวน dataset |", "|---|---|"]
    for name, ds in sorted(where.items(), key=lambda x: -len(x[1]))[:15]:
        out.append(f"| `{name}` | {len(ds)} |")
    out += ["", "> วิธี join ที่ถูกต้องอยู่ที่ [[fund-identifiers|Fund Identifiers]]", ""]

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {len(fields)} fields, "
          f"{len(enum_fields)} enums")


if __name__ == "__main__":
    main()
