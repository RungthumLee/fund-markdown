---
title: Data Dictionary
tags: [guide, reference, data-model]
---

# 📖 Data Dictionary — Unified Field Reference

A comprehensive catalog of all 104 unique fields across all 21 SEC Open API endpoints, including data types, dataset origins, and descriptions.

**Related:** [[fund-identifiers|Fund Identifiers]] · [[fund-taxonomy|Fund Taxonomy]] · [[../api-reference/00-index|API Reference]]

---

## Common Response Structure

Every endpoint response shares a consistent wrapper:

| Field | Type | Description |
|---|---|---|
| `message` | string | API status message (e.g., `success`) |
| `page_size` | number | Number of records returned per page |
| `next_cursor` | string | Opaque cursor string for pagination (empty/null when complete) |
| `items` | array&lt;object&gt; | Array of payload records |

> See [[pagination|Pagination]] for guidance on cursor traversal.

---

## Enumerated Fields (Enum)

These fields accept only predefined value sets — see the full code mapping at [[fund-taxonomy|Fund Taxonomy]]:

- `entity_type` — Used in: `involve_parties`
- `fee_type_desc` — Used in: `fs_fees`, `mutual_fund_fees`
- `fund_status` — Used in: `profiles`
- `invest_country_flag` — Used in: `profiles`
- `management_style` — Used in: `profiles`
- `proj_retail_type` — Used in: `profiles`
- `prospectus_type` — Used in: `fs_asset_alloc`, `fs_benchmarks`, `fs_dividend`, `fs_fees`, `fs_ipos`, `fs_min_amounts`, `fs_performance`, `fs_periods`, `fs_risk`, `fs_statistics`, `fs_top5`, `fs_urls`

---

## Complete Field Catalog (Alphabetical)

