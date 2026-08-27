"""
tagging.py - Faceted, investor-language tags for a fund, in Obsidian form.

The SEC data speaks in regulatory terms: a "policy = ตราสารหนี้, risk 1,
settlement T+1" fund is what an investor calls "a place to park cash you can pull
out tomorrow". This module turns the raw fields into a hierarchical tag set so
the vault answers questions the way people actually ask them - browse the
Obsidian tag pane or query with Dataview, no database required.

Tags nest with "/" (Obsidian's convention; the sister project's `asset:equity`
becomes `#asset/equity` here). Every tag in this file is DETERMINISTIC - derived
by rule from data already in funds.json - so it is reproducible and auditable.
Two facets are best-effort keyword matches and marked as such: `geo/*` beyond the
domestic split and `theme/*`; those are the ones an LLM pass would later sharpen.

    from tagging import investor_tags
    tags = investor_tags(fund)          # -> ["asset/fixed-income/money-market", ...]

Facets: asset · risk · liquidity · conc · fx · struct · style · use · tax ·
        compliance · geo · theme
"""
from __future__ import annotations

import re

# ---- asset class ---------------------------------------------------------
# policy is the trunk; sub-types are read from the policy text and fund name.
_POLICY_ASSET = {
    "ตราสารทุน": "equity",
    "ตราสารหนี้": "fixed-income",
    "ผสม": "mixed",
    "ทรัพย์สินทางเลือก": "alternative",
    "อื่น ๆ": "other",
}

# risk band 1-8(+) collapsed to five words an investor understands
_RISK_WORD = {
    "1": "very-low", "2": "low", "3": "low", "4": "moderate",
    "5": "moderate", "6": "high", "7": "very-high", "8": "very-high",
    "8+": "very-high",
}

# management style -> how the fund is run
_STYLE = {
    "AM": "active", "AN": "active", "PM": "passive", "PN": "passive",
    "SM": "enhanced-index", "IM": "inverse", "IN": "inverse",
    "LM": "leveraged", "LN": "leveraged", "BH": "buy-hold",
}

# keyword -> geo tag. Order matters: first hit wins for the primary region.
_GEO = [
    (r"เวียดนาม|vietnam", "geo/vietnam"),
    (r"อินเดีย|india", "geo/india"),
    (r"ญี่ปุ่น|japan", "geo/japan"),
    (r"เกาหลี|korea", "geo/korea"),
    (r"ไต้หวัน|taiwan", "geo/taiwan"),
    (r"จีน|china|a-?shares?|h-?shares?", "geo/china"),
    (r"เอเชีย|asia", "geo/asia-pacific"),
    (r"ยุโรป|europe|stoxx|เยอรมัน|german", "geo/europe"),
    (r"สหรัฐ|อเมริกา|\bus\b|u\.s\.|s&p ?500|nasdaq|russell", "geo/us"),
    (r"เกิดใหม่|emerging", "geo/emerging-markets"),
    (r"โกลบอล|global|world|ทั่วโลก", "geo/world"),
]

# keyword -> theme tag (best-effort; an LLM pass refines these later)
_THEME = [
    (r"เซมิคอนดักเตอร์|semiconductor|ชิป|\bchip", "theme/technology/semiconductor"),
    (r"\bai\b|เอไอ|artificial intel|robot|หุ่นยนต์", "theme/technology/ai-robotics"),
    (r"เทคโนโลยี|technology|\btech\b|internet|ดิจิทัล|digital|cloud|software",
     "theme/technology"),
    (r"สุขภาพ|health|biotech|pharma|เภสัช|medical|genomic", "theme/healthcare"),
    (r"พลังงานสะอาด|clean energy|renewable|ev[- ]?battery|electric vehicle|"
     r"รถไฟฟ้า|แบตเตอรี่|battery|solar|ยั่งยืน|\besg\b|sustainab",
     "theme/sustainability"),
    (r"พลังงาน|energy|น้ำมัน|oil|ปิโตร|petro", "theme/energy"),
    (r"อสังหา|property|reit|real ?estate", "theme/real-estate"),
    (r"ผู้บริโภค|consumer|อุปโภค", "theme/consumer"),
    (r"การเงิน|financ|ธนาคาร|bank", "theme/financials"),
    (r"ทองคำ|\bgold\b", "theme/metals-mining/gold"),
    (r"โครงสร้างพื้นฐาน|infrastructure", "theme/infrastructure"),
]

