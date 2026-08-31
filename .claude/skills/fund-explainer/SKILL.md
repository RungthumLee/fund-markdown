---
name: fund-explainer
description: Explains a single Thai mutual fund in clear, accessible investor language using structured data from the Fund Knowledge Base. Use when a user asks what a fund is, how it works, its strategy, or an overall breakdown of a specific fund (e.g. "กองนี้คืออะไร", "อธิบายกอง X", "กอง X เป็นยังไง").
---

# fund-explainer

Provides an intuitive, well-structured breakdown of a single Thai mutual fund grounded strictly in the repository's verified data.

## Execution Steps

1. **Locate Fund Note:**
   - Open `vault/Funds/<ABBR>.md`.
   - If the abbreviation or ticker is not known, look up the fund name in `vault/Indexes/all-funds.md` or search by keyword.
2. **Extract Key Sections:**
   - Frontmatter metadata (`policy_desc`, `risk_spectrum`, `ter_retail`, `perf_1y`, `perf_3y`, `perf_5y`, `mdd`, `master_fund`, `tags`).
   - Summary & Plain English overview sections.
   - Fee breakdown & transaction terms (settlement days $T+X$).
   - Geographical & Sector allocation.
   - Look-through underlying holdings section.
   - Factor sensitivity section (⚖️).
3. **If Feeder Fund:**
   - Open corresponding Master Fund profile in `vault/MasterFunds/<Master_Name>.md`.
   - Retrieve Master Fund details, foreign domicile, benchmark, and 2-tier expense figures.

## Recommended Response Layout

1. **Fund Profile & Core Strategy:**
   - Fund category, investment policy, management style (Active/Passive), and Master Fund relationship (if feeder).
2. **Key Practical Specs (Plain English):**
   - Risk Spectrum rating (Level 1 to 8+).
   - Liquidity & Settlement cycle ($T+1$, $T+2$, $T+3$, etc.).
   - FX hedging policy (Fully hedged, partially hedged, discretionary, or unhedged).
   - Dividend policy (Accumulation, Dividend payout, Auto-redemption).
3. **Where the Money Actually Goes:**
   - Geographical & sector exposure.
   - Top underlying corporate holdings (leveraging look-through analysis).
4. **All-in Cost Structure:**
   - Retail Total Expense Ratio (TER) + Master Fund OCF (if feeder).
5. **Historical Performance & Volatility:**
   - Trailing returns (1Y, 3Y, 5Y, Since Inception).
   - Maximum Drawdown (MDD) and standard deviation.
6. **Macro Sensitivity (Two-Sided):**
   - Key positive catalysts and downside risk factors.

## Core Rules

- **Purely Informational:** Never provide financial advice, ratings, or buy/sell/hold recommendations.
- **Historical Context:** Always specify the calculation timeframe for performance and metrics, noting that past performance does not guarantee future results.
- **Data Fidelity:** If a data point is unrecorded or not reported by the AMC, state clearly that it is unavailable rather than assuming.
