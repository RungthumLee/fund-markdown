---
name: holding-explorer
description: Queries a specific company, stock, or security to identify every Thai mutual fund that holds it — both through direct portfolio holdings and indirect look-through via foreign Master Funds. Use when a user asks which Thai funds hold a stock or company (e.g. "กองไหนถือหุ้น NVDA บ้าง", "อยากได้ exposure ใน TSMC มีกองไหน", "which funds hold Apple").
---

# holding-explorer

Traces a single security or company across the entire Thai mutual fund universe, uncovering both direct domestic holdings and indirect global exposures via Master Funds.

## Inspection Steps

1. **Locate Entity Profile:**
   - Search in `vault/Entities/<Security_Name>.md` (or query by ticker, ISIN, or FIGI).
   - Review entity metadata: Country of primary exchange, sector classification, Bloomberg FIGI identifier, and market cap tier.
2. **Examine Holding Sections:**
   - **Direct Holdings (กองทุนไทยที่ถือโดยตรง):** Table of Thai funds with direct quarterly filings, including portfolio weight (% NAV).
   - **Indirect Holdings (🔭 กองทุนไทยที่ถือทางอ้อม):** Table of Thai feeder funds with indirect exposure via Master Funds, including calculated effective weight (% NAV) and the intermediate Master Fund.
3. **Cross-Check Aggregate Data:**
   - Consult `data/processed/lookthrough.json` and `vault/Indexes/by-lookthrough.md` for market-wide rankings.

## Response Structure

1. **Security Overview:**
   - Company name, primary exchange ticker, domicile country, sector, and international FIGI.
2. **Direct Thai Fund Exposures:**
   - Total count of funds with direct holdings + funds with the highest allocation weights (% NAV).
3. **Indirect Exposures via Feeder Funds:**
   - Total count of feeder funds holding the security through foreign Master Funds + top funds and intermediate Master Funds.
4. **Combined Summary & Key Insights:**
   - Total unique fund reach across both direct and indirect routes.
   - Any notable exposure patterns (e.g., global stocks held 100% via feeders without direct domestic ownership).
5. **Methodology Caveats:**
   - Remind the user that indirect look-through figures represent minimum conservative estimates derived from disclosed top holdings of Master Funds.

## Core Rules

- **Factual Mapping Only:** Provide transparency on where assets are held without suggesting that holding a specific fund is the optimal way to gain security exposure.
- **Cite Data Sources:** Reference underlying quarterly filings, master fund factsheets, and as-of reporting dates.
