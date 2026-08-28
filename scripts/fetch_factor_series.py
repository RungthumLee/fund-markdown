"""
fetch_factor_series.py - Daily series for a small set of macro factors, from
Yahoo, so a fund's NAV can be correlated against them (R-05 -> correlation).

Yahoo must be called from a machine with internet (fine here; the assistant
sandbox got 429 on raw curl - yfinance handles cookies). Small and fast: seven
series.

Output: data/processed/factor_series.json
    { key: {name_th, symbol, type: price|yield, points:[[date,value],...]} }

Nothing here forecasts anything - these are raw factor levels, used only to
measure realized (past) correlation. See docs/project/ideas.md section 0.

    python scripts/fetch_factor_series.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("fetch_factor_series")
OUT = ROOT / "data" / "processed" / "factor_series.json"

# key -> (Thai name, Yahoo symbol, type). `yield` series are compared by daily
# difference (Δ), price series by daily return.
FACTORS = {
    "gold":    ("ราคาทองคำ", "GLD", "price"),
    "oil":     ("ราคาน้ำมัน (Brent)", "BZ=F", "price"),
    "sp500":   ("หุ้นสหรัฐ (S&P 500)", "^GSPC", "price"),
    "us10y":   ("ดอกเบี้ยสหรัฐ 10 ปี", "^TNX", "yield"),
    "usd":     ("ดัชนีดอลลาร์ (DXY)", "DX-Y.NYB", "price"),
    "set":     ("หุ้นไทย (SET)", "^SET.BK", "price"),
    "msci_em": ("หุ้นตลาดเกิดใหม่ (EM)", "EEM", "price"),
}


def main() -> None:
    import yfinance as yf
    out: dict[str, dict] = {}
    for key, (name, symbol, typ) in FACTORS.items():
        try:
            h = yf.Ticker(symbol).history(period="8mo")
        except Exception as e:
            LOG.warning("failed %s (%s): %s", key, symbol, str(e)[:60])
            continue
        points = [[d.strftime("%Y-%m-%d"), round(float(c), 4)]
                  for d, c in h["Close"].items() if c == c]  # c==c drops NaN
        if len(points) < 20:
            LOG.warning("thin series for %s (%d pts)", key, len(points))
            continue
        out[key] = {"name_th": name, "symbol": symbol, "type": typ,
                    "points": points}
        LOG.info("  %-8s %-10s %d pts", key, symbol, len(points))

    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    LOG.info("wrote %s (%d factors)", OUT.relative_to(ROOT), len(out))


if __name__ == "__main__":
    main()
