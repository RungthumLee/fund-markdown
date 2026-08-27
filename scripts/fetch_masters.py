"""
fetch_masters.py - Enrich the master-fund registry from Yahoo Finance and FT.

The two sources are complementary rather than redundant:

  Yahoo (yfinance)  price, YTD/3y/5y return, Morningstar rating, and - the
                    part FT does not publish - sector weightings, top holdings
                    and asset-class split. Complete for ETFs; on UCITS SICAVs
                    it returns an expense ratio of 0.0, meaning "unknown".
  FT tearsheet      ongoing charge (OCF/TER), fund size, domicile, legal
                    structure, named manager, Morningstar category. Covers the
                    non-ETF share classes Yahoo is thin on.

Every master is cached to data/masters/<key>.json, so re-runs only fetch what
is missing. Masters with no ISIN are looked up by name on Yahoo's search.

    python scripts/fetch_masters.py               # all, resumable
    python scripts/fetch_masters.py --limit 25    # smoke test
    python scripts/fetch_masters.py --force       # refetch everything
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import requests  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402
from ft_scraper import fetch as ft_fetch  # noqa: E402

LOG = get_logger("fetch_masters")
PROC = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "masters"
CACHE.mkdir(parents=True, exist_ok=True)

RATE_DELAY = 0.7

YF_FIELDS = [
    "longName", "shortName", "symbol", "exchange", "quoteType", "currency",
    "category", "fundFamily", "legalType", "navPrice", "previousClose",
    "totalAssets", "netExpenseRatio", "annualReportExpenseRatio", "yield",
    "ytdReturn", "threeYearAverageReturn", "fiveYearAverageReturn",
    "beta3Year", "fundInceptionDate", "morningStarOverallRating",
    "morningStarRiskRating", "longBusinessSummary",
]


def yahoo(symbol: str) -> dict | None:
    """Look a fund up on Yahoo by ISIN or ticker."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
    except Exception:
        return None
    if not (info.get("longName") or info.get("shortName")):
        return None

    out = {k: info[k] for k in YF_FIELDS if info.get(k) is not None}
    out["source"] = "yahoo"

    # An expense ratio of exactly 0 is Yahoo's placeholder for "not reported"
    # on SICAV share classes. Dropping it stops the note claiming a free fund.
    for key in ("netExpenseRatio", "annualReportExpenseRatio"):
        if out.get(key) == 0:
            out.pop(key)
    if out.get("longBusinessSummary"):
        out["longBusinessSummary"] = out["longBusinessSummary"][:1500]

    try:
        fd = ticker.funds_data
        sectors = fd.sector_weightings or {}
        if sectors:
            out["sector_weightings"] = {k: round(v * 100, 2)
                                        for k, v in sectors.items() if v}
        holdings = fd.top_holdings
        if holdings is not None and not holdings.empty:
            out["top_holdings"] = [
                {"symbol": str(idx),
                 "name": str(row.get("Name", "")),
                 "percent": round(float(row.get("Holding Percent", 0)) * 100, 2)}
                for idx, row in holdings.head(10).iterrows()
            ]
        classes = fd.asset_classes or {}
        if classes:
            out["asset_classes"] = {k: round(v * 100, 2)
                                    for k, v in classes.items() if v}
    except Exception:
        pass
    return out


def yahoo_search(name: str) -> str | None:
    """Resolve a fund name to a Yahoo symbol when we have no ISIN."""
    try:
        r = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": name[:80], "quotesCount": 6, "newsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        if r.status_code != 200:
            return None
        for q in r.json().get("quotes", []):
            if q.get("quoteType") in ("ETF", "MUTUALFUND") and q.get("symbol"):
                return q["symbol"]
    except Exception:
        return None
    return None


def enrich(entry: dict, session: requests.Session) -> dict:
    key, isin = entry["key"], entry.get("isin")
    rec: dict = {"key": key, "isin": isin,
                 "display_name": entry["display_name"],
                 "feeder_count": entry["feeder_count"]}

    yf_data = None
    if isin:
        yf_data = yahoo(isin)
        time.sleep(RATE_DELAY)
    # Yahoo indexes US-listed ETFs by ticker, not ISIN, so an ISIN alone can
    # miss funds it clearly knows (US92189F7915 -> GDXJ). Always fall back to
    # the name search, not only when the ISIN is absent.
    if not yf_data:
        symbol = yahoo_search(entry["display_name"])
        rec["resolved_symbol"] = symbol
        time.sleep(RATE_DELAY)
        if symbol:
            yf_data = yahoo(symbol)
            time.sleep(RATE_DELAY)
    if yf_data:
        rec["yahoo"] = yf_data

    if isin:
        # FT lists a class under the currency it is priced in; USD alone
        # misses every EUR/GBP-priced share class.
        for cur in ("USD", "EUR", "GBP"):
            ft_data = ft_fetch(isin, cur, session=session)
            if ft_data and (ft_data.get("ongoing_charge")
                            or ft_data.get("fund_size")):
                rec["ft"] = ft_data
                break
            time.sleep(RATE_DELAY)

    rec["has_data"] = bool(rec.get("yahoo") or rec.get("ft"))
    return rec


def main() -> None:
    argv = sys.argv[1:]
    force = "--force" in argv
    retry_empty = "--retry-empty" in argv
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    masters = json.loads((PROC / "master_funds.json").read_text(encoding="utf-8"))
    items = list(masters.values())
    if limit:
        items = items[:limit]

    LOG.info("enriching %d master funds (cached results are skipped)", len(items))
    session = requests.Session()
    t0 = time.time()
    counts = {"cached": 0, "yahoo+ft": 0, "yahoo": 0, "ft": 0, "none": 0}

    for i, entry in enumerate(items, 1):
        safe = entry["key"].replace(":", "_").replace("/", "_")[:80]
        path = CACHE / f"{safe}.json"
        if path.exists() and not force:
            if retry_empty:
                try:
                    old = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    old = {}
                if not old.get("has_data"):
                    pass          # fall through and try again
                else:
                    counts["cached"] += 1
                    continue
            else:
                counts["cached"] += 1
                continue
        try:
            rec = enrich(entry, session)
        except Exception as e:
            LOG.exception("failed on %s: %s", entry["key"], e)
            rec = {"key": entry["key"], "isin": entry.get("isin"),
                   "display_name": entry["display_name"],
                   "feeder_count": entry["feeder_count"],
                   "has_data": False, "error": str(e)[:200]}
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                        encoding="utf-8")

        has_y, has_f = bool(rec.get("yahoo")), bool(rec.get("ft"))
        counts["yahoo+ft" if has_y and has_f else
               "yahoo" if has_y else "ft" if has_f else "none"] += 1
        if i % 25 == 0:
            LOG.info("  %d/%d (%.0fs) %s", i, len(items), time.time() - t0,
                     json.dumps(counts))

    LOG.info("done in %.0fs -> %s", time.time() - t0,
             json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
