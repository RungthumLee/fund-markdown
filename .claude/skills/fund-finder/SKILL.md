---
name: fund-finder
description: Finds Thai mutual funds matching natural-language criteria by translating requirements into faceted tags, policy classifications, and metadata filters. Use when a user asks for fund recommendations or filtered lists matching specific criteria (e.g. "มีกองไหนที่...", "หากองสำหรับพักเงิน", "อยากได้กองเทคค่าธรรมเนียมถูก", "find funds that invest in...").
---

# fund-finder

Translates natural-language investment requirements into faceted tags and metadata filters to identify matching Thai mutual funds.

## Tag & Category Mapping

| User Need | Relevant Tags & Filters |
|---|---|
| Cash Management / Liquidity | `#use/park-cash`, `#risk/very-low`, `#liquidity/t1` |
| Tax Deduction | `#use/tax-saving`, `#tax/rmf`, `#tax/ssf`, `#tax/thai-esg` |
| Income / Dividend Generation | `#use/income`, `#dist/dividend`, `#dist/auto-redemption` |
| Sector Equities | `#sector/technology`, `#sector/financials`, `#sector/energy`, `#sector/healthcare` |
| Large Cap / Mega Cap Equities | `#cap/large`, `#theme/global-leaders` |
| Fixed Income Duration & Quality | `#duration/short`, `#duration/medium-long`, `#credit/investment-grade`, `#credit/high-yield` |
| Currency Neutral / Domestic Focus | `country_top: Thailand` / `market_countries: [TH]` |
| Passive Index Tracking | `management_style: Passive`, `tags: [#strategy/passive]` |

## Discovery & Screening Process

1. **Consult Master Indexes:**
   - Tag Catalog: `vault/Indexes/tags.md`
   - Screener: `vault/Indexes/screener.md`
   - Dimensional Indexes: `vault/Indexes/by-country.md`, `vault/Indexes/by-sector.md`, `vault/Indexes/compare-fees.md`, `vault/Indexes/by-risk.md`, `vault/Indexes/by-tax-incentive.md`.
2. **Filter Frontmatter Fields in `vault/Funds/*.md`:**
   - Key filter attributes: `policy_desc`, `ter_retail`, `perf_1y`, `perf_3y`, `risk_spectrum`, `fund_size`, `country_top`, `tags`.
3. **Format Shortlist (5–15 funds):**
   - Provide a comparison table: Fund Abbreviation/Ticker, Asset Class/Theme, Retail TER, Trailing 1Y Return, Risk Level, and Rationale for Match.

## Strict Boundaries

- **Factual Match vs Recommendation:** State that the results represent mechanical filtering based on public fund disclosures, not investment advice or endorsements.
- **Risk Disclosures:** Remind users that low risk does not mean zero risk, and past performance is not indicative of future results.
- **Empower Decision Making:** Present fee and performance numbers neutrally to allow users to compare and decide.
