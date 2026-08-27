"""
lookthrough.py - See through a feeder fund to the shares it really owns.

A Thai feeder's own portfolio filing says one thing: "99.5% - units of
iShares Core S&P 500 ETF". Truthful, and useless for answering the question
that matters - how much NVIDIA do I own, and do my five funds overlap?

The master registry already knows what each master holds (Yahoo publishes top
holdings for 426 of the 618 masters). Multiplying the feeder's weight in the
master by the master's weight in each share gives the feeder's true exposure:

    KKP GNP-H holds 97% of Capital Group New Perspective
    Capital Group New Perspective holds 4.1% Microsoft
    -> KKP GNP-H holds roughly 4.0% Microsoft

Two limits are stated on every note that uses this, because they are not small:

  * **Top holdings only.** Yahoo publishes the top ten. A fund holding 300
    shares has most of its portfolio below the cut, so look-through weights
    sum to well under the feeder's stake in the master. They are a floor, not
    a complete picture.
  * **Different as-of dates.** The Thai filing is quarterly; Yahoo's holdings
    are their own vintage. A fast-turnover master will have moved.

Output: data/processed/lookthrough.json
    per fund   -> resolved exposures, biggest first
    per entity -> which Thai funds reach it, directly and indirectly

    python scripts/lookthrough.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize_entities import ISIN_RE, norm_key  # noqa: E402
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("lookthrough")
PROC = ROOT / "data" / "processed"
CACHE = ROOT / "data" / "masters"
OUT = PROC / "lookthrough.json"

# below this the number is noise against the two caveats above
MIN_PCT = 0.05

# 234 feeders file a stake above 100% of their own NAV, LHLONGEVITY at 151.75%
# with no offsetting negative row to explain it (unlike ISS-007, where the
# excess was a gross position netted off elsewhere in the same table).
# Multiplying by 1.5175 would inflate every exposure by half, so the multiplier
# is capped at 100% - you cannot have more than all of your money in one place.
# The uncapped figure is kept alongside so the note can show what was filed.
MAX_STAKE = 100.0


def master_cache(key: str) -> dict:
    path = CACHE / f"{key.replace(':', '_').replace('/', '_')[:80]}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def entity_lookup(entities: dict) -> dict[str, str]:
    """normalised name -> entity id, so a master's holdings can join the
    same canonical entities the Thai portfolios resolved to."""
    out: dict[str, str] = {}
    for eid, e in entities.items():
        for alias in [e["name"], *e.get("aliases", [])]:
            key = norm_key(alias)
            if key:
                out.setdefault(key, eid)
    return out


def main() -> None:
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    masters = json.loads((PROC / "master_funds.json").read_text(encoding="utf-8"))
    entities = json.loads((PROC / "entities.json").read_text(encoding="utf-8"))
    by_name = entity_lookup(entities)

    # which master each feeder points at, and how much of the feeder sits there
    feeder_master: dict[str, tuple[str, float]] = {}
    for key, entry in masters.items():
        for feeder in entry["feeders"]:
            pct = feeder.get("pct_nav")
            if pct:
                feeder_master[feeder["proj_id"]] = (key, float(pct))

    per_fund: dict[str, dict] = {}
    per_entity: dict[str, dict] = defaultdict(
        lambda: {"direct": {}, "indirect": {}})

    # direct holdings first: these are filed by the Thai fund itself
    for pid, fund in funds.items():
        for item in (fund.get("portfolio") or {}).get("items") or []:
            eid = item.get("entity")
            pct = item.get("percent_nav")
            if eid and pct:
                cur = per_entity[eid]["direct"].get(pid, 0)
                per_entity[eid]["direct"][pid] = max(cur, float(pct))

    stats = {"feeders": 0, "resolved": 0, "unmatched_names": 0}
    for pid, (mkey, stake) in feeder_master.items():
        if pid not in funds:
            continue
        stats["feeders"] += 1
        rec = master_cache(mkey)
        holdings = (rec.get("yahoo") or {}).get("top_holdings") or []
        if not holdings:
            continue

        entry = masters[mkey]
        stake_used = min(stake, MAX_STAKE)
        exposures = []
        for h in holdings:
            name = str(h.get("name") or "").strip()
            pct = h.get("percent")
            if not name or not pct:
                continue
            # the feeder owns `stake`% of the master, which owns `pct`% of this
            effective = round(stake_used * float(pct) / 100.0, 4)
            if effective < MIN_PCT:
                continue
            # try the ticker as well as the name: the Thai filings often
            # carry "2330 TT" where Yahoo says "Taiwan Semiconductor
            # Manufacturing Co Ltd", and only the symbol joins those two
            bare = str(h.get("symbol") or "").split(".")[0]
            eid = (by_name.get(norm_key(name))
                   or (by_name.get(norm_key(bare)) if bare else None))
            if eid is None:
                stats["unmatched_names"] += 1
            exposures.append({
                "name": name, "symbol": h.get("symbol"),
                "entity": eid,
                "pct_of_master": float(pct),
                "pct_of_fund": effective,
            })
            if eid:
                cur = per_entity[eid]["indirect"].get(pid, 0)
                per_entity[eid]["indirect"][pid] = max(cur, effective)

        if not exposures:
            continue
        stats["resolved"] += 1
        exposures.sort(key=lambda x: -x["pct_of_fund"])
        per_fund[pid] = {
            "master_key": mkey,
            "master_name": entry["display_name"],
            "stake_pct": round(stake_used, 2),
            "stake_filed_pct": round(stake, 2),
            "stake_capped": stake > MAX_STAKE,
            "covered_pct": round(sum(e["pct_of_fund"] for e in exposures), 2),
            "holdings_source": "yahoo-top-holdings",
            "exposures": exposures,
        }

    # rank entities by how many Thai funds reach them at all
    entity_rollup = {}
    for eid, sides in per_entity.items():
        both = set(sides["direct"]) | set(sides["indirect"])
        if not both:
            continue
        entity_rollup[eid] = {
            "direct": dict(sorted(sides["direct"].items(),
                                  key=lambda kv: -kv[1])),
            "indirect": dict(sorted(sides["indirect"].items(),
                                    key=lambda kv: -kv[1])),
            "fund_count": len(both),
            "indirect_count": len(sides["indirect"]),
        }

    OUT.write_text(json.dumps(
        {"funds": per_fund, "entities": entity_rollup},
        ensure_ascii=False, indent=1), encoding="utf-8")

    with_indirect = sum(1 for e in entity_rollup.values() if e["indirect_count"])
    LOG.info("feeders with a known stake: %(feeders)d, "
             "resolved through to holdings: %(resolved)d", stats)
    LOG.info("master holding names with no matching entity: %d",
             stats["unmatched_names"])
    LOG.info("entities reachable indirectly: %d", with_indirect)
    capped = sum(1 for r in per_fund.values() if r["stake_capped"])
    LOG.info("feeders whose filed stake exceeded 100%% and was capped: %d", capped)

    top = sorted(entity_rollup.items(),
                 key=lambda kv: -kv[1]["indirect_count"])[:10]
    LOG.info("most widely held through master funds:")
    for eid, roll in top:
        LOG.info("   %3d funds  %s", roll["indirect_count"],
                 entities[eid]["name"][:52])


if __name__ == "__main__":
    main()
