"""
geography.py - Where a fund's money actually sits, read from its holdings.

DEC-L01 (voted 3/3): keep two country facts apart.
  * domicile_country - the literal ISIN prefix (ISO 6166), always known.
  * market_country   - the market the money is exposed to. For a feeder that is
                       the look-through of its master; for a direct holding it is
                       the holding's own ISIN.

The split exists because ~680 securities carry LU / IE / KY ISINs - Luxembourg,
Ireland, Cayman - which are FUND DOMICILES, not markets. A Thai fund feeding a
Luxembourg-domiciled China ETF is exposed to China, not Luxembourg, so the
country rollup must run on market_country. Look-through only resolves part of
each master (Yahoo publishes the top holdings), so every rollup reports a
`covered_pct`; the uncovered tail is stated, never silently dropped.

    from geography import country_of_isin, fund_country_mix
"""
from __future__ import annotations

# ISIN prefix (ISO 6166, = ISO 3166-1 alpha-2 of the numbering agency) -> Thai
# country name. Only the prefixes that actually occur in the data are listed.
ISIN_COUNTRY = {
    "TH": "ไทย", "US": "สหรัฐฯ", "CN": "จีน", "HK": "ฮ่องกง", "TW": "ไต้หวัน",
    "JP": "ญี่ปุ่น", "KR": "เกาหลีใต้", "SG": "สิงคโปร์", "MY": "มาเลเซีย",
    "ID": "อินโดนีเซีย", "VN": "เวียดนาม", "PH": "ฟิลิปปินส์", "IN": "อินเดีย",
    "AU": "ออสเตรเลีย", "GB": "สหราชอาณาจักร", "FR": "ฝรั่งเศส", "DE": "เยอรมนี",
    "CH": "สวิตเซอร์แลนด์", "NL": "เนเธอร์แลนด์", "ES": "สเปน", "IT": "อิตาลี",
    "SE": "สวีเดน", "BE": "เบลเยียม", "CA": "แคนาดา", "LI": "ลิกเตนสไตน์",
    "MT": "มอลตา", "GG": "เกิร์นซีย์",
    # fund/ETF domiciles - a place a fund is registered, not a market
    "LU": "ลักเซมเบิร์ก", "IE": "ไอร์แลนด์", "KY": "หมู่เกาะเคย์แมน",
    # supranational / international securities (Eurobonds etc.)
    "XS": "ระหว่างประเทศ",
}

# prefixes that name where a fund is registered, not where the money is invested.
# KY (Cayman) is here too: for a bare ISIN it signals incorporation, not market -
# but a Cayman-incorporated Chinese tech name usually carries a .HK symbol, which
# is resolved first below, so those are still placed in their listing market.
DOMICILE_PREFIXES = {"LU", "IE", "KY"}

# Yahoo symbol suffix -> listing market. Look-through exposures carry symbols
# like "0700.HK" or "688256.SS"; a bare ticker ("NVDA", "PDD") is a US listing.
# market_country is the market a security TRADES in - an ADR counts at its US
# listing, an HK-listed Chinese name counts as Hong Kong. This is deterministic
# (the suffix is data) and honestly sourced; economic exposure is a separate idea.
SUFFIX_MARKET = {
    "HK": "ฮ่องกง", "SS": "จีน", "SZ": "จีน", "T": "ญี่ปุ่น", "KS": "เกาหลีใต้",
    "KQ": "เกาหลีใต้", "TW": "ไต้หวัน", "TWO": "ไต้หวัน", "SI": "สิงคโปร์",
    "KL": "มาเลเซีย", "JK": "อินโดนีเซีย", "BK": "ไทย", "NS": "อินเดีย",
    "BO": "อินเดีย", "L": "สหราชอาณาจักร", "PA": "ฝรั่งเศส", "DE": "เยอรมนี",
    "F": "เยอรมนี", "SW": "สวิตเซอร์แลนด์", "AS": "เนเธอร์แลนด์", "MI": "อิตาลี",
    "AX": "ออสเตรเลีย", "TO": "แคนาดา", "VN": "เวียดนาม", "HM": "เวียดนาม",
}


