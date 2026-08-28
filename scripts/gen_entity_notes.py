"""
gen_entity_notes.py - One note per canonical holding, plus the cross-fund index.

This is the view the raw SEC data cannot give you: start from a company and see
every Thai fund that owns it, sorted by weight. It only works once
`normalize_entities.py` has folded the dozen spellings of each name into one
entity - before that, "MSFT US" and "Microsoft Corp" were separate rows that
never met.

Notes are written for entities held by 2 or more funds. A security only one
fund holds needs no note of its own: the fund note already lists it, and 2,018
such notes would bury the ones worth reading. All of them stay resolvable in
data/processed/entities.json.

    python scripts/gen_entity_notes.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geography  # noqa: E402
from gen_vault import safe_name as gen_vault_safe_name, table  # noqa: E402
from normalize_entities import KIND_LABEL  # noqa: E402

# OpenFIGI security types mapped onto our own asset kinds, so a disagreement
# between what an AMC filed and what Bloomberg says can be spotted and shown.
FIGI_KIND = {
    "Common Stock": "equity", "Preference": "equity", "REIT": "reit",
    "Open-End Fund": "fund", "Closed-End Fund": "fund",
    "Fund of Funds": "fund", "ETP": "fund", "Mutual Fund": "fund",
    "Unit": "fund",
}
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("gen_entity_notes")
PROC = ROOT / "data" / "processed"
VAULT = ROOT / "vault"
OUT = VAULT / "Entities"
INDEX = VAULT / "Indexes" / "by-holding.md"
LOOK_INDEX = VAULT / "Indexes" / "by-lookthrough.md"
LINKS = PROC / "entity_links.json"
LOOKTHROUGH = PROC / "lookthrough.json"

# below this a note adds noise, not signal - see module docstring
MIN_FUNDS = 2
MAX_FUNDS_LISTED = 60

KIND_ICON = {
    "equity": "🏢", "bond": "📄", "govbond": "🏛️", "bill": "🧾",
    "deposit": "🏦", "fund": "📦", "reit": "🏗️", "other": "•",
}


def safe_name(text: str) -> str:
    """A filename Obsidian can use as the wikilink target.

    Delegates to gen_vault so the two agree byte for byte: gen_vault maps
    "KT25/75RMF" to "KT25-75RMF", and an entity note that turned the slash
    into a space instead would link to a file that does not exist.
    """
    return gen_vault_safe_name(text)[:110]


def cell(text) -> str:
    return str(text if text not in (None, "") else "—").replace("|", "\\|")


def pct(value) -> str:
    return f"{value:.2f}%" if isinstance(value, (int, float)) else "—"


def render(entity: dict, funds: dict, note_names: dict[str, str],
           reach: dict | None = None) -> str:
    kind = entity["kind"]
    icon = KIND_ICON.get(kind, "•")
    o: list[str] = []
    a = o.append

    a("---")
    a(f'title: "{entity["name"]}"')
    a(f'entity_id: "{entity["id"]}"')
    if entity.get("isin"):
        a(f'isin: "{entity["isin"]}"')
    for key in ("ticker", "figi", "share_class_figi"):
        if entity.get(key):
            a(f'{key}: "{entity[key]}"')
    if entity.get("figi_type"):
        a(f'figi_type: "{entity["figi_type"]}"')
    a(f'kind: "{kind}"')
    # country (DEC-L01 at the security level): domicile from the ISIN prefix,
    # market from a Bloomberg ticker alias or the symbol; `country` prefers market
    _domicile = geography.country_of_isin(entity.get("isin"))
    _market = (geography.market_from_aliases(entity.get("aliases"))
               or geography.market_of_symbol(entity.get("ticker")))
    if _domicile:
        a(f'domicile_country: "{_domicile}"')
    if _market:
        a(f'market_country: "{_market}"')
    if _market or _domicile:
        a(f'country: "{_market or _domicile}"')
    indirect = (reach or {}).get("indirect") or {}
    a(f"fund_count: {entity['fund_count']}")
    a(f"indirect_fund_count: {len(indirect)}")
    a(f"alias_count: {entity['alias_count']}")
    tags = ["entity", f"entity-{kind}"]
    if indirect:
        tags.append("held-indirectly")
    if entity.get("via_master_only"):
        tags.append("via-master-only")
    if entity["alias_count"] > 1:
        tags.append("multi-alias")
    if entity["fund_count"] >= 100:
        tags.append("widely-held")
    a(f"tags: [{', '.join(tags)}]")
    a("---")
    a("")
    a(f"# {icon} {entity['name']}")
    a("")

    bits = [f"**ประเภท:** {KIND_LABEL.get(kind, kind)}"]
    if entity.get("isin"):
        bits.append(f"**ISIN:** `{entity['isin']}`")
    if entity.get("ticker"):
        ticker = entity["ticker"]
        if entity.get("exch_code"):
            ticker += f" ({entity['exch_code']})"
        bits.append(f"**Ticker:** `{ticker}`")
    a(" · ".join(bits))
    a("")
    # country line: market is where it trades, domicile is where it is registered
    if _market or _domicile:
        geo = []
        if _market:
            geo.append(f"**ตลาดซื้อขาย:** {_market}")
        if _domicile and _domicile != _market:
            src = "จาก ISIN" if entity.get("isin") else ""
            geo.append(f"**จดทะเบียน:** {_domicile} {src}".strip())
        a(" · ".join(geo))
        a("")

    figi_type = entity.get("figi_type")
    if figi_type:
        mapped = FIGI_KIND.get(figi_type)
        if mapped and mapped != kind:
            a(f"> [!WARNING] บลจ. ยื่นสินทรัพย์นี้เป็น "
              f"**{KIND_LABEL.get(kind, kind)}** แต่ Bloomberg ระบุว่าเป็น "
              f"**{figi_type}**")
            a("> ข้อมูล ก.ล.ต. ใช้รหัสที่ บลจ. เป็นผู้กรอก ซึ่งแต่ละรายไม่ตรงกัน "
              "— หน้านี้ยังจัดกลุ่มตามรหัสที่ยื่น")
            a("")
    parts = [f"ถือโดยตรง **{entity['fund_count']:,}** กอง"]
    if indirect:
        parts.append(f"ถือทางอ้อมผ่านกองทุนหลักอีก **{len(indirect):,}** กอง")
    a(" · ".join(parts))
    a("")
    a("[[../Indexes/by-holding|ดัชนีสินทรัพย์]] · "
      "[[../Indexes/by-lookthrough|ดัชนีการถือทางอ้อม]] · "
      "[[../Concepts/การรวมชื่อสินทรัพย์|ชื่อนี้รวมมาจากไหน]] · "
      "[[../Concepts/Look-through การถือทางอ้อม|Look-through คืออะไร]]")
    a("")
    if entity.get("via_master_only"):
        a("> [!NOTE] ไม่มีกองทุนไทยกองใดถือหลักทรัพย์นี้โดยตรง")
        a("> ทุกกองเข้าถึงผ่าน**กองทุนหลัก**ที่ตัวเองลงทุนอยู่")
        a("")

    if entity["alias_count"] > 1:
        a("## ชื่อที่พบในข้อมูลดิบ")
        a("")
        a(f"ข้อมูล ก.ล.ต. สะกดสินทรัพย์นี้ **{entity['alias_count']} แบบ** "
          "ซึ่งถูกรวมเป็นรายการเดียวแล้ว")
        a("")
        a("> [!NOTE] ถ้าไม่รวม ตัวเลขการกระจุกตัวจะต่ำกว่าความจริง "
          "เพราะฐานะเดียวถูกนับแยกเป็นหลายรายการ")
        a("")
        shown = entity["aliases"][:24]
        a(" · ".join(f"`{x}`" for x in shown)
          + (f" _...และอีก {len(entity['aliases']) - 24}_"
             if len(entity["aliases"]) > 24 else ""))
        a("")

    if indirect:
        a(f"## 🔭 กองทุนไทยที่ถือทางอ้อม ({len(indirect):,} กอง)")
        a("")
        a("> [!CAUTION] ตัวเลขนี้เป็น**ขั้นต่ำ** ไม่ใช่สัดส่วนที่แท้จริงทั้งหมด")
        a("> คำนวณจาก _สัดส่วนที่กองไทยถือกองหลัก_ × _สัดส่วนที่กองหลักถือหลักทรัพย์นี้_")
        a("> โดยใช้เฉพาะ **10 อันดับแรก**ที่กองหลักเปิดเผย และวันอ้างอิงของสองฝั่งไม่ตรงกัน")
        a("> อ่าน [[../Concepts/Look-through การถือทางอ้อม|ข้อจำกัดฉบับเต็ม]] ก่อนใช้ตัดสินใจ")
        a("")
        rows = sorted(indirect.items(), key=lambda kv: -kv[1])[:MAX_FUNDS_LISTED]
        body = ["| กองทุน | บลจ. | ~% NAV (ทางอ้อม) | ผ่านกองทุนหลัก |",
                "|---|---|---|---|"]
        vias = (reach or {}).get("via") or {}
        for pid, weight in rows:
            f = funds.get(pid) or {}
            note = note_names.get(pid)
            label = (f"[[{note}\|{f.get('abbr') or pid}]]" if note
                     else cell(f.get("abbr")))
            body.append(f"| {label} | {cell(f.get('amc_th'))} | {pct(weight)} "
                        f"| {cell(vias.get(pid))} |")
        if len(indirect) > MAX_FUNDS_LISTED:
            body.append(f"| _...และอีก {len(indirect) - MAX_FUNDS_LISTED:,} กอง_ "
                        "| | | |")
        o.extend(body)
        a("")

    a(f"## กองทุนไทยที่ถือโดยตรง ({entity['fund_count']:,} กอง)")
    a("")
    if not entity["funds"]:
        a("_ไม่มีกองทุนไทยกองใดถือโดยตรง_")
        a("")
    rows = list(entity["funds"].items())[:MAX_FUNDS_LISTED]
    body = ["| กองทุน | บลจ. | % NAV | นโยบาย |", "|---|---|---|---|"]
    for pid, weight in rows:
        f = funds.get(pid) or {}
        note = note_names.get(pid)
        label = f"[[{note}\\|{f.get('abbr') or pid}]]" if note else cell(f.get("abbr"))
        body.append(f"| {label} | {cell(f.get('amc_th'))} | {pct(weight)} "
                    f"| {cell(f.get('policy'))} |")
    if len(entity["funds"]) > MAX_FUNDS_LISTED:
        collapsed = len(entity["funds"]) - MAX_FUNDS_LISTED
        body.append(f"| _...และอีก {collapsed:,} กอง_ | | | |")
    o.extend(body)
    a("")
    a(f"> น้ำหนักที่แสดงคือ **% NAV สูงสุด** ที่กองนั้นเคยรายงานถือสินทรัพย์นี้ "
      "ในงวดที่มีข้อมูล")
    a("")

    if entity.get("figi"):
        a("## รหัสอ้างอิงสากล")
        a("")
        o.extend(table(["รายการ", "ค่า"], [
            ["FIGI", f"`{entity['figi']}`"],
            ["Share Class FIGI",
             f"`{entity['share_class_figi']}`"
             if entity.get("share_class_figi") else "—"],
            ["ประเภทตาม Bloomberg", cell(entity.get("figi_type"))],
            ["หมวดตลาด", cell(entity.get("market_sector"))],
        ]))
        a("ที่มา: OpenFIGI ของ Bloomberg · "
          "[วิธีใช้และข้อจำกัด](../../docs/guides/openfigi.md)")
        a("")

    a("[[../Indexes/00-home|🏠 Home]] · [[../Indexes/by-holding|ดัชนีสินทรัพย์]]")
    a("")
    return "\n".join(o)


def render_index(chosen: list[dict], stats: dict,
                 links: dict[str, str]) -> str:
    o: list[str] = []
    a = o.append
    a("---")
    a("title: ดัชนีสินทรัพย์ที่กองทุนถือ")
    a("tags: [index, entity, holdings]")
    a("---")
    a("")
    a("# 🔗 ดัชนีสินทรัพย์ที่กองทุนถือ")
    a("")
    a("[[00-home|🏠 Home]] · [[all-funds|กองทุนทั้งหมด]] · "
      "[[master-funds|กองทุนหลัก]] · "
      "[[../Concepts/การรวมชื่อสินทรัพย์|วิธีรวมชื่อ]]")
    a("")
    a("เริ่มจาก**สินทรัพย์** แล้วดูว่ากองทุนไทยกองไหนถืออยู่บ้าง — "
      "มุมกลับของโน้ตกองทุนที่เริ่มจากกองแล้วดูว่าถืออะไร")
    a("")
    a("| รายการ | จำนวน |")
    a("|---|---|")
    a(f"| แถวการถือครองทั้งหมด | {stats['rows']:,} |")
    a(f"| สินทรัพย์ที่ไม่ซ้ำ (หลังรวมชื่อ) | {stats['entities']:,} |")
    a(f"| สินทรัพย์ที่มีชื่อสะกดมากกว่า 1 แบบ | {stats['multi_alias']:,} |")
    a(f"| ชื่อซ้ำที่ถูกยุบรวม | {stats['collapsed']:,} |")
    a(f"| โน้ตที่สร้าง (ถือโดย ≥{MIN_FUNDS} กอง) | {len(chosen):,} |")
    a("")

    for kind in ("equity", "fund", "reit", "bond", "govbond",
                 "deposit", "bill", "other"):
        group = [e for e in chosen if e["kind"] == kind][:40]
        if not group:
            continue
        a(f"## {KIND_ICON.get(kind, '•')} {KIND_LABEL.get(kind, kind)}")
        a("")
        a("| สินทรัพย์ | ISIN | จำนวนกองที่ถือ | ชื่อที่สะกดต่างกัน |")
        a("|---|---|---|---|")
        for e in group:
            a(f"| [[../Entities/{links[e['id']]}\\|{cell(e['name'])}]] "
              f"| {'`' + e['isin'] + '`' if e.get('isin') else '—'} "
              f"| {e['fund_count']:,} | {e['alias_count']} |")
        a("")

    a("## ค้นด้วย Dataview")
    a("")
    a("````")
    a("```dataview")
    a('TABLE fund_count AS "กองที่ถือ", isin, alias_count AS "ชื่อที่ต่างกัน"')
    a("FROM #entity-equity")
    a("SORT fund_count DESC")
    a("LIMIT 50")
    a("```")
    a("````")
    a("")
    return "\n".join(o)


def render_lookthrough_index(chosen: list[dict], reach: dict,
                             links: dict[str, str], funds: dict) -> str:
    o: list[str] = []
    a = o.append
    a("---")
    a("title: ดัชนีการถือทางอ้อม (Look-through)")
    a("tags: [index, lookthrough, holdings]")
    a("---")
    a("")
    a("# 🔭 ดัชนีการถือทางอ้อม")
    a("")
    a("[[00-home|🏠 Home]] · [[by-holding|ดัชนีสินทรัพย์]] · "
      "[[master-funds|กองทุนหลัก]] · "
      "[[../Concepts/Look-through การถือทางอ้อม|Look-through คืออะไร]]")
    a("")
    a("กองทุนไทยที่เป็น feeder รายงานพอร์ตของตัวเองว่าถือ "
      "\"หน่วยลงทุนของกองทุนหลัก 99%\" ซึ่งจริงแต่ตอบไม่ได้ว่า"
      "**เงินไปอยู่ในหุ้นตัวไหน** ตารางนี้คูณทะลุอีกชั้นให้")
    a("")
    a("> [!CAUTION] ตัวเลขทั้งหมดในหน้านี้เป็น **ขั้นต่ำ**")
    a("> ใช้เฉพาะ 10 อันดับแรกที่กองทุนหลักเปิดเผย และวันอ้างอิงของสองฝั่งไม่ตรงกัน")
    a("> ห้ามใช้เป็นตัวเลขสัดส่วนที่แท้จริง — อ่าน"
      "[[../Concepts/Look-through การถือทางอ้อม|ข้อจำกัดฉบับเต็ม]]")
    a("")

    ranked = sorted(
        ((e, reach.get(e["id"]) or {}) for e in chosen),
        key=lambda pair: -len((pair[1].get("indirect") or {})))
    ranked = [(e, r) for e, r in ranked if r.get("indirect")]

    a(f"หลักทรัพย์ที่กองทุนไทยเข้าถึงทางอ้อม: **{len(ranked):,}** รายการ")
    a("")
    a("## หลักทรัพย์ที่กองทุนไทยเข้าถึงมากที่สุด 50 อันดับ")
    a("")
    a("| # | หลักทรัพย์ | กองที่ถือทางอ้อม | กองที่ถือโดยตรง | สูงสุด ~% NAV |")
    a("|---|---|---|---|---|")
    for i, (e, r) in enumerate(ranked[:50], 1):
        ind = r.get("indirect") or {}
        top = max(ind.values()) if ind else 0
        a(f"| {i} | [[../Entities/{links[e['id']]}\|{cell(e['name'])}]] "
          f"| {len(ind):,} | {e['fund_count']:,} | {pct(top)} |")
    a("")

    a("## กองทุนไทยที่กระจุกตัวสูงสุดในหลักทรัพย์เดียว")
    a("")
    a("> สัดส่วนทางอ้อมของหลักทรัพย์ตัวเดียวในกองเดียว "
      "— ยิ่งสูงยิ่งใกล้เป็นการถือหุ้นตัวเดียว")
    a("")
    names = {e["id"]: e["name"] for e in chosen}
    worst: list[tuple[float, str, str]] = []
    for e, r in ranked:
        for pid, weight in (r.get("indirect") or {}).items():
            worst.append((weight, pid, e["id"]))
    worst.sort(reverse=True)
    a("| กองทุน | บลจ. | หลักทรัพย์ | ~% NAV |")
    a("|---|---|---|---|")
    seen: set[tuple[str, str]] = set()
    shown = 0
    for weight, pid, eid in worst:
        if (pid, eid) in seen or shown >= 30:
            continue
        seen.add((pid, eid))
        f = funds.get(pid) or {}
        a(f"| [[../Funds/{safe_name(f.get('abbr') or pid)}\|"
          f"{cell(f.get('abbr'))}]] | {cell(f.get('amc_th'))} "
          f"| [[../Entities/{links[eid]}\|{cell(names[eid])}]] | {pct(weight)} |")
        shown += 1
    a("")
    a("## ค้นด้วย Dataview")
    a("")
    a("````")
    a("```dataview")
    a('TABLE indirect_fund_count AS "กองที่ถือทางอ้อม", fund_count AS "ถือตรง"')
    a("FROM #held-indirectly")
    a("SORT indirect_fund_count DESC")
    a("LIMIT 50")
    a("```")
    a("````")
    a("")
    return "\n".join(o)


def main() -> None:
    entities = json.loads((PROC / "entities.json").read_text(encoding="utf-8"))
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))

    note_names = {pid: safe_name(f.get("abbr") or pid) for pid, f in funds.items()}

    # Obsidian resolves a wikilink by filename, so an entity note that lands on
    # the same stem as a fund or master-fund note silently steals its links.
    # "Kasikorn Bank Pcl" and the fund abbreviated "GLD" both collide this way.
    # Compared case-insensitively on purpose: NTFS treats
    # "KASIKORNBANK PUBLIC COMPANY LIMITED.md" and
    # "Kasikornbank Public Company Limited.md" as one file, so the bank's
    # equity note and its deposit note - deliberately separate entities -
    # silently overwrote each other. 29 notes were being lost this way, and
    # validate_vault could not see it because Path.exists() is case-insensitive
    # on Windows too.
    reserved = {n.lower() for n in note_names.values()}
    for folder in ("MasterFunds", "AMCs", "Concepts", "Indexes", "Factsheets"):
        reserved.update(p.stem.lower() for p in (VAULT / folder).glob("*.md"))

    lt = (json.loads(LOOKTHROUGH.read_text(encoding="utf-8"))
          if LOOKTHROUGH.exists() else {"funds": {}, "entities": {}})
    reach = lt.get("entities", {})
    # which master each fund reaches the share through, for the note's table
    for pid, rec in lt.get("funds", {}).items():
        for exp in rec.get("exposures", []):
            eid = exp.get("entity")
            if eid and eid in reach:
                reach[eid].setdefault("via", {})[pid] = rec["master_name"]

    def total_reach(e: dict) -> int:
        """How many distinct Thai funds reach this entity at all.

        The union, not max(): a share held directly by one fund and indirectly
        by a different one is reached by two, and 15 entities were being
        dropped from the vault because max() saw only 1 on each side.
        """
        r = reach.get(e["id"]) or {}
        return len(set(e["funds"]) | set(r.get("indirect") or {}))

    # a share reached only through master funds still deserves a note: nobody
    # holds Eli Lilly directly, but 60 Thai funds own a slice of it
    chosen = [e for e in entities.values() if total_reach(e) >= MIN_FUNDS]
    chosen.sort(key=lambda e: (-total_reach(e), e["name"]))

    # the generator owns this folder, so a renamed entity leaves no stale note
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.md"):
        try:
            old.unlink()
        except PermissionError:
            # Obsidian or a file indexer can hold a note open; it will be
            # overwritten below if it is still wanted, and a leftover file is
            # better than aborting the whole rebuild
            LOG.warning("could not remove %s (in use)", old.name)

    used: dict[str, str] = {}
    links: dict[str, str] = {}
    for e in chosen:
        stem = safe_name(e["name"])
        if (stem.lower() in reserved
                or (stem.lower() in used and used[stem.lower()] != e["id"])):
            # collides with a fund/master note, or with another entity that
            # cleans down to the same filename - qualify it so both survive
            qualifier = e["isin"] or KIND_LABEL.get(e["kind"], e["kind"])
            stem = safe_name(f"{e['name']} ({qualifier})")
            if stem.lower() in reserved or stem.lower() in used:
                stem = safe_name(f"{e['name']} ({e['id']})")
        used[stem.lower()] = e["id"]
        links[e["id"]] = stem
        (OUT / f"{stem}.md").write_text(
            render(e, funds, note_names, reach.get(e["id"])), encoding="utf-8")

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "rows": sum(len((f.get("portfolio") or {}).get("items") or [])
                    for f in funds.values()),
        "entities": len(entities),
        "multi_alias": sum(1 for e in entities.values() if e["alias_count"] > 1),
        "collapsed": sum(e["alias_count"] - 1 for e in entities.values()),
    }
    INDEX.write_text(render_index(chosen, stats, links), encoding="utf-8")
    LOOK_INDEX.write_text(render_lookthrough_index(chosen, reach, links, funds),
                          encoding="utf-8")
    LINKS.write_text(json.dumps(links, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    by_kind = Counter(e["kind"] for e in chosen)
    on_disk = len(list(OUT.glob("*.md")))
    if on_disk != len(chosen):
        LOG.error("wrote %d notes but %d files exist - filename collision",
                  len(chosen), on_disk)
    LOG.info("wrote %d entity notes (held by >=%d funds) -> %s",
             len(chosen), MIN_FUNDS, OUT.relative_to(ROOT))
    LOG.info("  by kind: %s", json.dumps(dict(by_kind.most_common())))
    LOG.info("index -> %s", INDEX.relative_to(ROOT))


if __name__ == "__main__":
    main()
