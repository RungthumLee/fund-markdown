# 📊 Thai Mutual Funds Knowledge Base

An open knowledge base and structured [Obsidian](https://obsidian.md/) vault covering Thai mutual funds, built using data from the **Securities and Exchange Commission (SEC) of Thailand Open Data API v2**.

This repository provides an automated data pipeline that harvests, cleanses, enriches, and structures fund data into interconnected Markdown notes, complete with master fund look-through analysis, entity normalization via Bloomberg OpenFIGI, macro factor sensitivities, and 21-endpoint API documentation.

> **Scope:** 2,121 active registered mutual funds (`Registered`) and 4,663 share classes across 22 Asset Management Companies (AMCs) in Thailand. Excludes fixed-term funds (Term Funds) and Provident Funds (PVD).

---

## 🧠 Knowledge Vault Structure (`vault/`)

The generated Obsidian knowledge vault contains **8,000+ interconnected Markdown notes** equipped with YAML frontmatter for seamless querying via the [Dataview](https://github.com/blacksmithgu/obsidian-dataview) plugin:

```text
vault/
├── Indexes/          (17 MOCs)   Master tables of content, screener, and multi-dimensional indexes
├── Funds/            (2,121 notes) Complete mutual fund profiles with 12 structured sections
├── AMCs/             (22 notes)    Asset Management Company profiles, AUM, and fund rosters
├── MasterFunds/      (591 notes)   Foreign master fund profiles enriched via Yahoo Finance & FT.com
├── Entities/         (3,136 notes) Underlying stock/bond holdings with OpenFIGI IDs and cross-holdings
├── Factsheets/       (2,120 notes) Full text and parsed tables extracted from official PDF factsheets
├── Concepts/         (18 notes)    Investment policy classifications and concept guides
└── Changes/          (Daily log)   Automated changelogs tracking daily market changes
```

### 📋 What's Inside Each Fund Note (`vault/Funds/`)

Every fund note provides a standardized, 12-section comprehensive profile:
1. **General Information**: Registration ID, project ID, inception date, share classes, retail qualification tier.
2. **Investment Policy & Strategy**: Official policy text, benchmark specification, and tax incentives (RMF, SSF, Thai ESG).
3. **Fees & Expenses**: Retail Total Expense Ratio (TER), prospectus statutory ceilings, front-end/back-end/switching transaction fees.
4. **Historical Performance**: Trailing returns (YTD, 3M, 6M, 1Y, 3Y, 5Y, 10Y, Since Inception) vs. benchmark.
5. **Risk Metrics & Statistics**: Risk Spectrum (Level 1–8+), Maximum Drawdown (MDD), Standard Deviation, Sharpe Ratio, Beta, Portfolio Turnover Ratio (PTR), Duration, and YTM.
6. **Asset Allocation & Geography**: Asset class breakdown and country allocations.
7. **Holdings & Look-Through**: Direct quarterly top holdings + indirect look-through into underlying master fund equities/bonds.
8. **Factor Sensitivity (⚖️)**: Two-sided structural exposure analysis (catalysts vs downside risks).
9. **Historical Correlation (📊)**: Empirical correlation coefficients against macro benchmarks (Gold, Crude Oil, Interest Rates, USD/THB, SET Index).
10. **Trading Terms & Dealing Schedule**: Minimum initial/subsequent subscriptions, redemption processing, and settlement cycles ($T+1$ to $T+5$).
11. **Involved Parties**: Trustee, Auditor, Registrar, and Fund Managers.
12. **Factsheet Archives & External Links**: Direct links to SEC PDF archives, AMC URLs, and extracted factsheet markdown.

---

## ⚡ Key Features

- **End-to-End SEC API Pipeline**: Automatically harvests all 21 endpoints from the SEC Open Data API v2 with resilient pagination, key failover, and rate limiting.
- **Feeder Fund Look-Through**: Multiplies feeder allocations by foreign master fund holdings to reveal true underlying company exposures (e.g., discovering indirect exposures to global leaders like TSMC, Eli Lilly, and Alphabet).
- **Security Normalization & OpenFIGI**: Standardizes 26,000+ raw holding names into 3,100+ unique corporate and sovereign entities mapped to Bloomberg FIGI identifiers.
- **2-Tier Fee Breakdown**: Calculates the true all-in cost for feeder funds by aggregating Thai retail TER with foreign Master Fund Ongoing Charges Figures (OCF).
- **Macro Sensitivity & Empirical Correlation**: Combines structural factor sensitivities with empirical historical NAV correlations across macro drivers.
- **Daily Incremental Sync (`daily.py`)**: Automatically detects and refreshes aged datasets, producing automated changelogs and validation reports.

---

## 🤖 Built-in Claude / AI Assistant Skills (`.claude/skills/`)

The repository includes pre-configured agentic skills for AI assistants (e.g. Claude Desktop, Antigravity, Claude Code):

| Skill | Description |
|---|---|
| [`fund-explainer`](.claude/skills/fund-explainer/SKILL.md) | Explains a single Thai fund in plain investor language with 2-tier fees and look-through. |
| [`fund-finder`](.claude/skills/fund-finder/SKILL.md) | Screens and filters funds based on natural-language criteria and faceted tags. |
| [`fee-audit`](.claude/skills/fee-audit/SKILL.md) | Audits true all-in costs and identifies lower-cost alternatives within AIMC peer groups. |
| [`factor-analysis`](.claude/skills/factor-analysis/SKILL.md) | Analyzes structural sensitivities and historical correlations to macro factors. |
| [`holding-explorer`](.claude/skills/holding-explorer/SKILL.md) | Finds all Thai mutual funds holding a specific stock (directly and indirectly). |
| [`portfolio-overlap`](.claude/skills/portfolio-overlap/SKILL.md) | Evaluates duplication, shared master funds, and overlapping stock concentration. |

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- SEC Open Data API Subscription Key ([Register for free at the SEC Open Data Portal](https://secopendata.sec.or.th/sec-open-apis))

Install required dependencies:

```bash
pip install requests pymupdf
```

### 2. Configuration

Create a `.env.local` file in the root directory:

```ini
SEC_SUBSCRIPTION_KEY=your_primary_key_here
SEC_SECONDARY_KEY=your_secondary_key_here
```

### 3. Build the Knowledge Vault

Run the complete pipeline from scratch:

```bash
python run_all.py
```

CLI options:

```bash
python run_all.py --smoke          # Fast test run on a small sample
python run_all.py --from vault      # Resume from vault generation
python run_all.py --skip factsheets # Skip downloading PDF factsheets
```

For scheduled daily maintenance, run:

```bash
python daily.py
```

---

## 📖 Opening the Vault in Obsidian

1. Open **Obsidian**.
2. Click **Open folder as vault** and select the `vault/` directory.
3. Start exploring from `Indexes/00-home.md`.
4. *(Recommended)* Install the **Dataview** community plugin to enable dynamic frontmatter tables and queries.

---

## 📁 Repository Structure

```text
├── docs/                   # API reference, data dictionary, and architectural guides
│   ├── api-reference/      # Comprehensive documentation for all 21 SEC endpoints
│   └── guides/             # Technical guides (quickstart, look-through, pipeline, etc.)
├── scripts/                # Data collection, transformation, normalization, and note generators
├── vault/                  # The Obsidian Knowledge Vault (Funds, AMCs, Entities, Indexes)
├── .claude/skills/         # AI assistant skills for interactive exploration
├── daily.py                # Daily sync and incremental update runner
├── run_all.py              # Full end-to-end pipeline runner
└── README.md
```

---

## 📚 Documentation

Comprehensive guides and references are located in [`docs/`](docs/):

- [Quickstart Guide](docs/guides/quickstart.md) — API setup and initial vault generation
- [API Reference](docs/api-reference/00-index.md) — Detailed guide to all 21 SEC Open API endpoints
- [Data Dictionary](docs/guides/data-dictionary.md) — Catalog of all 104 fields and schema models
- [Pipeline Architecture](docs/guides/pipeline.md) — End-to-end pipeline design and data flow
- [Look-Through Analysis](docs/guides/lookthrough.md) — Feeder fund exposure mechanics and limitations
- [Entity Normalization](docs/guides/entity-normalization.md) — Security deduplication and FIGI resolution
- [Daily Operations](docs/guides/daily-operation.md) — Automated sync schedules and changelogs

---

## ⚖️ Data Source & Disclaimer

- **Data Source:** [Securities and Exchange Commission of Thailand Open Data Portal](https://secopendata.sec.or.th/sec-open-apis)
- **API Host:** `https://api.sec.or.th`

> **Disclaimer:** All information in this repository is sourced from public disclosures by the Securities and Exchange Commission of Thailand. This repository is strictly for educational, research, and informational purposes, and does **not** constitute financial, legal, or investment advice.
