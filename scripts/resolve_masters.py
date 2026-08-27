"""
resolve_masters.py - Build the master-fund registry from the Thai fund data.

A Thai feeder fund puts nearly all of its money into one foreign master fund.
The SEC data names that master in `feederfund_master_fund`, and - far more
usefully - the feeder's own quarterly portfolio contains the master as a single
holding with its ISIN. The ISIN is what makes external lookup reliable; the
name alone is not (AMCs spell the same master a dozen ways, sometimes prefixed
with "กองทุน").

Output: data/processed/master_funds.json, keyed by ISIN where known and by a
normalised name otherwise. Each entry lists every Thai feeder pointing at it.

    python scripts/resolve_masters.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("resolve_masters")
PROC = ROOT / "data" / "processed"
OUT = PROC / "master_funds.json"

# assetliab_id values that mean "units of another fund" - the master holding
FUND_UNIT_CODES = {"108", "109", "117", "118", "119", "120", "121", "130", "139"}

# a holding this large in a feeder can only be the master fund
MASTER_MIN_PCT = 50.0

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def clean_master_name(name: str) -> str:
    """Strip the Thai prefixes and noise AMCs put in front of the master name."""
    s = unicodedata.normalize("NFKC", str(name or "")).strip()
    s = re.sub(r"^กองทุน(รวม)?\s*", "", s)
    s = re.sub(r"^(หน่วยลงทุนของ|หน่วยลงทุน)\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -–—,;:")


def norm_key(name: str) -> str:
    """Loose key for grouping masters that have no ISIN."""
    s = clean_master_name(name).lower()
    s = re.sub(r"[^a-z0-9ก-๙ ]+", " ", s)
    s = re.sub(r"\b(fund|funds|class|shares?|acc|inc|cap|usd|eur|gbp|thb|jpy)\b",
               " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pick_master_holding(fund: dict) -> dict | None:
    """Find the holding that represents the master fund, if there is one."""
    pf = fund.get("portfolio") or {}
    best = None
    for item in pf.get("items") or []:
        pct = item.get("percent_nav") or 0
        if pct < MASTER_MIN_PCT:
            continue
        code = str(item.get("type_code") or "")
        isin = str(item.get("isin") or "").strip().upper()
        # prefer a fund-unit line; fall back to any dominant ISIN holding
        score = (code in FUND_UNIT_CODES, bool(ISIN_RE.match(isin)), pct)
        if best is None or score > best[0]:
            best = (score, item)
    return best[1] if best else None


def main() -> None:
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))

    masters: dict[str, dict] = {}
    stats = {"feeders": 0, "with_isin": 0, "name_only": 0, "no_master": 0}

    for pid, f in funds.items():
        master_name = f.get("feeder_master")
        style = f.get("management_style") or ""
        is_feeder = bool(master_name) or style in ("AN", "PN", "IN", "LN")
        if not is_feeder:
            continue
        stats["feeders"] += 1

        holding = pick_master_holding(f)
        isin = str((holding or {}).get("isin") or "").strip().upper()
        has_isin = bool(ISIN_RE.match(isin))

        if has_isin:
            key = isin
            stats["with_isin"] += 1
        elif master_name:
            key = "name:" + norm_key(master_name)
            stats["name_only"] += 1
        else:
            stats["no_master"] += 1
            continue

        entry = masters.setdefault(key, {
            "key": key,
            "isin": isin if has_isin else None,
            "names": [],
            "countries": [],
            "feeders": [],
        })
        name = clean_master_name(master_name) if master_name else None
        if name and name not in entry["names"]:
            entry["names"].append(name)
        country = f.get("feeder_country")
        if country and country not in entry["countries"]:
            entry["countries"].append(country)
        entry["feeders"].append({
            "proj_id": pid,
            "abbr": f.get("abbr"),
            "name_th": f.get("name_th"),
            "amc_th": f.get("amc_th"),
            "policy": f.get("policy"),
            "risk_spectrum": f.get("risk_spectrum"),
            "management_style": style,
            "pct_nav": (holding or {}).get("percent_nav"),
            "as_of": (f.get("portfolio") or {}).get("as_of"),
        })

    # a stable display name: the one most feeders agree on, else the longest
    for entry in masters.values():
        entry["feeders"].sort(key=lambda x: str(x.get("abbr") or ""))
        entry["feeder_count"] = len(entry["feeders"])
        entry["display_name"] = (
            max(entry["names"], key=len) if entry["names"]
            else (entry["isin"] or entry["key"]))

    # Some "master funds" are themselves Thai funds - an RMF/SSF share class
    # feeding into the AMC's own flagship. Those already have a full note in
    # vault/Funds/, so point at it rather than writing a thin external stub.
    by_name_th = {}
    for pid, f in funds.items():
        if f.get("name_th"):
            by_name_th[re.sub(r"\s+", "", f["name_th"])] = (pid, f)

    domestic = 0
    for entry in masters.values():
        if "ไทย" not in (entry.get("countries") or []):
            continue
        needle = re.sub(r"\s+", "", entry["display_name"])
        if not needle:
            continue
        hit = next((v for k, v in by_name_th.items()
                    if needle in k or k.endswith(needle)), None)
        if hit:
            pid, f = hit
            entry["thai_master"] = {"proj_id": pid, "abbr": f.get("abbr"),
                                    "name_th": f.get("name_th")}
            domestic += 1
    if domestic:
        LOG.info("resolved %d masters to existing Thai fund notes", domestic)

    ordered = dict(sorted(masters.items(),
                          key=lambda kv: -kv[1]["feeder_count"]))
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    multi = sum(1 for e in masters.values() if e["feeder_count"] > 1)
    LOG.info("feeders=%(feeders)d with_isin=%(with_isin)d "
             "name_only=%(name_only)d no_master=%(no_master)d", stats)
    LOG.info("distinct masters: %d (%d shared by >1 Thai fund)",
             len(masters), multi)
    LOG.info("top masters by feeder count:")
    for e in list(ordered.values())[:8]:
        LOG.info("   %2d feeders  %-14s %s",
                 e["feeder_count"], e["isin"] or "(no isin)",
                 e["display_name"][:60])


if __name__ == "__main__":
    main()
