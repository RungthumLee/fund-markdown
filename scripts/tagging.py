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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import securities  # noqa: E402  (dormant until fetch_sectors.py has run)

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

# NOTE: theme/* and geo/* facets were removed on purpose. They were the only
# keyword-guessed tags (read from the fund name) and were not reliable enough -
# "China AI" is better answered by the AIMC peer_group ("Greater China Equity",
# "Technology Equity"), which is real factsheet data, not a guess. Clustering
# lives in the by-peer-group index instead. Everything below is deterministic.

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


def _is_rmf(f: dict, name: str) -> bool:
    """RMF has no flag in the source: `fund_class_tax_incentive_type` only ever
    carries SSF and Thai ESG (verified across every profile row). The registered
    Thai name does carry it — "เพื่อการเลี้ยงชีพ" is the statutory designation an
    RMF must use — so the name, not the abbreviation, is the signal.

    Measured on the full profile dump: the Thai phrase plus the English wording
    covers 379 projects and is a strict superset of the 341 the old abbreviation
    match found, adding real RMFs it missed (SCBRMS&P500, M-VALUE, SCB2576)
    whose abbreviation never spells "RMF". See OUT-001.
    """
    if "เพื่อการเลี้ยงชีพ" in name:
        return True
    if re.search(r"rmf|retirement", name):
        return True
    return "RMF" in str(f.get("abbr") or "").upper()


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


def _duration_years(text) -> float | None:
    """Parse a Thai duration like '3 ปี 6 เดือน' or '9 เดือน' into years.

    fs_statistics stores duration as free text, not a number, so it has to be
    read out: sum the ปี (years) and เดือน (months) parts. Also accepts a bare
    numeric string as years.
    """
    if isinstance(text, (int, float)):
        return float(text) or None
    s = str(text or "")
    yrs = re.search(r"(\d+(?:\.\d+)?)\s*ปี", s)
    mos = re.search(r"(\d+(?:\.\d+)?)\s*เดือน", s)
    total = (float(yrs.group(1)) if yrs else 0) + (float(mos.group(1)) / 12 if mos else 0)
    if not total:
        try:
            total = float(s)
        except ValueError:
            return None
    return total or None


def _bond_tags(f: dict) -> list[str]:
    """Duration band and credit quality for a bond/mixed fund, from real data.

    duration comes from fs_statistics (years); credit from the factsheet's rating
    breakdown. Both are stated only when the fund actually reports them.
    """
    out: list[str] = []
    if (f.get("policy") or "") not in ("ตราสารหนี้", "ผสม"):
        return out

    durs = [_duration_years(s.get("duration")) for s in f.get("statistics") or []]
    durs = [v for v in durs if v]
    if durs:
        d = max(durs)
        out.append("duration/short" if d < 1.5
                   else "duration/medium" if d <= 5 else "duration/long")

    ratings = (f.get("factsheet_sections") or {}).get("credit_ratings") or []
    if ratings:
        # a band counts as sub-investment-grade if it names BB/B/C/unrated and
        # carries a meaningful weight; a government band is its own signal
        hy = gov = 0.0
        for r in ratings:
            name = str(r.get("name") or "").upper()
            pct = r.get("percent") or 0
            if re.search(r"\bBB|\bB[/ ]|\bC[C/ ]|UNRATED|NON.?INVESTMENT|ต่ำกว่า|ไม่จัดอันดับ",
                         name):
                hy += pct
            if "GOV" in name or "รัฐบาล" in name:
                gov += pct
        if hy >= 10:
            out.append("credit/high-yield")
        elif gov >= 50:
            out.append("credit/government")
        else:
            out.append("credit/investment-grade")
    return out


