"""
gen_changelog.py - Snapshot the vault's facts and report what moved since the
previous run.

A daily rebuild that silently overwrites 7,000 notes is not much use: the
interesting output of run number two is not the notes, it is the *difference*.
This stage keeps a compact snapshot (one small record per fund, no holdings
detail) and diffs today's against the last one.

What it watches, and why each one matters to someone holding the fund:

    scope          a fund entering or leaving the "still sold, not Term/PVD"
                   universe - a closure or a new launch
    ter            the fee actually charged. A rise is money out of pocket
    front / back   sales charges
    risk_spectrum  a re-rating changes who is allowed to hold it
    policy         a change of investment policy
    master         the feeder pointing at a different master fund
    portfolio      a new quarterly filing, and how concentration moved
    nav            latest NAV per unit and its date

Snapshots live in data/state/. The newest is snapshot.json; each run also
archives the previous one as snapshot-<date>.json, so a bad day can be
inspected rather than guessed at.

    python scripts/gen_changelog.py            # diff + write notes
    python scripts/gen_changelog.py --init     # first snapshot, no diff
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fees  # noqa: E402
from gen_vault import safe_name  # noqa: E402
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("gen_changelog")
PROC = ROOT / "data" / "processed"
STATE = ROOT / "data" / "state"
SNAPSHOT = STATE / "snapshot.json"
VAULT = ROOT / "vault"
CHANGES = VAULT / "Changes"
INDEX = VAULT / "Indexes" / "changelog.md"

# a move smaller than this is rounding in the source data, not a fee change
TER_EPSILON = 0.001
KEEP_DAILY_NOTES = 120


def ter_of(fund: dict) -> float | None:
    """What a retail buyer is charged - see scripts/fees.py for why not min()."""
    return fees.retail_ter(fund)


def fee_of(fund: dict, kind: str) -> float | None:
    return fees.fee_of(fund, kind)


def latest_nav(fund: dict) -> tuple[str | None, float | None]:
    rows = [r for r in fund.get("nav") or [] if r.get("date")]
    if not rows:
        return None, None
    row = max(rows, key=lambda r: r["date"])
    return row.get("date"), row.get("nav_per_unit")


def snapshot_funds() -> dict:
    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    entities_path = PROC / "entities.json"
    entities = (json.loads(entities_path.read_text(encoding="utf-8"))
                if entities_path.exists() else {})

    out: dict[str, dict] = {}
    for pid, f in funds.items():
        pf = f.get("portfolio") or {}
        nav_date, nav_value = latest_nav(f)
        out[pid] = {
            "abbr": f.get("abbr"),
            "name_th": f.get("name_th"),
            "amc_th": f.get("amc_th"),
            "policy": f.get("policy"),
            "risk": f.get("risk_spectrum"),
            "ter": ter_of(f),
            "front": fee_of(f, "front"),
            "back": fee_of(f, "back"),
            "master": f.get("feeder_master"),
            "port_period": pf.get("period"),
            "port_top10": pf.get("top10_pct_nav"),
            "port_rows": pf.get("total_rows"),
            "nav_date": nav_date,
            "nav": nav_value,
        }
    return {
        "taken_at": datetime.now().isoformat(timespec="seconds"),
        "date": str(date.today()),
        "funds": out,
        "entities": {eid: e["fund_count"] for eid, e in entities.items()},
        "entity_names": {eid: e["name"] for eid, e in entities.items()},
    }


FIELD_LABEL = {
    "ter": "ค่าธรรมเนียมรวมที่เก็บจริง (%)",
    "front": "ค่าธรรมเนียมขาย Front-end (%)",
    "back": "ค่าธรรมเนียมรับซื้อคืน Back-end (%)",
    "risk": "ระดับความเสี่ยง",
    "policy": "นโยบายการลงทุน",
    "master": "กองทุนหลัก",
    "port_period": "งวดพอร์ตล่าสุด",
    "name_th": "ชื่อกองทุน",
    "amc_th": "บลจ.",
}
NUMERIC_FIELDS = {"ter", "front", "back"}


def diff(old: dict, new: dict) -> dict:
    old_f, new_f = old.get("funds", {}), new.get("funds", {})
    added = [new_f[p] | {"proj_id": p} for p in new_f.keys() - old_f.keys()]
    removed = [old_f[p] | {"proj_id": p} for p in old_f.keys() - new_f.keys()]

    changed: list[dict] = []
    for pid in old_f.keys() & new_f.keys():
        a, b = old_f[pid], new_f[pid]
        moves = []
        for field in FIELD_LABEL:
            before, after = a.get(field), b.get(field)
            if field in NUMERIC_FIELDS:
                if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                    if abs(before - after) < TER_EPSILON:
                        continue
                elif before == after:
                    continue
            elif before == after:
                continue
            moves.append({"field": field, "before": before, "after": after})
        if moves:
            changed.append({"proj_id": pid, "abbr": b.get("abbr"),
                            "amc_th": b.get("amc_th"), "moves": moves})

    old_e, new_e = old.get("entities", {}), new.get("entities", {})
    names = new.get("entity_names", {})
    new_entities = sorted(
        ({"id": eid, "name": names.get(eid, eid), "funds": new_e[eid]}
         for eid in new_e.keys() - old_e.keys() if new_e[eid] >= 2),
        key=lambda e: -e["funds"])

    return {"added": added, "removed": removed, "changed": changed,
            "new_entities": new_entities}


def fund_link(abbr) -> str:
    """A wikilink to a fund note.

    Must go through gen_vault.safe_name: the abbreviation "KT25/75RMF" is
    stored with a slash but the note on disk is "KT25-75RMF.md", and
    "ES-CHCHALLENGE#1" would otherwise read as a heading anchor.
    """
    if not abbr:
        return "—"
    return f"[[../Funds/{safe_name(abbr)}\|{cell(abbr)}]]"


def cell(value) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|")


def render_note(d: dict, new: dict, old: dict) -> str:
    o: list[str] = []
    a = o.append
    today = new["date"]
    total = len(d["added"]) + len(d["removed"]) + len(d["changed"])

    a("---")
    a(f"title: การเปลี่ยนแปลง {today}")
    a(f"date: {today}")
    a(f"changes: {total}")
    a("tags: [changelog]")
    a("---")
    a("")
    a(f"# 📆 การเปลี่ยนแปลง {today}")
    a("")
    a(f"เทียบกับ snapshot เมื่อ **{old.get('date', '-')}** · "
      "[[../Indexes/changelog|ดัชนีการเปลี่ยนแปลง]] · [[../Indexes/00-home|🏠 Home]]")
    a("")

    if not total and not d["new_entities"]:
        a("> [!NOTE] ไม่มีการเปลี่ยนแปลงในรอบนี้")
        a("")
        return "\n".join(o)

    a("| รายการ | จำนวน |")
    a("|---|---|")
    a(f"| กองทุนใหม่ | {len(d['added'])} |")
    a(f"| กองทุนที่หลุดจากขอบเขต | {len(d['removed'])} |")
    a(f"| กองทุนที่มีข้อมูลเปลี่ยน | {len(d['changed'])} |")
    a(f"| สินทรัพย์ที่เพิ่งปรากฏ | {len(d['new_entities'])} |")
    a("")

    if d["added"]:
        a("## 🆕 กองทุนใหม่")
        a("")
        a("| กองทุน | บลจ. | นโยบาย | ความเสี่ยง |")
        a("|---|---|---|---|")
        for f in sorted(d["added"], key=lambda x: str(x.get("abbr"))):
            a(f"| {fund_link(f.get('abbr'))} "
              f"| {cell(f.get('amc_th'))} | {cell(f.get('policy'))} "
              f"| {cell(f.get('risk'))} |")
        a("")

    if d["removed"]:
        a("## 🚪 หลุดจากขอบเขต (ปิดกอง / เปลี่ยนสถานะ)")
        a("")
        a("> ไม่มีโน้ตของกองเหล่านี้ในวอลต์แล้ว รายละเอียดจึงมาจาก snapshot เดิม")
        a("")
        a("| กองทุน | บลจ. | นโยบาย |")
        a("|---|---|---|")
        for f in sorted(d["removed"], key=lambda x: str(x.get("abbr"))):
            a(f"| {cell(f.get('abbr'))} | {cell(f.get('amc_th'))} "
              f"| {cell(f.get('policy'))} |")
        a("")

    fee_moves = [c for c in d["changed"]
                 if any(m["field"] in NUMERIC_FIELDS for m in c["moves"])]
    if fee_moves:
        a("## 💰 ค่าธรรมเนียมเปลี่ยน")
        a("")
        a("> [!IMPORTANT] ค่าธรรมเนียมที่เพิ่มขึ้นคือเงินที่ผู้ถือหน่วยจ่ายเพิ่มโดยตรง")
        a("")
        a("| กองทุน | รายการ | เดิม | ใหม่ | ส่วนต่าง |")
        a("|---|---|---|---|---|")
        for c in sorted(fee_moves, key=lambda x: str(x.get("abbr"))):
            for m in c["moves"]:
                if m["field"] not in NUMERIC_FIELDS:
                    continue
                before, after = m["before"], m["after"]
                if isinstance(before, (int, float)) and isinstance(after, (int, float)):
                    delta = after - before
                    arrow = "🔺" if delta > 0 else "🔻"
                    delta_text = f"{arrow} {abs(delta):.3f}"
                else:
                    delta_text = "—"
                a(f"| {fund_link(c['abbr'])} "
                  f"| {FIELD_LABEL[m['field']]} | {cell(before)} | {cell(after)} "
                  f"| {delta_text} |")
        a("")

    other = [c for c in d["changed"]
             if any(m["field"] not in NUMERIC_FIELDS for m in c["moves"])]
    if other:
        a("## 🔄 ข้อมูลอื่นที่เปลี่ยน")
        a("")
        a("| กองทุน | รายการ | เดิม | ใหม่ |")
        a("|---|---|---|---|")
        for c in sorted(other, key=lambda x: str(x.get("abbr")))[:200]:
            for m in c["moves"]:
                if m["field"] in NUMERIC_FIELDS:
                    continue
                a(f"| {fund_link(c['abbr'])} "
                  f"| {FIELD_LABEL[m['field']]} | {cell(m['before'])} "
                  f"| {cell(m['after'])} |")
        if len(other) > 200:
            a(f"| _...และอีก {len(other) - 200} กอง_ | | | |")
        a("")

    if d["new_entities"]:
        a("## 🧩 สินทรัพย์ที่เพิ่งปรากฏในพอร์ต")
        a("")
        a("| สินทรัพย์ | จำนวนกองที่ถือ |")
        a("|---|---|")
        for e in d["new_entities"][:40]:
            a(f"| {cell(e['name'])} | {e['funds']} |")
        a("")

    return "\n".join(o)


def render_index(notes: list[Path]) -> str:
    o: list[str] = []
    a = o.append
    a("---")
    a("title: ดัชนีการเปลี่ยนแปลง")
    a("tags: [index, changelog]")
    a("---")
    a("")
    a("# 📆 ดัชนีการเปลี่ยนแปลง")
    a("")
    a("[[00-home|🏠 Home]] · [[all-funds|กองทุนทั้งหมด]] · "
      "[คู่มือรันประจำวัน](../../docs/guides/daily-operation.md)")
    a("")
    a("แต่ละโน้ตคือส่วนต่างระหว่างการรันสองครั้งติดกัน "
      "ไม่ใช่ภาพรวมของทั้งวอลต์")
    a("")
    a("| วันที่ | จำนวนการเปลี่ยนแปลง |")
    a("|---|---|")
    for path in notes:
        text = path.read_text(encoding="utf-8")
        count = next((line.split(":", 1)[1].strip()
                      for line in text.splitlines()[:8]
                      if line.startswith("changes:")), "?")
        a(f"| [[../Changes/{path.stem}\\|{path.stem}]] | {count} |")
    a("")
    a("## ค้นด้วย Dataview")
    a("")
    a("````")
    a("```dataview")
    a('TABLE changes AS "การเปลี่ยนแปลง"')
    a("FROM #changelog")
    a("SORT date DESC")
    a("```")
    a("````")
    a("")
    return "\n".join(o)


def main() -> None:
    init = "--init" in sys.argv
    STATE.mkdir(parents=True, exist_ok=True)
    CHANGES.mkdir(parents=True, exist_ok=True)

    new = snapshot_funds()

    if not SNAPSHOT.exists() or init:
        SNAPSHOT.write_text(json.dumps(new, ensure_ascii=False),
                            encoding="utf-8")
        LOG.info("snapshot created for %d funds - no diff on the first run",
                 len(new["funds"]))
        INDEX.write_text(render_index(sorted(CHANGES.glob("*.md"), reverse=True)),
                         encoding="utf-8")
        return

    old = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    d = diff(old, new)

    note = CHANGES / f"{new['date']}.md"
    note.write_text(render_note(d, new, old), encoding="utf-8")

    # keep the previous snapshot so a surprising diff can be re-examined
    archive = STATE / f"snapshot-{old.get('date', 'unknown')}.json"
    if not archive.exists():
        archive.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
    SNAPSHOT.write_text(json.dumps(new, ensure_ascii=False), encoding="utf-8")

    notes = sorted(CHANGES.glob("*.md"), reverse=True)
    for stale in notes[KEEP_DAILY_NOTES:]:
        stale.unlink()
    INDEX.write_text(render_index(notes[:KEEP_DAILY_NOTES]), encoding="utf-8")

    LOG.info("vs %s: +%d funds, -%d funds, %d changed, %d new entities",
             old.get("date"), len(d["added"]), len(d["removed"]),
             len(d["changed"]), len(d["new_entities"]))
    LOG.info("note -> %s", note.relative_to(ROOT))


if __name__ == "__main__":
    main()
