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

## LLM Interaction

### Role in Valuation Agent:
- Primarily used for final reasoning display
- Formats the quantitative analysis results
- Does not influence signal or confidence calculations

### Example Prompt:
```
"Format this valuation analysis as a clear investment recommendation:
{quantitative_results}"
```

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
```

# Fundamental Analysis Agent Documentation

## Overview
The Fundamental Analysis Agent evaluates companies across four key dimensions to generate investment signals.

## Core Methodology

### 1. Profitability Analysis (33% weight)
- **Return on Equity**: >15% is strong
- **Net Margin**: >20% is healthy  
- **Operating Margin**: >15% is efficient
- **Signal**: Bullish if ≥2 metrics meet thresholds

### 2. Growth Analysis (33% weight)
- **Revenue Growth**: >10% is strong
- **Earnings Growth**: >10% is strong
- **Book Value Growth**: >10% is strong
- **Signal**: Bullish if ≥2 metrics meet thresholds

### 3. Financial Health (17% weight)
- **Current Ratio**: >1.5 indicates liquidity
- **Debt/Equity**: <0.5 is conservative
- **FCF Conversion**: FCF >80% of EPS
- **Signal**: Bullish if ≥2 metrics meet thresholds

### 4. Valuation Ratios (17% weight)
- **P/E Ratio**: <25 is reasonable
- **P/B Ratio**: <3 is reasonable
- **P/S Ratio**: <5 is reasonable
- **Signal**: Bearish if ≥2 metrics exceed thresholds

## Signal Generation
1. For each ticker:
   - Calculate scores for all four dimensions
   - Determine signals for each dimension
   - Count bullish/bearish signals

2. Final Signal:
   - **Bullish**: More bullish signals
   - **Bearish**: More bearish signals  
   - **Neutral**: Equal signals

3. Confidence:
   - Based on ratio of dominant signals to total signals
   - Scaled from 0-100%

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 75,
    "reasoning": {
      "profitability_signal": {
        "signal": "bullish",
        "details": "ROE: 18.5%, Net Margin: 22.1%, Op Margin: 25.3%"
      },
      "growth_signal": {
        "signal": "neutral", 
        "details": "Revenue Growth: 8.2%, Earnings Growth: 12.5%"
      }
    }
  }
}
```

# Warren Buffett Agent Documentation

## Overview
The Warren Buffett Agent emulates the investment philosophy of Warren Buffett, focusing on:
- Economic moats (durable competitive advantages)
- Quality management
- Owner earnings valuation
- Margin of safety principle

## Core Methodology

### 1. Fundamental Analysis (0-10 points)
- **Profitability**: ROE >15%, strong margins
- **Financial Health**: Low debt, good liquidity
- **Consistency**: Stable/improving earnings

### 2. Moat Analysis (0-3 points)
- **Stable ROE**: >15% across multiple periods
- **Stable Margins**: >15% operating margins
- **Both**: Indicates strongest moat

### 3. Management Quality (0-2 points)
- **Positive**: Share buybacks, dividends
- **Negative**: Share dilution

### 4. Intrinsic Value Calculation
- Uses owner earnings (Net Income + Depreciation - Maintenance Capex)
- Discounted cash flow with conservative assumptions
- Requires >30% margin of safety

## Signal Generation
- **Bullish**: Total score ≥70% AND margin ≥30%
- **Bearish**: Total score ≤30% OR margin ≤-30% 
- **Neutral**: Between thresholds

## LLM Interaction

### Role in Buffett Agent:
- Central to signal generation and confidence scoring
- Evaluates qualitative factors beyond pure numbers
- Applies Buffett's principles to final decision

### Key Questions to LLM:
1. "Does this company have durable competitive advantages?"
2. "Is management acting in shareholders' best interests?"
3. "Would Warren Buffett consider this a wonderful business?"
4. "Is the margin of safety sufficient given the business quality?"

### Confidence Calculation
1. Quantitative Score (0-100):
   - Scales with total points achieved
   - Adjusted by margin of safety magnitude
2. Qualitative LLM Assessment:
   - Incorporates Buffett-style reasoning
   - Final confidence score determined
   - Considers business quality and management

### Output Example
```json
{
  "KO": {
    "signal": "bullish",
    "confidence": 88,
    "reasoning": {
      "fundamentals": "Strong ROE (18%), consistent earnings growth",
      "moat": "Wide moat - dominant market position",
      "management": "Shareholder-friendly - consistent buybacks",
      "margin_of_safety": "35% undervaluation"
    }
  }
}
```
