---
title: Pipeline Overview
tags: [guide, architecture, pipeline]
---

# 🔄 Pipeline — System Architecture & Data Flow

An overview of the end-to-end data pipeline powering the Thai Mutual Funds Knowledge Base.

**Related:** [[quickstart|Quickstart]] · [[bulk-vs-per-fund|Bulk vs Per-fund]] · [[scope-and-filters|Scope & Filters]]

---

## Architecture Diagram

```text
                 ┌──────────────────────┐
                 │   SEC Open API v2    │
                 │  api.sec.or.th       │
                 └──────────┬───────────┘
                            │  21 endpoints, cursor pagination
                            ▼
   ┌────────────────────────────────────────────────┐
   │ 1. harvest.py            data/raw/*.jsonl      │
   │    bulk fetch + checkpoint (.done)             │
   └────────────────────────┬───────────────────────┘
                            ▼
   ┌────────────────────────────────────────────────┐
   │ 2. transform.py          data/processed/*.json │
   │    streaming join by proj_id                   │
   │    scope filter · decode base64/HTML           │
   └───────────┬────────────────────────┬───────────┘
               │                        │
               ▼                        ▼
   ┌────────────────────────┐  ┌────────────────────────┐
   │ 3. fetch_factsheets.py │  │ 5. gen_vault.py        │
   │    data/factsheets/    │  │    vault/Funds/        │
   │    *.pdf (8 workers)   │  │    vault/AMCs/         │
   └───────────┬────────────┘  │    vault/Indexes/      │
               ▼               └───────────┬────────────┘
   ┌────────────────────────┐              │
   │ 4. parse_factsheets.py │──────────────┤
   │    vault/Factsheets/   │              │
   │    *.md  (PyMuPDF)     │              │
   └────────────────────────┘              ▼
                              ┌────────────────────────┐
                              │ 6. validate_vault.py   │
                              │    integrity checks    │
                              └────────────────────────┘
```

---

## Running the Pipeline

Run the entire pipeline end-to-end:

```bash
python run_all.py                    # Complete run (skips already processed stages)
python run_all.py --smoke            # Fast smoke test with small sample
python run_all.py --from vault       # Resume starting from a specific stage
python run_all.py --skip factsheets  # Skip long-running PDF downloads
```

---

## Pipeline Stages Breakdown

### 1. `harvest.py` — Raw Data Collection
- Fetches all 21 SEC datasets in bulk without filtering by individual `proj_id`.
- Saves newline-delimited JSON (`data/raw/<dataset>.jsonl`).
- Records completion status in `<dataset>.done` checkpoints to skip completed stages on resume.
- **Force re-download:** `python scripts/harvest.py --force <dataset>`

### 2. `transform.py` — Aggregation & Cleansing
- Streams multi-gigabyte JSONL files memory-efficiently.
- Indexes records by `proj_id` and aggregates across all endpoints.
- Applies scope filters: active `Registered` status, excluding Term Funds and Provident Funds (PVD).
- Sanitizes unstructured descriptions (Base64 decoding, HTML stripping, length normalization).
- Extracts current latest factsheets and filings.
- **Output:** `funds.json`, `amcs.json`, `excluded.json`, `stats.json`.

### 3. `fetch_factsheets.py` — PDF Factsheet Downloader
- Downloads official fund factsheet PDFs using a thread pool worker (8 concurrent threads).
- Validates `%PDF` magic bytes to verify file integrity.
- Maintains a local manifest (`_manifest.json`) tracking download status, timestamps, and error codes.

### 4. `parse_factsheets.py` — PDF Text & Table Extraction
- Uses PyMuPDF (`fitz`) to extract structured text and tables from PDF factsheets.
- Extracts sector allocations, geographic exposures, credit rating distributions, fund managers, and master fund top holdings.
- Outputs Markdown files to `vault/Factsheets/` and intermediate parsed data to `data/processed/factsheet_sections.json`.

### 5. `gen_vault.py` — Obsidian Vault Generation
- Generates interconnected, Obsidian-ready Markdown notes:
  - `vault/Funds/<ABBR>.md` — Detailed fund notes with 12 standardized sections.
  - `vault/AMCs/<AMC_Name>.md` — Asset management company profiles and fund rosters.
  - `vault/Indexes/` — Multi-dimensional indexes (by AMC, policy, risk level, tax incentive, fees).
  - `vault/Concepts/` — Concept guides and asset class definitions.
- All notes include Dataview-compatible YAML frontmatter and internal wikilinks.

### 6. `validate_vault.py` — Integrity & Link Validation
- Verifies vault structure, broken wikilinks, orphan notes, schema completeness, and naming consistency.

---

## Estimated Execution Times

| Stage | Clean Run Duration | Resumed / Incremental |
|---|---|---|
| `harvest` | ~40–60 mins | Instant (cached) |
| `transform` | ~2–5 mins | ~2–5 mins |
| `fetch_factsheets` | ~15–30 mins | < 1 min |
| `parse_factsheets` | ~5–10 mins | < 1 min |
| `gen_vault` | ~1–2 mins | ~1–2 mins |
| `validate_vault` | < 30 secs | < 30 secs |

---

## Incremental Maintenance

For periodic monthly or daily refreshes:

```bash
# Refresh specific datasets and regenerate notes
python scripts/harvest.py --force nav fs_fees
python scripts/transform.py
python scripts/gen_vault.py
```
