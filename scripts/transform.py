"""
transform.py - Turn data/raw/*.jsonl into one clean record per fund.

Reads every harvested dataset as a stream (some raw files are 150-200 MB),
indexes rows by proj_id, applies the scope filter from
docs/guides/scope-and-filters.md, and writes:

    data/processed/funds.json      one object per in-scope proj_id
    data/processed/amcs.json       AMC directory + fund counts
    data/processed/excluded.json   what was dropped and why
    data/processed/stats.json      coverage / data-quality counters
"""
from __future__ import annotations

import base64
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("transform")
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# Long free-text fields get decoded + truncated so the vault stays readable.
MAX_TEXT = 4000

# Code 903 is a summary row in both outstanding-portfolio datasets:
#   out_portfolio        -> "มูลค่าทรัพย์สินสุทธิ" (always 100% of NAV)
#   out_port_asset_type  -> "รวม = sum(101-599) - sum(601-699)"
# It is a total, not a position, and doubles any weighting that includes it.
PORT_TOTAL_CODE = "903"


# --------------------------------------------------------------- helpers

def iter_jsonl(name: str) -> Iterator[dict]:
    path = RAW / f"{name}.jsonl"
    if not path.exists():
        LOG.warning("missing dataset %s", path.name)
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    LOG.warning("bad json line in %s", name)


def index_by(name: str, key: str = "proj_id",
             keep: set[str] | None = None) -> dict[str, list[dict]]:
    """Group a dataset by key. `keep` optionally whitelists fields."""
    out: dict[str, list[dict]] = defaultdict(list)
    n = 0
    for row in iter_jsonl(name):
        k = row.get(key)
        if not k:
            continue
        if keep:
            row = {f: v for f, v in row.items() if f in keep}
        out[k].append(row)
        n += 1
    LOG.info("indexed %-20s %7d rows -> %5d keys", name, n, len(out))
    return out


def clean_text(value: Any) -> str:
    """Decode base64/HTML blobs that SEC uses for long descriptions."""
    if value in (None, ""):
        return ""
    s = str(value).strip()

    # SEC sometimes base64-encodes long HTML. Detect and decode.
    if len(s) > 40 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", s):
        try:
            decoded = base64.b64decode(s, validate=True).decode("utf-8")
            if decoded.strip():
                s = decoded
        except Exception:
            pass

    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|li|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    if len(s) > MAX_TEXT:
        s = s[:MAX_TEXT].rstrip() + " …(ตัดทอน)"
    return s


def num(value: Any):
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def norm_risk(value: Any) -> str | None:
    """Normalise SEC risk codes to a plain level.

    The API returns 'RS1'..'RS8', plus the odd 'RS8+' and 'RS81'. Anything in
    the 8-and-above family is reported as '8+', which is how SEC presents the
    highest band on a factsheet. The untouched code is kept alongside as
    `risk_spectrum_raw` so the mapping stays auditable.
    """
    if not value:
        return None
    token = str(value).strip().upper().removeprefix("RS")
    if not token:
        return None
    if re.fullmatch(r"[1-8]", token):
        return token
    if token.startswith("8"):
        return "8+"
    return None


def latest_by(rows: list[dict], date_field: str = "start_date") -> list[dict]:
    """Keep only rows belonging to the most recent effective date."""
    dated = [r for r in rows if r.get(date_field)]
    if not dated:
        return rows
    newest = max(str(r[date_field]) for r in dated)
    return [r for r in dated if str(r[date_field]) == newest]


# --------------------------------------------------------------- scope

def is_in_scope(classes: list[dict]) -> tuple[bool, str]:
    """Decide whether a whole project (all its share classes) is kept.

    Rules are documented in docs/guides/scope-and-filters.md
    """
    if not any(c.get("fund_status") == "Registered" for c in classes):
        return False, "not-registered"
    if any(c.get("proj_term_flag") == "Y" for c in classes):
        return False, "term-fund"
    if any(c.get("proj_retail_type") == "V" for c in classes):
        return False, "pvd"
    return True, "in-scope"


# --------------------------------------------------------------- build

PROFILE_KEEP = {
    "unique_id", "comp_name_th", "comp_name_en", "proj_id", "regis_id",
    "proj_name_th", "proj_name_en", "proj_abbr_name", "fund_status",
    "init_date", "regis_date", "cancel_date", "invest_country_flag",
    "proj_retail_type", "proj_term_flag", "proj_term_year", "proj_term_month",
    "proj_term_day", "policy_desc", "investment_policy_desc",
    "management_style", "feederfund_master_fund", "feederfund_country",
    "exchange_rate_protection_policy", "fund_class_name", "fund_class_detail",
    "fund_class_description", "fund_class_tax_incentive_type",
    "fund_class_isin_code", "last_upd_date",
}


