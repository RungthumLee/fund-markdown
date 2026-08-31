---
name: portfolio-overlap
description: Analyzes true portfolio overlap, duplication, and concentration across multiple Thai mutual funds — identifying shared Master Funds, common underlying stock exposures via look-through, and redundant multi-tier fees. Use when a user provides a list of funds and asks about portfolio overlap, diversification, or duplication (e.g. "ถือกองพวกนี้ซ้ำซ้อนไหม", "check overlap between Fund A and Fund B").
---

# portfolio-overlap

Evaluates true underlying duplication across multiple Thai mutual funds, revealing whether supposedly diversified funds actually hold the same underlying assets or feed into identical foreign Master Funds.

## Analysis Workflow

1. **Resolve Funds:**
   - For each fund abbreviation provided by the user, look up its `proj_id` and metadata in `vault/Funds/<ABBR>.md`.
2. **Layer 1: Master Fund Level Duplication:**
   - Inspect frontmatter field `master_fund` and check `data/processed/lookthrough.json` (or `vault/MasterFunds/`).
   - Identify funds from different Thai AMCs that feed into the **exact same Master Fund** (representing ~95–100% asset duplication).
3. **Layer 2: Underlying Asset Overlap (Look-Through):**
   - Query `data/processed/lookthrough.json` for each fund's direct and indirect constituent holdings.
   - Calculate the intersection of underlying companies/securities across the selected funds.
   - If the user provided portfolio weights (e.g., 50% Fund A, 50% Fund B), calculate the weighted aggregate exposure to each top overlapping security.
4. **Layer 3: Fee Redundancy Assessment:**
   - If multiple funds feed into the same Master Fund or hold the same underlying index, highlight the respective Thai retail TERs being paid concurrently for duplicate exposure.

## Recommended Response Structure

1. **Master Fund Duplication Summary:**
   - Clearly flag pairs/groups of funds sharing the same foreign Master Fund.
2. **Top Overlapping Holdings:**
   - Table of common underlying companies, showing individual weights in each fund and combined portfolio exposure.
3. **Factual Concentration Insights:**
   - Highlight portfolio concentration points (e.g., *"While holding 4 different funds, ~32% of total portfolio exposure is concentrated in 5 mega-cap technology stocks"*).
4. **Fee Redundancy Observations:**
   - Factual breakdown of expense ratios across overlapping holdings.
5. **Look-Through Coverage Disclaimer:**
   - State the percentage of each fund's portfolio resolved via look-through and note that unlisted minor holdings may contain additional overlap.

## Strict Guidelines

- **Neutral Factual Presentation:** Present concentration and duplication facts clearly to empower user decisions; never advise the user to sell, rebalance, or switch funds.
- **Coverage Transparency:** Explicitly state the look-through coverage ratio for each analyzed fund.
