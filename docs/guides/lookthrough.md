---
title: Look-through Analysis
tags: [guide, lookthrough, holdings, master-fund]
updated: 2026-08-27
---

# 🔭 Look-Through — Analyzing Underlying Holdings of Feeder Funds

A technical explanation of the look-through methodology used to map Thai feeder funds to their ultimate underlying equity and debt holdings.

**Related:** [[entity-normalization|Entity Normalization]] · [[master-fund-sources|Master Funds]] · [[holdings-data|Holdings Data]]

---

## The Problem

When Thai feeder funds submit regulatory filings to the SEC, their disclosed portfolio typically reports a single line item:
> *"99.5% invested in Master Fund units"*

While accurate from a regulatory perspective, this does not reveal the fund's actual exposure to individual companies, sectors, or sovereign debt.

By multiplying the Thai feeder fund's allocation by the underlying holdings disclosed in the Master Fund's portfolio disclosures, we calculate the effective indirect economic exposure:

$$\text{Effective Indirect Holding (\%)} = \frac{\text{Feeder Stake in Master (\%)} \times \text{Master Holding (\%)}}{100}$$

---

## Look-Through Statistics

| Metric | Count |
|---|---|
| Thai feeder funds with identifiable master fund stakes | 959 |
| **Feeder funds successfully resolved to underlying securities** | **680** |
| Unique global underlying securities mapped | **788** |
| Entity name resolution rate | **99.95%** |

### Top Indirect Exposures (Examples)

| Security | Indirect Exposure Count (Feeder Funds) | Direct Exposure Count (Thai Mutual Funds) |
|---|---|---|
| NVIDIA Corp | 201 | 16 |
| Microsoft Corp | 193 | 19 |
| Alphabet Inc. (Class A) | 147 | **0** |
| Taiwan Semiconductor Manufacturing (TSMC) | 139 | **0** |
| Eli Lilly & Co | 60 | **0** |

> [!NOTE]
> Global market leaders like **Alphabet, TSMC, and Eli Lilly** have **zero direct holdings** across Thai mutual funds due to international custody setups. Without feeder fund look-through analysis, these exposures would remain completely invisible.

---

## Entity Resolution & Name Normalization

Matching security names across disparate data sources required multi-tier normalization:

| SEC Thailand Filing Symbol | Master Fund Provider (Yahoo / FT) Name | Normalized Entity |
|---|---|---|
| `2330 TT` | `Taiwan Semiconductor Manufacturing Co Ltd` | `TSMC (2330 TT)` |
| `NVDA US` | `NVIDIA Corp` | `NVIDIA Corp (NVDA)` |
| `700 HK` | `Tencent Holdings Ltd` | `Tencent Holdings Ltd (700 HK)` |

### Resolution Pipeline:

1. **Symbol Matching**: Strips exchange prefixes/suffixes (e.g., `2330.TW` $\to$ `2330`) and matches canonical tickers.
2. **Bloomberg OpenFIGI Integration**: Resolves tickers to unique international FIGI identifiers, standardized company names, and asset classes.
3. **Master-Fund-Only Entities**: Automatically instantiates entity notes for global securities that exist exclusively through foreign master funds (tagged `#via-master-only`).

---

## Methodological Limitations

When reviewing look-through metrics, consider two inherent constraints:

1. **Top Holdings Visibility**: Foreign master fund disclosures typically publish Top 10 or Top 20 holdings. If a master fund holds 300+ securities, only ~40–60% of total portfolio weight is observable. All look-through notes display `covered_pct` alongside `stake_pct` to maintain transparency.
2. **Filing Date Asynchrony**: Quarterly Thai regulatory disclosures may differ by a few weeks from the latest reporting date of foreign master funds.

---

## Vault Integration & Outputs

- **Fund Notes (`vault/Funds/`)**: Dedicated section showing transparent look-through exposures.
- **Entity Notes (`vault/Entities/`)**: Profiles for each security listing all Thai funds that invest in it directly or indirectly.
- **Index View (`vault/Indexes/by-lookthrough.md`)**: Market-wide ranking of the most widely held global companies across all Thai funds.
- **Data Export (`data/processed/lookthrough.json`)**: Raw calculated look-through graph for programmatic use.
