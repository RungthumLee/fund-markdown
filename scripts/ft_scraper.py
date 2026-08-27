"""
ft_scraper.py - Read a fund tearsheet from markets.ft.com by ISIN.

FT fills exactly the gaps Yahoo leaves on non-ETF share classes: ongoing
charge (OCF/TER), fund size, domicile, legal structure, the named manager and
their start date, and the Morningstar category. Yahoo covers ETFs well but
returns an expense ratio of 0.0 for most UCITS SICAVs, which reads as "free"
rather than "unknown".

The tearsheet renders as a flat label/value sequence once tags are stripped,
so parsing walks the text lines rather than the DOM.

    python scripts/ft_scraper.py LU0248059726
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://markets.ft.com/data/funds/tearsheet/summary"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# FT label -> our field name. Matched on a whitespace-normalised prefix.
LABELS: dict[str, str] = {
    "fund type": "legal_structure",
    "morningstar category": "category",
    "ima sector": "ima_sector",
    "domicile": "domicile",
    "isin": "isin_confirmed",
    "manager & start date": "manager",
    "fund size": "fund_size",
    "ongoing charge": "ongoing_charge",
    "initial charge": "initial_charge",
    "income treatment": "income_treatment",
    "investment style (stocks)": "style_stocks",
    "investment style (bonds)": "style_bonds",
    "price currency": "price_currency",
    "1 year change": "change_1y",
    "3 year change": "change_3y",
    "5 year change": "change_5y",
    "net expense ratio": "net_expense_ratio",
}

# a value that is really the next label, so the field was actually empty
NOT_A_VALUE = re.compile(
    r"^(select a|income treatment|ima sector|isin|manager|fund size|"
    r"ongoing charge|initial charge|domicile|investment style|"
    r"morningstar|category average|currency converter|data delayed)",
    re.I)

PAGE_NOT_FUND = re.compile(
    r"Equities, ETF and Funds prices|Page not found", re.I)


def _text_lines(raw_html: str) -> list[str]:
    body = re.sub(r"<script.*?</script>", " ", raw_html, flags=re.S)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    body = html.unescape(re.sub(r"<[^>]+>", "\n", body))
    return [ln.strip() for ln in body.split("\n") if ln.strip()]


def fetch(isin: str, currency: str = "", timeout: int = 25,
          session: requests.Session | None = None) -> dict[str, Any] | None:
    """Return the parsed tearsheet, or None when FT has no fund for this ISIN."""
    symbol = f"{isin}:{currency}" if currency else isin
    get = (session or requests).get
    try:
        r = get(BASE, params={"s": symbol},
                headers={"User-Agent": UA, "Accept": "text/html"},
                timeout=timeout)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None

    # FT serves UTF-8 but does not always say so, and requests then guesses
    # latin-1 - which turns "£ Strategic Bond" into "Â£ Strategic Bond".
    r.encoding = "utf-8"
    lines = _text_lines(r.text)
    title = next((ln for ln in lines[:5] if "FT.com" in ln), "")
    if PAGE_NOT_FUND.search(title) or not title:
        return None

    out: dict[str, Any] = {"isin": isin, "source": "ft.com",
                           "url": f"{BASE}?s={symbol}"}
    # "<name>, <ISIN>:<CUR> summary - FT.com"
    name = re.split(r",\s*[A-Z]{2}[A-Z0-9]{9,10}", title)[0].strip()
    out["name"] = name or title.split(" - FT.com")[0].strip()

    for i, line in enumerate(lines):
        key = LABELS.get(re.sub(r"\s+", " ", line).strip().lower())
        if not key or key in out:
            continue
        value = lines[i + 1] if i + 1 < len(lines) else ""
        # FT prints "--" for a field it has no value for; storing that makes
        # the note render "ขนาดกองทุน | --" as though it were data.
        if value.strip(" -–—") in ("", "n/a", "N/A"):
            continue
        if not value or NOT_A_VALUE.match(value):
            continue
        # fund size prints the number and its currency on separate lines
        if key == "fund_size" and i + 2 < len(lines):
            unit = lines[i + 2]
            if re.fullmatch(r"[A-Z]{3}", unit):
                value = f"{value} {unit}"
        if key == "manager" and i + 2 < len(lines):
            start = lines[i + 2]
            if re.match(r"\d{1,2} \w{3} \d{4}", start):
                out["manager_start"] = start
        out[key] = value[:120]

    # a page with a title but no recognisable fields is not a real tearsheet
    if len(out) <= 4:
        return None
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for isin in sys.argv[1:]:
        data = fetch(isin, "USD")
        print(json.dumps(data, ensure_ascii=False, indent=1) if data
              else f"{isin}: not found on FT")
        time.sleep(1)


if __name__ == "__main__":
    main()
