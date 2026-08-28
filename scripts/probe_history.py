"""
probe_history.py — Measure how far back the SEC API actually serves data,
and what the real rate limit is, before committing to a longer retention
window (ideas.md 5.5 / OUT-002 / DEC-002).

It answers three questions with real calls, cheaply:
  1. NAV: which calendar years return rows, per sample fund?
  2. Outstanding portfolio: which periods (YYYYMM) return rows?
  3. Rate limit: what burst rate does the API tolerate before 429?

Usage:  python scripts/probe_history.py [--funds M0017_2538,M0999_2568]
        python scripts/probe_history.py --no-burst
Writes: data/processed/history_probe.json  (+ prints a summary table)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import SECClient, EP, ROOT, get_logger, save_json  # noqa: E402

LOG = get_logger("probe_history")
TODAY = date.today()

# One long-lived fund, one mid-life, one born last year: the reach limit could
# be the API's or simply the fund's own age, and only a spread tells them apart.
DEFAULT_FUNDS = ["M0017_2538", "M0512_2546", "M0999_2568"]


def _rows(client: SECClient, path: str, params: dict, page_size: int = 100) -> int:
    """Row count for one page — enough to answer 'does this window exist'."""
    data = client.get(path, {**params, "page_size": page_size})
    return len(data.get("items") or [])


def probe_nav(client: SECClient, pid: str, first_year: int) -> dict:
    """One call per calendar year: does NAV exist for that year?"""
    years: dict[int, int] = {}
    for y in range(first_year, TODAY.year + 1):
        n = _rows(client, EP["nav"], {
            "proj_id": pid,
            "start_nav_date": f"{y}-01-01",
            "end_nav_date": f"{y}-12-31",
        })
        years[y] = n
        LOG.info("NAV %s %s -> %s rows (first page)", pid, y, n)
    return years


def count_nav_year(client: SECClient, pid: str, year: int) -> tuple[int, int]:
    """Full paginated count for one year: rows and API calls it took."""
    before = client.calls
    n = sum(1 for _ in client.paginate(EP["nav"], {
        "proj_id": pid,
        "start_nav_date": f"{year}-01-01",
        "end_nav_date": f"{year}-12-31",
    }))
    return n, client.calls - before


def probe_portfolio(client: SECClient, pid: str, first_year: int) -> dict:
    """Quarter-end periods only — the portfolio is published quarterly."""
    periods: dict[str, int] = {}
    for y in range(first_year, TODAY.year + 1):
        for m in (3, 6, 9, 12):
            if (y, m) > (TODAY.year, TODAY.month):
                continue
            p = f"{y}{m:02d}"
            n = _rows(client, EP["out_portfolio"], {
                "proj_id": pid, "start_period": p, "end_period": p}, page_size=1)
            if n:
                periods[p] = n
    LOG.info("portfolio %s -> %s periods with rows", pid, len(periods))
    return periods


def probe_concurrent(n: int = 40, workers_list=(2, 4, 8)) -> dict:
    """Same burst, in parallel: sequential throughput is bounded by round-trip
    latency, so it cannot find a limiter that sits above ~12 req/s."""
    from concurrent.futures import ThreadPoolExecutor
    out = {}
    for w in workers_list:
        c = SECClient(rate_delay=0.0)

        def one(_i: int) -> int:
            try:
                c.get(EP["amcs"], {"page_size": 1}, max_retries=1)
                return 1
            except RuntimeError:
                return 0

        t0 = time.time()
        with ThreadPoolExecutor(w) as ex:
            ok = sum(ex.map(one, range(n)))
        dt = time.time() - t0
        out[w] = {"ok": ok, "of": n, "seconds": round(dt, 2),
                  "req_per_sec": round(n / dt, 1)}
        LOG.info("concurrency %s workers: %s", w, out[w])
    return out


def probe_burst(client: SECClient, n: int = 40) -> dict:
    """Fire n calls with no politeness delay and see what the API does."""
    saved, client.rate_delay = client.rate_delay, 0.0
    t0 = time.time()
    codes = {"ok": 0, "retried": 0}
    try:
        for i in range(n):
            try:
                client.get(EP["amcs"], {"page_size": 1})
                codes["ok"] += 1
            except RuntimeError as e:                # retries exhausted
                codes["retried"] += 1
                LOG.warning("burst call %s failed: %s", i, e)
    finally:
        client.rate_delay = saved
    dt = time.time() - t0
    return {"calls": n, "seconds": round(dt, 2),
            "req_per_sec": round(n / dt, 2) if dt else None, **codes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--funds", default=",".join(DEFAULT_FUNDS))
    ap.add_argument("--no-burst", action="store_true")
    args = ap.parse_args()

    funds_meta = json.loads(
        (ROOT / "data" / "processed" / "funds.json").read_text(encoding="utf-8"))
    client = SECClient()
    out: dict = {"probed_at": str(TODAY), "funds": {}}

    for pid in [f.strip() for f in args.funds.split(",") if f.strip()]:
        meta = funds_meta.get(pid, {})
        init = (meta.get("init_date") or "2000-01-01")[:4]
        # Start one year before inception: if rows appear there, the reach limit
        # is not the fund's age.
        first_year = max(1990, int(init) - 1)
        LOG.info("=== %s (%s, init %s) ===", pid, meta.get("abbr"), meta.get("init_date"))
        nav_years = probe_nav(client, pid, first_year)
        have = [y for y, n in nav_years.items() if n]
        earliest = min(have) if have else None
        rec = {
            "abbr": meta.get("abbr"),
            "init_date": meta.get("init_date"),
            "nav_years": nav_years,
            "nav_earliest_year": earliest,
            "nav_years_available": len(have),
            "portfolio_periods": probe_portfolio(client, pid, first_year),
        }
        if earliest:
            rows, calls = count_nav_year(client, pid, earliest)
            rec["nav_rows_in_earliest_year"] = rows
            rec["api_calls_for_that_year"] = calls
        out["funds"][pid] = rec

    if not args.no_burst:
        out["burst"] = probe_burst(client)
        LOG.info("burst: %s", out["burst"])
        out["concurrent"] = probe_concurrent()

    out["total_api_calls"] = client.calls
    save_json(out, ROOT / "data" / "processed" / "history_probe.json")

    print("\n=== NAV reach ===")
    for pid, r in out["funds"].items():
        span = f"{r['nav_earliest_year']}-{TODAY.year}" if r["nav_earliest_year"] else "none"
        print(f"{r['abbr']:<10} init {r['init_date']}  NAV {span} "
              f"({r['nav_years_available']} yr)  portfolio periods "
              f"{len(r['portfolio_periods'])}")
    print(f"\ntotal API calls: {out['total_api_calls']}")


if __name__ == "__main__":
    main()