# Factsheet sector name (Thai SET group or English GICS) -> canonical sector.
# This is NOT a fund-name keyword guess (the reason theme/geo were dropped): it
# reads the factsheet's actual sector allocation, so it is real reported data.
_SECTOR_MAP = [
    (r"ธนาคาร|เงินทุน|หลักทรัพย์|ประกัน|financ|\bbank|insurance", "financials"),
    (r"เทคโนโลยี|สารสนเทศ|อิเล็กทรอนิก|อิเลคโทรนิค|information tech|technology|"
     r"semiconductor|\btech\b|software", "technology"),
    (r"สื่อสาร|โทรคมนาคม|communication|telecom", "communication"),
    # energy before utilities: SET groups them as "พลังงานและสาธารณูปโภค", which
    # is dominated by energy names (PTT, GULF); standalone utilities falls through
    (r"พลังงาน|energy|น้ำมัน|ปิโตรเลียม|oil|gas", "energy"),
    (r"สาธารณูปโภค|utilit", "utilities"),
    (r"อสังหา|real ?estate|property|กองทรัสต์|reit", "real-estate"),
    (r"การแพทย์|สุขภาพ|health|pharma|biotech|medical", "healthcare"),
    (r"ขนส่ง|โลจิสติกส์|industr|อุตสาหกรรม|เครื่องจักร|transport", "industrials"),
    (r"วัสดุ|material|ปิโตรเคมี|เคมี|chemical|เหล็ก|steel|mining|เหมือง", "materials"),
    (r"พาณิชย์|consumer|อาหาร|เครื่องดื่ม|ค้าปลีก|retail|ท่องเที่ยว|สันทนาการ|"
     r"tourism|media|บันเทิง", "consumer"),
]


def _sector_tags(f: dict) -> list[str]:
    """Canonical sector(s) from the factsheet's own allocation - the dominant
    sector, plus any other carrying >= 25% of the equity sleeve."""
    sectors = (f.get("factsheet_sections") or {}).get("sectors") or []
    if not sectors:
        return []
    ranked = sorted(
        ((s.get("name") or "", s.get("percent") or 0) for s in sectors),
        key=lambda kv: -kv[1])
    out: list[str] = []
    for i, (name, pct) in enumerate(ranked):
        if i > 0 and pct < 25:
            break
        for pat, canon in _SECTOR_MAP:
            if re.search(pat, name, re.I):
                tag = f"sector/{canon}"
                if tag not in out:
                    out.append(tag)
                break
    return out[:2]


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
    tags += _bond_tags(f)
    # sector: the factsheet allocation first; Yahoo (via look-through) only fills
    # in when the factsheet gave none. cap/* comes from Yahoo market caps. Both
    # securities.* calls are no-ops until fetch_sectors.py has run.
    _sect = _sector_tags(f)
    tags += _sect
    if not _sect:
        tags += securities.fund_sector_tags(f)
    tags += securities.fund_cap_tags(f)
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
    if _is_rmf(f, name):
        tags.append("tax/rmf")
    if re.search(r"ชารีอะห์|อิสลาม|sharia|islamic", name):
        tags.append("compliance/sharia")
    if re.search(r"ทริกเกอร์|trigger", name):
        tags.append("compliance/trigger-fund")

    tags += _use_tags(f, set(tags))

    # de-duplicate, keep first-seen order
    seen: set[str] = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---- plain-language summary ---------------------------------------------
# The point of the tag layer: turn the facets back into a sentence an ordinary
# reader understands, instead of "policy=ตราสารหนี้, risk 1, settlement T+1".

_ASSET_PHRASE = {
    "asset/fixed-income/money-market": "กองตลาดเงิน",
    "asset/fixed-income/short-term": "กองตราสารหนี้ระยะสั้น",
    "asset/fixed-income": "กองตราสารหนี้",
    "asset/equity": "กองหุ้น",
    "asset/mixed": "กองผสม",
    "asset/commodity/gold": "กองทองคำ",
    "asset/commodity/oil": "กองน้ำมัน",
    "asset/real-estate": "กองอสังหา/REIT",
    "asset/alternative": "กองสินทรัพย์ทางเลือก",
    "asset/other": "กองประเภทอื่น",
}
_RISK_PHRASE = {"very-low": "ความเสี่ยงต่ำมาก", "low": "ความเสี่ยงต่ำ",
                "moderate": "ความเสี่ยงปานกลาง", "high": "ความเสี่ยงสูง",
                "very-high": "ความเสี่ยงสูงมาก"}
_USE_PHRASE = {"park-cash": "พักเงินระยะสั้น", "income": "รับกระแสเงินปันผล",
               "tax-saving": "ลดหย่อนภาษี", "accumulate": "สะสมระยะยาว"}
