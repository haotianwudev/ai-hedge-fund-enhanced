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
- **P/E Ratio**: <25 is reasonable (bearish if >25)
- **P/B Ratio**: <3 is reasonable (bearish if >3)  
- **P/S Ratio**: <5 is reasonable (bearish if >5)
- **Signal Calculation**:
  - Bearish if ≥2 ratios exceed thresholds
  - Bullish if 0 ratios exceed thresholds
  - Neutral if 1 ratio exceeds threshold

## Signal Generation
1. For each ticker and dimension:
   - Calculate metrics against thresholds
   - Count how many metrics meet/exceed thresholds
   - Determine dimension signal:
     - Bullish if ≥2 metrics meet thresholds (or 0 exceed for valuation)
     - Bearish if 0 metrics meet thresholds (or ≥2 exceed for valuation)
     - Neutral otherwise

2. Final Signal:
   - **Bullish**: More bullish than bearish dimension signals
   - **Bearish**: More bearish than bullish dimension signals
   - **Neutral**: Equal bullish/bearish signals

3. Confidence:
   - Calculated as: (dominant_signals / total_signals) * 100
   - Example: 3 bullish, 1 bearish → 75% confidence

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

# Sentiment Agent Documentation

## Overview
The Sentiment Agent analyzes market sentiment from two key sources:
1. Insider trading activity (30% weight)
2. Company news sentiment (70% weight)

## Core Methodology

### Insider Trading Analysis
- **Bullish Signal**: Buying activity (positive transaction shares)
- **Bearish Signal**: Selling activity (negative transaction shares)
- **Transaction Values**:
  - Bullish: Sum of buy transaction values (positive)
  - Bearish: Sum of sell transaction values (negative)
  - Total: Net of bullish and bearish values
- Data from past 1000 insider transactions

### News Sentiment Analysis
- **Bullish Signal**: Positive sentiment articles
- **Bearish Signal**: Negative sentiment articles  
- **Neutral Signal**: Neutral sentiment articles
- Data from past 100 news articles

### Signal Generation Process
1. For each ticker:
   - Count bullish/bearish signals from both sources
   - Calculate transaction value sums (bullish positive, bearish negative)
   - Apply weights (30% insider, 70% news)
   - Calculate weighted signal counts:
     ```
     bullish_signals = (insider_bullish * 0.3) + (news_bullish * 0.7)
     bearish_signals = (insider_bearish * 0.3) + (news_bearish * 0.7)
     ```
2. Determine final signal:
   - Bullish: bullish_signals > bearish_signals
   - Bearish: bearish_signals > bullish_signals  
   - Neutral: equal signals
3. Calculate confidence:
   - Scaled from 0-100% based on signal dominance
   - Formula: max(bullish_signals, bearish_signals) / total_signals * 100

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 75,
    "detail": {
      "insider_total": 42,
      "insider_bullish": 30,
      "insider_bearish": 12,
      "insider_value_total": 1250000.0,
      "insider_value_bullish": 1500000.0,
      "insider_value_bearish": -250000.0,
      "news_total": 85,
      "news_bullish": 45,
      "news_bearish": 15,
      "news_neutral": 25,
      "weighted_bullish": 42.3,
      "weighted_bearish": 28.1
    }
  }
}

# Technical Analysis Agent Documentation

## Overview
The Technical Analysis Agent combines multiple quantitative trading strategies to generate signals based on price action and market statistics. It uses an ensemble approach with weighted signals from five different methodologies.

## Core Strategies

### 1. Trend Following (25% weight)
**Rationale**: Markets trend about 30% of the time, and catching these trends early can generate significant returns. The multiple EMA approach identifies trends across different time horizons while ADX filters out weak trends that may reverse.

**Methodology**:
- Uses EMA crossovers (8/21/55 days) for trend direction
- ADX indicator (14-day) for trend strength
- Confirms with price position relative to EMAs

**Signals**:
- Bullish: EMAs in uptrend (8>21>55) with ADX > 25
- Bearish: EMAs in downtrend (8<21<55) with ADX > 25  
- Neutral: Mixed signals or weak trend (ADX < 25)

