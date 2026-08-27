"""
fees.py - Read fees the way an investor actually pays them: per share class.

Why this module exists
----------------------
A Thai fund is one project with up to a dozen share classes, and they do not
charge the same fee. PRINCIPAL GOPP has seven classes whose Total Fee and
Expense runs from **0.01% to 2.19%**; SCBLT3FUND runs 0.10% to 2.24%.
259 funds report more than one figure and 85 of those differ by over one
percentage point.

The first version of the vault collapsed that with `min()`, which put those
funds at the top of a cheapest-first ranking on the strength of a class no
individual can buy - the institutional or group class. That is the same
failure as ISS-009: a number that looks reasonable and silently ranks funds
wrongly.

So every fee figure here is tagged with the class it belongs to, and each
class is tagged with who is allowed to hold it. Rankings use `retail_ter()`,
which only considers classes an individual can actually buy.

    from fees import fee_rows, class_index, retail_ter, AUDIENCE_LABEL
"""
from __future__ import annotations

import re
from collections import defaultdict

# The fee line that matters for comparison. AMCs spell the label consistently
# because it comes from the standard factsheet template.
TOTAL_FEE = "Total Fee and Expense"

FEE_KINDS = {
    "total": TOTAL_FEE,
    "management": "Management Fee",
    "front": "Front-end Fee",
    "back": "Back-end Fee",
    "switch_in": "SWITCHING IN",
    "switch_out": "SWITCHING OUT",
}
FEE_LABEL = {
    "total": "ค่าธรรมเนียมรวมทั้งหมด",
    "management": "ค่าธรรมเนียมการจัดการ",
    "front": "ค่าธรรมเนียมขาย (Front-end)",
    "back": "ค่าธรรมเนียมรับซื้อคืน (Back-end)",
    "switch_in": "สับเปลี่ยนเข้า",
    "switch_out": "สับเปลี่ยนออก",
}

# Who a share class is sold to, read from the Thai `detail` on the class.
# The distinction matters because a fee an individual cannot access must not
# be used to rank a fund as cheap.
AUDIENCE_RULES: list[tuple[str, str]] = [
    ("institution", "ผู้ลงทุนสถาบัน"),
    ("institution", "ผู้ลงทุนกลุ่ม"),
    ("institution", "ผู้ลงทุนพิเศษ"),
    ("institution", "เงินลงทุนเดิม"),
    ("insurance", "ควบประกัน"),
    ("tax", "เพื่อการออม"),
    ("tax", "เพื่อการเลี้ยงชีพ"),
    ("tax", "หุ้นระยะยาว"),
    ("retail", "สะสมมูลค่า"),
    ("retail", "จ่ายเงินปันผล"),
    ("retail", "รับซื้อคืน"),
    ("retail", "ขายคืน"),
    ("retail", "ช่องทางอิเล็กทรอนิกส์"),
    ("retail", "ผู้ลงทุนทั่วไป"),
    ("retail", "ทั่วไป"),
]
AUDIENCE_LABEL = {
    "retail": "รายย่อยทั่วไป",
    "tax": "รายย่อย (ลดหย่อนภาษี)",
    "institution": "สถาบัน / กลุ่มบุคคล",
    "insurance": "ควบกรมธรรม์ (Unit Linked)",
    "unknown": "ไม่ระบุ",
}
AUDIENCE_ICON = {
    "retail": "🟢", "tax": "🟢", "institution": "🔒",
    "insurance": "🛡️", "unknown": "⚪",
}

# classes an individual can put their own money into
BUYABLE = {"retail", "tax", "unknown"}


def classify_audience(detail: str | None, name: str | None = None) -> str:
    """Who may hold this share class.

    `unknown` is deliberately treated as buyable further down: several AMCs
    label retail classes with a bare letter ("ชนิด F", "ชนิด M") and excluding
    those would hide the only class some funds have.
    """
    text = f"{detail or ''} {name or ''}"
    for audience, needle in AUDIENCE_RULES:
        if needle in text:
            return audience
    return "unknown"


def _positive(value) -> float | None:
    """Zero is never a fee here.

    AMCs file 0.00 both for "not charged this period" and for "not reported",
    and the feed gives no way to tell them apart. Treating either as free would
    rank the fund cheapest.
    """
    return float(value) if isinstance(value, (int, float)) and value > 0 else None


def _pair(row: dict) -> dict:
    """The two numbers a fee row carries, kept apart.

    `actual` is what was charged over the reported period; `rate` is the
    ceiling the prospectus permits. Collapsing them with a fallback - which an
    earlier version of this module did - silently compares one fund's charged
    rate against another's ceiling, and made 308 classes look like they
    reported a total below their own management fee when in fact the total was
    an `actual` and the management fee was a `rate`.
    """
    return {"actual": _positive(row.get("actual")),
            "rate": _positive(row.get("rate"))}


def _kind_of(fee_type: str) -> str | None:
    for kind, needle in FEE_KINDS.items():
        if needle in fee_type:
            return kind
    return None


