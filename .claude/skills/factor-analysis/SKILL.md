---
name: factor-analysis
description: Analyzes and explains the macroeconomic factor exposures of Thai mutual funds — both structural sensitivities (two-sided opportunities/risks) and empirical historical correlations (Gold, Oil, Interest Rates, USD/THB, SET Index). Use when a user asks what drives a fund, what affects it, what it moves with, its sensitivity, or factor exposures (e.g. "กองนี้ไวต่ออะไร", "กระทบจากอะไร"). Strictly descriptive, never a forecast.
---

# factor-analysis

Explains what factors drive a Thai mutual fund from two complementary angles: **Structural Sensitivity** (derived from asset/sector/country composition) and **Empirical Historical Correlation** (measured against macro benchmarks).

## Data Sources to Inspect

1. **Fund Note** `vault/Funds/<ABBR>.md`:
   - Section: **⚖️ Factor Sensitivity (Two-sided / ปัจจัยที่กระทบกอง)** — Structural qualitative analysis with both upside opportunities (▲) and downside risks (▼).
   - Section: **📊 Historical Correlation (เคลื่อนไหวสัมพันธ์กับอะไร)** — Empirically measured correlation coefficients against benchmarks:
     - Gold (XAU/USD)
     - Crude Oil (WTI/Brent)
     - Policy Interest Rate (TH / US 10Y Treasury)
     - USD/THB Exchange Rate
     - SET Index & Emerging Markets Index
2. **Processed Data & Scripts** (for deep inspection if needed):
   - `data/processed/correlations.json` — Precomputed rolling and historical correlation tables.
   - `data/processed/factor_series.json` — Macro factor historical time series.
   - `scripts/factor_map.json` & `scripts/factors.py` — Factor mapping heuristics and sector weights.

## Response Structure

1. **Structural Drivers (What it is sensitive to):** Key economic factors driving the fund, explaining **both sides** (positive driver when factor rises vs. risk when factor declines).
2. **Empirical Correlation (How it historically moved):** Correlation coefficient ($r$), direction (positive/negative), sample period, and data points.
3. **Synthesis:** Cross-validate structural expectations with empirical numbers (e.g., if gold equity fund has $+0.89$ correlation to spot gold).
4. **Important Caveats:** Remind that correlation $\neq$ causation, correlations can spike during market panics, and past correlation does not guarantee future co-movement.

## Strict Guidelines

- **Never forecast** price targets, returns, or future directions. No "will gain X%" or confidence intervals.
- **Always present two-sided impacts** without predicting macroeconomic outcomes.
- **Cite the historical time period** and sample size for every statistic.
- **Prohibited terms/fields:** Do not generate `estimated_change`, `confidence_score`, `target_price`, or buy/sell `signals`.
