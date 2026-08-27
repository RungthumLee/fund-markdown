"""
factsheet_sections.py - Pull structured sections out of SEC factsheet PDF text.

The SEC factsheet template is consistent enough to segment by heading: each
section is a heading line followed by alternating label / numeric-value lines.
This recovers several breakdowns the API does not expose at all - sector,
country and credit-rating allocation, plus the fund manager roster.

Headings vary in spacing and wording between AMCs ("ทรัพย์สินที่ลงทุน 5 อันดับแรก"
vs "ทรัพย์สินที่ลงทุนสูงสุด 5 อันดับแรก" vs "ทรัพย์สินที่ลงทุน5 อันดับแรก"), so
matching is done on a whitespace-stripped form against a prefix list.
"""
from __future__ import annotations

import re

# section key -> heading prefixes (whitespace already removed when matching)
SECTIONS: dict[str, list[str]] = {
    "asset_types": ["สัดส่วนประเภททรัพย์สินที่ลงทุน", "สัดส่วนประเภททรัพย์สิน"],
    "top_holdings": ["ทรัพย์สินที่ลงทุน5อันดับแรก", "ทรัพย์สินที่ลงทุนสูงสุด5อันดับแรก",
                     "ทรัพย์สินที่ลงทุน5อันดับ", "การลงทุนสูงสุด5อันดับแรก"],
    "sectors": ["การจัดสรรการลงทุนในกลุ่มอุตสาหกรรม", "การจัดสรรการลงทุนตามกลุ่มอุตสาหกรรม",
                "สัดส่วนการลงทุนในกลุ่มอุตสาหกรรม"],
    "countries": ["การจัดสรรการลงทุนในต่างประเทศ", "การจัดสรรการลงทุนในตางประเทศ",
                  "การจัดสรรการลงทุนตามประเทศ"],
    "credit_ratings": ["การจัดสรรการลงทุนตามอันดับความน่าเชื่อถือ",
                       "การจัดสรรการลงทุนตามอันดับความนาเชื่อถือ",
                       "อันดับความน่าเชื่อถือ"],
    "statistics": ["ข้อมูลเชิงสถิติ"],
    "managers": ["ผู้จัดการกองทุนรวม", "ผู้จัดการกองทุน"],
    "benchmark": ["ดัชนีชี้วัด"],
    "peer_group": ["ประเภทกองทุนรวม/กลุ่มกองทุนรวม", "ประเภทกองทุนรวม/กลุมกองทุนรวม",
                   "กลุ่มกองทุนรวม"],
    "strategy": ["นโยบายและกลยุทธ์การลงทุน"],
}

# lines that are table headers or boilerplate, never data
NOISE = {
    "%nav", "%ของnav", "ประเภททรัพย์สิน", "ทรัพย์สิน", "กลุ่มอุตสาหกรรม", "ประเทศ",
    "อันดับความน่าเชื่อถือ", "สัดส่วน", "ชื่อ", "%", "อัตราส่วน", "ประเภท",
}

VALUE_RE = re.compile(r"^-?[\d,]+(?:\.\d+)?\s*%?$")
STAT_VALUE_RE = re.compile(r"^-?[\d,]+(?:\.\d+)?\s*(?:%|เท่า|ปี|เดือน|วัน)?$|^N/?A$",
                           re.I)
# a heading marking the end of the data area even when it isn't a known section
STOP_PREFIXES = ["คำอธิบาย", "หมายเหตุ", "ผลการดำเนินงาน", "ค่าธรรมเนียม",
                 "@สงวนสิทธิ์", "ผู้ลงทุนสามารถ", "การซื้อหน่วยลงทุน",
                 "การขายคืนหน่วยลงทุน", "หนังสือชี้ชวน", "คำเตือน"]

_SQUASH = re.compile(r"\s+")


def squash(text: str) -> str:
    return _SQUASH.sub("", text)


def _match_section(line: str) -> str | None:
    """Return the section key, suffixed `_master` for feeder-fund look-through.

    Feeder factsheets repeat the same breakdowns twice - once for the Thai fund
    and once "ของกองทุนหลัก" (of the master fund). Keeping them apart matters:
    the two sets describe different portfolios and merging them produces
    weightings that add to well over 100%.
    """
    flat = squash(line)
    if not flat or len(flat) > 80:
        return None
    master = "ของกองทุนหลัก" in flat or flat.endswith("กองทุนหลัก")
    for key, prefixes in SECTIONS.items():
        for prefix in prefixes:
            if flat.startswith(prefix):
                return f"{key}_master" if master else key
    return None


def _is_stop(line: str) -> bool:
    flat = squash(line)
    return any(flat.startswith(p) for p in STOP_PREFIXES)


def split_sections(text: str) -> dict[str, list[str]]:
    """Return {section_key: body lines}. First occurrence of a heading wins."""
    lines = [ln.strip() for ln in text.split("\n")]
    found: dict[str, list[str]] = {}
    current: str | None = None
    body: list[str] = []

    for line in lines:
        key = _match_section(line)
        if key:
            if current and current not in found:
                found[current] = body
            current, body = key, []
            continue
        if current:
            if _is_stop(line) or len(body) > 90:
                if current not in found:
                    found[current] = body
                current, body = None, []
            elif line:
                body.append(line)

    if current and current not in found:
        found[current] = body
    return found


