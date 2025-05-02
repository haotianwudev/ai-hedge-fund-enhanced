# Valuation Agent Documentation

## Overview
The Valuation Agent implements four complementary valuation methodologies to determine investment signals and confidence levels.

## Core Concepts

### The Valuation "Gap"
The gap represents the percentage difference between intrinsic value and market cap:
```
gap = (intrinsic_value - market_cap) / market_cap
```
- Positive gap → Undervalued
- Negative gap → Overvalued
- Used for both signals and confidence

### Why Use Gap?
1. **Signal Direction**:
   - +15%+ gap → Bullish (meaningful undervaluation)
   - -15%- gap → Bearish (meaningful overvaluation)
   - Between → Neutral

2. **Confidence**:
   ```
   confidence = min(abs(gap), 30%) / 30% * 100
   ```
   - Scales with gap magnitude (stronger mispricing = higher confidence)
   - Caps at 30% gap (maximum meaningful difference)

## Valuation Methods

1. **Owner Earnings (35% weight)**
   - Buffett's method: Net Income + Depreciation - Maintenance Capex
   - Discounted with margin of safety

2. **DCF (35% weight)**  
   - 5-year free cash flow projection
   - Conservative growth (5%) and discount (10%) rates

3. **EV/EBITDA (20% weight)**
   - Median historical multiple applied
   - Converts enterprise value to equity value

4. **Residual Income (10% weight)**
   - Accounts for cost of capital
   - Based on book value growth

## Signal Generation Process

1. For each ticker:
   - Calculate all four valuations
   - Compute gap for each valid method
   - Apply method weights

2. Calculate weighted average gap:
   ```
   weighted_gap = Σ(method_weight * method_gap) / total_weight
   ```

3. Determine final signal:
   - Bullish: weighted_gap > +15%
   - Bearish: weighted_gap < -15%
   - Neutral: between -15% and +15%

4. Calculate confidence:
   - Scaled from 0-100% based on gap magnitude
   - Capped at 30% gap (absolute value)

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 82,
    "reasoning": {
      "dcf_analysis": {
        "signal": "bullish",
        "details": "Value: $150B, Market Cap: $120B, Gap: +25%, Weight: 35%"
      },
      "owner_earnings_analysis": {
        "signal": "bullish", 
        "details": "Value: $140B, Market Cap: $120B, Gap: +16.7%, Weight: 35%"
      }
    }
  }
}
