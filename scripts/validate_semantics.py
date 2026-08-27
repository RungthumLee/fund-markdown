"""
validate_semantics.py - Check that the data *makes sense*, not just that the
notes link up.

`validate_vault.py` guards structural integrity: every [[link]] resolves, no
note is orphaned, no filename clashes, no render block silently stopped. All of
that can pass while the numbers underneath are wrong. Two live examples this
module was written to catch:

  * A SET50 fund whose benchmark is filed as "MSCI Emerging Markets Index".
    Structurally fine - it is just a benchmark string. Semantically it means the
    performance table compares the fund against an index it does not track. This
    is a **source** error in the SEC feed; we cannot fix it, only warn.

  * A Thai holding (ISIN TH0128B10Z09, Minor International) whose resolved entity
    was named "Mapletree Industrial Trust" - a Singapore REIT that happens to
    share the ticker MINT. 377 fund notes linked the wrong company. This is a
    **pipeline** error in entity naming, and it is ours to fix.

Both are the family the issue log keeps returning to (ISS-009, ISS-014,
ISS-020): a value that looks reasonable and is therefore never questioned. The
only defence is to state, in code, what "reasonable" means for each field and
count the rows that violate it.

Severity:
    HIGH    a pipeline error we introduced and can fix. Gates the run when the
            count climbs past S1_BUDGET (a regression guard, same idea as the
            SECTION_FLOORS in validate_vault).
    MEDIUM  a source error we can only surface to the reader.
    LOW     worth a look; usually a source gap, never blocks.

    python scripts/validate_semantics.py
    python scripts/validate_semantics.py --strict   # any HIGH finding exits 1
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("validate_semantics")
PROC = ROOT / "data" / "processed"
REPORT = ROOT / "docs" / "project" / "semantic-report.md"

# How many HIGH-severity S1 findings are known and accepted right now. The run
# fails when the real count exceeds this, so any *new* naming collision is
# caught. The Mapletree/Minor fix in normalize_entities brought S1 to zero, so
# the budget is zero: the next misnamed Thai security trips the gate. (The five
# rows that filed a real Mapletree holding under Minor's ISIN moved to S8, a
# source keying error, and no longer count here.)
S1_BUDGET = 0

# ---------------------------------------------------------------- text utils

# words that carry no identity - dropping them stops "PTT PUBLIC COMPANY
# LIMITED" and "PTT PCL" from looking like different companies
_STOP = set(
    "the of and for public company limited co ltd inc incorporated corporation "
    "corp plc pcl fund trust holding holdings group ordinary shares class acc "
    "จำกัด มหาชน บริษัท กองทุน บมจ หน่วยลงทุน".split()
)


def toks(s: str | None) -> set[str]:
    """Identity tokens of a name: letters/digits, stopwords and 1-char noise out.

    Short tokens are kept down to length 2 so tickers like "AP" or "BH" still
    register; only single characters (the S/P/V/I of "S P V I") are dropped,
    since those split a real name into meaningless letters.
    """
    s = re.sub(r"[^a-z0-9฀-๿ ]", " ", (s or "").lower())
    return {t for t in s.split() if len(t) >= 2 and t not in _STOP}


# An issuer that is an asset manager means the holding is units of another fund
# (a fund-of-funds leg), so the entity name legitimately differs from the
# issuer. Those are not naming bugs and must not be flagged.
_IS_AMC = re.compile(
    r"asset management|จัดการกองทุน|หลักทรัพย์จัดการ|บลจ|securities|sicav|"
    r"investment management|fund management",
    re.I,
)

# Benchmark geography. A name is "Thai" only if it names a real Thai market
# index; "foreign" if it names a non-Thai market or asset. Thailand is matched
# before foreign so "MSCI Thailand" reads as domestic, not foreign.
#
# A deposit/cash-rate benchmark ("อัตราดอกเบี้ยเงินฝาก...", "USD 3M deposit") is
# geography-neutral: Thai AMCs use it as a placeholder for money-market and even
# foreign funds, so it must count as neither side or it produces false mismatches
# (a USD fund benchmarked to a USD deposit rate is correct, not wrong).
_BM_CASH = re.compile(r"เงินฝาก|ดอกเบี้ย|deposit|LIBOR|SOFR|ประจำ", re.I)
_BM_THAI = re.compile(
    r"\bSET\b|\bSET50\b|\bSET100\b|\bsSET\b|ThaiBMA|\bMAI\b|Thailand|\bThai\b|"
    r"ตลาดหลักทรัพย์|หุ้นไทย|พันธบัตร.*ไทย|ไทยบีเอ็มเอ",
    re.I,
)
_BM_FOREIGN = re.compile(
    r"MSCI|S&P|S ?& ?P|NASDAQ|NIKKEI|\bDOW\b|FTSE|Barclays|Hang Seng|STOXX|"
    r"Russell|Euro|Emerging|Developed|\bWorld\b|Global|\bUS\b|U\.S\.|China|"
    r"Japan|India|Vietnam|Korea|Asia|Europe|Gold|Bloomberg|ICE BofA|MVIS",
    re.I,
)

# invest_country_flag (from gen_vault.COUNTRY_FLAG):
#   1 = เน้นลงทุนต่างประเทศ      2 = ต่างประเทศบางส่วน
#   3 = ไม่มีความเสี่ยงต่างประเทศ  4 = ทั้งในและต่างประเทศ
# So 3 is domestic-only, 1 and 2 are foreign-focused, and 4 is genuinely mixed
# and never flagged - its benchmark can legitimately be Thai or foreign.
DOMESTIC_FLAG = "3"
FOREIGN_FLAGS = {"1", "2"}


def load_funds() -> dict:
    return json.loads((PROC / "funds.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the checks
#
# Each check appends findings to `out`, a flat list of dicts:
#   {check, severity, fund, name, detail}
# so the report renderer stays independent of any single check's internals.


def check_entity_issuer(funds: dict, out: list[dict]) -> None:
    """S1 (HIGH) + S8 (LOW) - a Thai ISIN whose name and its issuers disagree.

    For every Thai ISIN, gather the resolved entity name and count the issuers
    filed against it (asset managers excluded - those are fund-of-funds legs).
    Two different faults hide here and must be told apart:

    S1 (HIGH, our bug): the entity NAME shares no token with the *dominant*
        issuer. The security itself is misnamed - the Mapletree/Minor archetype,
        where a cross-market ticker fold scored a foreign name onto a Thai stock.
        This is fixable in normalize_entities and gates the run.

    S8 (LOW, source): the name matches the dominant issuer, but a minority of
        rows carry a *different* real issuer. That is one ISIN filed for two
        securities by different AMCs - a source keying error we can only surface.
        After the Minor fix, the five KKP/K-PROP rows that filed a real Mapletree
        holding under Minor's ISIN land here, not in S1.
    """
    # isin -> {"name": resolved entity name, "issuers": Counter, "funds": {issuer: set}}
    by_isin: dict[str, dict] = {}
    for pid, f in funds.items():
        abbr = f.get("abbr") or pid
        for x in (f.get("portfolio") or {}).get("items") or []:
            ent = x.get("entity") or ""
            en = x.get("entity_name") or ""
            iss = (x.get("issuer") or "").strip()
            isin = x.get("isin") or ""
            if not en or len(iss) < 8:
                continue
            if not (isin.startswith("TH") or ent.startswith("isin:TH")):
                continue
            if _IS_AMC.search(iss):
                continue
            # A row filed without an ISIN still resolves to one via its entity
            # id ("isin:TH…"); fold both spellings to the bare ISIN so the 377
            # rows that carry the ISIN and the few that only carry the entity
            # land in one group instead of two.
            key = (isin or ent).replace("isin:", "")
            rec = by_isin.setdefault(key, {"name": en, "issuers": Counter(),
                                           "funds": defaultdict(set)})
            rec["issuers"][iss] += 1
            rec["funds"][iss].add(abbr)

    for key, rec in by_isin.items():
        en = rec["name"]
        if not rec["issuers"]:
            continue
        dominant = rec["issuers"].most_common(1)[0][0]
        te = toks(en)
        if te and toks(dominant) and not (te & toks(dominant)):
            # the name itself is wrong - flag against the dominant issuer
            abbrs = rec["funds"][dominant]
            out.append({
                "check": "S1", "severity": "HIGH", "fund": "", "name": en,
                "detail": f"ควรเป็น **{dominant}** — ปรากฏใน {len(abbrs)} กอง "
                          f"(เช่น {', '.join(sorted(abbrs)[:5])})",
            })
            continue
        # name is right; report any minority issuer that disagrees with it
        for iss, _ in rec["issuers"].items():
            if iss == dominant or not toks(iss) or (te & toks(iss)):
                continue
            abbrs = rec["funds"][iss]
            out.append({
                "check": "S8", "severity": "LOW", "fund": "", "name": en,
                "detail": f"ISIN `{key}` ({en}) ถูกยื่นเป็น **{iss}** ใน "
                          f"{len(abbrs)} กอง (เช่น {', '.join(sorted(abbrs)[:5])}) "
                          "— น่าจะกรอก ISIN ผิดที่ต้นทาง",
            })


def check_benchmark_geography(funds: dict, out: list[dict]) -> None:
    """S2 (MEDIUM) - benchmark geography contradicts the fund's own geography.

    A domestic fund whose every benchmark is a foreign index, or a foreign fund
    benchmarked only against Thai indices. Either way the performance table
    measures the fund against something it does not track. The mismatch is in
    the SEC feed, so this only warns.
    """
    for pid, f in funds.items():
        bms = [b.get("name") or "" for b in (f.get("benchmarks") or [])]
        bms = [b for b in bms if b.strip()]
        if not bms:
            continue
        flag = f.get("invest_country_flag")
        domestic = flag == DOMESTIC_FLAG

        thai = [b for b in bms if _BM_THAI.search(b)]
        foreign = [b for b in bms if _BM_FOREIGN.search(b) and not _BM_THAI.search(b)]

        problem = None
        if domestic and foreign and not thai:
            problem = f"กองในประเทศ แต่ดัชนีชี้วัดเป็นต่างประเทศล้วน: {foreign[0]}"
        elif flag in FOREIGN_FLAGS and thai and not foreign:
            problem = f"กองต่างประเทศ แต่ดัชนีชี้วัดเป็นของไทยล้วน: {thai[0]}"
        if problem:
            out.append({
                "check": "S2", "severity": "MEDIUM",
                "fund": f.get("abbr") or pid, "name": f.get("name_th") or "",
                "detail": problem,
            })


def check_asset_alloc_sum(funds: dict, out: list[dict]) -> None:
    """S5 (LOW) - factsheet asset allocation that does not add up to ~100%.

    A complete allocation sums to roughly 100. A total far off usually means the
    factsheet listed only some sleeves, or a parse dropped a row - a source/parse
    gap, so this only warns.
    """
    for pid, f in funds.items():
        aa = f.get("asset_allocation") or []
        if len(aa) < 2:
            continue
        s = sum((x.get("ratio") or 0) for x in aa)
        if s and (s < 80 or s > 120):
            out.append({
                "check": "S5", "severity": "LOW",
                "fund": f.get("abbr") or pid, "name": f.get("name_th") or "",
                "detail": f"ผลรวมการจัดสรรสินทรัพย์ = {s:.1f}% (ควรใกล้ 100)",
            })


def check_nav_stale(funds: dict, out: list[dict]) -> None:
    """S6 (LOW) - a fund whose latest NAV lags the corpus by over a month.

    Everything is a snapshot, so all NAVs share roughly one date. A fund far
    behind that date has usually stopped reporting - dormant, suspended, or on
    its way out - which is worth surfacing.
    """
    latest: dict[str, str] = {}
    for pid, f in funds.items():
        ds = [r.get("date") for r in (f.get("nav") or []) if r.get("date")]
        if ds:
            latest[pid] = max(ds)
    if not latest:
        return
    corpus_max = max(latest.values())
    cmax = date.fromisoformat(corpus_max)
    for pid, d in latest.items():
        gap = (cmax - date.fromisoformat(d)).days
        if gap > 30:
            f = funds[pid]
            out.append({
                "check": "S6", "severity": "LOW",
                "fund": f.get("abbr") or pid, "name": f.get("name_th") or "",
                "detail": f"NAV ล่าสุด {d} ช้ากว่าคลัง ({corpus_max}) {gap} วัน",
            })


def check_holding_over_nav(funds: dict, out: list[dict]) -> None:
    """S7 (LOW) - a single holding filed at over 150% of NAV.

    A feeder legitimately reads a touch over 100% on a gross basis (ISS-007,
    ISS-027), so the bar is set high. Anything past 150% is almost certainly a
    filing or unit error rather than a real position; this is a tripwire for
    future data, not a claim about today's.
    """
    for pid, f in funds.items():
        for x in (f.get("portfolio") or {}).get("items") or []:
            p = x.get("percent_nav")
            if isinstance(p, (int, float)) and p > 150:
                out.append({
                    "check": "S7", "severity": "LOW",
                    "fund": f.get("abbr") or pid,
                    "name": x.get("entity_name") or x.get("name") or "",
                    "detail": f"หลักทรัพย์เดียวถือ {p:.1f}% ของ NAV",
                })


# (id, label, severity, fn). fn is None for a check whose findings are produced
# as a by-product of another check (S8 comes out of check_entity_issuer); it is
# listed here only so the renderer knows its label and severity.
CHECKS = [
    ("S1", "หลักทรัพย์ไทยที่ตั้งชื่อตัวตนผิดบริษัท", "HIGH", check_entity_issuer),
    ("S8", "ISIN ไทยถูกใช้ปนหลายหลักทรัพย์ (ต้นทางกรอกผิด)", "LOW", None),
    ("S2", "ดัชนีชี้วัดขัดกับพื้นที่ลงทุนของกอง", "MEDIUM", check_benchmark_geography),
    ("S5", "การจัดสรรสินทรัพย์รวมไม่ถึง/เกิน 100%", "LOW", check_asset_alloc_sum),
    ("S6", "NAV ค้างเก่ากว่าคลังเกิน 30 วัน", "LOW", check_nav_stale),
    ("S7", "หลักทรัพย์เดียวถือเกิน 150% ของ NAV", "LOW", check_holding_over_nav),
]

SEV_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}


def render(findings: list[dict]) -> str:
    by_check: defaultdict[str, list[dict]] = defaultdict(list)
    for fn in findings:
        by_check[fn["check"]].append(fn)

    o: list[str] = [
        "---", "title: Semantic Report", "tags: [project, qa, semantics]",
        f"updated: {date.today()}", "---", "",
        "# 🧭 Semantic Report", "",
        "สร้างอัตโนมัติโดย `scripts/validate_semantics.py` — ตรวจว่าข้อมูล "
        "**สมเหตุสมผล** ไม่ใช่แค่ลิงก์ครบ", "",
        "[[validation-report|Validation Report]] · [[data-quality|Data Quality]] "
        "· [[issues|Issues]]", "",
        "> [!INFO] ระดับความรุนแรง", ">",
        "> - 🔴 **HIGH** — บั๊กใน pipeline ที่เราแก้ได้ (เกินโควตาแล้ว run จะ fail)",
        "> - 🟡 **MEDIUM** — ข้อมูลผิดที่ต้นทาง SEC — เตือนผู้อ่าน แก้ที่เราไม่ได้",
        "> - 🟢 **LOW** — ควรดู มักเป็นช่องว่างของข้อมูลต้นทาง",
        "",
        "## สรุป", "", "| รหัส | สิ่งที่ตรวจ | ระดับ | พบ |", "|---|---|---|---|",
    ]
    for cid, label, sev, _ in CHECKS:
        n = len(by_check.get(cid, []))
        mark = "✅" if n == 0 else str(n)
        o.append(f"| {cid} | {label} | {SEV_ICON[sev]} {sev} | {mark} |")
    o.append("")

    for cid, label, sev, _ in CHECKS:
        items = by_check.get(cid, [])
        o += [f"## {SEV_ICON[sev]} {cid} · {label}", ""]
        if not items:
            o += ["✅ ไม่พบ", ""]
            continue
        if cid == "S1":
            o += ["> [!WARNING] ตัวตนของหลักทรัพย์ถูกตั้งชื่อผิด — โน้ตกองทุน"
                  "ที่ถือหลักทรัพย์นี้ลิงก์ไปบริษัทผิด แก้ที่ `normalize_entities.py`",
                  "", "| ตัวตน (ชื่อที่ผิด) | อาการ |", "|---|---|"]
            for fn in items:
                o.append(f"| `{fn['name']}` | {fn['detail']} |")
        else:
            head = "หลักทรัพย์" if cid == "S8" else "กองทุน"
            o += [f"| {head} | รายละเอียด |", "|---|---|"]
            for fn in items[:200]:
                if fn["fund"]:
                    who = f"`{fn['fund']}`" + (f" — {fn['name']}" if fn.get("name") else "")
                else:
                    who = fn.get("name") or ""
                o.append(f"| {who} | {fn['detail']} |")
            if len(items) > 200:
                o.append(f"| _...และอีก {len(items) - 200} รายการ_ | |")
        o.append("")

    o += ["---", "",
          f"S1 budget = {S1_BUDGET} · พบจริง {sum(1 for f in findings if f['check']=='S1')}"
          " — ถ้าพบเกินโควตา แปลว่ามี collision ใหม่ที่ยังไม่ได้ตรวจ", ""]
    return "\n".join(o)


def main() -> None:
    strict = "--strict" in sys.argv
    funds = load_funds()
    LOG.info("checking %d funds", len(funds))

    findings: list[dict] = []
    for _, _, _, fn in CHECKS:
        if fn is not None:
            fn(funds, findings)

    by_sev = Counter(f["severity"] for f in findings)
    s1_total = sum(1 for f in findings if f["check"] == "S1")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render(findings), encoding="utf-8")

    LOG.info("findings: %s", json.dumps({
        "high": by_sev.get("HIGH", 0), "medium": by_sev.get("MEDIUM", 0),
        "low": by_sev.get("LOW", 0), "s1_distinct": s1_total,
        "s1_budget": S1_BUDGET,
    }))
    LOG.info("report -> %s", REPORT.relative_to(ROOT))

    over_budget = s1_total > S1_BUDGET
    if over_budget:
        LOG.error("S1 naming collisions = %d, over budget %d - a new entity was "
                  "named after the wrong company", s1_total, S1_BUDGET)
    if over_budget or (strict and by_sev.get("HIGH")):
        sys.exit(1)


if __name__ == "__main__":
    main()
