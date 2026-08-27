"""
fetch_figi.py - Resolve entities against Bloomberg's OpenFIGI symbology.

What it is for
--------------
Three things the SEC feed cannot settle on its own:

  **securityType**  AMCs disagree about what a security *is*. CapitaLand
                    Ascendas REIT is filed as assetliab_id 101 (equity) by one
                    AMC, 118 (fund units) by another and 130 (REIT) by a third
                    (ISS-029). OpenFIGI is a neutral third party that says
                    "REIT" and settles it.
  **name**          102 entities carry an ISIN but no readable name - the best
                    the scorer can do is `BLACKROC` or `FFGSYAU_LX_USD`.
  **shareClassFIGI** a canonical share-class identifier, usable as a merge key
                    where an ISIN is missing.

Why OpenFIGI and not Finnhub or FMP: measured, not assumed. Finnhub gates ISIN
behind an entitlement and international coverage behind a paid plan, and our
ISINs are 1,597 Thai plus LU/IE/SG/VN/MY/JP. FMP allows 250 requests a day,
which is 13 days for one pass over 3,149 ISINs. OpenFIGI resolved 8 of 8 test
ISINs including Thai mutual funds, and with the key in .env.local takes 100
jobs per request.

Two rules that exist because ignoring them produces confident wrong answers:

  * **A ticker is never looked up without an exchange code.** `MTRE` alone
    resolves to MAK-TUTUN AD RESEN, a Macedonian company; our entity is
    Muangthai Real Estate. Only aliases that carry an exchange suffix -
    "FRT VN", "SPXS LN" - are used.
  * **The name is only taken when ours is a code.** OpenFIGI returns
    Bloomberg's abbreviations: KASIKORNBANK PCL against the registered
    KASIKORNBANK PUBLIC COMPANY LIMITED, CAPITAL GP NEW PERS-BUSD against
    Capital Group New Perspective Fund. Same guard as the Yahoo names.

Output: data/processed/figi.json, keyed by entity id.

    python scripts/fetch_figi.py              # resumable
    python scripts/fetch_figi.py --force      # refetch everything
    python scripts/fetch_figi.py --limit 200  # smoke test
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize_entities import ISIN_RE, EX_SET  # noqa: E402
from sec_client import ROOT, get_logger, load_env  # noqa: E402

LOG = get_logger("fetch_figi")
PROC = ROOT / "data" / "processed"
OUT = PROC / "figi.json"
API = "https://api.openfigi.com/v3/mapping"

# 100 with a key, 10 without. The published limit is 25 requests per 6 seconds
# for keyed traffic; 0.4s between requests keeps us inside it with room spare.
BATCH_WITH_KEY = 100
BATCH_NO_KEY = 10
DELAY_WITH_KEY = 0.4
DELAY_NO_KEY = 2.6

# ISIN country prefix -> the exchange code OpenFIGI uses for that market.
# Only needed to pick which listing's ticker to keep; the name and security
# type are decided by majority vote across all listings, which needs no map.
HOME_EXCHANGE = {
    "TH": "TB", "US": "US", "SG": "SP", "VN": "VN", "JP": "JP", "MY": "MK",
    "HK": "HK", "GB": "LN", "IE": "ID", "LU": "LX", "KR": "KS", "TW": "TT",
    "IN": "IS", "ID": "IJ", "PH": "PM", "AU": "AU", "CA": "CN", "CH": "SW",
    "DE": "GR", "FR": "FP", "NL": "NA", "KY": "KY",
}

# "FRT VN" / "SPXS LN" / "2330 TT" - ticker plus an exchange code we recognise
TICKER_WITH_EX = re.compile(r"^([A-Z0-9][A-Z0-9.\-]{0,11})\s+([A-Z]{1,2})$")


def load_cache() -> dict:
    if not OUT.exists():
        return {}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def ticker_job(entity: dict) -> dict | None:
    """A TICKER lookup only when an alias carries its exchange code."""
    for alias in [entity["name"], *entity.get("aliases", [])]:
        m = TICKER_WITH_EX.match(str(alias).strip().upper())
        if m and m.group(2) in EX_SET:
            return {"idType": "TICKER", "idValue": m.group(1),
                    "exchCode": m.group(2)}
    return None


def build_jobs(entities: dict, cache: dict, force: bool) -> list[tuple]:
    """(entity_id, job) for everything still worth asking about."""
    jobs: list[tuple] = []
    for eid, e in entities.items():
        if not force and eid in cache:
            continue
        isin = (e.get("isin") or "").upper()
        if ISIN_RE.match(isin):
            jobs.append((eid, {"idType": "ID_ISIN", "idValue": isin}))
            continue
        # a deposit is a bank balance, not a security - it has no FIGI, and
        # asking would only invite a wrong match on the bank's shares
        if e["kind"] == "deposit":
            continue
        job = ticker_job(e)
        if job:
            jobs.append((eid, job))
    return jobs


def pick(listings: list[dict], isin: str | None) -> dict:
    """Condense many listings of one security into the fields we keep.

    Name and security type are decided by majority vote: all 247 NVIDIA
    listings agree on both, and voting avoids needing to know which venue is
    primary. The ticker is taken from the home-market listing where we can
    identify it, because tickers legitimately differ by venue - SPDR Gold is
    GLD in New York and GQ9 in Frankfurt.
    """
    names = Counter(x.get("name") for x in listings if x.get("name"))
    types = Counter(x.get("securityType") for x in listings
                    if x.get("securityType"))
    sectors = Counter(x.get("marketSector") for x in listings
                      if x.get("marketSector"))
    classes = Counter(x.get("shareClassFIGI") for x in listings
                      if x.get("shareClassFIGI"))

    home = HOME_EXCHANGE.get((isin or "")[:2])
    composite = [x for x in listings if x.get("compositeFIGI") == x.get("figi")]
    preferred = ([x for x in composite if x.get("exchCode") == home]
                 or [x for x in listings if x.get("exchCode") == home]
                 or composite or listings)
    best = preferred[0]

    return {
        "figi": best.get("figi"),
        "ticker": best.get("ticker"),
        "exch_code": best.get("exchCode"),
        "name": names.most_common(1)[0][0] if names else None,
        "security_type": types.most_common(1)[0][0] if types else None,
        "market_sector": sectors.most_common(1)[0][0] if sectors else None,
        "share_class_figi": (classes.most_common(1)[0][0] if classes else None),
        "listings": len(listings),
        "source": "openfigi",
    }


def request(jobs: list[dict], key: str | None) -> list[dict]:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-OPENFIGI-APIKEY"] = key
    req = urllib.request.Request(API, data=json.dumps(jobs).encode(),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    argv = sys.argv[1:]
    force = "--force" in argv
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    key = load_env().get("OPEN_FIGI_KEY")
    batch = BATCH_WITH_KEY if key else BATCH_NO_KEY
    delay = DELAY_WITH_KEY if key else DELAY_NO_KEY
    LOG.info("api key: %s (batch=%d, delay=%.1fs)",
             "present" if key else "MISSING - using the slower public limit",
             batch, delay)

    entities = json.loads((PROC / "entities.json").read_text(encoding="utf-8"))
    cache = {} if force else load_cache()
    jobs = build_jobs(entities, cache, force)
    if limit:
        jobs = jobs[:limit]

    by_type = Counter(j["idType"] for _, j in jobs)
    LOG.info("%d entities to resolve (%s), %d already cached",
             len(jobs), json.dumps(dict(by_type)), len(cache))
    if not jobs:
        return

    t0 = time.time()
    stats = Counter()
    for start in range(0, len(jobs), batch):
        chunk = jobs[start:start + batch]
        try:
            results = request([j for _, j in chunk], key)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                LOG.warning("rate limited - waiting 10s and retrying once")
                time.sleep(10)
                try:
                    results = request([j for _, j in chunk], key)
                except Exception as retry_error:
                    LOG.error("batch failed after retry: %s", retry_error)
                    stats["failed"] += len(chunk)
                    continue
            else:
                LOG.error("HTTP %s on batch at %d: %s", e.code, start,
                          e.read().decode()[:160])
                stats["failed"] += len(chunk)
                continue
        except Exception as e:                       # network
            LOG.error("batch at %d failed: %s", start, e)
            stats["failed"] += len(chunk)
            continue

        for (eid, job), res in zip(chunk, results):
            data = res.get("data")
            if not data:
                cache[eid] = {"source": "openfigi", "found": False,
                              "warning": res.get("warning", "not found"),
                              "asked": job["idType"]}
                stats["not_found"] += 1
                continue
            rec = pick(data, entities[eid].get("isin"))
            rec["found"] = True
            rec["asked"] = job["idType"]
            cache[eid] = rec
            stats[job["idType"]] += 1

        done = start + len(chunk)
        if done % (batch * 5) == 0 or done >= len(jobs):
            LOG.info("  %d/%d (%.0fs) %s", done, len(jobs), time.time() - t0,
                     json.dumps(dict(stats)))
            OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        time.sleep(delay)

    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    found = sum(1 for v in cache.values() if v.get("found"))
    LOG.info("done in %.0fs: %d resolved of %d cached -> %s",
             time.time() - t0, found, len(cache), OUT.relative_to(ROOT))
    types = Counter(v.get("security_type") for v in cache.values()
                    if v.get("found"))
    LOG.info("security types: %s", json.dumps(dict(types.most_common(10))))


if __name__ == "__main__":
    main()