_HEDGE_DISCRETION = re.compile(r"ดุลยพินิจ|ตามความเหมาะสม|discretion", re.I)
_HEDGE_WORD = re.compile(r"ป้องกันความเสี่ยง.*อัตราแลกเปลี่ยน|hedg", re.I)


def _name_text(f: dict) -> str:
    """Just the fund's names - the reliable signal for theme and geography.

    The investment-policy field is boilerplate that mentions banks, energy,
    sustainability and every asset class in passing, so matching themes against
    it tags a gold fund as 'financials'. The name is what the AMC chose to say
    the fund IS, so themes and regions are read from the name only.
    """
    return " ".join(str(f.get(k) or "") for k in
                    ("name_th", "name_en", "abbr")).lower()


def _text(f: dict) -> str:
    """Name + policy text. Used only where the policy wording is the point
    (money-market/short-term sub-type, currency-hedging intent)."""
    return " ".join(str(f.get(k) or "") for k in
                    ("name_th", "name_en", "abbr", "investment_policy",
                     "policy")).lower()


def _asset_tags(f: dict, text: str) -> list[str]:
    policy = f.get("policy") or ""
    base = _POLICY_ASSET.get(policy, "other")
    out = [f"asset/{base}"]

    if base == "fixed-income":
        risk = str(f.get("risk_spectrum") or "")
        if "ตลาดเงิน" in policy or "ตลาดเงิน" in text or "money market" in text:
            out.append("asset/fixed-income/money-market")
        elif re.search(r"ระยะสั้น|short|เดลี่|daily|3 เดือน|6 เดือน", text) \
                or risk in ("1", "2"):
            out.append("asset/fixed-income/short-term")
    elif base == "alternative":
        if re.search(r"ทองคำ|\bgold\b", text):
            out.append("asset/commodity/gold")
        elif re.search(r"น้ำมัน|\boil\b", text):
            out.append("asset/commodity/oil")
        elif re.search(r"อสังหา|property|reit|real ?estate|โครงสร้างพื้นฐาน|infra",
                       text):
            out.append("asset/real-estate")
    return out


def _concentration_tags(f: dict) -> list[str]:
    """From how many names the fund holds - data we already carry per fund.

    A feeder holding one master fund is not 'ultra-concentrated' in the risky
    sense, so feeders are left out of this facet; it describes direct portfolios.
    """
    # concentration is a signal only for stock-picking portfolios; a bond or
    # money-market fund naturally holds dozens of short instruments and calling
    # that "focused" misleads. Restrict to equity / mixed / alternative.
    if (f.get("policy") or "") not in ("ตราสารทุน", "ผสม", "ทรัพย์สินทางเลือก"):
        return []
    pf = f.get("portfolio") or {}
    n = pf.get("total_rows")
    if not n or f.get("feeder_master"):
        return []
    if n <= 10:
        return ["conc/ultra-concentrated/ten-stock", "conc/ultra-concentrated"]
    if n < 15:
        return ["conc/ultra-concentrated"]
    if n <= 40:
        return ["conc/concentrated"]
    if n <= 100:
        return ["conc/focused"]
    return ["conc/total-market"]


