"""
securities.py - Turn Yahoo security metadata (from fetch_sectors.py) into a
fund's sector and market-cap facets.

Everything here is dormant until `scripts/fetch_sectors.py` has been run on a
machine with internet: with no data/processed/security_meta.json, every function
returns nothing and the vault is unchanged. Once the file exists, feeders gain a
`cap/*` band (large/mid/small) and, where the Thai factsheet gave no sector, a
`sector/*` tag rolled up from the underlying holdings.

    import securities
    securities.fund_cap_tags(fund)      # ["cap/large"] or []
    securities.fund_sector_tags(fund)   # ["sector/technology"] or []
    securities.meta_of("0700.HK")       # {sector, market_cap, ...} or None
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

# Yahoo's GICS sector names -> the canonical sectors used by the factsheet layer
# (scripts/tagging.py), so a fund tagged from either source reads the same.
YAHOO_SECTOR = {
    "Technology": "technology",
    "Financial Services": "financials", "Financial": "financials",
    "Healthcare": "healthcare",
    "Consumer Cyclical": "consumer", "Consumer Defensive": "consumer",
    "Energy": "energy",
    "Industrials": "industrials",
    "Basic Materials": "materials",
    "Communication Services": "communication",
    "Real Estate": "real-estate",
    "Utilities": "utilities",
}

# Market-cap bands. Thresholds are in the security's own currency; most large
# caps read large in any major currency, so this is a deliberate approximation
# (an exact split would need every value in one currency, which Yahoo does not
# give). Values are USD-scale: >= 10bn large, 2-10bn mid, < 2bn small.
_LARGE = 10e9
_MID = 2e9

_meta_cache: dict | None = None
_lt_cache: dict | None = None


def _meta() -> dict:
    global _meta_cache
    if _meta_cache is None:
        path = PROC / "security_meta.json"
        try:
            _meta_cache = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _meta_cache = {}
    return _meta_cache


def _lookthrough() -> dict:
    global _lt_cache
    if _lt_cache is None:
        path = PROC / "lookthrough.json"
        try:
            _lt_cache = json.loads(path.read_text(encoding="utf-8")).get("funds", {})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _lt_cache = {}
    return _lt_cache


def available() -> bool:
    """True once fetch_sectors.py has produced security_meta.json."""
    return bool(_meta())


def meta_of(symbol: str | None) -> dict | None:
    return _meta().get(symbol) if symbol else None


def canonical_sector(yahoo_sector: str | None) -> str | None:
    return YAHOO_SECTOR.get((yahoo_sector or "").strip())


def cap_band(market_cap) -> str | None:
    if not isinstance(market_cap, (int, float)) or market_cap <= 0:
        return None
    return "large" if market_cap >= _LARGE else "mid" if market_cap >= _MID else "small"


def _weighted(fund: dict, pick):
    """Sum look-through weights by whatever `pick(meta)` returns for each holding.

    Only feeders are covered - their exposures carry the Yahoo symbols this data
    is keyed by. Returns {value: pct} plus the covered total.
    """
    meta = _meta()
    if not meta:
        return {}, 0.0
    lt = _lookthrough().get(fund.get("proj_id"))
    if not lt:
        return {}, 0.0
    weights: dict[str, float] = defaultdict(float)
    for ex in lt.get("exposures") or []:
        m = meta.get(ex.get("symbol"))
        w = ex.get("pct_of_fund") or 0
        if not m or not w:
            continue
        v = pick(m)
        if v:
            weights[v] += w
    return dict(weights), round(sum(weights.values()), 1)


def fund_cap_tags(fund: dict) -> list[str]:
    """Dominant market-cap band of the fund's underlying holdings."""
    weights, _ = _weighted(fund, lambda m: cap_band(m.get("market_cap")))
    if not weights:
        return []
    band = max(weights, key=weights.get)
    return [f"cap/{band}"]


def fund_sector_tags(fund: dict) -> list[str]:
    """Dominant sector(s) from Yahoo, rolled up through look-through.

    Meant to fill the gap for foreign feeders the Thai factsheet gives no sector
    for; tagging.py only calls this when the factsheet produced none.
    """
    weights, total = _weighted(fund, lambda m: canonical_sector(m.get("sector")))
    if not weights or total < 20:
        return []
    ranked = sorted(weights.items(), key=lambda kv: -kv[1])
    out = [f"sector/{ranked[0][0]}"]
    if len(ranked) > 1 and ranked[1][1] >= 25:
        out.append(f"sector/{ranked[1][0]}")
    return out
