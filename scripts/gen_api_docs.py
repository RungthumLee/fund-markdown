"""
gen_api_docs.py - Generate docs/api-reference/*.md from the SEC developer catalog.

Source: _spec/fund.json (machine-readable mirror of the SEC Open API portal).
Output: one markdown page per endpoint + an index, in Thai with English notes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "_spec" / "fund.json"
OUT = ROOT / "docs" / "api-reference"
OUT.mkdir(parents=True, exist_ok=True)

# operation id -> short slug used for filenames & wiki links
SLUG = {
    "getAmcList": "01-amcs",
    "getFundProfile": "02-fund-profiles",
    "getFundSpecification": "03-fund-specifications",
    "getMutualfundFee": "04-mutual-fund-fees",
    "getFundRelative": "05-involve-parties",
    "getFactsheetUrl": "06-factsheet-urls",
    "getFactsheetIPO": "07-factsheet-ipos",
    "getFactsheetBenchmark": "08-factsheet-benchmarks",
    "getFactsheetRedemptionInvestment": "09-subscription-redemption-minimums",
    "getFactsheetRedemption": "10-subscription-redemption-periods",
    "getFactsheetRiskSpectrum": "11-risk-spectrum",
    "getFactsheetStatisticsinfo": "12-statistics",
    "getFactsheetDividend": "13-dividend-policy",
    "getFactsheetFee": "14-factsheet-fees",
    "getFactsheetPerformance": "15-performance",
    "getFactsheetAssetAllocation": "16-asset-allocation",
    "getFactsheetTop5Holding": "17-top5-holdings",
    "get-outstanding-port": "18-outstanding-portfolio",
    "get-outstanding-portassettype": "19-outstanding-portfolio-asset-type",
    "getFundDailyInfoNAV": "20-daily-nav",
    "getFundDailyInfoDividendHistory": "21-dividend-history",
}

GROUP = {
    "01-amcs": "General Info", "02-fund-profiles": "General Info",
    "03-fund-specifications": "General Info", "04-mutual-fund-fees": "General Info",
    "05-involve-parties": "General Info",
    "18-outstanding-portfolio": "Outstanding",
    "19-outstanding-portfolio-asset-type": "Outstanding",
    "20-daily-nav": "Daily Info", "21-dividend-history": "Daily Info",
}

# dataset name in scripts/harvest.py, keyed by slug
HARVEST = {
    "01-amcs": "amcs", "02-fund-profiles": "profiles",
    "03-fund-specifications": "specifications", "04-mutual-fund-fees": "mutual_fund_fees",
    "05-involve-parties": "involve_parties", "06-factsheet-urls": "fs_urls",
    "07-factsheet-ipos": "fs_ipos", "08-factsheet-benchmarks": "fs_benchmarks",
    "09-subscription-redemption-minimums": "fs_min_amounts",
    "10-subscription-redemption-periods": "fs_periods",
    "11-risk-spectrum": "fs_risk", "12-statistics": "fs_statistics",
    "13-dividend-policy": "fs_dividend", "14-factsheet-fees": "fs_fees",
    "15-performance": "fs_performance", "16-asset-allocation": "fs_asset_alloc",
    "17-top5-holdings": "fs_top5", "18-outstanding-portfolio": "out_portfolio",
    "19-outstanding-portfolio-asset-type": "out_port_asset_type",
    "20-daily-nav": "nav", "21-dividend-history": "dividend_history",
}


def clean(text) -> str:
    if not text:
        return ""
    t = str(text).replace("[!NOTE]", "").strip()
    return re.sub(r"\r\n?", "\n", t)


def md_cell(text) -> str:
    """Flatten multi-line text so it survives inside a markdown table cell."""
    t = clean(text).replace("|", "\\|").replace("\n", "<br>")
    return t or "-"


def param_table(params) -> str:
    if not params:
        return "_(ไม่มี)_\n"
    lines = ["| Parameter | Type | Required | คำอธิบาย |", "|---|---|---|---|"]
    for p in params:
        req = "**yes**" if p.get("required") else "no"
        desc = p.get("description") or {}
        lines.append(
            f"| `{p['name']}` | {p.get('type', 'string')} | {req} | "
            f"{md_cell(desc.get('th') or desc.get('en'))} |")
    return "\n".join(lines) + "\n"


def dict_table(dd) -> str:
    if not dd:
        return "_(ไม่มี data dictionary ใน catalog)_\n"
    lines = ["| Field | Type | คำอธิบาย |", "|---|---|---|"]
    for f in dd:
        desc = f.get("description") or {}
        lines.append(
            f"| `{f.get('fieldName')}` | {f.get('type', '')} | "
            f"{md_cell(desc.get('th') or desc.get('en'))} |")
    return "\n".join(lines) + "\n"


def render(api: dict, slug: str) -> str:
    name = api.get("name") or {}
    desc = api.get("description") or {}
    resp = api.get("responses") or {}
    title_th = clean(name.get("th")) or slug
    title_en = clean(name.get("en"))
    method = api.get("method", "GET")
    endpoint = api.get("endpoint", "")
    qp = api.get("queryParameters") or []
    ds = HARVEST.get(slug, "")

    example_params = "&".join(
        f"{p['name']}=<{p['name']}>" for p in qp if p.get("required")) or "page_size=100"

    out = []
    add = out.append

    add("---")
    add(f"title: {title_en or title_th}")
    add(f"operation_id: {api.get('id')}")
    add(f"endpoint: {endpoint}")
    add(f"dataset: {ds}")
    add("tags: [sec-api, fund, api-reference]")
    add("---")
    add("")
    add(f"# {title_th}")
    add("")
    add(f"> **{title_en}**  ")
    add(f"> `{method} {endpoint}`  ")
    add(f"> Operation id: `{api.get('id')}`")
    add("")
    add("[[00-index|← สารบัญ API]] · [[../guides/quickstart|Quickstart]] · "
        "[[../guides/pagination|Pagination]] · "
        "[[../guides/rate-limits-and-errors|Errors]]")
    add("")
    add("## คำอธิบาย")
    add("")
    add(clean(desc.get("th")) or "_ไม่ระบุ_")
    add("")

    if clean(desc.get("noteTh")):
        add("> [!NOTE]")
        add("> " + clean(desc["noteTh"]).replace("\n", "\n> "))
        add("")

    if clean(desc.get("en")):
        add("<details><summary>English description</summary>")
        add("")
        add(clean(desc["en"]))
        add("")
        add("</details>")
        add("")

    add("## Request")
    add("")
    add("```http")
    add(f"{method} https://api.sec.or.th{endpoint}?{example_params}")
    add("Ocp-Apim-Subscription-Key: <SEC_SUBSCRIPTION_KEY>")
    add("Accept: application/json")
    add("```")
    add("")
    add("### Path parameters")
    add("")
    add(param_table(api.get("parameters") or []))
    add("### Query parameters")
    add("")
    add(param_table(qp))
    add("## Response")
    add("")
    add(f"- Status: `{resp.get('statusCode', 200)}`")
    add(f"- Content-Type: `{resp.get('contentType', 'application/json')}`")
    add("")
    add("### Data dictionary")
    add("")
    add(dict_table(resp.get("dataDictionary") or []))

    example = resp.get("dataExample")
    if example:
        txt = example if isinstance(example, str) else json.dumps(
            example, ensure_ascii=False, indent=1)
        if len(txt) > 5000:
            txt = txt[:5000] + "\n... (ตัดทอน)"
        add("### ตัวอย่าง response")
        add("")
        add("```json")
        add(txt)
        add("```")
        add("")

    add("## การใช้งานในโปรเจกต์นี้")
    add("")
    if ds:
        add(f"- Dataset: `data/raw/{ds}.jsonl`")
        add(f"- ดึงข้อมูล: `python scripts/harvest.py {ds}`")
    add("- Client: `scripts/sec_client.py` → `SECClient.paginate()`")
    add("- โครงสร้างข้อมูลรวม: [[../guides/data-dictionary|Data Dictionary]]")
    add("")
    return "\n".join(out)


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    apis = [a for a in spec["apiLists"] if a.get("endpoint")]
    rows = []
    for api in apis:
        slug = SLUG.get(api["id"])
        if not slug:
            print("!! no slug mapped for", api["id"])
            continue
        (OUT / f"{slug}.md").write_text(render(api, slug), encoding="utf-8")
        rows.append((GROUP.get(slug, "Factsheet"), slug, api["method"],
                     api["endpoint"], clean((api.get("name") or {}).get("th")),
                     clean((api.get("name") or {}).get("en"))))

    idx = [
        "---", "title: SEC Fund API Reference", "tags: [sec-api, index]", "---", "",
        "# 📚 SEC Open API — Fund (v2) Reference", "",
        "คู่มืออ้างอิง API ทั้ง **21 endpoints** ของกลุ่ม `fund` จาก "
        "SEC Open Data Developer Portal", "",
        "| | |", "|---|---|",
        "| Base URL | `https://api.sec.or.th` |",
        "| Auth header | `Ocp-Apim-Subscription-Key` |",
        "| Pagination | `page_size` (1–100) + `next_cursor` |",
        "| Portal | https://secopendata.sec.or.th/sec-open-apis |", "",
        "**อ่านก่อนเริ่ม →** [[../guides/quickstart|Quickstart]] · "
        "[[../guides/authentication|Authentication]] · "
        "[[../guides/pagination|Pagination]] · "
        "[[../guides/rate-limits-and-errors|Rate limits & Errors]]", "",
    ]
    for group in ["General Info", "Factsheet", "Outstanding", "Daily Info"]:
        grows = sorted([r for r in rows if r[0] == group], key=lambda r: r[1])
        if not grows:
            continue
        idx += [f"## {group}", "",
                "| # | Endpoint | Method | Path | Dataset |", "|---|---|---|---|---|"]
        for _, slug, method, path, th, en in grows:
            idx.append(f"| {slug.split('-')[0]} | [[{slug}\\|{th or en}]] | "
                       f"`{method}` | `{path}` | `{HARVEST.get(slug, '')}` |")
        idx.append("")
    (OUT / "00-index.md").write_text("\n".join(idx), encoding="utf-8")
    print(f"generated {len(rows)} endpoint pages + index")


if __name__ == "__main__":
    main()
