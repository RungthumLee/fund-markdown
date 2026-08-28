"""
fetch_sectors.py - Pull sector, industry and market cap for the securities that
Thai funds hold through their foreign masters.

WHY THIS IS A SEPARATE, USER-RUN STEP
-------------------------------------
Sector/industry is not in the SEC feed and not in the Thai factsheets for
foreign holdings; Yahoo has it per ticker. Yahoo must be called from a machine
with normal internet - inside the assistant's sandbox it returns HTTP 429. The
existing master-fund enrichment (fetch_masters.py) already fetches Yahoo the
same way and works on your machine, so run this there:

    python scripts/fetch_sectors.py            # all look-through symbols, resumable
    python scripts/fetch_sectors.py --limit 30 # smoke test
    python scripts/fetch_sectors.py --force     # refetch everything

Input  : data/processed/lookthrough.json - its exposures already carry
         Yahoo-native symbols ("0700.HK", "PDD", "688256.SS").
Cache  : data/sectors/<symbol>.json, one per symbol, so re-runs only fetch what
         is missing (exactly like fetch_masters).
Output : data/processed/security_meta.json  { symbol: {sector, industry,
         market_cap, currency, quote_type, name, country} }

Once it has run, re-run `python scripts/gen_vault.py` (and gen_entity_notes) -
scripts/securities.py picks up security_meta.json and turns it into the
`sector/*` (Yahoo) and `cap/*` (large/mid/small) tags. Until it runs, everything
degrades gracefully: securities.py sees no file and adds nothing.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("fetch_sectors")
PROC = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "sectors"
CACHE.mkdir(parents=True, exist_ok=True)

RATE_DELAY = 0.6


def collect_symbols() -> list[str]:
    """Distinct Yahoo symbols seen in look-through exposures."""
    path = PROC / "lookthrough.json"
    if not path.exists():
        LOG.error("no lookthrough.json - run the pipeline first")
        return []
    lt = json.loads(path.read_text(encoding="utf-8"))
    seen: dict[str, None] = {}
    for rec in (lt.get("funds") or {}).values():
        for ex in rec.get("exposures") or []:
            s = (ex.get("symbol") or "").strip()
            # skip obvious non-equity codes (deposits, blanks); keep tickers
            if s and not s.replace(".", "").replace("-", "").isdigit():
                seen.setdefault(s, None)
    return list(seen)


def yahoo_meta(symbol: str) -> dict | None:
    """Sector / industry / market cap for one ticker via yfinance."""
    import yfinance as yf
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        return None
    sector = info.get("sector")
    industry = info.get("industry")
    mcap = info.get("marketCap")
    if not (sector or industry or mcap):
        return None
    out = {"symbol": symbol}
    if sector:
        out["sector"] = sector
    if industry:
        out["industry"] = industry
    if isinstance(mcap, (int, float)) and mcap > 0:
        out["market_cap"] = mcap
    for k, src in (("currency", "currency"), ("quote_type", "quoteType"),
                   ("name", "longName"), ("country", "country")):
        if info.get(src):
            out[k] = info[src]
    return out


def main() -> None:
    argv = sys.argv[1:]
    force = "--force" in argv
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    symbols = collect_symbols()
    if limit:
        symbols = symbols[:limit]
    LOG.info("fetching sector/market-cap for %d symbols (cached are skipped)",
             len(symbols))

    t0 = time.time()
    counts = {"cached": 0, "ok": 0, "none": 0}
    for i, sym in enumerate(symbols, 1):
        safe = sym.replace(":", "_").replace("/", "_")[:80]
        path = CACHE / f"{safe}.json"
        if path.exists() and not force:
            counts["cached"] += 1
            continue
        try:
            rec = yahoo_meta(sym)
        except Exception as e:
            LOG.exception("failed on %s: %s", sym, e)
            rec = None
        path.write_text(json.dumps(rec or {"symbol": sym, "found": False},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        counts["ok" if rec else "none"] += 1
        time.sleep(RATE_DELAY)
        if i % 50 == 0:
            LOG.info("  %d/%d (%.0fs) %s", i, len(symbols), time.time() - t0,
                     json.dumps(counts))

    # aggregate every cached record into one file the generators read
    meta: dict[str, dict] = {}
    for p in CACHE.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if rec.get("symbol") and (rec.get("sector") or rec.get("market_cap")):
            meta[rec["symbol"]] = rec
    (PROC / "security_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    LOG.info("done in %.0fs -> %s · security_meta.json holds %d securities",
             time.time() - t0, json.dumps(counts), len(meta))
    LOG.info("next: python scripts/gen_vault.py  (turns this into sector/cap tags)")


if __name__ == "__main__":
    main()
