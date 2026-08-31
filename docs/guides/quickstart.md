---
title: Quickstart
tags: [guide, sec-api, getting-started]
---

# 🚀 Quickstart — Getting Started with the SEC Fund API

A beginner's guide to fetching Thai mutual fund data using the SEC Open Data API v2.

**Related:** [[authentication|Authentication]] · [[pagination|Pagination]] · [[rate-limits-and-errors|Errors]] · [[../api-reference/00-index|API Reference]]

---

## 1. Prepare API Credentials

1. Register and subscribe at the [SEC Open Data Developer Portal](https://secopendata.sec.or.th/sec-open-apis).
2. Add your subscription keys to `.env.local` in the project root:

```ini
SEC_SUBSCRIPTION_KEY=your_32_char_primary_key
SEC_SECONDARY_KEY=your_secondary_key
```

> [!IMPORTANT]
> Never commit `.env.local` to version control.

---

## 2. Make Your First API Request

```bash
curl "https://api.sec.or.th/v2/fund/general-info/amcs?page_size=5" \
  -H "Ocp-Apim-Subscription-Key: $SEC_SUBSCRIPTION_KEY"
```

Example response:

```json
{
  "message": "success",
  "page_size": 5,
  "next_cursor": "MnxFMTBBQzI3YkQvUXNQ...",
  "items": [
    {
      "unique_id": "C0000033452",
      "comp_name_en": "EASTSPRING ASSET MANAGEMENT (THAILAND) COMPANY LIMITED",
      "comp_name_th": "บริษัทหลักทรัพย์จัดการกองทุน อีสท์สปริง (ประเทศไทย) จำกัด",
      "last_upd_date": "2026-08-27T07:42:19.577"
    }
  ]
}
```

Every endpoint response follows the same structure: `message` · `page_size` · `next_cursor` · `items[]`.

---

## 3. Using the Python Client

This repository provides a built-in client (`SECClient`) that handles rate-limiting, retries with exponential backoff, key failover, and automatic cursor pagination.

```python
import sys; sys.path.insert(0, "scripts")
from sec_client import SECClient, EP

client = SECClient()  # Automatically loads credentials from .env.local

# Fetch a single page
data = client.get(EP["profiles"], {"fund_status": "Registered", "page_size": 100})

# Iterate over all records (automatic cursor-based pagination)
for fund in client.paginate(EP["profiles"], {"fund_status": "Registered"}):
    print(fund["proj_abbr_name"], fund["proj_name_en"])
```

---

## 4. Bulk Harvesting

```bash
python scripts/harvest.py              # Download all datasets
python scripts/harvest.py fs_fees      # Download a specific dataset
python scripts/harvest.py --force nav  # Force re-download
```

Harvested raw data is stored in `data/raw/<dataset>.jsonl` with `.done` checkpoint files to enable idempotent, resumable execution.

> [!TIP]
> Most endpoints can be called **without specifying `proj_id`**, which returns the entire market in bulk. This is up to 24x faster than querying 2,300+ funds individually. See [[bulk-vs-per-fund|Bulk vs Per-fund]].

---

## 5. Generating the Obsidian Vault

```bash
python scripts/transform.py         # Transform raw JSONL -> data/processed/funds.json
python scripts/gen_vault.py         # Generate Markdown notes in vault/
python scripts/fetch_factsheets.py  # Download fund factsheet PDFs
python scripts/parse_factsheets.py  # Parse PDF text into Markdown
```

For the complete end-to-end workflow, see [[pipeline|Pipeline Overview]].

---

## Recommended Reading Path

1. [[authentication|Authentication]] — How API keys and failover work
2. [[pagination|Pagination]] — Cursor-based pagination patterns
3. [[fund-identifiers|Fund Identifiers]] — Understanding `proj_id` vs `regis_id` vs `fund_class_name`
4. [[fund-taxonomy|Fund Taxonomy]] — Fund classification and filter criteria
5. [[../api-reference/00-index|API Reference (21 Endpoints)]]
