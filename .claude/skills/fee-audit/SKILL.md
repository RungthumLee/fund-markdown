---
name: fee-audit
description: Audits and breaks down the true total cost of ownership of Thai mutual funds (retail TER + Master Fund OCF for feeder funds = 2-tier fee structure) and identifies lower-cost alternatives within the same AIMC peer group. Use when a user asks about fund fees, expense ratios, whether a fund is expensive, or cheaper alternatives (e.g., "กองนี้ค่าธรรมเนียมแพงไหม", "มีกองไหนถูกกว่า").
---

# fee-audit

Audits the true all-in cost of a Thai mutual fund and benchmarks it against peer funds in the same category.

## Inspection Steps

1. **Retail TER (Thai Fund):**
   - Open `vault/Funds/<ABBR>.md`.
   - Read frontmatter field `ter_retail` — represents the actual Total Expense Ratio charged to **retail investor share classes** (derived via `scripts/fees.py`, avoiding distorted institutional fee ceilings).
2. **Two-Tier Feeder Fees (If Feeder Fund):**
   - If the fund is a feeder, check the Master Fund profile in `vault/MasterFunds/<Master_Name>.md`.
   - Retrieve the Master Fund's Ongoing Charges Figure (OCF / TER).
   - **Effective 2-Tier Cost $\approx$ Thai Fund Retail TER + Master Fund OCF**.
3. **Peer Benchmark Comparison:**
   - Consult `vault/Indexes/compare-fees.md` and `vault/Indexes/by-peer-group.md`.
   - Determine the fee quartile / rank of the fund within its AIMC category.
   - Identify lower-cost alternatives in the identical asset class / peer group.

## Response Structure

1. **True All-in Cost:**
   - Breakdown of Thai retail TER (+ Master OCF if feeder = Total effective annual drag).
   - Transaction fee summary (Front-end, Back-end, Switching fees).
2. **Peer Group Ranking:**
   - Factual rank within the AIMC peer group (e.g., lowest 25%, median, or top quartile).
3. **Lower-Cost Alternatives:**
   - Table of comparable funds in the same category with lower total expense ratios.
4. **Data Completeness Notes:**
   - Note any reporting anomalies (e.g., funds with incomplete fee disclosures or pending factsheet updates).

## Core Principles

- **Compare Actual to Actual:** Ensure comparisons use actual charged expense ratios (`actual_value`), not prospectus statutory ceilings (`rate`).
- **Objective & Factual:** Low fees do not automatically imply superior risk-adjusted performance; present numbers neutrally to help the user evaluate.
- **Strict Peer Matching:** Compare only within the identical asset class, investment policy, and management style (Active vs Passive).
