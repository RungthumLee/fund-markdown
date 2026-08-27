"""
validate_vault.py - Sanity-check the generated vault and docs.

Checks performed:
  1. broken [[wikilinks]] (target note does not exist)
  2. notes with no inbound links (orphans)
  3. missing YAML frontmatter
  4. duplicate note titles across folders
  5. coverage of key sections in fund notes

Writes a human-readable report to docs/project/validation-report.md and exits
non-zero when broken links are found, so it can gate a pipeline run.

    python scripts/validate_vault.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("validate_vault")
VAULT = ROOT / "vault"
DOCS = ROOT / "docs"
REPORT = DOCS / "project" / "validation-report.md"

# [[target]] or [[target|label]] — capture the target, ignore the label.
# Inside a markdown table the pipe is escaped as "\|", so allow and then strip
# that trailing backslash; it belongs to the table syntax, not the note name.
LINK = re.compile(r"\[\[([^\]|#]+?)\\?(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")

REQUIRED_SECTIONS = [
    "## 1. ข้อมูลทั่วไป", "## 4. ความเสี่ยง", "## 5. ค่าธรรมเนียม",
    "## 6. ผลการดำเนินงาน", "## 7. พอร์ตการลงทุน", "## 8. NAV",
    "## 12. Factsheet",
]

# How much of each folder is expected to carry a section, as a floor.
#
# This exists because of ISS-034: a string replacement in a generator failed
# silently, the "รหัสอ้างอิงสากล" block stopped being written, and every other
# check still passed - no broken link, no orphan, no error. A render block that
# quietly stops emitting is invisible unless something counts it.
#
# Floors are set from measured coverage minus roughly ten points of slack, so
# ordinary data movement does not trip them but a block disappearing does.
# Raise a floor when a section genuinely becomes more common.
SECTION_FLOORS: dict[str, list[tuple[str, float]]] = {
    "Funds": [
        ("## 5. ค่าธรรมเนียม", 1.00),
        ("### สรุปต่อชนิดหน่วยลงทุน", 0.90),
        ("## 7. พอร์ตการลงทุน", 1.00),
        ("### 🔭 ทะลุกองทุนหลัก", 0.20),
        ("## 12. Factsheet", 1.00),
    ],
    "Entities": [
        ("## กองทุนไทยที่ถือโดยตรง", 1.00),
        ("## รหัสอ้างอิงสากล", 0.50),
        ("## 🔭 กองทุนไทยที่ถือทางอ้อม", 0.15),
        ("## ชื่อที่พบในข้อมูลดิบ", 0.65),
    ],
    "MasterFunds": [
        ("## ข้อมูลกองทุน", 1.00),
        ("## แหล่งข้อมูล", 1.00),
        ("## กองทุนไทยที่ลงทุน", 0.95),
    ],
}


def collect_notes() -> dict[str, Path]:
    """Map both bare stem and relative path (no extension) to each note."""
    notes: dict[str, Path] = {}
    for root in (VAULT, DOCS):
        for p in root.rglob("*.md"):
            notes.setdefault(p.stem, p)
            rel = p.relative_to(ROOT).with_suffix("").as_posix()
            notes[rel] = p
    return notes


def resolve(target: str, source: Path, notes: dict[str, Path]) -> bool:
    """Obsidian resolves links by stem, or by path relative to the note."""
    target = target.strip().rstrip("\\").strip()
    if not target:
        return False
    if target in notes:
        return True
    # only treat it as a path when it actually looks like one - Path().stem
    # would cut "T. Rowe Price US Blue Chip Eq I" down to "T"
    if "/" in target and Path(target).name in notes:
        return True
    # relative path from the linking note
    try:
        cand = (source.parent / target).resolve()
        for suffix in ("", ".md"):
            if Path(str(cand) + suffix).exists():
                return True
        rel = cand.relative_to(ROOT).as_posix()
        if rel in notes or Path(rel).stem in notes:
            return True
    except (ValueError, OSError):
        pass
    return False


def main() -> None:
    notes = collect_notes()
    md_files = sorted({p for p in notes.values()})
    LOG.info("scanning %d notes", len(md_files))

    broken: list[tuple[str, str]] = []
    inbound: Counter[str] = Counter()
    no_frontmatter: list[str] = []
    stems: defaultdict[str, list[str]] = defaultdict(list)
    missing_sections: Counter[str] = Counter()
    fund_notes = 0

    for path in md_files:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        stems[path.stem].append(rel)

        if not text.startswith("---"):
            no_frontmatter.append(rel)

        for target in LINK.findall(text):
            target = target.strip().rstrip("\\").strip()
            if resolve(target, path, notes):
                key = notes.get(target) or notes.get(Path(target).name)
                if key is not None:
                    inbound[key.relative_to(ROOT).as_posix()] += 1
            else:
                broken.append((rel, target.strip()))

        if path.parent.name == "Funds":
            fund_notes += 1
            for section in REQUIRED_SECTIONS:
                if section not in text:
                    missing_sections[section] += 1

    # ---- section coverage floors (ISS-034) ------------------------------
    seen_sections: defaultdict[str, Counter[str]] = defaultdict(Counter)
    folder_totals: Counter[str] = Counter()
    for path in md_files:
        folder = path.parent.name
        if folder not in SECTION_FLOORS:
            continue
        folder_totals[folder] += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for section, _ in SECTION_FLOORS[folder]:
            if section in text:
                seen_sections[folder][section] += 1

    coverage: list[dict] = []
    for folder, rules in SECTION_FLOORS.items():
        total = folder_totals.get(folder, 0)
        for section, floor in rules:
            hits = seen_sections[folder][section]
            share = hits / total if total else 0.0
            coverage.append({"folder": folder, "section": section,
                             "hits": hits, "total": total,
                             "share": share, "floor": floor,
                             "ok": total > 0 and share >= floor})
    below_floor = [c for c in coverage if not c["ok"]]

    orphans = [p.relative_to(ROOT).as_posix() for p in md_files
               if inbound[p.relative_to(ROOT).as_posix()] == 0]
    dupes = {s: paths for s, paths in stems.items() if len(paths) > 1}

    # NTFS is case-insensitive, so two generators can write "APPLE INC.md" and
    # "Apple Inc.md" and the second silently replaces the first. Neither the
    # stem check above nor Path.exists() sees it on Windows, which is exactly
    # how 29 entity notes went missing without a single broken link reported.
    by_folder: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list))
    for path in md_files:
        by_folder[path.parent.name][path.stem.lower()].append(path.stem)
    case_clashes = {f"{folder}/{low}": names
                    for folder, group in by_folder.items()
                    for low, names in group.items()
                    if len({n for n in names}) > 1}

    broken_by_target = Counter(t for _, t in broken)

    # ---- report ---------------------------------------------------------
    out = ["---", "title: Validation Report", "tags: [project, qa]", "---", "",
           "# 🔍 Validation Report", "",
           "สร้างอัตโนมัติโดย `scripts/validate_vault.py`", "",
           "[[tasks|Tasks]] · [[issues|Issues]] · [[data-quality|Data Quality]]", "",
           "## สรุป", "", "| รายการ | จำนวน |", "|---|---|",
           f"| โน้ตทั้งหมด | {len(md_files):,} |",
           f"| โน้ตกองทุน | {fund_notes:,} |",
           f"| ลิงก์ที่เสีย | {len(broken):,} |",
           f"| เป้าหมายที่เสีย (ไม่ซ้ำ) | {len(broken_by_target):,} |",
           f"| โน้ตที่ไม่มีใครลิงก์มา | {len(orphans):,} |",
           f"| โน้ตที่ไม่มี frontmatter | {len(no_frontmatter):,} |",
           f"| ชื่อโน้ตซ้ำกัน | {len(dupes):,} |",
           f"| ชื่อไฟล์ชนกันเมื่อไม่สนตัวพิมพ์ | {len(case_clashes):,} |",
           f"| หัวข้อที่หายไปจากโน้ต | {len(below_floor):,} |", ""]

    out += ["## ลิงก์ที่เสีย (20 เป้าหมายที่พบบ่อยที่สุด)", ""]
    if broken_by_target:
        out += ["| เป้าหมาย | จำนวนครั้ง |", "|---|---|"]
        for target, n in broken_by_target.most_common(20):
            out.append(f"| `{target}` | {n} |")
    else:
        out.append("✅ ไม่มีลิงก์เสีย")
    out.append("")

    out += ["## โน้ตที่ไม่มีใครลิงก์มา (orphan)", ""]
    if orphans:
        out += [f"- `{o}`" for o in orphans[:40]]
        if len(orphans) > 40:
            out.append(f"- _...และอีก {len(orphans) - 40} รายการ_")
    else:
        out.append("✅ ไม่มี")
    out.append("")

    out += ["## โน้ตที่ขาด frontmatter", ""]
    out += ([f"- `{p}`" for p in no_frontmatter[:30]] if no_frontmatter
            else ["✅ ไม่มี"])
    out.append("")

    out += ["## ชื่อโน้ตซ้ำกัน", ""]
    if dupes:
        for stem, paths in list(dupes.items())[:30]:
            out.append(f"- `{stem}` → {', '.join(f'`{p}`' for p in paths)}")
    else:
        out.append("✅ ไม่มี")
    out.append("")

    out += ["## ชื่อไฟล์ที่ชนกันเมื่อไม่สนตัวพิมพ์เล็กใหญ่", ""]
    if case_clashes:
        out += ["> [!WARNING] บน Windows ไฟล์เหล่านี้เขียนทับกัน "
                "โน้ตที่เขียนทีหลังจะลบของเดิมโดยไม่มีสัญญาณเตือน", ""]
        for key, names in list(case_clashes.items())[:30]:
            out.append(f"- `{key}` → {', '.join(f'`{n}`' for n in names)}")
    else:
        out.append("✅ ไม่มี")
    out.append("")

    out += ["## ความครอบคลุมของหัวข้อในโน้ตที่สร้างอัตโนมัติ", "",
            "> ตรวจว่าบล็อกใน generator ยังทำงานอยู่ ถ้าบล็อกไหนหยุดสร้าง "
            "โดยไม่มี error สัดส่วนจะตกต่ำกว่าเกณฑ์และรายงานตรงนี้", "",
            "| โฟลเดอร์ | หัวข้อ | พบ | สัดส่วน | เกณฑ์ขั้นต่ำ | |",
            "|---|---|---|---|---|---|"]
    for c in coverage:
        out.append(f"| {c['folder']} | `{c['section']}` | {c['hits']:,}/{c['total']:,} "
                   f"| {c['share']:.1%} | {c['floor']:.0%} "
                   f"| {'✅' if c['ok'] else '❌'} |")
    out.append("")

    out += ["## หัวข้อที่หายไปในโน้ตกองทุน", ""]
    if missing_sections:
        out += ["| หัวข้อ | จำนวนโน้ตที่ขาด |", "|---|---|"]
        for section, n in missing_sections.most_common():
            out.append(f"| `{section}` | {n} |")
    else:
        out.append("✅ โน้ตกองทุนทุกฉบับมีหัวข้อครบ")
    out.append("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")

    summary = {"notes": len(md_files), "fund_notes": fund_notes,
               "broken_links": len(broken), "orphans": len(orphans),
               "no_frontmatter": len(no_frontmatter), "duplicate_stems": len(dupes),
               "case_clashes": len(case_clashes),
               "sections_below_floor": len(below_floor)}
    LOG.info("validation: %s", json.dumps(summary))
    LOG.info("report -> %s", REPORT.relative_to(ROOT))

    if case_clashes:
        LOG.error("%d filenames clash only by case - notes are being "
                  "overwritten on Windows", len(case_clashes))
    for c in below_floor:
        LOG.error("section '%s' present in only %.1f%% of %s (floor %.0f%%) - "
                  "did a generator block stop emitting?",
                  c["section"], c["share"] * 100, c["folder"], c["floor"] * 100)
    if broken or case_clashes or below_floor:
        if broken:
            LOG.warning("%d broken links found", len(broken))
        sys.exit(1)


if __name__ == "__main__":
    main()