def class_index(fund: dict) -> dict[str, dict]:
    """class name -> {detail, audience, isin, tax_incentive}."""
    out: dict[str, dict] = {}
    for cl in fund.get("classes") or []:
        name = (cl.get("name") or "").strip()
        if not name:
            continue
        out[name] = {
            "name": name,
            "detail": (cl.get("detail") or "").strip(),
            "audience": classify_audience(cl.get("detail"), name),
            "isin": cl.get("isin"),
            "tax_incentive": cl.get("tax_incentive"),
        }
    return out


def fee_rows(fund: dict) -> list[dict]:
    """One row per share class, with each fee kind resolved to a number.

    Where a class reports the same fee kind more than once - AMCs file one row
    per effective period - the highest figure wins. Understating what someone
    pays is the more expensive mistake.
    """
    classes = class_index(fund)
    by_class: dict[str, dict] = defaultdict(dict)

    for row in fund.get("factsheet_fees") or []:
        kind = _kind_of(str(row.get("type") or ""))
        if kind is None:
            continue
        pair = _pair(row)
        if pair["actual"] is None and pair["rate"] is None:
            continue
        name = (row.get("class") or "main").strip() or "main"
        current = by_class[name].setdefault(kind, {"actual": None, "rate": None})
        # AMCs file one row per effective period; keep the highest of each,
        # because understating what someone pays is the costlier mistake
        for key in ("actual", "rate"):
            if pair[key] is not None:
                current[key] = (pair[key] if current[key] is None
                                else max(current[key], pair[key]))

    out = []
    for name, fees in by_class.items():
        meta = classes.get(name) or {
            "name": name, "detail": "", "isin": None,
            "audience": classify_audience(None, name),
        }
        if name == "main" and len(by_class) == 1:
            # a single unnamed row means the project has one class; inherit the
            # audience from the only declared class rather than guessing
            only = next(iter(classes.values()), None)
            if only:
                meta = only | {"name": only["name"]}
        out.append(meta | {"fees": fees})

    out.sort(key=lambda r: (charged(r, "total") is None,
                            charged(r, "total") or 0, r["name"]))
    return out


def charged(row: dict, kind: str) -> float | None:
    """What this class was actually charged for `kind`, or None."""
    return (row["fees"].get(kind) or {}).get("actual")


def ceiling(row: dict, kind: str) -> float | None:
    """The prospectus ceiling for `kind`, or None."""
    return (row["fees"].get(kind) or {}).get("rate")


# Total Fee and Expense cannot be lower than the Management Fee inside it.
# 308 classes across 216 funds report exactly that, almost certainly because a
# class launched mid-period files an actual covering only the months it
# existed. The figure is not comparable to a full-year one, so it is excluded
# from rankings and flagged in the note rather than quietly published.
SUSPECT_TOLERANCE = 0.001


def is_suspect(row: dict) -> bool:
    """True when this class's charged total is below its charged management fee.

    Both sides must be `actual`. Comparing a charged total against a ceiling
    is meaningless - the ceiling is routinely the larger number by design.
    """
    total = charged(row, "total")
    management = charged(row, "management")
    if total is None or management is None:
        return False
    return total < management - SUSPECT_TOLERANCE


def is_incomplete(row: dict) -> bool:
    """True when the class filed a charged total but no charged management fee.

    262 classes do this, and their total is well under their own management
    ceiling - K-FIXED-Z files 0.06% against a 0.54% management ceiling. Either
    the fee was genuinely waived or the class reported a part-year figure, and
    the feed cannot tell us which. The number is kept and ranked, because
    dropping 215 funds from the fee table would hide more than it fixes, but
    every place it appears says that the report is incomplete.
    """
    total = charged(row, "total")
    if total is None or charged(row, "management") is not None:
        return False
    cap = ceiling(row, "management")
    return cap is not None and total < cap


def usable_rows(fund: dict) -> list[dict]:
    """Fee rows fit to compare: a charged total, not internally impossible."""
    return [r for r in fee_rows(fund)
            if charged(r, "total") and not is_suspect(r)]


def retail_ter(fund: dict) -> float | None:
    """Cheapest total expense among classes an individual can actually buy."""
    values = [charged(r, "total") for r in usable_rows(fund)
              if r["audience"] in BUYABLE]
    return min(values) if values else None


def any_ter(fund: dict) -> float | None:
    """Cheapest total expense across every class, buyable or not."""
    values = [charged(r, "total") for r in usable_rows(fund)]
    return min(values) if values else None


def ter_spread(fund: dict) -> tuple[float, float] | None:
    """(cheapest, dearest) total expense across all classes, or None."""
    values = sorted(charged(r, "total") for r in usable_rows(fund))
    return (values[0], values[-1]) if values else None


def restricted_cheapest(fund: dict) -> bool:
    """True when the fund's cheapest class is one an individual cannot buy.

    These are exactly the funds a naive cheapest-first ranking gets wrong.
    """
    rows = usable_rows(fund)
    if len(rows) < 2:
        return False
    cheapest = min(rows, key=lambda r: charged(r, "total"))
    return cheapest["audience"] not in BUYABLE


def fee_of(fund: dict, kind: str, audience_only: bool = True) -> float | None:
    """Lowest value of one fee kind across the classes an individual can buy."""
    values = [charged(r, kind) for r in fee_rows(fund)
              if charged(r, kind) is not None
              and (not audience_only or r["audience"] in BUYABLE)]
    return min(values) if values else None
