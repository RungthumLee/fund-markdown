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
SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK[0] * len(values)
    return "".join(SPARK[min(7, int((v - lo) / (hi - lo) * 7.999))] for v in values)


def stats(points: list[tuple[str, float]]) -> dict:
    navs = [p[1] for p in points]
    ret = (navs[-1] / navs[0] - 1) * 100 if navs[0] else None
    # annualised volatility from daily log returns
    rets = [math.log(navs[i] / navs[i - 1])
            for i in range(1, len(navs)) if navs[i - 1] > 0 and navs[i] > 0]
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
    for pid, by_class in series.items():
        # pick the class with the most points (most complete history)
        cls, pts = max(by_class.items(), key=lambda kv: len(kv[1]))
        pts = sorted(set(pts))                       # dedupe + sort by date
        if len(pts) < 5:
            continue
        out[pid] = {"class": cls, **stats(pts), "horizons": horizons(pts),
                    "points": [[d, round(v, 4)] for d, v in pts]}

    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    LOG.info("wrote %s for %d funds", OUT.relative_to(ROOT), len(out))


if __name__ == "__main__":
    main()
