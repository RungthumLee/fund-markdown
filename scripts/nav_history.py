"""
nav_history.py - Build the daily NAV series per fund from the raw NAV dump.

funds.json keeps only the latest NAV (DEC-002); the daily history lives in
data/raw/nav.jsonl, now five years deep (harvest.py NAV_YEARS). For each fund
this picks the share class with the most complete series, keeps every day of it,
and computes DESCRIPTIVE stats over several horizons - 1Y / 3Y / 5Y, each one
kept only when the fund is actually old enough to fill it, and each labelled
with the dates and the number of days it was measured over. All backward-looking
- no forecast (docs ideas §0).

The full series is kept, not a window: correlations.py reads these points, and
its standard error is roughly 1/sqrt(n), so the sample size here is what makes a
correlation trustworthy (ideas §5.1).

Output: data/processed/nav_history.json
    { proj_id: {class, from, to, n, points:[[date,nav],...], sparkline,
                window_return_pct, volatility_annualized_pct, high, low,
                horizons: [{label, from, to, n, return_pct, volatility_pct}]} }

gen_vault reads it and renders a "NAV ย้อนหลัง" block; if the file is absent the
block is simply skipped. This is the gateway to correlation work (R-05).

    python scripts/nav_history.py
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("nav_history")
RAW = ROOT / "data" / "raw" / "nav.jsonl"
OUT = ROOT / "data" / "processed" / "nav_history.json"

# Horizons reported in the note, longest last. A horizon is shown only when the
# series covers at least 80% of it: a two-year-old fund gets 1Y, not a "3Y"
# return quietly measured over two years.
HORIZONS = [("1 ปี", 365), ("3 ปี", 365 * 3), ("5 ปี", 365 * 5)]
HORIZON_FILL = 0.8

# A price change measured across a hole is not a daily return. The SEC feed has
# a market-wide gap of ~2 weeks in Nov 2024 and individual funds go missing for
# months, and feeding those straight into a daily volatility inflates it (a
# 15-day move counted as one day). Pairs further apart than this are skipped -
# the level is still real, only the "per day" reading of it is not. (ISS-041)
MAX_GAP_DAYS = 7

# A fund that is renamed keeps its NAV, but the feed files it under the new
# label, so the old label just stops. Chain them when the handover is immediate
# and the NAV level carries across it - a real rename moves the name, not the
# price. Both bars must hold, or an unrelated class would be glued on.
LINEAGE_GAP_DAYS = 7
LINEAGE_STEP_PCT = 0.05
SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK[0] * len(values)
    return "".join(SPARK[min(7, int((v - lo) / (hi - lo) * 7.999))] for v in values)


def stats(points: list[tuple[str, float]]) -> dict:
    navs = [p[1] for p in points]
    ret = (navs[-1] / navs[0] - 1) * 100 if navs[0] else None
    # annualised volatility from daily log returns, skipping any pair that spans
    # a reporting hole (MAX_GAP_DAYS)
    rets = [math.log(navs[i] / navs[i - 1])
            for i in range(1, len(navs))
            if navs[i - 1] > 0 and navs[i] > 0
            and (_date.fromisoformat(points[i][0])
                 - _date.fromisoformat(points[i - 1][0])).days <= MAX_GAP_DAYS]
    vol = None
    if len(rets) > 5:
        mean = sum(rets) / len(rets)
        sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / (len(rets) - 1))
        vol = sd * math.sqrt(252) * 100
    # downsample sparkline to <= 40 points so the note stays compact
    step = max(1, len(navs) // 40)
    return {
        "from": points[0][0], "to": points[-1][0], "n": len(navs),
        "window_return_pct": round(ret, 2) if ret is not None else None,
        "volatility_annualized_pct": round(vol, 1) if vol is not None else None,
        "high": round(max(navs), 4), "low": round(min(navs), 4),
        "sparkline": sparkline(navs[::step]),
    }


def _overlaps(a: list, b: list) -> bool:
    """Do two labels report on the same days? A label that coexists with the
    current one is a *different* share class (1AMSET50-RA and -RU trade within
    1% of each other), not the same units under an old name - and must never be
    spliced in. A label that never coexists is a candidate."""
    # actual shared days, not just overlapping spans: a fund can switch to
    # another label and back, so the old label's span brackets the new one while
    # the two never report on the same day (ASP-NCLR / ASP-POWER).
    return bool({d for d, _ in a} & {d for d, _ in b})


def _suffix(cls: str) -> str:
    return cls.rsplit("-", 1)[-1] if "-" in cls else ""


def _match(a_val: float | None, b_val: float | None) -> float | None:
    """Relative NAV step between two labels at a handover, or None."""
    if not a_val or not b_val:
        return None
    return abs(b_val / a_val - 1)


def stitch_lineage(by_class: dict) -> tuple[str, list, list[str]]:
    """Follow one share class through the labels it used to carry.

    The feed has no name history: `profiles` holds exactly one name per project
    (verified across all 4,892 rows), so when a fund is renamed the only trace
    left is that its old `fund_class_name` stops and a new one starts the next
    business day at the same NAV - ASP-POWER -> ASP-NCLR, ASP-LTF-A ->
    ASP-THDEQ-A. Taking the longest label alone cuts the history at the rename
    and leaves a hole where the fund was reporting all along.

    Two moves, both restricted to labels that never coexist with the current one
    and whose NAV level carries across the seam (LINEAGE_STEP_PCT):
      * extend backwards, when an old label ends just as this one starts;
      * fill an internal hole, when a label covers exactly the missing stretch
        (ASP-NCLR reported as ASP-POWER for 19 months, then switched back).

    Returns (current label, merged points, labels used in order).
    """
    spans = {c: p for c, p in by_class.items() if p}
    if not spans:
        return "", [], []
    cur = max(spans, key=lambda c: (spans[c][-1][0], len(spans[c])))
    chain, points = [cur], list(spans[cur])
    free = [c for c in spans if c != cur and not _overlaps(spans[cur], spans[c])]

    # 1. extend backwards through predecessors
    while True:
        head_date, head_val = _date.fromisoformat(points[0][0]), points[0][1]
        best, best_key = None, None
        for c in free:
            if c in chain:
                continue
            gap = (head_date - _date.fromisoformat(spans[c][-1][0])).days
            if not 0 <= gap <= LINEAGE_GAP_DAYS:
                continue
            diff = _match(spans[c][-1][1], head_val)
            if diff is None or diff > LINEAGE_STEP_PCT:
                continue
            key = (_suffix(c) != _suffix(chain[0]), diff)   # same suffix first
            if best_key is None or key < best_key:
                best, best_key = c, key
        if best is None:
            break
        chain.insert(0, best)
        points = list(spans[best]) + points

    # 2. fill internal holes left by a label the fund switched to and back from
    for c in free:
        if c in chain:
            continue
        c0, c1 = spans[c][0][0], spans[c][-1][0]
        before = [p for p in points if p[0] < c0]
        after = [p for p in points if p[0] > c1]
        if not before or not after:
            continue
        hole = (_date.fromisoformat(after[0][0])
                - _date.fromisoformat(before[-1][0])).days
        if hole <= LINEAGE_GAP_DAYS:
            continue
        d_in, d_out = _match(before[-1][1], spans[c][0][1]), _match(spans[c][-1][1], after[0][1])
        if d_in is None or d_out is None:
            continue
        if d_in > LINEAGE_STEP_PCT or d_out > LINEAGE_STEP_PCT:
            continue
        points = sorted(before + list(spans[c]) + after)
        chain.insert(chain.index(cur), c)

    return cur, sorted(set(points)), chain


def horizons(points: list[tuple[str, float]]) -> list[dict]:
    """Same descriptive stats over 1Y / 3Y / 5Y, skipping any horizon the fund
    is too young to fill - a short series would otherwise be labelled with a
    span it never covered."""
    last = _date.fromisoformat(points[-1][0])
    span = (last - _date.fromisoformat(points[0][0])).days
    out = []
    for label, days in HORIZONS:
        if span < days * HORIZON_FILL:
            continue
        sub = [p for p in points
               if (last - _date.fromisoformat(p[0])).days <= days]
        if len(sub) < 20:
            continue
        s = stats(sub)
        out.append({"label": label, "from": s["from"], "to": s["to"],
                    "n": s["n"], "return_pct": s["window_return_pct"],
                    "volatility_pct": s["volatility_annualized_pct"]})
    return out


def main() -> None:
    if not RAW.exists():
        LOG.error("no data/raw/nav.jsonl - run harvest first")
        return

    # collect (date, nav) per (proj_id, class); nav per unit is `last_val`
    series: dict[str, dict[str, list[tuple[str, float]]]] = defaultdict(
        lambda: defaultdict(list))
    rows = 0
    with RAW.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = r.get("proj_id")
            date = str(r.get("nav_date") or "")[:10]
            nav = r.get("last_val")
            if not pid or not date or not isinstance(nav, (int, float)) or nav <= 0:
                continue
            series[pid][r.get("fund_class_name") or "main"].append((date, nav))
            rows += 1
    LOG.info("read %d NAV rows for %d funds", rows, len(series))

    out: dict[str, dict] = {}
    stitched = 0
    for pid, by_class in series.items():
        by_class = {c: sorted(set(p)) for c, p in by_class.items()}
        cls, pts, chain = stitch_lineage(by_class)
        if len(pts) < 5:
            continue
        if len(chain) > 1:
            stitched += 1
        out[pid] = {"class": cls, **stats(pts), "horizons": horizons(pts),
                    "class_history": chain if len(chain) > 1 else [],
                    "points": [[d, round(v, 4)] for d, v in pts]}
    LOG.info("stitched a former label into the series for %d funds", stitched)

    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    LOG.info("wrote %s for %d funds", OUT.relative_to(ROOT), len(out))


if __name__ == "__main__":
    main()