| Field | Type | Datasets | Description |
|---|---|---|---|
| `actual_value` | float | `fs_fees` | Actual fee rate charged |
| `address` | string | `involve_parties` | Physical address of involved party |
| `alpha` | string | `fs_statistics` | Jensen's Alpha (Equity funds only) |
| `amc_url_factsheet` | string | `fs_urls` | External URL to Fund Factsheet hosted on the AMC's website |
| `as_of_date` | date | `fs_urls`, `out_portfolio` | As-of effective date for factsheets or quarterly portfolio filings |
| `asset_name` | string | `fs_asset_alloc`, `fs_top5` | Name or asset category of investment |
| `asset_ratio` | float | `fs_asset_alloc`, `fs_top5` | Weight (% NAV) of the asset or category |
| `asset_seq` | number | `fs_asset_alloc`, `fs_top5` | Ordering sequence number |
| `assetliab_code` | string | `out_port_asset_type`, `out_portfolio` | Asset/liability category code |
| `assetliab_desc` | string | `out_port_asset_type`, `out_portfolio` | Asset/liability category description |
| `benchmark` | string | `fs_benchmarks` | Benchmark index identifier / description |
| `beta` | string | `fs_statistics` | Beta metric (Equity funds only) |
| `book_close_date` | date | `dividend_history` | Record book closing date (YYYY-MM-DD) |
| `buy_price` | number | `nav` | Redemption price (THB / unit) |
| `buy_swap_price` | number | `nav` | Switching redemption price (THB / unit) |
| `cancel_date` | date | `profiles` | Fund cancellation/liquidation date |
| `class_abbr_name` | string | `dividend_history` | Fund class abbreviation |
| `comp_name_en` | string | `amcs`, `profiles` | Asset Management Company name in English |
| `comp_name_th` | string | `amcs`, `profiles` | Asset Management Company name in Thai |
| `dividend_date` | date | `dividend_history` | Dividend payout date (YYYY-MM-DD) |
| `dividend_policy` | string | `fs_dividend` | Dividend payment policy description |
| `dividend_value` | number | `dividend_history` | Dividend amount per unit (THB) |
| `end_date` | date | `fs_*` | Factsheet end validity date (null for current latest active factsheet) |
| `entity_name_en` | string | `involve_parties` | Legal party entity name (English) |
| `entity_name_th` | string | `involve_parties` | Legal party entity name (Thai) |
| `entity_type` | string | `involve_parties` | Involved party role code (Trustee, Auditor, etc.) |
| `exchange_rate_protection_policy` | string | `profiles` | FX hedging policy description |
| `fee_other_desc` | string | `fs_fees`, `mutual_fund_fees` | Additional fee condition remarks |
| `fee_type_desc` | string | `fs_fees`, `mutual_fund_fees` | Statutory or factsheet fee classification code |
| `feederfund_country` | string | `profiles` | Domicile country of the Master Fund |
| `feederfund_master_fund` | string | `profiles` | Master Fund name (for Feeder funds) |
| `first_sell_end_date` | string | `fs_ipos` | IPO offer period end date |
| `first_sell_start_date` | string | `fs_ipos` | IPO offer period start date |
| `fund_class_description` | string | `profiles` | Fund share class extra description |
| `fund_class_detail` | string | `profiles` | Fund share class full name |
| `fund_class_isin_code` | string | `profiles` | International Securities Identification Number (ISIN) for class |
| `fund_class_name` | string | `fs_*`, `nav`, `profiles` | Share class code (`main` for non-class funds, or class suffix e.g., `SSF`, `A`) |
| `fund_class_tax_incentive_type` | string | `profiles` | Tax privilege classification (e.g., SSF, Thai ESG) |
| `fund_status` | string | `profiles` | Operational status (e.g., `Registered`, `Terminated`) |
| `fx_hedging` | string | `fs_statistics` | FX hedging status and policy |
| `group_seq` | string | `fs_benchmarks` | Benchmark grouping sequence |
| `init_date` | date | `profiles` | Fund inception/establishment date |
| `invest_country_flag` | string | `profiles` | Geographic investment focus flag (Domestic vs Foreign) |
| `investment_policy_desc` | string | `profiles` | Full investment policy text (Base64/HTML sanitized) |
| `isin_code` | string | `out_portfolio` | ISIN of held security |
| `issue_code` | string | `out_portfolio` | Local ticker/symbol of held security |
| `issuer` | string | `out_portfolio` | Security issuer name |
| `last_upd_date` | datetime | `*` | Timestamp of last record update |
| `last_val` | number | `nav` | NAV per unit (THB) |
| `lowbal_unit` | string | `fs_min_amounts` | Minimum remaining account balance (units) |
| `lowbal_val` | float | `fs_min_amounts` | Minimum remaining account balance (amount) |
| `lowbal_val_cur` | string | `fs_min_amounts` | Currency for minimum balance |
| `management_style` | string | `profiles` | Management strategy (`Active` vs `Passive` vs `Index`) |
| `market_value` | number | `out_port_asset_type`, `out_portfolio` | Market value in THB (rounded to 5 decimal places) |
| `maximum_drawdown` | string | `fs_statistics` | Maximum historical drawdown over 5 years / since inception |
| `minimum_redempt` | float | `fs_min_amounts` | Minimum redemption value |
| `minimum_redempt_cur` | string | `fs_min_amounts` | Currency for minimum redemption |
| `minimum_redempt_unit` | string | `fs_min_amounts` | Minimum redemption units |
| `minimum_sub` | float | `fs_min_amounts` | Minimum subsequent subscription value |
| `minimum_sub_cur` | string | `fs_min_amounts` | Currency for subsequent subscription |
| `minimum_sub_ipo` | float | `fs_min_amounts` | Minimum initial IPO subscription value |
| `minimum_sub_ipo_cur` | string | `fs_min_amounts` | Currency for initial subscription |
| `minimum_sub_unit` | string | `fs_min_amounts` | Minimum subscription units |
| `nav_date` | date | `nav` | NAV calculation date (YYYY-MM-DD) |
| `net_asset` | number | `nav` | Total Net Asset Value in THB |
| `pdf_factsheet` | string | `fs_urls` | Direct link to factsheet PDF archived on SEC servers |
| `percent_nav` | number | `out_port_asset_type`, `out_portfolio` | Weight as % of NAV |
| `performance_type_desc` | string | `fs_performance` | Return type description (e.g., Total Return, Annualized) |
| `performance_value` | string | `fs_performance` | Performance return figure |
| `period` | string | `fs_periods`, `out_*` | Period identifier or Dealing schedule |
| `policy_desc` | string | `profiles` | AIMC asset class category description |
| `portfolio_duration_period` | string | `fs_statistics` | Average portfolio duration (Fixed Income funds) |
| `portfolio_turnover_ratio` | string | `fs_statistics` | Portfolio Turnover Ratio (PTR) |
| `proj_abbr_name` | string | `profiles` | Fund project symbol / short name |
| `proj_id` | string | `*` | Primary unique project ID (`{Type}{ID}_{Year}` e.g., `M0000_2552`) |
| `proj_name_en` | string | `profiles` | Full fund project name in English |
| `proj_name_th` | string | `profiles` | Full fund project name in Thai |
| `proj_retail_type` | string | `profiles` | Retail investor qualification tier |
| `proj_term_day` | string | `profiles` | Fixed fund term duration (days) |
| `proj_term_flag` | string | `profiles` | Fixed-term flag (`Y` = Fixed term, `N` = Open-ended) |
| `proj_term_month` | string | `profiles` | Fixed fund term duration (months) |
| `proj_term_year` | string | `profiles` | Fixed fund term duration (years) |
| `prospectus_type` | string | `fs_*` | Filing category code |
| `rate` | string | `fs_fees`, `mutual_fund_fees` | Prospectus ceiling / statutory fee rate |
| `rate_unit` | string | `mutual_fund_fees` | Unit of fee rate (% per annum, THB, etc.) |
| `recovering_period` | string | `fs_statistics` | Recovery period after drawdown |
| `redemp_period_oth` | string | `fs_periods` | Description for custom trading cycles |
| `reference_period` | string | `fs_performance` | Trailing horizon (YTD, 1Y, 3Y, 5Y, etc.) |
| `regis_date` | date | `profiles` | SEC official registration date |
| `regis_id` | string | `profiles` | SEC mutual fund registration number |
| `remark` | string | `fs_benchmarks` | Footnotes / benchmark calculation notes |
| `risk_spectrum` | string | `fs_risk` | Standard risk tier (`RS1` through `RS8` and `RS81`) |
| `risk_spectrum_desc` | string | `fs_risk` | Risk category description |
| `sell_price` | number | `nav` | Subscription offer price (THB / unit) |
| `sell_swap_price` | number | `nav` | Switching subscription price (THB / unit) |
| `settlement_period` | string | `fs_periods` | Settlement cycle duration (e.g., T+2, T+3, T+4) |
| `sharpe_ratio` | string | `fs_statistics` | Sharpe Ratio metric |
| `spec_code` | string | `specifications` | Special specification code |
| `spec_desc` | string | `specifications` | Special classification description (SEC Notice SorNor. 87/2558) |
| `start_date` | date | `fs_*` | Factsheet effective start date |
| `tracking_error` | string | `fs_statistics` | Tracking error vs benchmark |
| `type` | string | `fs_periods` | Order type (`subscription` vs `redemption`) |
| `unique_id` | string | `amcs`, `nav`, `profiles` | Unique identifier for reporting Asset Management Company |
| `yield_to_maturity` | string | `fs_statistics` | Fixed income portfolio Yield to Maturity (YTM) |

---

## Primary Join Keys

| Field | Dataset Frequency | Usage |
|---|---|---|
| `last_upd_date` | 20 | Timestamp tracking for incremental sync |
| `proj_id` | 20 | Master fund project identifier (Primary Join Key) |
| `prospectus_type` | 12 | Version discriminator for factsheet filings |
| `fund_class_name` | 11 | Secondary join key for multi-class funds |
| `start_date` / `end_date` | 11 | Temporal validity window for historical factsheets |
| `unique_id` | 4 | Management company identifier |

> For join mechanics and best practices, see [[fund-identifiers|Fund Identifiers]].
