"""
factors.py - Two-sided factor exposure for a fund, from its own holdings.

Combines what we already know about a fund (its asset class, sectors, dominant
markets, currency hedging, concentration, fee) with scripts/factor_map.json - a
static, authored map of which factors each of those is sensitive to and which
way the factor pushes. The result is a DESCRIPTIVE, TWO-SIDED view:

    "this fund is exposed to X; if X rises Y, if X falls Z"

It is not a forecast. There is no predicted return, no probability, no signal -
see docs/project/ideas.md section 0 for the rules. Every factor shows both a
bull and a bear case so no direction is implied.

    from factors import fund_factors
    fund_factors(tags, market_countries, ter)  # -> [ {factor, category, ...}, ... ]
"""
from __future__ import annotations

import json
from pathlib import Path

_MAP: dict | None = None

# Thai market-country name (from geography.py) -> geo key in factor_map
_COUNTRY_GEO = {
    "จีน": "china", "ฮ่องกง": "china",
    "สหรัฐฯ": "us",
}

# a total expense ratio at or above this is called out as a standing fee drag
_FEE_DRAG = 1.5


def _map() -> dict:
    global _MAP
    if _MAP is None:
        path = Path(__file__).resolve().parent / "factor_map.json"
        _MAP = json.loads(path.read_text(encoding="utf-8"))
    return _MAP


def _strength_rank(s: str) -> int:
    return {"always": 3, "high": 2, "medium": 1, "low": 0}.get(s, 0)


def fund_factors(tags: list[str], market_countries: list[str] | None = None,
                 ter: float | None = None) -> list[dict]:
    """Two-sided factor list for a fund. `source` names the exposure it came
    from; entries are de-duplicated by factor name, strongest kept."""
    m = _map()
    picked: dict[str, dict] = {}

    def add(entry: dict, source: str) -> None:
        key = entry["factor"]
        cand = dict(entry, source=source)
        if key not in picked or _strength_rank(cand.get("strength", "")) > \
                _strength_rank(picked[key].get("strength", "")):
            picked[key] = cand

    # sorted, not set order: Python randomises string hashing per process, so
    # iterating the raw set reshuffles equal-strength factors on every run and
    # regenerating the vault produces diffs in notes whose data never changed.
    tagset = sorted(set(tags or []))

    # asset (gold, oil, real-estate...) and sector, keyed by the exact tag
    for tag in tagset:
        if tag in m.get("asset", {}):
            for e in m["asset"][tag]:
                add(e, f"สินทรัพย์: {tag.split('/')[-1]}")
        if tag.startswith("sector/"):
            key = tag.split("/", 1)[1]
            for e in m.get("sector", {}).get(key, []):
                add(e, f"หมวด: {key}")
        if tag in m.get("structure", {}):
            for e in m["structure"][tag]:
                add(e, "โครงสร้างกอง")

    # geography from the fund's dominant markets (names, not tags)
    for c in market_countries or []:
        geo = _COUNTRY_GEO.get(c)
        for e in m.get("geo", {}).get(geo or "", []):
            add(e, f"ประเทศ: {c}")

    # a high fee is a factor that always drags, regardless of market direction
    if ter is not None and ter >= _FEE_DRAG:
        for e in m.get("structure", {}).get("fee", []):
            add(dict(e, factor=f"ค่าธรรมเนียมรวมสูง ({ter:.2f}%/ปี)"), "โครงสร้างกอง")

    return sorted(picked.values(),
                  key=lambda e: (-_strength_rank(e.get("strength", "")),
                                 e.get("factor", "")))