def build() -> None:
    # ---- profiles drive everything -------------------------------------
    projects: dict[str, list[dict]] = defaultdict(list)
    for row in iter_jsonl("profiles"):
        row = {k: v for k, v in row.items() if k in PROFILE_KEEP}
        if row.get("proj_id"):
            projects[row["proj_id"]].append(row)
    LOG.info("profiles: %d projects / %d classes",
             len(projects), sum(len(v) for v in projects.values()))

    in_scope, excluded = {}, {}
    for pid, classes in projects.items():
        ok, reason = is_in_scope(classes)
        if ok:
            in_scope[pid] = classes
        else:
            excluded[pid] = {
                "proj_id": pid,
                "proj_abbr_name": classes[0].get("proj_abbr_name"),
                "proj_name_th": classes[0].get("proj_name_th"),
                "comp_name_th": classes[0].get("comp_name_th"),
                "reason": reason,
            }
    LOG.info("scope: %d kept / %d excluded", len(in_scope), len(excluded))

    # ---- side datasets --------------------------------------------------
    specs = index_by("specifications")
    mf_fees = index_by("mutual_fund_fees")
    parties = index_by("involve_parties")
    fs_urls = index_by("fs_urls")
    fs_bench = index_by("fs_benchmarks")
    fs_minamt = index_by("fs_min_amounts")
    fs_periods = index_by("fs_periods")
    fs_risk = index_by("fs_risk")
    fs_stats = index_by("fs_statistics")
    fs_div = index_by("fs_dividend")
    fs_fees = index_by("fs_fees")
    fs_perf = index_by("fs_performance")
    fs_alloc = index_by("fs_asset_alloc")
    fs_top5 = index_by("fs_top5")
    div_hist = index_by("dividend_history")
    port_type = index_by("out_port_asset_type")
    portfolio = index_by("out_portfolio")

    # NAV: keep only the newest row per (proj_id, class)
    nav_latest: dict[str, dict[str, dict]] = defaultdict(dict)
    nav_rows = 0
    for row in iter_jsonl("nav"):
        pid, cls, d = row.get("proj_id"), row.get("fund_class_name") or "main", row.get("nav_date")
        if not pid or not d:
            continue
        nav_rows += 1
        cur = nav_latest[pid].get(cls)
        if cur is None or str(d) > str(cur.get("nav_date")):
            nav_latest[pid][cls] = row
    LOG.info("indexed %-20s %7d rows -> %5d keys", "nav", nav_rows, len(nav_latest))

    # ---- assemble -------------------------------------------------------
    funds = {}
    for pid, classes in in_scope.items():
        base = classes[0]
        class_names = sorted({c.get("fund_class_name") or "main" for c in classes})

        fund = {
            "proj_id": pid,
            "regis_id": base.get("regis_id"),
            "abbr": base.get("proj_abbr_name"),
            "name_th": base.get("proj_name_th"),
            "name_en": base.get("proj_name_en"),
            "amc_id": base.get("unique_id"),
            "amc_th": base.get("comp_name_th"),
            "amc_en": base.get("comp_name_en"),
            "status": base.get("fund_status"),
            "init_date": base.get("init_date"),
            "regis_date": base.get("regis_date"),
            "policy": base.get("policy_desc"),
            "management_style": base.get("management_style"),
            "retail_type": base.get("proj_retail_type"),
            "invest_country_flag": base.get("invest_country_flag"),
            "feeder_master": base.get("feederfund_master_fund"),
            "feeder_country": base.get("feederfund_country"),
            "fx_policy": clean_text(base.get("exchange_rate_protection_policy")),
            "investment_policy": clean_text(base.get("investment_policy_desc")),
            "last_upd_date": base.get("last_upd_date"),
            "class_count": len(class_names),
            "classes": [],
        }

        for c in classes:
            fund["classes"].append({
                "name": c.get("fund_class_name") or "main",
                "detail": clean_text(c.get("fund_class_detail")),
                "description": clean_text(c.get("fund_class_description")),
                "tax_incentive": c.get("fund_class_tax_incentive_type") or "",
                "isin": c.get("fund_class_isin_code"),
            })

        # risk spectrum (project level)
        risk = latest_by(fs_risk.get(pid, []))
        if risk:
            fund["risk_spectrum"] = norm_risk(risk[0].get("risk_spectrum"))
            fund["risk_spectrum_raw"] = risk[0].get("risk_spectrum")
            fund["risk_desc"] = clean_text(risk[0].get("risk_spectrum_desc"))

        # benchmarks
        fund["benchmarks"] = [
            {"seq": r.get("group_seq"),
             "name": clean_text(r.get("benchmark")),
             "remark": clean_text(r.get("benchmark_remark"))[:500]}
            for r in sorted(latest_by(fs_bench.get(pid, [])),
                            key=lambda r: (r.get("group_seq") is None,
                                           r.get("group_seq")))
            if clean_text(r.get("benchmark"))
        ]

        # fees
        fund["factsheet_fees"] = [
            {"class": r.get("fund_class_name") or "main",
             "type": r.get("fee_type_desc"),
             "rate": num(r.get("rate")),
             "actual": num(r.get("actual_value")),
             "note": clean_text(r.get("fee_other_desc"))[:600]}
            for r in latest_by(fs_fees.get(pid, []))
        ]
        fund["project_fees"] = [
            {"class": r.get("fund_class_name") or "main",
             "type": r.get("fee_type_desc"),
             "rate": num(r.get("rate")),
             "unit": r.get("rate_unit"),
             "note": clean_text(r.get("fee_other_desc"))[:600]}
            for r in mf_fees.get(pid, [])
        ]

        # performance
        fund["performance"] = [
            {"class": r.get("fund_class_name") or "main",
             "type": r.get("performance_type_desc"),
             "period": r.get("reference_period"),
             "value": num(r.get("performance_value"))}
            for r in latest_by(fs_perf.get(pid, []))
        ]

        # statistics
        stat_rows = latest_by(fs_stats.get(pid, []))
        fund["statistics"] = [
            {"class": r.get("fund_class_name") or "main",
             "turnover": num(r.get("portfolio_turnover_ratio")),
             "max_drawdown": num(r.get("maximum_drawdown")),
             "sharpe": num(r.get("sharpe_ratio")),
             "beta": num(r.get("beta")),
             "alpha": num(r.get("alpha")),
             "tracking_error": num(r.get("tracking_error")),
             "recovering_period": r.get("recovering_period"),
             "duration": r.get("portfolio_duration_period"),
             "fx_hedging": r.get("fx_hedging")}
            for r in stat_rows
        ]

        # asset allocation + top5
        fund["asset_allocation"] = [
            {"name": clean_text(r.get("asset_name") or r.get("assetliab_desc")),
             "ratio": num(r.get("asset_ratio") or r.get("percent_nav"))}
            for r in latest_by(fs_alloc.get(pid, []))
        ]
        fund["top5_holdings"] = sorted(
            [{"seq": r.get("asset_seq"),
              "name": clean_text(r.get("asset_name")),
              "ratio": num(r.get("asset_ratio"))}
             for r in latest_by(fs_top5.get(pid, []))],
            key=lambda x: (x["seq"] is None, x["seq"]))

        # dividend
        # `dividend_policy` is a Y/N flag, not free text
        div_label = {"Y": "จ่ายเงินปันผล", "N": "ไม่จ่ายเงินปันผล"}
        fund["dividend_policy"] = [
            {"class": r.get("fund_class_name") or "main",
             "pays_dividend": r.get("dividend_policy"),
             "policy": div_label.get(str(r.get("dividend_policy") or "").strip(),
                                     "ไม่ระบุ")}
            for r in latest_by(fs_div.get(pid, []))
        ]
        fund["dividend_history"] = sorted(
            [{"class": r.get("class_abbr_name"),
              "book_close": str(r.get("book_close_date") or "")[:10],
              "pay_date": str(r.get("dividend_date") or "")[:10],
              "value": num(r.get("dividend_value"))}
             for r in div_hist.get(pid, [])],
            key=lambda x: x["pay_date"], reverse=True)[:20]

        # dealing
        fund["min_amounts"] = [
            {k: v for k, v in r.items() if k not in ("last_upd_date", "prospectus_type")}
            for r in latest_by(fs_minamt.get(pid, []))
        ]
        fund["dealing_periods"] = [
            {k: v for k, v in r.items() if k not in ("last_upd_date", "prospectus_type")}
            for r in latest_by(fs_periods.get(pid, []))
        ]

        # parties
        fund["involve_parties"] = [
            {"type": r.get("entity_type"),
             "name_th": clean_text(r.get("entity_name_th")),
             "name_en": clean_text(r.get("entity_name_en"))}
            for r in parties.get(pid, [])
        ]

        # specifications
        fund["specifications"] = sorted({
            (r.get("spec_code"), clean_text(r.get("spec_desc")))
            for r in specs.get(pid, [])
        })

        # NAV
        fund["nav"] = [
            {"class": cls,
             "date": r.get("nav_date"),
             "net_asset": num(r.get("net_asset")),
             "nav_per_unit": num(r.get("last_val")),
             "sell": num(r.get("sell_price")),
             "buy": num(r.get("buy_price"))}
            for cls, r in sorted(nav_latest.get(pid, {}).items())
        ]

        # portfolio by asset type (latest period)
        pt = port_type.get(pid, [])
        if pt:
            newest = max(str(r.get("period") or "") for r in pt)
            pt_rows = [r for r in pt if str(r.get("period")) == newest]
            pt_total = next((r for r in pt_rows
                             if str(r.get("assetliab_code")) == PORT_TOTAL_CODE), None)
            fund["portfolio_asset_type"] = {
                "period": newest,
                "net_asset_value": num((pt_total or {}).get("market_value")),
                "items": sorted(
                    [{"code": r.get("assetliab_code"),
                      "name": clean_text(r.get("assetliab_desc")),
                      "market_value": num(r.get("market_value")),
                      "percent_nav": num(r.get("percent_nav"))}
                     for r in pt_rows
                     if str(r.get("assetliab_code")) != PORT_TOTAL_CODE],
                    key=lambda x: -(x["percent_nav"] or 0)),
            }

        # full portfolio — every holding reported for the latest period
        pf = portfolio.get(pid, [])
        if pf:
            newest = max(str(r.get("period") or "") for r in pf)
            rows = [r for r in pf if str(r.get("period")) == newest]
            # assetliab_id 903 is the fund's own net asset value: a total row
            # printed at 100% of NAV, not a holding. Leaving it in doubled
            # every concentration figure.
            total_row = next((r for r in rows
                              if str(r.get("assetliab_id")) == PORT_TOTAL_CODE), None)
            rows = [r for r in rows
                    if str(r.get("assetliab_id")) != PORT_TOTAL_CODE]
            items = sorted(
                [{"name": clean_text(r.get("issue_code") or r.get("issuer")),
                  "issuer": clean_text(r.get("issuer")),
                  "isin": r.get("isin_code"),
                  "type": clean_text(r.get("assetliab_desc")),
                  "type_code": r.get("assetliab_id"),
                  "value": num(r.get("assetliab_value")),
                  "percent_nav": num(r.get("percent_nav"))}
                 for r in rows],
                key=lambda x: -(x["percent_nav"] or 0))
            weights = [i["percent_nav"] or 0 for i in items]
            total_w = sum(weights)
            fund["portfolio"] = {
                "period": newest,
                "as_of": next((r.get("as_of_date") for r in rows), None),
                "net_asset_value": num((total_row or {}).get("assetliab_value")),
                "total_rows": len(items),
                "issuer_count": len({i["issuer"] for i in items if i["issuer"]}),
                "top10_pct_nav": round(sum(weights[:10]), 2),
                "top10_share_of_port": (round(sum(weights[:10]) / total_w * 100, 1)
                                        if total_w else None),
                "items": items,
            }

        # factsheet urls
        fund["factsheet_urls"] = [
            {"class": r.get("fund_class_name") or "main",
             "amc_url": r.get("amc_url_factsheet"),
             "pdf": r.get("pdf_factsheet"),
             "as_of": r.get("as_of_date")}
            for r in fs_urls.get(pid, [])
            if r.get("pdf_factsheet") or r.get("amc_url_factsheet")
        ]

        funds[pid] = fund

    # ---- AMC directory --------------------------------------------------
    amcs = {}
    for row in iter_jsonl("amcs"):
        amcs[row["unique_id"]] = {
            "unique_id": row["unique_id"],
            "name_th": row.get("comp_name_th"),
            "name_en": row.get("comp_name_en"),
            "fund_count": 0,
            "proj_ids": [],
        }
    for pid, f in funds.items():
        a = amcs.setdefault(f["amc_id"] or "UNKNOWN", {
            "unique_id": f["amc_id"], "name_th": f["amc_th"],
            "name_en": f["amc_en"], "fund_count": 0, "proj_ids": []})
        a["fund_count"] += 1
        a["proj_ids"].append(pid)

    # ---- stats ----------------------------------------------------------
    def cover(field: str) -> int:
        return sum(1 for f in funds.values() if f.get(field))

    stats = {
        "funds_in_scope": len(funds),
        "share_classes": sum(f["class_count"] for f in funds.values()),
        "amcs_with_funds": sum(1 for a in amcs.values() if a["fund_count"]),
        "excluded_total": len(excluded),
        "excluded_by_reason": {
            r: sum(1 for e in excluded.values() if e["reason"] == r)
            for r in {e["reason"] for e in excluded.values()}
        },
        "coverage": {k: cover(k) for k in [
            "risk_spectrum", "investment_policy", "benchmarks", "factsheet_fees",
            "project_fees", "performance", "statistics", "asset_allocation",
            "top5_holdings", "dividend_policy", "dividend_history", "nav",
            "involve_parties", "factsheet_urls", "portfolio",
            "portfolio_asset_type", "min_amounts", "dealing_periods",
        ]},
    }

    (OUT / "funds.json").write_text(
        json.dumps(funds, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "amcs.json").write_text(
        json.dumps(amcs, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "excluded.json").write_text(
        json.dumps(excluded, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.info("wrote %d funds, %d amcs, %d excluded",
             len(funds), len(amcs), len(excluded))
    LOG.info("stats: %s", json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    build()
