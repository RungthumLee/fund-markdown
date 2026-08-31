# 📊 Thai Mutual Funds Knowledge Base

An open knowledge base and structured [Obsidian](https://obsidian.md/) vault covering Thai mutual funds, built using data from the **Securities and Exchange Commission (SEC) of Thailand Open Data API v2**.

This repository contains an end-to-end data pipeline that harvests, enriches, and transforms fund data into cross-linked Markdown notes, complete with comprehensive API documentation and analytical look-through capabilities.

> **Scope:** Active registered mutual funds (`Registered`) in Thailand. Excludes Term Funds and Provident Funds (PVD).

---

## ✨ Features

- 🧠 **Obsidian Knowledge Vault**: Interconnected Markdown notes for mutual funds, Asset Management Companies (AMCs), asset classes, and factsheets, optimized with Dataview-compatible metadata.
- ⚡ **SEC Open Data API v2 Integration**: Automated data harvesting pipeline covering all 21 SEC endpoints with robust pagination, key failover, and rate-limiting resilience.
- 📄 **Factsheet & Holdings Look-Through**: Automated PDF factsheet extraction, entity normalization across tens of thousands of holdings, OpenFIGI international identifier mapping, and master fund look-through for feeder funds.
- 📚 **Comprehensive API Reference & Guides**: Detailed documentation of endpoints, data dictionaries, schema taxonomies, and pipeline architecture.

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- SEC Open Data API Subscription Key ([Register for free at SEC Open Data Portal](https://secopendata.sec.or.th/sec-open-apis))

Install required Python dependencies:

```bash
pip install requests pymupdf
```

### 2. Configuration

Create a `.env.local` file in the project root with your SEC API credentials:

```ini
SEC_SUBSCRIPTION_KEY=your_primary_key_here
SEC_SECONDARY_KEY=your_secondary_key_here
```

### 3. Running the Pipeline

Run the complete pipeline from scratch:

```bash
python run_all.py
```

Useful CLI options:

```bash
python run_all.py --smoke          # Run a fast smoke test on a subset of data
python run_all.py --from vault      # Resume from the vault generation stage
python run_all.py --skip factsheets # Skip downloading PDF factsheets
```

> **Note:** Pipeline stages are designed to be idempotent and resumable. Re-running will safely skip already completed items.

---

## 📖 Opening the Vault in Obsidian

1. Open **Obsidian**.
2. Select **Open folder as vault** and choose the `vault/` folder in this repository.
3. Start exploring from `Indexes/00-home.md`.
4. *(Recommended)* Install the **Dataview** community plugin in Obsidian to take full advantage of frontmatter queries and dynamic tables.

---

## 📁 Repository Structure

```text
├── docs/                   # API reference, data dictionary, and integration guides
├── scripts/                # Data harvesting, processing, and note generation scripts
├── vault/                  # Obsidian vault (Funds, AMCs, Indexes, Factsheets, Entities)
├── daily.py                # Scheduled daily update and sync script
├── run_all.py              # End-to-end pipeline runner
└── README.md
```

---

## 📚 Documentation

Detailed documentation and guides are available in the [`docs/`](docs/) directory:

- [Quickstart Guide](docs/guides/quickstart.md) — Setup keys and build your first vault
- [API Reference](docs/api-reference/00-index.md) — Comprehensive guide to all 21 SEC endpoints
- [Data Dictionary](docs/guides/data-dictionary.md) — Field definitions and schema reference
- [Pipeline Architecture](docs/guides/pipeline.md) — Overview of data processing stages
- [Holdings & Look-Through](docs/guides/lookthrough.md) — Understanding feeder funds and asset look-through

---

## ⚖️ Data Source & Disclaimer

- **Data Source:** [SEC Open Data Developer Portal](https://secopendata.sec.or.th/sec-open-apis)
- **API Endpoint:** `https://api.sec.or.th`

> **Disclaimer:** All data is sourced from public disclosures by the Securities and Exchange Commission of Thailand. This repository is strictly intended for educational and research purposes and does **not** constitute financial, legal, or investment advice.
