"""
check_nav_continuity.py - Is each share class's NAV series actually continuous,
and what happens to it when a fund is renamed?

Both questions have to be asked of the raw feed, not of nav_history.json, which
has already stitched and cleaned. This reads data/raw/nav.jsonl and reports:

  1. cadence per (proj_id, fund_class_name) - daily / weekly / monthly, because
     a monthly-priced fund is not a "gap", it just does not price daily;
  2. holes in the daily-priced series, and whether a sibling label covers them;
  3. market-wide holes - dates where nearly every fund is missing at once;
  4. label handovers that look like a rename: one label stops, another starts
     within days at the same NAV, and the two never report on the same day.

Output: docs/project/nav-continuity.md  (+ a summary in the log)

    python scripts/check_nav_continuity.py
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("check_nav_continuity")
RAW = ROOT / "data" / "raw" / "nav.jsonl"
OUT = ROOT / "docs" / "project" / "nav-continuity.md"

GAP_DAYS = 10          # a hole worth reporting, for a daily-priced class
CADENCE_WEEKLY = 4     # median spacing above this is not daily
CADENCE_MONTHLY = 20
HANDOVER_DAYS = 7      # a rename hands over this fast
HANDOVER_STEP = 0.05   # and does not move the NAV more than this
PIPE = "\\|"           # an escaped pipe, so a label never breaks a table cell


def load() -> dict:
    series: dict[tuple[str, str], list] = defaultdict(list)
    with RAW.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid, d = r.get("proj_id"), str(r.get("nav_date") or "")[:10]
            if not pid or not d:
                continue
            series[(pid, r.get("fund_class_name") or "main")].append(
                (d, r.get("last_val")))
    return {k: sorted(set(v)) for k, v in series.items()}


def business_days(a: date, b: date) -> int:
    n, d = 0, a
    while d <= b:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def main() -> None:
    if not RAW.exists():
        LOG.error("no data/raw/nav.jsonl - run harvest first")
        return
    funds = json.loads((ROOT / "data" / "processed" / "funds.json")
                       .read_text(encoding="utf-8"))
    series = load()
    LOG.info("read %d class-series", len(series))

    by_fund: dict[str, dict] = defaultdict(dict)
    for (pid, cls), pts in series.items():
        by_fund[pid][cls] = pts

    cadence: Counter = Counter()
    holes: list[dict] = []
    market: Counter = Counter()
    for (pid, cls), pts in series.items():
        if pid not in funds or len(pts) < 5:
            continue
        ds = [date.fromisoformat(d) for d, _ in pts]
        steps = [(ds[i] - ds[i - 1]).days for i in range(1, len(ds))]
        med = statistics.median(steps)
        kind = ("monthly" if med > CADENCE_MONTHLY else
                "weekly" if med > CADENCE_WEEKLY else "daily")
        cadence[kind] += 1
        if kind != "daily":
            continue
        for i in range(1, len(ds)):
            gap = (ds[i] - ds[i - 1]).days
            if gap <= GAP_DAYS:
                continue
            market[(str(ds[i - 1]), str(ds[i]))] += 1
            covered = any(
                ds[i - 1] < date.fromisoformat(d) < ds[i]
                for c, p in by_fund[pid].items() if c != cls for d, _ in p)
            holes.append({"abbr": funds[pid].get("abbr"), "pid": pid, "cls": cls,
                          "from": str(ds[i - 1]), "to": str(ds[i]), "days": gap,
                          "covered": covered})

    # renames: label A stops, label B starts, never on the same day, NAV carries
    renames: list[dict] = []
    for pid, cl in by_fund.items():
        if pid not in funds or len(cl) < 2:
            continue
        for a, ap in cl.items():
            for b, bp in cl.items():
                if a == b or {d for d, _ in ap} & {d for d, _ in bp}:
                    continue
                gap = (date.fromisoformat(bp[0][0])
                       - date.fromisoformat(ap[-1][0])).days
                if not 0 < gap <= HANDOVER_DAYS:
                    continue
                va, vb = ap[-1][1], bp[0][1]
                if not va or not vb or abs(vb / va - 1) > HANDOVER_STEP:
                    continue
                renames.append({"abbr": funds[pid].get("abbr"), "pid": pid,
                                "old": a, "new": b, "on": bp[0][0],
                                "step": round((vb / va - 1) * 100, 2)})

    daily = cadence["daily"] or 1
    affected = len({(h["pid"], h["cls"]) for h in holes})
    wide = [(k, n) for k, n in market.most_common(6) if n > 50]

    L = [
        "---", "title: NAV Continuity Report",
        "tags: [project, data-quality, nav, generated]",
        f"updated: {date.today()}", "---", "",
        "# NAV Continuity - ความต่อเนื่องของ NAV รายชนิดหน่วยลงทุน", "",
        "> สร้างอัตโนมัติโดย `scripts/check_nav_continuity.py` จาก "
        "`data/raw/nav.jsonl` - **อย่าแก้ด้วยมือ**", "",
        "ที่เกี่ยวข้อง: [[data-quality|Data Quality]] · [[issues|Issues]] · "
        "[[../../vault/Concepts/การเปลี่ยนชื่อกองทุนกับ NAV|แนวคิด: เปลี่ยนชื่อกับ NAV]]",
        "",
        "## 1. ความถี่ในการประกาศ NAV", "",
        "ไม่ใช่ทุกกองประกาศ NAV ทุกวันทำการ - ถ้าไม่แยกออกก่อน กองที่ประกาศรายเดือน "
        "จะดูเหมือน 'ข้อมูลขาด' ทั้งที่เป็นเรื่องปกติของกองนั้น", "",
        "| ความถี่ | จำนวน class-series (ในขอบเขต) |", "|---|---|",
        f"| รายวัน | {cadence['daily']:,} |",
        f"| รายสัปดาห์ | {cadence['weekly']:,} |",
        f"| รายเดือน | {cadence['monthly']:,} |", "",
        "## 2. ช่องว่างของกองที่ประกาศรายวัน", "",
        f"- series รายวันทั้งหมด **{cadence['daily']:,}**",
        f"- มีช่องว่างเกิน {GAP_DAYS} วันอย่างน้อย 1 ครั้ง: **{affected:,}** "
        f"({affected / daily * 100:.0f}%)",
        "- ช่องว่างที่มีป้ายชื่ออื่นของกองเดียวกันครอบคลุมอยู่ "
        f"(= เปลี่ยนป้าย ไม่ใช่ข้อมูลหาย): **{sum(1 for h in holes if h['covered']):,}** ครั้ง",
        "",
    ]

    if wide:
        L += ["### ช่วงที่หายพร้อมกันทั้งตลาด", "",
              "ช่องว่างเดียวกันโผล่ในหลายร้อยกองพร้อมกัน = **ข้อมูลต้นทางขาด** "
              "ไม่ใช่เรื่องของกองใดกองหนึ่ง", "",
              "| ข้อมูลล่าสุดก่อนหาย | กลับมามีข้อมูล | จำนวน series ที่กระทบ |",
              "|---|---|---|"]
        L += [f"| {a} | {b} | {n:,} |" for (a, b), n in wide]
        L += [""]

    worst = sorted(holes, key=lambda h: -h["days"])[:15]
    L += ["### ช่องว่างที่ยาวที่สุด 15 อันดับ", "",
          "| กอง | ชนิด | หายตั้งแต่ | กลับมา | วัน | มีป้ายอื่นครอบคลุม |",
          "|---|---|---|---|---|---|"]
    L += [f"| [[../../vault/Funds/{h['abbr']}{PIPE}{h['abbr']}]] | `{h['cls']}` | "
          f"{h['from']} | {h['to']} | {h['days']:,} | "
          f"{'ใช่' if h['covered'] else 'ไม่'} |" for h in worst]

    L += ["", "## 3. การเปลี่ยนชื่อที่ตรวจพบจากป้าย class", "",
          "ต้นทางไม่เก็บประวัติชื่อ (`profiles` มีชื่อเดียวต่อโครงการ) - "
          "ร่องรอยเดียวคือป้าย `fund_class_name` ในชุดข้อมูล NAV", "",
          "พบการส่งไม้ที่เข้าเกณฑ์ (ไม่เคยรายงานวันเดียวกัน · ห่างไม่เกิน "
          f"{HANDOVER_DAYS} วัน · NAV ต่างไม่เกิน {HANDOVER_STEP:.0%}): "
          f"**{len(renames):,}** คู่", "",
          "| กอง | ป้ายเดิม | ป้ายใหม่ | เริ่มใช้ | NAV ขยับ |", "|---|---|---|---|---|"]
    seen: set = set()
    for r in sorted(renames, key=lambda r: (r["abbr"] or "", r["on"])):
        key = (r["pid"], r["old"], r["new"])
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 40:
            break
        L.append(f"| [[../../vault/Funds/{r['abbr']}{PIPE}{r['abbr']}]] | "
                 f"`{r['old']}` | `{r['new']}` | {r['on']} | {r['step']:+.2f}% |")
    L += ["", f"_แสดง 40 คู่แรกจาก {len(renames):,}_ · "
          "`nav_history.py` ต่อ series ให้อัตโนมัติตามเกณฑ์เดียวกันนี้", ""]

    OUT.write_text("\n".join(L), encoding="utf-8")
    LOG.info("cadence=%s daily_series_with_holes=%d renames=%d -> %s",
             dict(cadence), affected, len(renames), OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