def _fx_tags(f: dict, text: str) -> list[str]:
    # a domestic-only fund has no currency to hedge
    if f.get("invest_country_flag") == "3":
        return []
    hedged = None
    for row in f.get("statistics") or []:
        v = row.get("fx_hedging")
        try:
            hedged = float(v)
            break
        except (TypeError, ValueError):
            continue
    if hedged is not None and hedged > 0:
        if hedged >= 90:
            return ["fx/fully-hedged"]
        if hedged >= 10:
            return ["fx/partially-hedged"]
    if _HEDGE_DISCRETION.search(text) and _HEDGE_WORD.search(text):
        return ["fx/discretionary"]
    if _HEDGE_WORD.search(text):
        return ["fx/discretionary"]
    return ["fx/unhedged"]


def _struct_tags(f: dict) -> list[str]:
    style = f.get("management_style") or ""
    if f.get("feeder_master") or style in ("AN", "PN", "IN", "LN"):
        return ["struct/feeder"]
    return ["struct/direct"]


def _liquidity_tags(f: dict) -> list[str]:
    days = set()
    for d in f.get("dealing_periods") or []:
        typ = str(d.get("type") or "")
        if "redemp" in typ.lower() or "ขายคืน" in typ:
            m = re.search(r"[Tt]\s*\+?\s*(\d)", d.get("settlement_period") or "")
            if m:
                days.add(int(m.group(1)))
    # Obsidian tags cannot contain "+", so T+1 becomes the tag `liquidity/t1`
    return [f"liquidity/t{min(days)}"] if days else []


def _use_tags(f: dict, tags: set[str]) -> list[str]:
    out = []
    if {"asset/fixed-income/money-market", "asset/fixed-income/short-term"} & tags \
            and str(f.get("risk_spectrum") or "") in ("1", "2", "3"):
        out.append("use/park-cash")
    if any(t.startswith("tax/") for t in tags):
        out.append("use/tax-saving")
    if "style/dividend" in tags:
        out.append("use/income")
    if any(t.startswith("theme/") for t in tags) and "use/park-cash" not in out:
        out.append("use/thematic")
    if not out:
        out.append("use/accumulate")
    return out


def investor_tags(f: dict) -> list[str]:
    """The full faceted tag set for a fund. Deterministic and order-stable."""
    text = _text(f)          # name + policy: for asset sub-type & hedging intent
    name = _name_text(f)     # name only: for theme, geography, compliance
    tags: list[str] = []

    tags += _asset_tags(f, text)
    if f.get("risk_spectrum"):
        word = _RISK_WORD.get(str(f["risk_spectrum"]))
        if word:
            tags.append(f"risk/{word}")
    tags += _liquidity_tags(f)
    tags += _concentration_tags(f)
    tags += _fx_tags(f, text)
    tags += _struct_tags(f)

    style = _STYLE.get(f.get("management_style") or "")
    if style:
        tags.append(f"style/{style}")
    if (f.get("dividend_policy") or [{}])[0].get("pays_dividend") == "Y":
        tags.append("style/dividend")

    # tax / compliance
    taxes = {str(c.get("tax_incentive") or "") for c in f.get("classes") or []}
    if any("SSF" in t for t in taxes):
        tags.append("tax/ssf")
    if any("ESG" in t for t in taxes):
        tags += ["tax/thai-esg", "compliance/sri-fund"]
    if "RMF" in str(f.get("abbr") or "").upper():
        tags.append("tax/rmf")
    if re.search(r"ชารีอะห์|อิสลาม|sharia|islamic", name):
        tags.append("compliance/sharia")
    if re.search(r"ทริกเกอร์|trigger", name):
        tags.append("compliance/trigger-fund")

    # geography: domestic split first, then the first keyword region (name only)
    if f.get("invest_country_flag") == "3":
        tags.append("geo/thailand")
    for pat, tag in _GEO:
        if re.search(pat, name, re.I):
            tags.append(tag)
            break

    # theme (best-effort keyword on the name; refined by a later LLM pass)
    for pat, tag in _THEME:
        if re.search(pat, name, re.I):
            tags.append(tag)
            break

    tags += _use_tags(f, set(tags))

    # de-duplicate, keep first-seen order
    seen: set[str] = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out