# Bloomberg exchange code (the 2-letter tail of tickers the SEC data carries,
# e.g. "700 HK", "2330 TT", "AAPL US") -> country. Distinct from Yahoo suffixes.
BLOOMBERG_COUNTRY = {
    "HK": "ฮ่องกง", "TT": "ไต้หวัน", "JP": "ญี่ปุ่น", "JT": "ญี่ปุ่น",
    "US": "สหรัฐฯ", "UW": "สหรัฐฯ", "UN": "สหรัฐฯ", "UQ": "สหรัฐฯ",
    "SP": "สิงคโปร์", "LN": "สหราชอาณาจักร", "C1": "จีน", "C2": "จีน",
    "CH": "จีน", "CG": "จีน", "IN": "อินเดีย", "IS": "อินเดีย",
    "VN": "เวียดนาม", "KS": "เกาหลีใต้", "MK": "มาเลเซีย", "IJ": "อินโดนีเซีย",
    "AU": "ออสเตรเลีย", "GR": "เยอรมนี", "FP": "ฝรั่งเศส", "NA": "เนเธอร์แลนด์",
    "SW": "สวิตเซอร์แลนด์", "IM": "อิตาลี", "SM": "สเปน", "TB": "ไทย",
    "SS": "สวีเดน", "PM": "ฟิลิปปินส์", "CT": "แคนาดา",
}

# a Bloomberg ticker alias: "<symbol> <XX>" ending in a 2-letter exchange code
_BBG_RE = __import__("re").compile(r"^\S+ ([A-Z]{2})$")


def market_from_aliases(aliases: list[str] | None) -> str | None:
    """Listing market inferred from a Bloomberg-style ticker among the aliases."""
    for a in aliases or []:
        m = _BBG_RE.match(str(a).strip())
        if m and m.group(1) in BLOOMBERG_COUNTRY:
            return BLOOMBERG_COUNTRY[m.group(1)]
    return None


def market_of_symbol(symbol: str | None) -> str | None:
    """Listing market from a Yahoo symbol suffix; bare tickers are US listings."""
    if not symbol:
        return None
    s = str(symbol).strip()
    if "." in s:
        return SUFFIX_MARKET.get(s.rsplit(".", 1)[1].upper())
    # a plain alphabetic ticker with no suffix is a US listing (NVDA, PDD, AAPL)
    return "สหรัฐฯ" if s.replace("-", "").isalpha() else None


def prefix(isin: str | None) -> str:
    return (isin or "")[:2].upper()


def country_of_isin(isin: str | None) -> str | None:
    """Country name for an ISIN, or None if the prefix is unknown/blank."""
    return ISIN_COUNTRY.get(prefix(isin))


def is_domicile(isin: str | None) -> bool:
    """True when the ISIN is a fund/ETF domicile rather than a market."""
    return prefix(isin) in DOMICILE_PREFIXES


def _isin_of_entity(entity_id: str | None) -> str | None:
    """look-through exposures carry entity ids like 'isin:US0378331005'."""
    if entity_id and entity_id.startswith("isin:"):
        return entity_id.split(":", 1)[1]
    return None


def fund_country_mix(fund: dict, lookthrough: dict | None) -> dict:
    """Market-country breakdown for one fund, weighted by % of the fund.

    Returns {"rows": [(country, pct), ...] desc, "covered": float,
             "source": str}. `covered` is how much of the fund the breakdown
            accounts for; 100 - covered is the tail we cannot see through.
    """
    pid = fund.get("proj_id")
    weights: dict[str, float] = {}

    lt = (lookthrough or {}).get(pid) if lookthrough else None
    if lt and lt.get("exposures"):
        # feeder: resolved underlying holdings. Prefer the symbol suffix (the
        # listing market); fall back to the ISIN prefix when there is no symbol,
        # skipping fund-domicile ISINs so a Cayman shell is never a "market".
        for ex in lt["exposures"]:
            w = ex.get("pct_of_fund") or 0
            if not w:
                continue
            isin = _isin_of_entity(ex.get("entity"))
            c = market_of_symbol(ex.get("symbol"))
            if not c and isin and not is_domicile(isin):
                c = country_of_isin(isin)
            if c:
                weights[c] = weights.get(c, 0.0) + w
        covered = round(sum(weights.values()), 1)
        source = "look-through (Yahoo top holdings) · symbol/ISIN"
    else:
        # direct portfolio: each holding's own ISIN is its market
        for x in (fund.get("portfolio") or {}).get("items") or []:
            isin = x.get("isin")
            c = country_of_isin(isin)
            w = x.get("percent_nav") or 0
            if c and not is_domicile(isin) and w > 0:
                weights[c] = weights.get(c, 0.0) + w
        covered = round(sum(weights.values()), 1)
        source = "ISIN ของหลักทรัพย์ในพอร์ต (ISO 6166)"

    rows = sorted(((c, round(p, 1)) for c, p in weights.items()),
                  key=lambda kv: -kv[1])
    return {"rows": rows, "covered": covered, "source": source}
