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
#
# Measured against the source on 2026-08-28 (scripts/probe_history.py): NAV goes
# back to a fund's inception with no ceiling of its own, so the number here is a
# retention choice - 5 years is one market cycle and the horizon 3/5Y statistics
# are quoted over, and correlation's standard error (~1/sqrt(n)) stops improving
# much past it. The portfolio is different: the API itself stops at 12 quarters,
# so PORT_QUARTERS_BACK=12 is simply everything that exists.
# See docs/project/ideas.md section 5.4 and DEC-002.
NAV_YEARS = 5
PORT_QUARTERS_BACK = 12
PORT_MONTHS_BACK = 4


def _period(d: date) -> str:
    return f"{d.year}{d.month:02d}"


NAV_START = date(TODAY.year - NAV_YEARS, TODAY.month, 1)


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
                             "start_nav_date": str(NAV_START),
                             "end_nav_date": str(TODAY)}),
    "dividend_history":  ("dividend_history", {}),
    "out_port_asset_type": ("out_port_asset_type", {
                             "start_period": _period(_months_ago(PORT_MONTHS_BACK)),
                             "end_period": _period(TODAY)}),
    "out_portfolio":     ("out_portfolio", {
                             "start_period": _period(_months_ago(PORT_QUARTERS_BACK * 3)),
                             "end_period": _period(TODAY)}),
}


# ---------------------------------------------------------------- slicing
#
# The two backfilled datasets are millions of rows pulled through one cursor.
# As a single stream an expired cursor an hour in loses the whole pull, so they
# are fetched one calendar slice at a time: each slice writes its own part file
# with its own .done marker, and a re-run picks up where it stopped. The parts
# are concatenated into the same .jsonl every consumer already reads.

def _nav_slices() -> list[tuple[str, dict]]:
    """One slice per calendar year."""
    out = []
    for y in range(NAV_START.year, TODAY.year + 1):
        start = str(NAV_START) if y == NAV_START.year else f"{y}-01-01"
        end = str(TODAY) if y == TODAY.year else f"{y}-12-31"
        out.append((str(y), {"start_nav_date": start, "end_nav_date": end}))
    return out


def _portfolio_slices() -> list[tuple[str, dict]]:
    """One slice per quarter-end period, oldest first."""
    out = []
    y, m = TODAY.year, (TODAY.month // 3) * 3 or 3
    for _ in range(PORT_QUARTERS_BACK):
        p = f"{y}{m:02d}"
        out.append((p, {"start_period": p, "end_period": p}))
        m -= 3
        if m <= 0:
            m += 12
            y -= 1
    return list(reversed(out))


SLICED = {"nav": _nav_slices, "out_portfolio": _portfolio_slices}


def _fetch_slice(name: str, label: str, extra: dict, i: int, total: int) -> int:
    """Fetch one slice into its own part file. Own client: safe to run in a
    thread, and a 429 backs that slice off without stalling the others."""
    ep_key, base = DATASETS[name]
    parts = RAW / f"{name}.parts"
    part, mark = parts / f"{label}.jsonl", parts / f"{label}.done"
    if mark.exists() and part.exists():
        n = int(mark.read_text(encoding="utf-8").strip() or 0)
        LOG.info("  slice %-7s %2d/%d skip (%s rows)", label, i, total, n)
        return n
    client = SECClient()
    n, t0 = 0, time.time()
    with part.open("w", encoding="utf-8") as fh:
        for item in client.paginate(EP[ep_key], {**base, **extra}):
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            n += 1
    mark.write_text(str(n), encoding="utf-8")
    LOG.info("  slice %-7s %2d/%d %7d rows in %.0fs", label, i, total,
             n, time.time() - t0)
    return n


def harvest_sliced(name: str, workers: int = 1) -> int:
    """Fetch one dataset slice by slice, then join the parts. Resumable.

    Slices are independent cursors, so they *can* run in parallel - but do not
    reach for it. The burst probe saw no 429 at 73 req/s over 40 calls, yet
    running the real backfill on 4 workers hit 429 within three minutes and kept
    hitting it: the limiter is a sustained quota, and a short burst never
    reveals it. Sequential at the client's 0.12s delay sustains ~120 KB/s with
    no 429 at all, which is why workers stays 1. See OUT-002.
    """
    parts = RAW / f"{name}.parts"
    parts.mkdir(exist_ok=True)
    slices = SLICED[name]()
    jobs = [(name, label, extra, i, len(slices))
            for i, (label, extra) in enumerate(slices, 1)]

    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(lambda a: _fetch_slice(*a), jobs))
    else:
        for a in jobs:
            _fetch_slice(*a)

    total = 0
    with (RAW / f"{name}.jsonl").open("w", encoding="utf-8") as out:
        for label, _ in slices:
            with (parts / f"{label}.jsonl").open(encoding="utf-8") as fh:
                for line in fh:
                    out.write(line)
                    total += 1
    return total


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


def harvest(name: str, force: bool = False, workers: int = 1) -> int:
    ep_key, params = DATASETS[name]
    out = RAW / f"{name}.jsonl"
    done = RAW / f"{name}.done"

    if done.exists() and not force:
        n = int(done.read_text(encoding="utf-8").strip() or 0)
        LOG.info("SKIP %-22s already complete (%s rows)", name, n)
        return n

    LOG.info("START %-21s %s %s", name, EP[ep_key], params or "")
    t0 = time.time()
    count = 0
    client = None
    if name in SLICED:
        # --force means refetch, so drop the slice markers a resume would honour
        if force:
            for m in (RAW / f"{name}.parts").glob("*.done"):
                m.unlink()
        count = harvest_sliced(name, workers)
    else:
        client = SECClient()
        with out.open("w", encoding="utf-8") as fh:
            for item in client.paginate(EP[ep_key], params):
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
                if count % 20_000 == 0:
                    LOG.info("  ... %-18s %d rows", name, count)
    done.write_text(str(count), encoding="utf-8")
    LOG.info("DONE  %-21s %d rows in %.1fs%s", name, count, time.time() - t0,
             f" ({client.calls} api calls)" if client else "")
    return count


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    workers = next((int(a.split("=", 1)[1]) for a in sys.argv
                    if a.startswith("--workers=")), 1)
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
            summary[name] = harvest(name, force=force, workers=workers)
        except Exception as e:                       # keep going; log the gap
            LOG.exception("FAILED %s: %s", name, e)
            summary[name] = f"ERROR: {e}"
    (RAW / "_harvest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    LOG.info("Harvest summary: %s", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
