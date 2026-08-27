"""
parse_factsheets.py - Extract text from downloaded factsheet PDFs into markdown.

Reads data/factsheets/*.pdf with PyMuPDF and writes one note per fund into
vault/Factsheets/, keeping page boundaries and pulling out a few high-signal
values (as-of date, NAV, risk level) into frontmatter so the notes are queryable
from Obsidian Dataview.

    python scripts/parse_factsheets.py
    python scripts/parse_factsheets.py --limit 20 --force
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402
from factsheet_sections import extract as extract_sections  # noqa: E402

LOG = get_logger("parse_factsheets")
PDF_DIR = ROOT / "data" / "factsheets"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "vault" / "Factsheets"
OUT.mkdir(parents=True, exist_ok=True)
SECTIONS_JSON = PROC / "factsheet_sections.json"

# section key -> (heading, value column label)
SECTION_TITLE = {
    "asset_types": ("สัดส่วนประเภททรัพย์สินที่ลงทุน", "ประเภททรัพย์สิน"),
    "top_holdings": ("ทรัพย์สินที่ลงทุนสูงสุด 5 อันดับแรก", "ทรัพย์สิน"),
    "sectors": ("การจัดสรรการลงทุนในกลุ่มอุตสาหกรรม", "กลุ่มอุตสาหกรรม"),
    "countries": ("การจัดสรรการลงทุนในต่างประเทศ", "ประเทศ / ภูมิภาค"),
    "credit_ratings": ("การจัดสรรตามอันดับความน่าเชื่อถือ", "อันดับความน่าเชื่อถือ"),
}

MAX_CHARS_PER_PAGE = 12_000
THAI = re.compile(r"[฀-๿]")


def safe_name(text: str) -> str:
    """Obsidian-safe filename (mirrors gen_vault.safe_name)."""
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s).strip(". ")
    return s or "untitled"


def tidy(text: str) -> str:
    """Collapse the ragged whitespace PDF extraction leaves behind."""
    text = text.replace("\r", "")
    text = re.sub(r"[ \t\xa0]{2,}", "  ", text)
    lines = []
    for line in text.split("\n"):
        line = line.rstrip()
        if not line.strip():
            if lines and lines[-1] == "":
                continue
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def scrape_signals(text: str) -> dict:
    """Pull the few values that can be read off a factsheet unambiguously.

    Deliberately narrow. Earlier attempts at scraping the risk level and NAV
    produced confidently wrong numbers — the risk regex matched the 1-8 scale
    legend rather than the fund's own level, and NAV labels are reused for
    several different figures on the page. Those values come from the API in
    the fund note, which is authoritative, so guessing here only adds noise.
    Only the as-of date and the AIMC peer group are extracted.
    """
    out: dict[str, str] = {}

    m = re.search(r"ข้อมูล\s*ณ\s*วันที่\s*([0-9]{1,2}\s*\S+\s*[0-9]{4})", text)
    if m:
        out["as_of_text"] = m.group(1).strip()

    m = re.search(r"กลุ่ม\s*([A-Za-z][A-Za-z0-9 /&+.-]{2,40})", text)
    if m:
        out["peer_group"] = m.group(1).strip()

    return out


def render(pid: str, fund: dict, pages: list[str], meta: dict,
           signals: dict, sections: dict) -> str:
    abbr = fund.get("abbr") or pid
    body_chars = sum(len(p) for p in pages)
    thai_ok = bool(THAI.search("".join(pages[:2])))

    out = ["---",
           f"title: Factsheet - {abbr}",
           f"proj_id: {pid}",
           f'abbr: "{abbr}"',
           f'fund: "[[{safe_name(abbr)}]]"',
           f"pages: {len(pages)}",
           f"chars: {body_chars}",
           f"thai_text_ok: {str(thai_ok).lower()}",
           f"pdf_bytes: {meta.get('bytes', 0)}"]
    for k, v in signals.items():
        out.append(f'{k}: "{v}"')
    if sections:
        out.append(f"sections: [{', '.join(sorted(sections))}]")
        if sections.get("managers"):
            names = ", ".join(f'"{n}"' for n in sections["managers"])
            out.append(f"fund_managers: [{names}]")
    out += ["tags: [factsheet, sec-data]", "---", ""]

    out.append(f"# 📄 Factsheet — {abbr}")
    out.append("")
    out.append(f"**กองทุน:** [[{safe_name(abbr)}|{fund.get('name_th') or abbr}]]  ")
    out.append(f"**บลจ.:** [[{safe_name(fund.get('amc_th') or 'ไม่ระบุ')}]]  ")
    out.append(f"**proj_id:** `{pid}`")
    out.append("")
    if meta.get("url"):
        out.append(f"**ต้นฉบับ:** [{meta['url']}]({meta['url']})  ")
    out.append(f"**ไฟล์ในเครื่อง:** `data/factsheets/{pid}.pdf`")
    out.append("")

    if signals:
        out.append("## ค่าที่แกะได้จาก PDF")
        out.append("")
        label = {"as_of_text": "ข้อมูล ณ วันที่", "peer_group": "กลุ่มกองทุน (AIMC)"}
        out.append("| รายการ | ค่า |")
        out.append("|---|---|")
        for k, v in signals.items():
            out.append(f"| {label.get(k, k)} | {v} |")
        out.append("")
        out.append("> [!NOTE]")
        out.append("> ค่าเหล่านี้แกะจากข้อความ PDF — ตัวเลขทางการเงินทั้งหมด")
        out.append(f"> (ค่าธรรมเนียม ความเสี่ยง NAV ผลตอบแทน) ให้ดูที่ [[{safe_name(abbr)}]]")
        out.append("> ซึ่งมาจาก API โดยตรง")
        out.append("")

    if not thai_ok:
        out.append("> [!CAUTION]")
        out.append("> แกะข้อความภาษาไทยไม่ได้ — PDF นี้อาจเป็นภาพสแกน (ต้องใช้ OCR)")
        out.append("")

    # ---- structured sections recovered from the PDF layout ---------------
    if sections:
        out.append("## ข้อมูลที่แกะเป็นตารางได้")
        out.append("")
        out.append("ส่วนนี้มีเฉพาะใน factsheet — API ไม่ได้ให้ข้อมูลกลุ่มอุตสาหกรรม "
                   "ประเทศ อันดับความน่าเชื่อถือ และรายชื่อผู้จัดการกองทุน")
        out.append("")

        if sections.get("strategy"):
            out.append("### นโยบายและกลยุทธ์การลงทุน (ฉบับย่อจาก factsheet)")
            out.append("")
            out.append(sections["strategy"])
            out.append("")

        if sections.get("benchmark"):
            out.append(f"**ดัชนีชี้วัด:** {sections['benchmark']}")
            out.append("")

        if sections.get("managers"):
            out.append("### ผู้จัดการกองทุน")
            out.append("")
            for name in sections["managers"]:
                out.append(f"- {name}")
            out.append("")

        for key, (heading, col) in SECTION_TITLE.items():
            for suffix, note in (("", ""), ("_master", " — **ของกองทุนหลัก**")):
                rows = sections.get(key + suffix)
                if not rows:
                    continue
                out.append(f"### {heading}{note}")
                out.append("")
                out.append(f"| {col} | % NAV |")
                out.append("|---|---|")
                for r in rows:
                    name = str(r["name"]).replace("|", "\\|")
                    out.append(f"| {name} | {r['percent']:,.2f} |")
                out.append("")

        if sections.get("statistics"):
            out.append("### ข้อมูลเชิงสถิติ (ตามที่พิมพ์ใน factsheet)")
            out.append("")
            out.append("| รายการ | ค่า |")
            out.append("|---|---|")
            for r in sections["statistics"]:
                out.append(f"| {r['name']} | {r['value']} |")
            out.append("")

        out.append("> [!NOTE]")
        out.append("> ตารางข้างต้นแกะจาก layout ของ PDF จึงอาจมีแถวคลาดเคลื่อนได้บ้าง")
        out.append(f"> ตัวเลขที่ API ให้มา (ซึ่งแม่นกว่า) อยู่ที่ [[{safe_name(abbr)}]]")
        out.append("")

    out.append("## เนื้อหาต้นฉบับ")
    out.append("")
    for i, page in enumerate(pages, 1):
        if not page.strip():
            continue
        out.append(f"### หน้า {i}")
        out.append("")
        out.append("```text")
        out.append(page[:MAX_CHARS_PER_PAGE])
        if len(page) > MAX_CHARS_PER_PAGE:
            out.append("... (ตัดทอน)")
        out.append("```")
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"← กลับไปที่ [[{safe_name(abbr)}]] · [[../Indexes/00-home|Home]]")
    out.append("")
    return "\n".join(out)


def main() -> None:
    argv = sys.argv[1:]
    force = "--force" in argv
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None

    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    manifest_path = PDF_DIR / "_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) \
        if manifest_path.exists() else {}

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if limit:
        pdfs = pdfs[:limit]
    LOG.info("parsing %d factsheet PDFs", len(pdfs))

    results = {"ok": 0, "skipped": 0, "no_text": 0, "error": 0, "orphan": 0}
    index_rows = []
    # reuse anything from a previous run so --limit does not shrink the file
    all_sections = json.loads(SECTIONS_JSON.read_text(encoding="utf-8"))         if SECTIONS_JSON.exists() else {}

    for pdf in pdfs:
        pid = pdf.stem
        fund = funds.get(pid)
        if not fund:
            results["orphan"] += 1
            continue

        abbr = fund.get("abbr") or pid
        dest = OUT / f"Factsheet - {safe_name(abbr)}.md"
        if dest.exists() and not force:
            results["skipped"] += 1
            index_rows.append((abbr, pid, "cached"))
            continue

        try:
            with fitz.open(pdf) as doc:
                pages = [tidy(p.get_text("text")) for p in doc]
        except Exception as e:
            LOG.warning("cannot open %s: %s", pdf.name, e)
            results["error"] += 1
            continue

        text = "\n".join(pages)
        if len(text.strip()) < 200:
            results["no_text"] += 1

        signals = scrape_signals(text)
        try:
            sections = extract_sections(text)
        except Exception:
            LOG.exception("section extraction failed for %s", pid)
            sections = {}
        if sections:
            all_sections[pid] = sections
        dest.write_text(
            render(pid, fund, pages, manifest.get(pid, {}), signals, sections),
            encoding="utf-8")
        results["ok"] += 1
        index_rows.append((abbr, pid, f"{len(pages)}p"))

    # index note for the Factsheets folder
    idx = ["---", "title: Factsheets Index", "tags: [factsheet, index]", "---", "",
           "# 📄 Factsheets ที่แกะเป็นข้อความแล้ว", "",
           f"ทั้งหมด **{len(index_rows)}** ฉบับ · "
           "PDF ต้นฉบับอยู่ที่ `data/factsheets/`", "",
           "[[../Indexes/00-home|← Home]]", "",
           "| Factsheet | กองทุน | proj_id | หน้า |", "|---|---|---|---|"]
    for abbr, pid, pages_txt in sorted(index_rows):
        idx.append(f"| [[Factsheet - {safe_name(abbr)}|{abbr}]] "
                   f"| [[{safe_name(abbr)}|โน้ตกองทุน]] | `{pid}` | {pages_txt} |")
    (OUT / "00-factsheets-index.md").write_text("\n".join(idx) + "\n",
                                                encoding="utf-8")

    SECTIONS_JSON.write_text(
        json.dumps(all_sections, ensure_ascii=False, indent=1), encoding="utf-8")
    LOG.info("parse results: %s", json.dumps(results))
    LOG.info("structured sections for %d funds -> %s",
             len(all_sections), SECTIONS_JSON.name)


if __name__ == "__main__":
    main()