def parse_pairs(body: list[str], limit: int = 30) -> list[dict]:
    """Read `label` / `value` line pairs out of a section body.

    PDF text extraction emits the label column then the number column, so a
    numeric line always belongs to the most recent non-numeric line.
    """
    out: list[dict] = []
    label: str | None = None
    for line in body:
        if squash(line).lower() in NOISE:
            continue
        if VALUE_RE.match(line):
            if label:
                value = line.replace("%", "").replace(",", "").strip()
                try:
                    out.append({"name": label, "percent": float(value)})
                except ValueError:
                    pass
                label = None
        else:
            # keep the last plain-text line as the pending label
            label = line if len(line) <= 120 else None
        if len(out) >= limit:
            break
    return out


def parse_stats(body: list[str], limit: int = 12) -> list[dict]:
    """Statistics block pairs a label with a value that may carry a unit."""
    out: list[dict] = []
    label: str | None = None
    for line in body:
        if STAT_VALUE_RE.match(line):
            if label:
                out.append({"name": label, "value": line})
                label = None
        elif 1 < len(line) <= 60:
            label = line
        if len(out) >= limit:
            break
    return out


# Thai personal-name honorifics that reliably start a fund manager entry
NAME_PREFIX = re.compile(r"^(นาย|นาง|น\.?ส\.?|นางสาว|ดร\.|ม\.ล\.|ม\.ร\.ว\.)\s*\S")


def parse_names(body: list[str], limit: int = 6) -> list[str]:
    """Fund manager roster.

    Requires a Thai honorific. Without it the block bleeds into the fund's own
    name and ticker, which sit immediately below the manager list on many
    factsheets and would otherwise be reported as people.
    """
    out: list[str] = []
    for line in body:
        if len(line) > 80 or VALUE_RE.match(line):
            continue
        name = re.sub(r"\s*\(.*?\)\s*$", "", line).strip(" :,-")
        if not NAME_PREFIX.match(name):
            continue
        # normalise the missing space after an honorific that PDF text drops
        name = re.sub(r"^(นาย|นาง|นางสาว|น\.ส\.|ดร\.)(\S)", r"\1 \2", name)
        if len(name) >= 5 and name not in out:
            out.append(name)
        if len(out) >= limit:
            break
    return out


def first_text(body: list[str], max_lines: int = 4) -> str:
    chunk = [ln for ln in body[:max_lines] if ln and not VALUE_RE.match(ln)]
    return " ".join(chunk).strip(" :•-")


PAIR_LIMITS = {"asset_types": 20, "top_holdings": 12, "sectors": 20,
               "countries": 20, "credit_ratings": 15}


def split_on_restart(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split a holdings list where a second table has been absorbed into it.

    Holdings tables are printed in descending weight. Some feeder factsheets
    word the master-fund heading in a way the heading matcher misses, so both
    tables land in one body; the giveaway is a weight that jumps back up.
    Everything from that jump on is treated as the second (master) table.
    """
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1]["percent"], rows[i]["percent"]
        if cur > prev * 1.5 and cur - prev > 1.0:
            return rows[:i], rows[i:]
    return rows, []

# text that signals the "benchmark" heading actually caught a footnote
BENCH_REJECT = ("ข้อมูลผลการดำเนินงาน", "ผลการดำเนินงานในอดีต", "ข้อมูล ณ วันที่")


def extract(text: str) -> dict:
    """Extract every supported section from one factsheet's full text."""
    sec = split_sections(text)
    out: dict = {}

    for base, limit in PAIR_LIMITS.items():
        for key in (base, f"{base}_master"):
            if key not in sec:
                continue
            rows = parse_pairs(sec[key], limit)
            if not rows:
                continue
            if base == "top_holdings" and not key.endswith("_master"):
                rows, tail = split_on_restart(rows)
                if tail and "top_holdings_master" not in out:
                    out["top_holdings_master"] = tail
            out[key] = rows

    for key in ("statistics", "statistics_master"):
        if key in sec:
            rows = parse_stats(sec[key])
            if rows:
                out[key] = rows

    if "managers" in sec:
        names = parse_names(sec["managers"])
        if names:
            out["managers"] = names

    for key in ("benchmark", "peer_group", "strategy"):
        if key in sec:
            value = first_text(sec[key], 6 if key == "strategy" else 3)
            if key == "benchmark" and value.startswith(BENCH_REJECT):
                continue
            if value:
                out[key] = value[:600 if key == "strategy" else 300]

    if "peer_group" in out:
        out["fund_type"] = out["peer_group"]
        aimc = aimc_group(out["peer_group"])
        if aimc:
            out["peer_group"] = aimc
        else:
            del out["peer_group"]

    # Not every AMC puts the AIMC group under the heading this parser matches;
    # many print it near the fund name instead. Fall back to the whole page.
    if "peer_group" not in out:
        aimc = aimc_group(text[:4000])
        if aimc:
            out["peer_group"] = aimc

    return out


# "ประเภทกองทุนรวม / กลุ่มกองทุนรวม" holds both the SEC fund type and the AIMC
# peer group. Only the AIMC half is a real comparison bucket, so pull it out.
AIMC_RE = re.compile(r"กลุ่ม\s*([A-Za-z][A-Za-z0-9 /&+.'-]{2,45})")


def aimc_group(text: str) -> str | None:
    m = AIMC_RE.search(text)
    if not m:
        return None
    name = m.group(1).strip(" /-.")
    # trailing words from the next sentence sometimes get swept in
    name = re.split(r"\s{2,}", name)[0].strip()
    return name if len(name) >= 3 else None
