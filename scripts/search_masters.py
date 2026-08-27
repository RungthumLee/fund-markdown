"""
search_masters.py - Fill the master-fund gaps that Yahoo and FT could not,
using web search as an *ISIN finder* rather than as a data source.

Why it works this way
---------------------
The obvious move is to let a search engine's AI summary answer "what is this
fund's OCF and size" and paste the answer into the note. Measured against FT,
that answer is unreliable: for GMO Quality Investment the summary said
"1.05% / $7.8bn" while the actual share class (IE00B3SBSR82) is 0.53% /
6.61bn GBP. It is not lying - it is blending numbers across share classes,
and a master fund is always a *specific* share class. Publishing that would
repeat the mistake of ISS-009: a confidently wrong number that ranks funds.

So search contributes the one thing it is genuinely good at and that we can
verify independently: **the ISIN**. An ISIN is checksum-shaped, and once we
have it the existing FT/Yahoo scrapers produce numbers we already trust. Any
candidate that FT cannot confirm is discarded, not published.

The narrative that search *does* own - "this Cayman feeder allocates to
Renaissance Institutional Equities" - is kept as prose in `search_note`,
clearly attributed, never parsed into numeric fields.

Usage
-----
    python scripts/search_masters.py queue [--limit N]   # what to search for
    python scripts/search_masters.py ingest <found.json> # verify + store

`found.json` maps a master key to what search turned up:

    {"name:wellspring gbl": {
        "isin":  ["IE000N9XFSD0"],          # verified against FT/Yahoo or dropped
        "facts": {"ongoing_charge": "1.08%"},  # kept only if no ISIN verified,
                                               # rendered as unverified
        "note":  "Cayman feeder into Renaissance Institutional Equities",
        "sources": ["https://..."]}}
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ft_scraper  # noqa: E402
from fetch_masters import yahoo  # noqa: E402
from resolve_masters import norm_key  # noqa: E402
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("search_masters")
PROC = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "masters"
QUEUE = PROC / "master_search_queue.json"

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# FT indexes the same ISIN under whichever currency the class is priced in.
CURRENCIES = ("USD", "EUR", "GBP")


def cache_path(key: str) -> Path:
    return CACHE / f"{key.replace(':', '_').replace('/', '_')[:80]}.json"


def load_cached(key: str) -> dict:
    p = cache_path(key)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def has_data(rec: dict) -> bool:
    return bool(rec.get("yahoo") or rec.get("ft"))


def build_queue(limit: int | None = None) -> list[dict]:
    """Masters with no external data, minus the ones that are just a
    name-spelled-differently duplicate of a master we already enriched."""
    masters = json.loads((PROC / "master_funds.json").read_text(encoding="utf-8"))

    enriched_names: dict[str, str] = {}
    pending: list[tuple[str, dict]] = []
    for key, entry in masters.items():
        if entry.get("thai_master"):
            continue          # already has a full Thai fund note
        nk = norm_key(entry["display_name"])
        if has_data(load_cached(key)):
            enriched_names.setdefault(nk, key)
        else:
            pending.append((nk, entry))

    queue = []
    for nk, entry in pending:
        twin = enriched_names.get(nk)
        if twin:
            # same fund, different spelling - no point searching for it
            entry = {**entry, "duplicate_of": twin}
        queue.append({
            "key": entry["key"],
            "isin": entry.get("isin"),
            "name": entry["display_name"],
            "feeder_count": entry["feeder_count"],
            "countries": entry.get("countries") or [],
            "duplicate_of": entry.get("duplicate_of"),
            "query": search_query(entry),
        })
    queue.sort(key=lambda q: (q["duplicate_of"] is not None, -q["feeder_count"]))
    return queue[:limit] if limit else queue


def search_query(entry: dict) -> str:
    """The query that has the best chance of surfacing an ISIN."""
    name = re.sub(r"\s*[-–,]\s*Class\b.*$", "", entry["display_name"]).strip()
    if entry.get("isin"):
        return f'"{entry["isin"]}" {name} ongoing charge fund size'
    return f'"{name}" fund ISIN ongoing charges figure fund size'


def verify_isin(isin: str, session: requests.Session) -> dict:
    """Accept an ISIN only if a data source actually confirms it."""
    isin = isin.strip().upper()
    if not ISIN_RE.match(isin):
        return {}
    out: dict = {}
    for cur in CURRENCIES:
        try:
            data = ft_scraper.fetch(isin, cur, session=session)
        except Exception as e:                       # network / parse
            LOG.debug("ft %s %s: %s", isin, cur, e)
            continue
        if data and (data.get("ongoing_charge") or data.get("fund_size")):
            out["ft"] = data
            break
        time.sleep(0.4)
    yf = yahoo(isin)
    if yf:
        out["yahoo"] = yf
    return out


def ingest(path: Path) -> None:
    found = json.loads(path.read_text(encoding="utf-8"))
    masters = json.loads((PROC / "master_funds.json").read_text(encoding="utf-8"))
    session = requests.Session()
    stats = {"resolved": 0, "unverified": 0, "rejected": 0, "unknown_key": 0}

    for key, payload in found.items():
        entry = masters.get(key)
        if entry is None:
            LOG.warning("no such master key: %s", key)
            stats["unknown_key"] += 1
            continue

        rec = load_cached(key) or {
            "key": key, "isin": entry.get("isin"),
            "display_name": entry["display_name"],
            "feeder_count": entry["feeder_count"],
        }

        candidates = payload.get("isin") or []
        if isinstance(candidates, str):
            candidates = [candidates]

        hit = {}
        for cand in candidates:
            hit = verify_isin(cand, session)
            if hit:
                rec.update(hit)
                rec["isin_from_search"] = cand.strip().upper()
                LOG.info("%-40s <- %s", entry["display_name"][:40], cand)
                break
            time.sleep(0.3)

        if candidates and not hit:
            rec["search_isin_rejected"] = [c.strip().upper() for c in candidates]
            LOG.info("%-40s    no source confirmed %s",
                     entry["display_name"][:40], candidates)

        if payload.get("note"):
            rec["search_note"] = str(payload["note"])[:1200]
        # Unverified figures live in their own namespace. The note renders them
        # in a separate, labelled block and no index or comparison table reads
        # them, so a blended-share-class number can never rank a fund.
        if payload.get("facts") and not hit:
            rec["search_facts"] = {str(k): str(v)[:120]
                                   for k, v in dict(payload["facts"]).items()}
        if payload.get("sources"):
            rec["search_sources"] = list(payload["sources"])[:6]

        rec["has_data"] = has_data(rec)
        cache_path(key).write_text(
            json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

        if hit:
            stats["resolved"] += 1
        elif payload.get("facts") or payload.get("note"):
            stats["unverified"] += 1
        else:
            stats["rejected"] += 1

    LOG.info("ingest: %s", json.dumps(stats))


def main() -> None:
    argv = sys.argv[1:]
    cmd = argv[0] if argv else "queue"

    if cmd == "queue":
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
        queue = build_queue(limit)
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        dupes = sum(1 for q in queue if q["duplicate_of"])
        LOG.info("%d masters need data (%d are duplicate spellings) -> %s",
                 len(queue), dupes, QUEUE.relative_to(ROOT))
        for q in queue[:15]:
            LOG.info("  %2d feeders  %s", q["feeder_count"], q["name"][:60])
    elif cmd == "ingest":
        ingest(Path(argv[1]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