### 2. Mean Reversion (20% weight)  
**Rationale**: Prices tend to revert to mean values over time, especially in range-bound markets. The z-score approach identifies extreme moves likely to reverse, while Bollinger Bands provide visual confirmation levels.

**Methodology**:
- Z-score measures deviation from 50-day mean
- Bollinger Bands (20-day, 2σ) identify overbought/oversold levels
- RSI (14/28-day) confirms momentum extremes

**Signals**:
- Bullish: z-score < -2 (2σ below mean) and RSI < 30
- Bearish: z-score > 2 (2σ above mean) and RSI > 70
- Neutral: Between thresholds

### 3. Momentum (25% weight)
**Rationale**: Momentum tends to persist in the short-to-medium term. The multi-timeframe approach captures momentum at different scales while volume confirms institutional participation.

**Methodology**:  
- Price momentum across 1/3/6 month windows
- Volume momentum confirms with 21-day average
- Weighted combination favors shorter-term signals

**Signals**:
- Bullish: Strong positive momentum (>5%) with volume support
- Bearish: Strong negative momentum (<-5%) with volume support
- Neutral: Weak or conflicting momentum

### 4. Volatility Analysis (15% weight)
**Rationale**: Volatility tends to cluster and mean-revert. Identifying volatility regimes helps anticipate breakouts or consolidations.

**Methodology**:
- Historical volatility (21-day annualized)  
- Volatility ratio vs 63-day average
- ATR ratio for normalized volatility measure

**Signals**:
- Bullish: Low vol regime (ratio < 0.8) with z-score < -1
- Bearish: High vol regime (ratio > 1.2) with z-score > 1  
- Neutral: Normal volatility range

### 5. Statistical Arbitrage (15% weight)
**Rationale**: Markets exhibit different statistical properties that can indicate likely future behavior. This strategy combines multiple quantitative approaches:

1. **Hurst Exponent Analysis**:
   - Measures the tendency of prices to mean-revert or trend
   - H < 0.5: Mean-reverting series (likely to reverse)
   - H = 0.5: Random walk (no predictable pattern)
   - H > 0.5: Trending series (likely to continue)
   - Calculated using Rescaled Range (R/S) analysis:
     1. Takes logarithmically spaced time windows (10-100 days)
     2. For each window, calculates normalized range (R/S)
     3. Fits log(R/S) vs log(window size) to get slope (Hurst)
   - More robust than simple autocorrelation tests

2. **Distribution Analysis**:
   - Skewness detects asymmetric return distributions
     - Positive skew: More large positive returns
     - Negative skew: More large negative returns
   - Kurtosis measures tail risk (fat tails = higher risk)

**Educational Insight**:
- The Hurst exponent helps identify when traditional technical patterns may work better:
  - Mean-reverting strategies perform best when H < 0.4
  - Trend-following works best when H > 0.6
- Combined with skewness, it can detect potential reversals:
  - High positive skew + low H → Likely mean reversion downward
  - High negative skew + low H → Likely mean reversion upward

**Signals**:
- Bullish: 
  - Strong mean-reversion (H<0.4) 
  - Positive skew (>1) suggesting upside potential
- Bearish: 
  - Strong mean-reversion (H<0.4)
  - Negative skew (<-1) suggesting downside risk  
- Neutral: 
  - Random walk (H≈0.5) 
  - Or trending behavior (H>0.5)
  - Or insignificant skew

**Example Interpretation**:
- H=0.35, skew=1.2 → Strong bullish mean-reversion signal
- H=0.55, skew=0.3 → Neutral trending market
- H=0.4, skew=-1.5 → Strong bearish mean-reversion signal

## Signal Combination
The agent combines these strategies using their weights and confidence scores to generate a final signal. This ensemble approach:
- Reduces reliance on any single indicator
- Captures different market regimes  
- Provides more robust signals than individual strategies

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish", 
    "confidence": 82,
    "strategy_signals": {
      "trend_following": {
        "signal": "bullish",
        "confidence": 85,
        "metrics": {
          "adx": 32.5,
          "trend_strength": 0.85
        }
      },
      "mean_reversion": {
        "signal": "neutral", 
        "confidence": 50,
        "metrics": {
          "z_score": -1.2,
          "rsi_14": 45.3
        }
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
