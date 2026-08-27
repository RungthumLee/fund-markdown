"""
fetch_factsheets.py - Download the latest factsheet PDF for every in-scope fund.

Sources the URLs from data/processed/funds.json (field `factsheet_urls`, which
comes from the SEC `factsheet/urls` endpoint). Downloads run in a small thread
pool; every file is written once and skipped on re-run, so the job is resumable.

    python scripts/fetch_factsheets.py            # all funds
    python scripts/fetch_factsheets.py --limit 50 # smoke test
    python scripts/fetch_factsheets.py --retry    # retry previously failed only
"""
from __future__ import annotations

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sec_client import ROOT, get_logger  # noqa: E402

LOG = get_logger("fetch_factsheets")
PROC = ROOT / "data" / "processed"
PDF_DIR = ROOT / "data" / "factsheets"
PDF_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = PDF_DIR / "_manifest.json"

WORKERS = 8
TIMEOUT = 90
MIN_PDF_BYTES = 1024

_lock = threading.Lock()
_manifest: dict[str, dict] = {}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/pdf,*/*",
}


def pick_url(fund: dict) -> tuple[str | None, str | None]:
    """Prefer a direct PDF link; fall back to the AMC landing page URL."""
    urls = fund.get("factsheet_urls") or []
    if not urls:
        return None, None
    # newest as_of first, 'main' class preferred
    urls = sorted(urls, key=lambda u: (str(u.get("as_of") or ""),
                                       u.get("class") == "main"), reverse=True)
    for u in urls:
        if u.get("pdf"):
            return u["pdf"], u.get("as_of")
    for u in urls:
        if u.get("amc_url"):
            return u["amc_url"], u.get("as_of")
    return None, None


def download(pid: str, fund: dict, session: requests.Session) -> dict:
    dest = PDF_DIR / f"{pid}.pdf"
    rec = {"proj_id": pid, "abbr": fund.get("abbr")}

    if dest.exists() and dest.stat().st_size >= MIN_PDF_BYTES:
        rec.update(status="cached", bytes=dest.stat().st_size, file=dest.name)
        return rec

    url, as_of = pick_url(fund)
    rec["url"] = url
    rec["as_of"] = as_of
    if not url:
        rec["status"] = "no-url"
        return rec

    delay = 2.0
    for attempt in range(1, 4):
        try:
            r = session.get(url, headers=HEADERS, timeout=TIMEOUT,
                            allow_redirects=True)
            if r.status_code != 200:
                rec.update(status=f"http-{r.status_code}")
                if r.status_code in (429,) or r.status_code >= 500:
                    time.sleep(delay)
                    delay *= 2
                    continue
                return rec

            body = r.content
            ctype = (r.headers.get("Content-Type") or "").lower()
            if not body.startswith(b"%PDF") and "pdf" not in ctype:
                rec.update(status="not-pdf", content_type=ctype,
                           bytes=len(body))
                return rec
            if len(body) < MIN_PDF_BYTES:
                rec.update(status="too-small", bytes=len(body))
                return rec

            dest.write_bytes(body)
            rec.update(status="ok", bytes=len(body), file=dest.name)
            return rec
        except requests.RequestException as e:
            rec.update(status="error", error=str(e)[:200])
            time.sleep(delay)
            delay *= 2
    return rec


def main() -> None:
    argv = sys.argv[1:]
    limit = None
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    retry_only = "--retry" in argv

    funds = json.loads((PROC / "funds.json").read_text(encoding="utf-8"))
    global _manifest
    if MANIFEST.exists():
        _manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    targets = list(funds.items())
    if retry_only:
        bad = {"error", "no-url", "not-pdf", "too-small"}
        targets = [(p, f) for p, f in targets
                   if _manifest.get(p, {}).get("status", "") not in ("ok", "cached")
                   or _manifest.get(p, {}).get("status") in bad]
    if limit:
        targets = targets[:limit]

    LOG.info("downloading factsheets for %d funds (workers=%d)", len(targets), WORKERS)
    t0 = time.time()
    done = 0

    session = requests.Session()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(download, p, f, session): p for p, f in targets}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:                        # never lose the batch
                rec = {"proj_id": pid, "status": "crash", "error": str(e)[:200]}
                LOG.exception("crash on %s", pid)
            with _lock:
                _manifest[pid] = rec
                done += 1
                if done % 100 == 0:
                    LOG.info("  %d/%d (%.0fs)", done, len(targets), time.time() - t0)
                    MANIFEST.write_text(
                        json.dumps(_manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    MANIFEST.write_text(json.dumps(_manifest, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    counts: dict[str, int] = {}
    for rec in _manifest.values():
        counts[rec.get("status", "?")] = counts.get(rec.get("status", "?"), 0) + 1
    LOG.info("finished in %.0fs -> %s", time.time() - t0,
             json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
