---
title: SEC Fund API Reference
tags: [sec-api, index]
---

# 📚 SEC Open API — Fund (v2) Reference

Complete reference documentation for all **21 endpoints** in the `fund` API group provided by the Securities and Exchange Commission (SEC) of Thailand.

| Property | Description |
|---|---|
| Base URL | `https://api.sec.or.th` |
| Auth Header | `Ocp-Apim-Subscription-Key` |
| Pagination | `page_size` (1–100) + `next_cursor` |
| Developer Portal | [SEC Open Data Portal](https://secopendata.sec.or.th/sec-open-apis) |

**Before you begin:** [[../guides/quickstart|Quickstart]] · [[../guides/authentication|Authentication]] · [[../guides/pagination|Pagination]] · [[../guides/rate-limits-and-errors|Rate limits & Errors]]

---

## 1. General Info

| # | Endpoint | Method | Path | Dataset | Description |
|---|---|---|---|---|---|
| 01 | [[01-amcs\|Asset Management Companies]] | `GET` | `/v2/fund/general-info/amcs` | `amcs` | List of licensed mutual fund management companies (AMCs) |
| 02 | [[02-fund-profiles\|Fund Profiles]] | `GET` | `/v2/fund/general-info/profiles` | `profiles` | Mutual funds under management and general characteristics |
| 03 | [[03-fund-specifications\|Fund Specifications]] | `GET` | `/v2/fund/general-info/specifications` | `specifications` | Special fund classifications (e.g., Feeder, Fund of Funds) |
| 04 | [[04-mutual-fund-fees\|Fund Fees]] | `GET` | `/v2/fund/general-info/mutual-fund-fees` | `mutual_fund_fees` | Total fund expense ratios and statutory fees |
| 05 | [[05-involve-parties\|Involved Parties]] | `GET` | `/v2/fund/general-info/involve-parties` | `involve_parties` | Trustees, auditors, registrars, and fund managers |

---

## 2. Factsheet

| # | Endpoint | Method | Path | Dataset | Description |
|---|---|---|---|---|---|
| 06 | [[06-factsheet-urls\|Factsheet URLs]] | `GET` | `/v2/fund/factsheet/urls` | `fs_urls` | Official Fund Fact Sheet PDF download links |
| 07 | [[07-factsheet-ipos\|Fund IPOs]] | `GET` | `/v2/fund/factsheet/ipos` | `fs_ipos` | Initial Public Offering dates and initial unit prices |
| 08 | [[08-factsheet-benchmarks\|Benchmarks]] | `GET` | `/v2/fund/factsheet/benchmarks` | `fs_benchmarks` | Benchmark indices used for performance comparison |
| 09 | [[09-subscription-redemption-minimums\|Min Subscription & Redemption]] | `GET` | `/v2/fund/factsheet/subscription-redemption-minimums` | `fs_min_amounts` | Minimum initial/subsequent investment and balance amounts |
| 10 | [[10-subscription-redemption-periods\|Trading Periods]] | `GET` | `/v2/fund/factsheet/subscription-redemption-periods` | `fs_periods` | Dealing schedule and settlement cycle (e.g., T+2, T+3) |
| 11 | [[11-risk-spectrum\|Risk Spectrum]] | `GET` | `/v2/fund/factsheet/risk-spectrum` | `fs_risk` | Risk level classification (Level 1 to 8+) |
| 12 | [[12-statistics\|Statistics]] | `GET` | `/v2/fund/factsheet/statistics` | `fs_statistics` | Maximum Drawdown, SD, Beta, Tracking Error, PTR |
| 13 | [[13-dividend-policy\|Dividend Policy]] | `GET` | `/v2/fund/factsheet/dividend-policy` | `fs_dividend` | Dividend payment policy and distribution conditions |
| 14 | [[14-factsheet-fees\|Factsheet Fees]] | `GET` | `/v2/fund/factsheet/fees` | `fs_fees` | Front-end, back-end, switching, and management fees |
| 15 | [[15-performance\|Historical Performance]] | `GET` | `/v2/fund/factsheet/performance` | `fs_performance` | Trailing returns (YTD, 3M, 6M, 1Y, 3Y, 5Y, 10Y, Since Inception) |
| 16 | [[16-asset-allocation\|Asset Allocation]] | `GET` | `/v2/fund/factsheet/asset-allocation` | `fs_asset_alloc` | Asset class allocation breakdown (% NAV) |
| 17 | [[17-top5-holdings\|Top 5 Holdings]] | `GET` | `/v2/fund/factsheet/top5-holdings` | `fs_top5` | Top 5 individual securities/assets held |

---

## 3. Outstanding Portfolio

| # | Endpoint | Method | Path | Dataset | Description |
|---|---|---|---|---|---|
| 18 | [[18-outstanding-portfolio\|Quarterly Portfolio]] | `GET` | `/v2/fund/outstanding/portfolio` | `out_portfolio` | Full security-level portfolio holdings at quarter-end |
| 19 | [[19-outstanding-portfolio-asset-type\|Monthly Asset Breakdown]] | `GET` | `/v2/fund/outstanding/portfolio-asset-type` | `out_port_asset_type` | Month-end asset/liability classification breakdown |

---

## 4. Daily Info

| # | Endpoint | Method | Path | Dataset | Description |
|---|---|---|---|---|---|
| 20 | [[20-daily-nav\|Daily NAV]] | `GET` | `/v2/fund/daily-info/nav` | `nav` | Daily Net Asset Value (NAV), unit price, and NAV date |
| 21 | [[21-dividend-history\|Dividend History]] | `GET` | `/v2/fund/daily-info/dividend-history` | `dividend_history` | Historical dividend payouts, book closing, and payment dates |
