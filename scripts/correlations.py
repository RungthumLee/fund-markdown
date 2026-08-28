"""
correlations.py - Realized (past) correlation of each fund's NAV to a set of
macro factors. Purely descriptive; the gateway that R-05 opened.

Method, kept honest and simple:
  * fund daily log-returns from nav_history.json.
  * factor daily change: log-return for price series, difference for yield.
  * align on common dates. A Thai fund holding foreign assets prices its NAV off
    the previous foreign close, so for each factor both lag 0 and lag 1 are tried
    and the stronger |corr| kept, with the lag recorded - a timezone alignment,
    not a fishing expedition (only two candidates, chosen a priori).
  * Pearson r, reported only when at least MIN_OBS overlapping days and
    |r| >= MIN_ABS (a short window inflates weak correlations - below the bar is
    noise, so it is dropped rather than shown).

NOTHING here forecasts. Correlation is past co-movement, is not causation, and is
unstable (it jumps toward 1 in a crisis). Those caveats travel with every number
(see docs/project/ideas.md section 0). Blocked without nav_history + factor_series
(no-op).

    python scripts/correlations.py
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("correlations")
PROC = ROOT / "data" / "processed"
OUT = PROC / "correlations.json"

MIN_OBS = 30
MIN_ABS = 0.40
TOP_N = 4

# A change measured across a reporting hole is not a daily change. The SEC NAV
# feed is missing ~2 weeks market-wide in Nov 2024, individual funds go quiet
# for months, and Yahoo has its own holidays. Pairing a 15-day move against one
# factor day is not a like-for-like observation, so it is dropped rather than
# correlated. (ISS-041)
MAX_GAP_DAYS = 7


def _returns(points: list, kind: str) -> dict[str, float]:
    """date -> daily change. Price: log-return; yield: level difference.

    Pairs spanning more than MAX_GAP_DAYS are skipped: the level either side is
    real, the "per day" reading of the step between them is not."""
    pts = sorted((d, v) for d, v in points)
    out: dict[str, float] = {}
    for i in range(1, len(pts)):
        (d0, v0), (d1, v1) = pts[i - 1], pts[i]
        if (date.fromisoformat(d1) - date.fromisoformat(d0)).days > MAX_GAP_DAYS:
            continue
        if kind == "yield":
            out[d1] = v1 - v0
        elif v0 > 0 and v1 > 0:
            out[d1] = math.log(v1 / v0)
    return out


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < MIN_OBS:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _shift(dates: list[str], by: int) -> dict[str, str]:
    """map a date to the factor date `by` positions earlier (lag)."""
    return {dates[i]: dates[i - by] for i in range(by, len(dates))}


def main() -> None:
    nh_path, fs_path = PROC / "nav_history.json", PROC / "factor_series.json"
    if not (nh_path.exists() and fs_path.exists()):
        LOG.error("need nav_history.json + factor_series.json - run those first")
        return
    nav = json.loads(nh_path.read_text(encoding="utf-8"))
    factors = json.loads(fs_path.read_text(encoding="utf-8"))

    fret = {k: (_returns(v["points"], v["type"]),
                sorted(d for d, _ in v["points"]), v)
            for k, v in factors.items()}

    out: dict[str, dict] = {}
    for pid, rec in nav.items():
        fund_r = _returns(rec["points"], "price")
        if len(fund_r) < MIN_OBS:
            continue
        results = []
        for key, (fac_r, fac_dates, meta) in fret.items():
            best = None
            for lag in (0, 1):
                shift = _shift(fac_dates, lag)          # fund date -> factor date
                xs, ys = [], []
                for d, r in fund_r.items():
                    fd = shift.get(d) if lag else d
                    if fd in fac_r:
                        xs.append(r)
                        ys.append(fac_r[fd])
                corr = _pearson(xs, ys)
                if corr is not None and (best is None or abs(corr) > abs(best[0])):
                    best = (corr, len(xs), lag)
            if best and abs(best[0]) >= MIN_ABS:
                results.append({
                    "key": key, "name": meta["name_th"],
                    "corr": round(best[0], 2), "n": best[1], "lag": best[2],
                    "relationship": "ไปทางเดียวกัน" if best[0] > 0 else "สวนทาง",
                })
        if results:
            results.sort(key=lambda r: -abs(r["corr"]))
            out[pid] = {"from": rec["from"], "to": rec["to"],
                        "factors": results[:TOP_N]}

    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    LOG.info("wrote %s for %d funds (|r|>=%.2f, >=%d obs)",
             OUT.relative_to(ROOT), len(out), MIN_ABS, MIN_OBS)


if __name__ == "__main__":
    main()
