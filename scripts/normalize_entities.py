"""
normalize_entities.py - Resolve every portfolio holding to a canonical entity.

The problem
-----------
The same company appears in the SEC portfolio data under a dozen spellings,
because each AMC exports from a different system. For SPDR Gold Shares alone
the `name` field contains:

    B046RT1 US · US78463V1070 · GLDSP · 2840 HK · SPDR SP · B3B85M0F

...which is a SEDOL, an ISIN, two vendor tickers, a Bloomberg-style ticker with
an exchange code, and another SEDOL. The `issuer` field is no cleaner:
"World Gold Trust Services" / "World Gold Trust Service., LLC" / "WGC" /
"STATE STREET BANK AND TRUST COMPANY".

Without resolution you cannot answer "which Thai funds hold Microsoft", and
every concentration number is understated because one position is split across
several spellings.

How it resolves
---------------
1. **ISIN is truth.** 59% of holding rows carry one, and an ISIN identifies a
   security exactly. All rows sharing an ISIN are one entity, full stop.
2. **Rows without an ISIN** fall back to a normalised name key: exchange and
   vendor suffixes stripped ("MSFT US Equity", "MSFTUW", "MSFT.US" -> "MSFT"),
   legal forms stripped (PCL / PLC / LLC / INC / บมจ. / จำกัด (มหาชน)), then
   uppercased and de-punctuated. Only **exact** normalised-key matches merge -
   fuzzy matching would happily fold "CP ALL" into "CP AXTRA".
3. **The display name is chosen by quality, not by vote.** Voting picks
   `B046RT1 US` for gold because the SEDOL happens to be most common. Instead
   every candidate string is scored: identifier-shaped strings (ISIN, SEDOL,
   ticker+exchange) score below zero, real names with spaces and mixed case
   score highest, and the master-fund registry - which has properly-cased
   names from Yahoo and FT - wins outright when the ISIN is known there.

Output: data/processed/entities.json plus an `entity` field written back onto
every holding in funds.json.

    python scripts/normalize_entities.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("normalize_entities")
PROC = ROOT / "data" / "processed"
FUNDS = PROC / "funds.json"
MASTERS = PROC / "master_funds.json"
CACHE = ROOT / "data" / "masters"
OUT = PROC / "entities.json"
FIGI = PROC / "figi.json"

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
# a SEDOL is 7 alphanumerics with no vowels; vendor feeds paste them into `name`
SEDOL_RE = re.compile(r"^[B-DF-HJ-NP-TV-XZ0-9]{7}$")

# Bloomberg / vendor decoration that follows a ticker.
#   "MSFT US Equity" · "MSFTUW" · "MSFT.US" · "GRID_US_USD" · "HPG VN-E"
EXCHANGE_CODES = (
    "US UW UQ UN UP UR UA HK JP JT VN SP SG LN L GR GY SW SS SZ CH TB TT KS "
    "KP AU AT IM MK ID IN IS NA AS FP PA MC SM BB TI IJ PM CN C1"
)
EX_SET = set(EXCHANGE_CODES.split())

SUFFIX_TAIL = re.compile(
    r"(?:\s+EQUITY|\s+CORP|\s+INDEX|\s+COMDTY|\s+CURNCY)\s*$", re.I)

LEGAL_FORMS = [
    "PUBLIC COMPANY LIMITED", "PUBLIC CO LTD", "COMPANY LIMITED",
    "PUBLIC LIMITED COMPANY", "INCORPORATED", "CORPORATION", "LIMITED",
    "HOLDINGS", "HOLDING", "GROUP", "PCL", "PLC", "LLC", "LP", "LLP", "INC",
    "CORP", "CO LTD", "CO", "LTD", "NV", "SA", "AG", "SE", "SPA", "ASA",
    "AB", "OYJ", "BHD", "TBK", "PT", "KK", "GMBH", "SICAV", "ETF", "TRUST",
]
LEGAL_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in LEGAL_FORMS) + r")\b\.?", re.I)

THAI_PREFIX = re.compile(r"^(บริษัท|บมจ\.?|บลจ\.?|ธนาคาร)\s*")
THAI_SUFFIX = re.compile(r"\s*\(?\s*(จำกัด\s*\(?มหาชน\)?|จำกัด|มหาชน)\s*\)?\s*$")

# assetliab_id groups. Different kinds must never merge with each other: a
# bank appears both as an equity and as the counterparty of a deposit.
KIND_BY_CODE = {
    "101": "equity", "102": "equity", "105": "equity", "106": "equity",
    "103": "bond", "104": "bond", "213": "govbond", "214": "govbond",
    "203": "bill", "204": "bill", "205": "bill", "206": "bill",
    "216": "deposit", "217": "deposit", "218": "deposit", "219": "deposit",
    "108": "fund", "109": "fund", "117": "fund", "118": "fund", "119": "fund",
    "120": "fund", "121": "fund", "130": "reit", "139": "fund",
    "401": "derivative", "402": "derivative", "403": "derivative",
    "404": "derivative",
}
KIND_LABEL = {
    "equity": "หุ้น", "bond": "หุ้นกู้", "govbond": "พันธบัตร",
    "bill": "ตั๋วเงิน", "deposit": "เงินฝาก", "fund": "หน่วยลงทุน",
    "reit": "กองทรัสต์/REIT", "derivative": "สัญญาอนุพันธ์",
    "other": "อื่น ๆ",
}
# For a deposit the security "name" is the account number; the entity that
# matters is the bank holding the money, which is in `issuer`.
COUNTERPARTY_KINDS = {"derivative", "deposit"}

# Derivative rows name an internal contract id ("CFX131239", "FWUSDTHB26N13L")
# and carry NO issuer at all - all 19,424 of them. There is no entity in the
# data to resolve, so making one per contract would add ~18k junk entities that
# no two funds ever share. They are counted and skipped instead.
UNRESOLVABLE_KINDS = {"derivative"}


def strip_accents(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def clean_ticker(text: str) -> str:
    """Reduce a vendor ticker to the bare symbol, or return '' if it is not one."""
    s = re.sub(r"[\s_.\-/]+", " ", text.strip().upper()).strip()
    s = SUFFIX_TAIL.sub("", s).strip()
    parts = s.split()
    if len(parts) >= 2 and parts[-1] in EX_SET:
        return " ".join(parts[:-1])
    if len(parts) == 1:
        token = parts[0]
        # "MSFTUW" / "IVVUP" - a symbol with the exchange code glued on.
        # Some feeds add a lower-case 'a' that survives the upper() above.
        token = re.sub(r"A$", "", token) if re.search(
            r"[A-Z]{2}A$", token) and token[-3:-1] in EX_SET else token
        for code in sorted(EX_SET, key=len, reverse=True):
            if len(token) > len(code) + 1 and token.endswith(code):
                return token[: -len(code)]
        return token
    return s


def norm_key(text: str) -> str:
    """The key two spellings must share to be treated as the same entity."""
    s = strip_accents(text).strip()
    if not s:
        return ""
    s = THAI_PREFIX.sub("", s)
    s = THAI_SUFFIX.sub("", s)
    s = clean_ticker(s) if not re.search(r"[ก-๙]", s) else s.upper()
    s = LEGAL_RE.sub(" ", s)
    s = re.sub(r"[^A-Z0-9ก-๙ ]+", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


def name_quality(text: str) -> int:
    """How much a string looks like a real name rather than an identifier."""
    s = (text or "").strip()
    if not s:
        return -100
    upper = s.upper()
    if ISIN_RE.match(upper):
        return -50
    if SEDOL_RE.match(upper) and not re.search(r"[aeiouAEIOU]", s):
        return -40
    # "NVDA US" is two words but it is still a ticker: the second word is an
    # exchange code. Without this it collected the multi-word bonus and beat
    # the real name Yahoo had for it.
    #
    # Only applied to strings with no lower-case letter. clean_ticker strips a
    # trailing " CORP" because Bloomberg appends it as a security-type suffix,
    # which turned the real name "NVIDIA Corp" into "NVIDIA" and scored it -20
    # as though it were a ticker. Vendor tickers are always upper-case, so the
    # presence of a lower-case letter is a reliable way to tell them apart.
    if not re.search(r"[ก-๙]", s) and not re.search(r"[a-z]", s):
        bare = clean_ticker(s)
        if bare and " " not in bare and len(bare) <= 6 and bare.isupper():
            return -20

    score = 0
    words = s.split()
    if len(words) >= 2:
        score += 25
    if len(s) >= 12:
        score += 15
    elif len(s) >= 7:
        score += 5
    if re.search(r"[a-z]", s) and re.search(r"[A-Z]", s):
        score += 15         # Mixed Case reads as a name, not a ticker
    if re.search(r"[ก-๙]", s):
        score += 20
    if len(s) <= 5 and s.isupper():
        score -= 15         # bare ticker
    if re.search(r"[_/]", s) or re.fullmatch(r"[A-Z0-9]{2,8}", upper):
        score -= 10
    return score


# a multi-word string already scores 25; below that we are looking at a
# ticker, an ISIN or a SEDOL and any real name is an improvement
REAL_NAME_SCORE = 25


def best_name(candidates: Counter) -> str:
    """Pick the most name-like string, breaking ties by how often it appears."""
    if not candidates:
        return ""
    return max(candidates.items(),
               key=lambda kv: (name_quality(kv[0]), kv[1], -len(kv[0])))[0]


# Words that carry no identity, so "PTT PCL" and "PTT PUBLIC COMPANY LIMITED"
# are not seen as different companies. Used only to decide whether a chosen
# name agrees with the filed issuer (ISS-035).
_NOISE = set(
    "the of and for public company limited co ltd inc incorporated corporation "
    "corp plc pcl fund trust holding holdings group ordinary shares class acc "
    "จำกัด มหาชน บริษัท กองทุน บมจ หน่วยลงทุน".split()
)

# An issuer that is an asset manager means the holding is units of another fund,
# so its name legitimately differs from the issuer and must not be overridden.
_ISSUER_IS_MANAGER = re.compile(
    r"asset management|จัดการกองทุน|หลักทรัพย์จัดการ|บลจ|securities|sicav|"
    r"investment management|fund management",
    re.I,
)


def identity_tokens(text: str) -> set[str]:
    """Significant tokens of a name; stopwords and single characters removed."""
    s = re.sub(r"[^a-z0-9ก-๙ ]", " ", (text or "").lower())
    return {t for t in s.split() if len(t) >= 2 and t not in _NOISE}


def master_names() -> dict[str, str]:
    """ISIN -> properly-cased name, from the master registry we already built."""
    out: dict[str, str] = {}
    if not MASTERS.exists():
        return out
    masters = json.loads(MASTERS.read_text(encoding="utf-8"))
    for key, entry in masters.items():
        isin = (entry.get("isin") or "").upper()
        if not ISIN_RE.match(isin):
            continue
        path = CACHE / f"{key.replace(':', '_').replace('/', '_')[:80]}.json"
        name = entry.get("display_name")
        if path.exists():
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                rec = {}
            y, ft = rec.get("yahoo") or {}, rec.get("ft") or {}
            name = y.get("longName") or ft.get("name") or name
        if name:
            out[isin] = name
    return out


def holding_names() -> dict[str, str]:
    """normalised ticker -> properly-cased company name, from Yahoo.

    The Thai filings often carry only a vendor ticker for a foreign share, so
    the best name scoring can find for Nvidia is "NVDA US". Yahoo publishes the
    top holdings of the master funds with real names attached, keyed by the
    same symbol - "NVDA" -> "NVIDIA Corp". Joining on the normalised symbol
    upgrades those entities and, because the master holdings then resolve to a
    known entity, makes the look-through join work at all.
    """
    out: dict[str, str] = {}
    if not MASTERS.exists():
        return out
    masters = json.loads(MASTERS.read_text(encoding="utf-8"))
    for key in masters:
        path = CACHE / f"{key.replace(':', '_').replace('/', '_')[:80]}.json"
        if not path.exists():
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for h in (rec.get("yahoo") or {}).get("top_holdings") or []:
            name = str(h.get("name") or "").strip()
            symbol = str(h.get("symbol") or "").strip()
            if not name or not symbol:
                continue
            # "ASML.AS" / "7013.T" / "HSBA.L" - the exchange suffix is not part
            # of the identity the Thai feed uses
            bare = symbol.split(".")[0]
            for candidate in (norm_key(bare), norm_key(name)):
                if candidate and name_quality(name) > name_quality(
                        out.get(candidate, "")):
                    out[candidate] = name
    return out


def load_figi() -> dict:
    """Bloomberg symbology from the previous run of fetch_figi.py.

    One run behind on purpose: fetch_figi reads entities.json to know what to
    ask about, so a brand-new security is annotated on the next pass. ISINs do
    not change, so the lag only ever affects genuinely new holdings.
    """
    if not FIGI.exists():
        return {}
    try:
        data = json.loads(FIGI.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {k: v for k, v in data.items() if v.get("found")}


def main() -> None:
    funds = json.loads(FUNDS.read_text(encoding="utf-8"))
    from_masters = master_names()
    from_holdings = holding_names()
    figi = load_figi()
    if figi:
        LOG.info("openfigi supplies symbology for %d entities", len(figi))
    LOG.info("master registry supplies %d clean names by ISIN", len(from_masters))
    LOG.info("master top-holdings supply %d clean names by ticker",
             len(from_holdings))

    # ---- pass 1: group rows into entities ------------------------------
    groups: dict[str, dict] = {}
    isin_of_key: dict[str, str] = {}          # norm key -> isin, to fold later
    skipped: Counter[str] = Counter()
    rows = 0

    def group_for(eid: str) -> dict:
        return groups.setdefault(eid, {
            "id": eid, "isin": None, "kind": None,
            "names": Counter(), "issuers": Counter(),
            "funds": {}, "aliases": Counter(),
        })

    for pid, fund in funds.items():
        for item in (fund.get("portfolio") or {}).get("items") or []:
            rows += 1
            code = str(item.get("type_code") or "")
            kind = KIND_BY_CODE.get(code, "other")
            name = (item.get("name") or "").strip()
            issuer = (item.get("issuer") or "").strip()
            isin = (item.get("isin") or "").strip().upper()

            # Some AMCs put the ISIN in the security *name* and leave the isin
            # column empty - 595 rows do this. Without picking it up, Apple,
            # Amazon, NVIDIA and Visa each end up as two entities: one keyed by
            # ISIN from the AMCs that filed it properly, and one keyed by the
            # ISIN-as-a-name from those that did not.
            # ...but never for a deposit, whose `name` is an account code:
            # SAUOBTSMART2 and FCCNHKBCHTG2 happen to fit the ISIN shape
            # (two letters, nine alphanumerics, a digit) without being one.
            if (not ISIN_RE.match(isin) and ISIN_RE.match(name.upper())
                    and kind not in COUNTERPARTY_KINDS):
                isin = name.upper()

            # a deposit or an FX forward is really an exposure to the bank
            if kind in UNRESOLVABLE_KINDS:
                skipped[kind] += 1
                continue
            label = issuer if kind in COUNTERPARTY_KINDS and issuer else name
            key = norm_key(label) or norm_key(issuer) or norm_key(name)
            if not key and not ISIN_RE.match(isin):
                skipped["no-identifier"] += 1
                continue

            if ISIN_RE.match(isin) and kind not in COUNTERPARTY_KINDS:
                eid = f"isin:{isin}"
                if key:
                    isin_of_key.setdefault(key, eid)
            else:
                eid = f"{kind}:{key}"

            g = group_for(eid)
            g["kind"] = g["kind"] or kind
            if ISIN_RE.match(isin):
                g["isin"] = g["isin"] or isin
            # for a deposit the name is an account number, not an alias
            if name and kind not in COUNTERPARTY_KINDS:
                g["names"][name] += 1
                g["aliases"][name] += 1
            if issuer:
                g["issuers"][issuer] += 1
                g["aliases"][issuer] += 1
            g["funds"][pid] = max(g["funds"].get(pid, 0),
                                  item.get("percent_nav") or 0)

    LOG.info("pass 1: %d rows -> %d raw groups (skipped %s)",
             rows, len(groups), json.dumps(dict(skipped)))

    # ---- pass 2: fold name-keyed groups into their ISIN twin -----------
    # "MSFT US" with no ISIN on one AMC's export is the same security as
    # "Microsoft Corp" carrying US5949181045 on another's.
    merged = 0
    for eid in list(groups):
        if eid.startswith("isin:"):
            continue
        kind, _, key = eid.partition(":")
        if kind in COUNTERPARTY_KINDS:
            continue
        target = isin_of_key.get(key)
        if not target or target not in groups:
            continue
        src, dst = groups.pop(eid), groups[target]
        dst["names"].update(src["names"])
        dst["issuers"].update(src["issuers"])
        dst["aliases"].update(src["aliases"])
        for pid, pct in src["funds"].items():
            dst["funds"][pid] = max(dst["funds"].get(pid, 0), pct)
        merged += 1
    LOG.info("pass 2: folded %d name-only groups into an ISIN entity", merged)

    # ---- pass 3: name + finalise ---------------------------------------
    entities: dict[str, dict] = {}
    for eid, g in groups.items():
        isin = g["isin"]
        scored = best_name(g["issuers"] + g["names"]
                           if g["kind"] in COUNTERPARTY_KINDS
                           else g["names"] + g["issuers"])
        # Yahoo's name only wins where our own is a bare identifier; a Thai
        # company's registered name is better than anything Yahoo has for it
        from_ticker = ""
        if g["kind"] not in COUNTERPARTY_KINDS:
            for alias in list(g["names"]) + [scored]:
                cand = from_holdings.get(norm_key(alias))
                if cand and name_quality(cand) > name_quality(from_ticker):
                    from_ticker = cand
        display = from_masters.get(isin or "") or scored
        # Yahoo steps in only where we have no real name of our own. Left
        # unguarded it "upgraded" the registered name KASIKORNBANK PUBLIC
        # COMPANY LIMITED to Yahoo's abbreviated Kasikornbank Public Co Ltd,
        # which is not an improvement.
        if from_ticker and name_quality(display) < REAL_NAME_SCORE:
            display = from_ticker
        if not display:
            display = isin or eid.split(":", 1)[1]
        # OpenFIGI's names are Bloomberg abbreviations - KASIKORNBANK PCL
        # against the registered KASIKORNBANK PUBLIC COMPANY LIMITED - so they
        # only step in where our own best is still an identifier.
        fg = figi.get(eid) or {}
        if fg.get("name") and name_quality(display) < REAL_NAME_SCORE:
            display = fg["name"]

        # ISS-035: for a Thai-listed security the filed issuer is the registered
        # company. A ticker collides across markets - "MINT" is Minor
        # International in Bangkok and Mapletree Industrial Trust in Singapore -
        # and the symbol fold can drag the foreign name (better-cased, so a
        # higher name_quality) onto the Thai ISIN. When the chosen name shares no
        # token with any filed issuer, rebuild it from issuer-consistent
        # candidates only. Skipped when the issuer is an asset manager, because
        # a fund-of-funds unit is named for the fund, not its manager.
        # Only listed-security kinds: there the filed issuer is the registered
        # company, so it can name the security. For a "fund" holding the issuer
        # is the asset manager (KTFIXPLUS is issued by KTAM), which must never
        # become the unit's name - that is the fund-of-funds case to leave alone.
        overrode_for_issuer = False
        if (isin or "").startswith("TH") and g["kind"] in {"equity", "reit"}:
            # The most-filed issuer is authoritative: the foreign collider is
            # also present as an issuer (dragged in with the folded master
            # holding), so agreement with *any* issuer is too weak - Mapletree
            # agrees with itself. MINOR INTERNATIONAL is filed 377 times against
            # this ISIN and Mapletree only a handful, so the top issuer wins.
            filed = Counter({iss: c for iss, c in g["issuers"].items()
                             if not _ISSUER_IS_MANAGER.search(iss)})
            if filed:
                authoritative = filed.most_common(1)[0][0]
                auth_tokens = identity_tokens(authoritative)
                if auth_tokens and not (identity_tokens(display) & auth_tokens):
                    consistent = Counter({
                        n: c for n, c in (g["names"] + g["issuers"]).items()
                        if identity_tokens(n) & auth_tokens
                    })
                    if consistent:
                        display = best_name(consistent)
                        overrode_for_issuer = True

        aliases = sorted({a for a in g["aliases"] if a != display})
        entities[eid] = {
            "id": eid,
            "isin": isin,
            "kind": g["kind"],
            "name": display,
            "name_source": ("issuer-th" if overrode_for_issuer
                            else "master-registry" if isin in from_masters
                            else "yahoo-holdings" if display == from_ticker
                            else "scored"),
            "aliases": aliases,
            "alias_count": len(aliases) + 1,
            "fund_count": len(g["funds"]),
            "funds": dict(sorted(g["funds"].items(),
                                 key=lambda kv: -(kv[1] or 0))),
            "max_pct_nav": round(max(g["funds"].values() or [0]), 2),
        }
        if fg:
            entities[eid].update({
                "figi": fg.get("figi"),
                "ticker": fg.get("ticker"),
                "exch_code": fg.get("exch_code"),
                "figi_type": fg.get("security_type"),
                "market_sector": fg.get("market_sector"),
                "share_class_figi": fg.get("share_class_figi"),
            })
            if fg.get("name") == display:
                entities[eid]["name_source"] = "openfigi"

    # ---- pass 4: shares reachable only through a master fund -----------
    # Eli Lilly, Alphabet Class C and 1,100 others appear in a master's
    # holdings but in no Thai filing, because the Thai fund holds the master,
    # not the share. Without a record here they would have no note and the
    # look-through would dead-end.
    seen_keys = set()
    for e in entities.values():
        for alias in [e["name"], *e["aliases"]]:
            key = norm_key(alias)
            if key:
                seen_keys.add((e["kind"], key))

    added = 0
    for key, name in from_holdings.items():
        if ("equity", key) in seen_keys or ("fund", key) in seen_keys:
            continue
        eid = f"equity:{key}"
        if eid in entities:
            continue
        entities[eid] = {
            "id": eid, "isin": None, "kind": "equity", "name": name,
            "name_source": "master-holdings-only",
            "aliases": [], "alias_count": 1,
            "fund_count": 0, "funds": {}, "max_pct_nav": 0,
            "via_master_only": True,
        }
        seen_keys.add(("equity", key))
        added += 1
    LOG.info("pass 4: %d entities exist only inside a master fund's holdings",
             added)

    # ---- write entity ids back onto the holdings -----------------------
    lookup: dict[tuple, str] = {}
    # AMCs disagree about what a security *is*: CapitaLand Ascendas REIT is
    # filed as assetliab_id 101 (equity) by one, 118 (fund units) by another
    # and 130 (REIT) by a third. Requiring an exact kind match left 124 rows
    # untagged even though the entity existed. `by_key` is the kind-agnostic
    # fallback - but it never crosses the counterparty boundary, because a
    # bank's shares and a deposit at that bank must stay separate entities.
    by_key: dict[str, str] = {}
    for eid, e in entities.items():
        if e["isin"]:
            lookup[("isin", e["isin"])] = eid
        for alias in e["aliases"] + [e["name"]]:
            key = norm_key(alias)
            lookup.setdefault((e["kind"], key), eid)
            if e["kind"] not in COUNTERPARTY_KINDS:
                by_key.setdefault(key, eid)

    tagged = cross_kind = untagged = 0
    for pid, fund in funds.items():
        for item in (fund.get("portfolio") or {}).get("items") or []:
            code = str(item.get("type_code") or "")
            kind = KIND_BY_CODE.get(code, "other")
            if kind in UNRESOLVABLE_KINDS:
                item.pop("entity", None)
                item.pop("entity_name", None)
                continue
            isin = (item.get("isin") or "").strip().upper()
            name = (item.get("name") or "").strip()
            issuer = (item.get("issuer") or "").strip()
            if (not ISIN_RE.match(isin) and ISIN_RE.match(name.upper())
                    and kind not in COUNTERPARTY_KINDS):
                isin = name.upper()
            label = issuer if kind in COUNTERPARTY_KINDS and issuer else name
            eid = None
            if ISIN_RE.match(isin) and kind not in COUNTERPARTY_KINDS:
                eid = lookup.get(("isin", isin))
            if not eid:
                for cand in (label, issuer, name):
                    eid = lookup.get((kind, norm_key(cand)))
                    if eid:
                        break
            if not eid and kind not in COUNTERPARTY_KINDS:
                for cand in (label, issuer, name):
                    eid = by_key.get(norm_key(cand))
                    if eid:
                        cross_kind += 1
                        break
            if eid:
                item["entity"] = eid
                item["entity_name"] = entities[eid]["name"]
                tagged += 1
            else:
                untagged += 1
                item.pop("entity", None)
                item.pop("entity_name", None)

    # Write funds.json back only when the content actually changed. This stage
    # reads funds.json and writes to it, so an unconditional write bumps its
    # mtime every run and makes daily.py rebuild every downstream stage even on
    # a day when nothing moved.
    payload = json.dumps(funds, ensure_ascii=False)
    if FUNDS.read_text(encoding="utf-8") != payload:
        FUNDS.write_text(payload, encoding="utf-8")
        LOG.info("funds.json updated with entity ids")
    else:
        LOG.info("funds.json unchanged - left alone to keep its mtime")

    ordered = dict(sorted(entities.items(),
                          key=lambda kv: (-kv[1]["fund_count"], kv[1]["name"])))
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    with_figi = sum(1 for e in entities.values() if e.get("figi"))
    from_figi = sum(1 for e in entities.values()
                    if e.get("name_source") == "openfigi")
    LOG.info("openfigi: %d entities annotated, %d took their name from it",
             with_figi, from_figi)
    by_kind = Counter(e["kind"] for e in entities.values())
    multi = sum(1 for e in entities.values() if e["alias_count"] > 1)
    saved = sum(e["alias_count"] - 1 for e in entities.values())
    LOG.info("entities: %d (from %d holding rows, %d tagged, %d skipped)",
             len(entities), rows, tagged, sum(skipped.values()))
    LOG.info("  %d rows matched an entity filed under a different asset type",
             cross_kind)
    if untagged:
        LOG.warning("  %d rows could not be resolved to any entity", untagged)
    LOG.info("  %d entities had >1 spelling; %d duplicate spellings collapsed",
             multi, saved)
    LOG.info("  by kind: %s", json.dumps(dict(by_kind.most_common())))
    LOG.info("top entities by number of Thai funds holding them:")
    for e in list(ordered.values())[:12]:
        LOG.info("   %3d funds  %-42s %s",
                 e["fund_count"], e["name"][:42], e["isin"] or "")


if __name__ == "__main__":
    main()