_FX_PHRASE = {"fx/fully-hedged": "ป้องกันความเสี่ยงค่าเงินเต็มจำนวน",
              "fx/partially-hedged": "ป้องกันค่าเงินบางส่วน",
              "fx/discretionary": "ป้องกันค่าเงินตามดุลยพินิจผู้จัดการ",
              "fx/unhedged": "ไม่ป้องกันความเสี่ยงค่าเงิน"}


_SECTOR_SUMMARY_TH = {
    "financials": "การเงิน/ธนาคาร", "technology": "เทคโนโลยี", "communication": "สื่อสาร",
    "energy": "พลังงาน", "utilities": "สาธารณูปโภค", "real-estate": "อสังหา/REIT",
    "healthcare": "การแพทย์/สุขภาพ", "industrials": "อุตสาหกรรม", "materials": "วัสดุ/โลหะ",
    "consumer": "สินค้า/บริการผู้บริโภค",
}


def plain_summary(f: dict, ter: float | None = None,
                  market_country: str | None = None) -> str:
    """One-paragraph, investor-language description built from the fund's own
    facts. Deterministic - no claim the data does not support, no prediction."""
    tags = investor_tags(f)
    tset = set(tags)

    # asset: the most specific asset/* tag wins
    asset = next((_ASSET_PHRASE[t] for t in sorted(tags, key=len, reverse=True)
                  if t in _ASSET_PHRASE), "กองทุนรวม")
    parts = [asset]

    risk = next((_RISK_PHRASE[t.split("/")[1]] for t in tags
                 if t.startswith("risk/")), None)
    rn = f.get("risk_spectrum")
    if risk:
        parts.append(f"{risk} ({rn}/8)" if rn else risk)

    uses = [_USE_PHRASE[t.split("/")[1]] for t in tags
            if t.startswith("use/") and t.split("/")[1] in _USE_PHRASE]
    if uses:
        parts.append("เหมาะกับ" + " / ".join(uses))

    # settlement (reliable, from dealing periods)
    liq = next((t for t in tags if t.startswith("liquidity/")), None)
    if liq:
        parts.append(f"ขายคืนแล้วได้เงินภายใน {liq.split('/')[1].upper().replace('T','T+')}")

    # dominant sector (from factsheet/Yahoo), stated in plain Thai
    sect = next((_SECTOR_SUMMARY_TH[t.split("/", 1)[1]] for t in tags
                 if t.startswith("sector/") and t.split("/", 1)[1] in _SECTOR_SUMMARY_TH),
                None)
    if sect:
        parts.append(f"เน้นกลุ่ม{sect}")

    # domestic vs foreign from the flag, plus the dominant market and hedging
    flag = f.get("invest_country_flag")
    if flag == "3":
        parts.append("ลงทุนในประเทศ ไม่มีความเสี่ยงค่าเงิน")
    elif flag in ("1", "2", "4"):
        fx = next((_FX_PHRASE[t] for t in tags if t in _FX_PHRASE), None)
        where = f"ลงทุนต่างประเทศ ({market_country})" if market_country else "ลงทุนต่างประเทศ"
        parts.append(where + (f" · {fx}" if fx else ""))

    if "struct/feeder" in tset:
        parts.append("ลงทุนผ่านกองทุนหลัก (feeder)")
    if "style/passive" in tset:
        parts.append("บริหารแบบอิงดัชนี (passive)")
    elif "style/active" in tset:
        parts.append("บริหารเชิงรุก (active)")

    if any(t.startswith("conc/") for t in tags) and "asset/equity" in tset:
        n = (f.get("portfolio") or {}).get("total_rows")
        if n:
            parts.append(f"พอร์ตถือราว {n} หลักทรัพย์")

    if ter is not None:
        parts.append(f"ค่าธรรมเนียมรวมที่รายย่อยจ่ายจริงราว {ter:.2f}%/ปี")

    tax = [t.split("/")[1].upper() for t in tags if t.startswith("tax/")]
    if tax:
        parts.append("ได้สิทธิลดหย่อนภาษี (" + "/".join(tax) + ")")

    return " · ".join(parts)
