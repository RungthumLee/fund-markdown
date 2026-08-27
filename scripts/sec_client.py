"""
sec_client.py — Thin, resilient client for SEC Thailand Open Data API v2.

Docs: docs/api-reference/  |  Base: https://api.sec.or.th
Auth: header Ocp-Apim-Subscription-Key (read from .env.local)
"""
from __future__ import annotations

import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import requests

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://api.sec.or.th"
DEFAULT_PAGE_SIZE = 100

# ---------------------------------------------------------------- env / auth

def load_env(path: Path | None = None) -> Dict[str, str]:
    path = path or (ROOT / ".env.local")
    env: Dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


ENV = load_env()
PRIMARY_KEY = ENV.get("SEC_SUBSCRIPTION_KEY", "")
SECONDARY_KEY = ENV.get("SEC_secondary_key", "")

# ---------------------------------------------------------------- logging

def get_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    (ROOT / "logs").mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s")
    fh = logging.FileHandler(ROOT / "logs" / f"{name}.log", encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    # The Windows console defaults to cp874 here, which cannot encode Thai or
    # even a "®" in a fund name and raises mid-log. Force UTF-8 on stdout.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    return log


LOG = get_logger("sec_client")

# ---------------------------------------------------------------- client

class SECClient:
    """GET-only client with retry, key failover and cursor pagination."""

    def __init__(self, key: str = PRIMARY_KEY, fallback_key: str = SECONDARY_KEY,
                 rate_delay: float = 0.12, timeout: int = 60):
        if not key:
            raise RuntimeError("SEC_SUBSCRIPTION_KEY missing from .env.local")
        self.keys = [k for k in (key, fallback_key) if k]
        self.key_idx = 0
        self.rate_delay = rate_delay
        self.timeout = timeout
        self.session = requests.Session()
        self.calls = 0

    @property
    def key(self) -> str:
        return self.keys[self.key_idx]

    def _rotate_key(self) -> bool:
        if self.key_idx + 1 < len(self.keys):
            self.key_idx += 1
            LOG.warning("Rotated to secondary subscription key")
            return True
        return False

    def get(self, path: str, params: Optional[Dict[str, Any]] = None,
            max_retries: int = 5) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.get(
                    url,
                    params=params,
                    headers={"Ocp-Apim-Subscription-Key": self.key,
                             "Accept": "application/json"},
                    timeout=self.timeout,
                )
                self.calls += 1
                time.sleep(self.rate_delay)

                if r.status_code == 200:
                    return r.json()
                if r.status_code == 204:
                    return {"message": "no content", "items": [], "next_cursor": ""}
                if r.status_code == 404:
                    return {"message": "not found", "items": [], "next_cursor": ""}
                if r.status_code in (401, 403):
                    if self._rotate_key():
                        continue
                    raise RuntimeError(f"Auth failed {r.status_code} on {path}")
                if r.status_code == 429 or r.status_code >= 500:
                    LOG.warning("HTTP %s on %s (attempt %s) - backoff %.1fs",
                                r.status_code, path, attempt, delay)
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
                raise RuntimeError(f"HTTP {r.status_code} on {path}: {r.text[:300]}")
            except (requests.RequestException, json.JSONDecodeError) as e:
                LOG.warning("Network error on %s (attempt %s): %s", path, attempt, e)
                time.sleep(delay)
                delay = min(delay * 2, 60)
        raise RuntimeError(f"Exhausted retries for {path} params={params}")

    def paginate(self, path: str, params: Optional[Dict[str, Any]] = None,
                 page_size: int = DEFAULT_PAGE_SIZE,
                 max_pages: int = 100_000) -> Iterator[Dict[str, Any]]:
        """Yield every item across all cursor pages."""
        params = dict(params or {})
        params["page_size"] = page_size
        cursor, pages = None, 0
        while True:
            if cursor:
                params["next_cursor"] = cursor
            data = self.get(path, params)
            for item in data.get("items") or []:
                yield item
            cursor = data.get("next_cursor") or ""
            pages += 1
            if not cursor or pages >= max_pages:
                return

    def fetch_all(self, path: str, params: Optional[Dict[str, Any]] = None,
                  **kw) -> list:
        return list(self.paginate(path, params, **kw))


# ------------------------------------------------- endpoint path constants

EP = {
    "amcs": "/v2/fund/general-info/amcs",
    "profiles": "/v2/fund/general-info/profiles",
    "specifications": "/v2/fund/general-info/specifications",
    "mutual_fund_fees": "/v2/fund/general-info/mutual-fund-fees",
    "involve_parties": "/v2/fund/general-info/involve-parties",
    "fs_urls": "/v2/fund/factsheet/urls",
    "fs_ipos": "/v2/fund/factsheet/ipos",
    "fs_benchmarks": "/v2/fund/factsheet/benchmarks",
    "fs_min_amounts": "/v2/fund/factsheet/subscription-redemption-minimums",
    "fs_periods": "/v2/fund/factsheet/subscription-redemption-periods",
    "fs_risk": "/v2/fund/factsheet/risk-spectrum",
    "fs_statistics": "/v2/fund/factsheet/statistics",
    "fs_dividend": "/v2/fund/factsheet/dividend-policy",
    "fs_fees": "/v2/fund/factsheet/fees",
    "fs_performance": "/v2/fund/factsheet/performance",
    "fs_asset_alloc": "/v2/fund/factsheet/asset-allocation",
    "fs_top5": "/v2/fund/factsheet/top5-holdings",
    "out_portfolio": "/v2/fund/outstanding/portfolio",
    "out_port_asset_type": "/v2/fund/outstanding/portfolio-asset-type",
    "nav": "/v2/fund/daily-info/nav",
    "dividend_history": "/v2/fund/daily-info/dividend-history",
}


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
