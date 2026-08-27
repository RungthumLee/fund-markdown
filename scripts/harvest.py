"""
harvest.py — Bulk-download every SEC fund dataset into data/raw/*.jsonl

Strategy: the SEC v2 API allows omitting `proj_id`, so each dataset is pulled
as one cursor-paginated stream instead of 2,300 per-fund calls. Each dataset
writes a .jsonl plus a .done marker so re-running resumes/skips cheaply.

Usage:  python scripts/harvest.py [dataset ...]      (default: all)
        python scripts/harvest.py --force fs_fees
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import SECClient, EP, ROOT, get_logger  # noqa: E402

LOG = get_logger("harvest")
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

TODAY = date.today()

# Windows for the huge time-series datasets, so the harvest stays bounded.
NAV_DAYS = 120
PORT_QUARTERS_BACK = 2
PORT_MONTHS_BACK = 4


def _period(d: date) -> str:
    return f"{d.year}{d.month:02d}"


def _months_ago(n: int) -> date:
    y, m = TODAY.year, TODAY.month - n
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


# name -> (endpoint key, extra params)
DATASETS: dict[str, tuple[str, dict]] = {
    # --- general info -----------------------------------------------------
    "amcs":              ("amcs", {}),
    "profiles":          ("profiles", {"fund_status": "Registered"}),
    "specifications":    ("specifications", {}),
    "mutual_fund_fees":  ("mutual_fund_fees", {}),
    "involve_parties":   ("involve_parties", {}),
    # --- factsheet (latest effective record only) -------------------------
    "fs_urls":           ("fs_urls", {}),
    "fs_ipos":           ("fs_ipos", {"latest": "true"}),
    "fs_benchmarks":     ("fs_benchmarks", {"latest": "true"}),
    "fs_min_amounts":    ("fs_min_amounts", {"latest": "true"}),
    "fs_periods":        ("fs_periods", {"latest": "true"}),
    "fs_risk":           ("fs_risk", {"latest": "true"}),
    "fs_statistics":     ("fs_statistics", {"latest": "true"}),
    "fs_dividend":       ("fs_dividend", {"latest": "true"}),
    "fs_fees":           ("fs_fees", {"latest": "true"}),
    "fs_performance":    ("fs_performance", {"latest": "true"}),
    "fs_asset_alloc":    ("fs_asset_alloc", {"latest": "true"}),
    "fs_top5":           ("fs_top5", {"latest": "true"}),
    # --- time series (windowed) -------------------------------------------
    "nav":               ("nav", {
                             "start_nav_date": str(TODAY - timedelta(days=NAV_DAYS)),
                             "end_nav_date": str(TODAY)}),
    "dividend_history":  ("dividend_history", {}),
    "out_port_asset_type": ("out_port_asset_type", {
                             "start_period": _period(_months_ago(PORT_MONTHS_BACK)),
                             "end_period": _period(TODAY)}),
    "out_portfolio":     ("out_portfolio", {
                             "start_period": _period(_months_ago(PORT_QUARTERS_BACK * 3)),
                             "end_period": _period(TODAY)}),
}


# How often each dataset is worth re-fetching, in hours. Nothing here changes
# at the same speed: NAV moves every business day, a fund's fee schedule moves
# when the prospectus is amended, and a quarterly portfolio appears once a
# quarter with a reporting lag. Re-pulling all 21 daily would cost ~40 minutes
# and ~2,000 API calls to rediscover data that did not move.
MAX_AGE_HOURS: dict[str, int] = {
    "nav": 20,                    # business-daily
    "profiles": 24,               # new funds / status changes
    "fs_urls": 24,                # a new factsheet URL is how we notice updates
    "out_port_asset_type": 24 * 7,
    "out_portfolio": 24 * 7,      # published quarterly, with a lag
    "fs_performance": 24 * 7,
    "fs_statistics": 24 * 7,
    "dividend_history": 24 * 7,
    "fs_dividend": 24 * 7,
}
DEFAULT_MAX_AGE_HOURS = 24 * 14   # reference data: fees, benchmarks, parties


def age_hours(name: str) -> float | None:
    """Hours since this dataset last completed, or None if it never has."""
    done = RAW / f"{name}.done"
    if not done.exists():
        return None
    return (time.time() - done.stat().st_mtime) / 3600


def is_stale(name: str) -> bool:
    age = age_hours(name)
    if age is None:
        return True
    return age >= MAX_AGE_HOURS.get(name, DEFAULT_MAX_AGE_HOURS)


def harvest(name: str, force: bool = False) -> int:
    ep_key, params = DATASETS[name]
    out = RAW / f"{name}.jsonl"
    done = RAW / f"{name}.done"

    if done.exists() and not force:
        n = int(done.read_text(encoding="utf-8").strip() or 0)
        LOG.info("SKIP %-22s already complete (%s rows)", name, n)
        return n

    LOG.info("START %-21s %s %s", name, EP[ep_key], params or "")
    client = SECClient()
    t0 = time.time()
    count = 0
    with out.open("w", encoding="utf-8") as fh:
        for item in client.paginate(EP[ep_key], params):
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1
            if count % 20_000 == 0:
                LOG.info("  ... %-18s %d rows", name, count)
    done.write_text(str(count), encoding="utf-8")
    LOG.info("DONE  %-21s %d rows in %.1fs (%d api calls)",
             name, count, time.time() - t0, client.calls)
    return count


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    stale_only = "--stale" in sys.argv
    targets = args or list(DATASETS)

    if stale_only:
        # daily mode: refresh only what has aged past its own cadence
        fresh = [n for n in targets if not is_stale(n)]
        targets = [n for n in targets if is_stale(n)]
        for name in targets:
            (RAW / f"{name}.done").unlink(missing_ok=True)
        LOG.info("stale: %d dataset(s) -> %s", len(targets),
                 ", ".join(targets) or "(none)")
        LOG.info("fresh: %d dataset(s) skipped", len(fresh))
        if not targets:
            return
    unknown = [t for t in targets if t not in DATASETS]
    if unknown:
        LOG.error("Unknown dataset(s): %s", unknown)
        sys.exit(2)

    summary = {}
    for name in targets:
        try:
            summary[name] = harvest(name, force=force)
        except Exception as e:                       # keep going; log the gap
            LOG.exception("FAILED %s: %s", name, e)
            summary[name] = f"ERROR: {e}"
    (RAW / "_harvest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    LOG.info("Harvest summary: %s", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
