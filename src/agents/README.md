# Hedge Fund AI Agents Documentation

## Table of Contents
1. [Valuation Agent](#valuation-agent-documentation)
2. [Fundamental Analysis Agent](#fundamental-analysis-agent-documentation)  
3. [Sentiment Agent](#sentiment-agent-documentation)
4. [Technical Analysis Agent](#technical-analysis-agent-documentation)
5. [Benjamin Graham Agent](#benjamin-graham-agent-documentation)
6. [Bill Ackman Agent](#bill-ackman-agent-documentation)
7. [Cathie Wood Agent](#cathie-wood-agent-documentation)
8. [Charlie Munger Agent](#charlie-munger-agent-documentation)
9. [Michael Burry Agent](#michael-burry-agent-documentation)
10. [Peter Lynch Agent](#peter-lynch-agent-documentation)
11. [Phil Fisher Agent](#phil-fisher-agent-documentation)
12. [Portfolio Manager Agent](#portfolio-manager-agent-documentation)
13. [Risk Manager Agent](#risk-manager-agent-documentation)
14. [Stanley Druckenmiller Agent](#stanley-druckenmiller-agent-documentation)
15. [Warren Buffett Agent](#warren-buffett-agent-documentation)

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
```

## Technical Analysis Agent Documentation

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

# Benjamin Graham Agent Documentation

## Historical Context
Benjamin Graham (1894-1976) is considered the "father of value investing" and authored the seminal book "The Intelligent Investor." He pioneered quantitative security analysis and emphasized buying stocks trading below their intrinsic value with a margin of safety. His approach focuses strictly on valuation metrics rather than qualitative factors.

## Investment Style
- **Primary Focus**: Deep value investing (quantitative valuation)
- **Secondary Focus**: Fundamental analysis (financial strength)
- **Ignores**: Technical analysis and market sentiment
- **Key Principle**: Margin of safety - only buy when price is significantly below calculated intrinsic value

## Overview
The Benjamin Graham Agent implements the classic value investing principles of Benjamin Graham, focusing on:
1. Earnings stability over multiple years
2. Solid financial strength (low debt, adequate liquidity)
3. Discount to intrinsic value (Graham Number or net-net)
4. Adequate margin of safety

## Core Methodology

### 1. Earnings Stability Analysis (Max 5 points)
- **Positive EPS Years**: Points for consecutive years of positive earnings
- **EPS Growth**: Points for growth from earliest to latest period
- **Scoring**:
  - 3 points if EPS positive in all available periods
  - 2 points if EPS positive in ≥80% of periods
  - 1 point if EPS grew from earliest to latest period

### 2. Financial Strength Analysis (Max 5 points)
- **Current Ratio**: Points for liquidity (current assets vs liabilities)
  - 2 points if ratio ≥2.0
  - 1 point if ratio ≥1.5
- **Debt Ratio**: Points for conservative leverage
  - 2 points if debt/assets <0.5
  - 1 point if debt/assets <0.8
- **Dividend Record**: 1 point if company paid dividends in majority of years

### 3. Valuation Analysis (Max 5 points)
- **Net-Net Working Capital**: 
  - 4 points if NCAV > Market Cap (deep value)
  - 2 points if NCAV per share ≥2/3 of price
- **Graham Number**:
  - 3 points if price has ≥50% margin below Graham Number
  - 1 point if some margin of safety exists

### Scoring Summary
- Maximum possible score: 15 points
- Signal thresholds:
  - Bullish: ≥70% of max score (≥10.5 points)
  - Bearish: ≤30% of max score (≤4.5 points)
  - Neutral: Between 4.5-10.5 points

## Key Metrics
- **Net Current Asset Value (NCAV)**:
  ``` 
  NCAV = Current Assets - Total Liabilities
  ```
- **Graham Number**:
  ```
  Graham Number = √(22.5 × EPS × Book Value per Share)
  ```
- **Current Ratio**:
  ```
  Current Ratio = Current Assets / Current Liabilities
  ```
- **Debt Ratio**:
  ```
  Debt Ratio = Total Liabilities / Total Assets
  ```

## Signal Generation Process
1. For each ticker:
   - Fetch financial metrics and line items
   - Calculate earnings stability score
   - Calculate financial strength score
   - Calculate valuation score
   - Sum scores and determine signal based on thresholds
   - Generate detailed reasoning using LLM in Graham's style

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the quantitative analysis into Graham-style reasoning:
- Explains key valuation metrics (Graham Number, NCAV)
- Highlights financial strength indicators
- References earnings stability
- Provides quantitative evidence
- Uses Graham's conservative, analytical voice

Example prompt:
```
"You are a Benjamin Graham AI agent, making investment decisions using his principles:
1. Insist on margin of safety by buying below intrinsic value
2. Emphasize financial strength (low leverage, ample current assets)
3. Prefer stable earnings over multiple years
4. Avoid speculative assumptions; focus on proven metrics

Format this analysis as a Graham-style recommendation:
{analysis_data}"
```

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 82,
    "reasoning": {
      "earnings_analysis": {
        "score": 4,
        "details": "EPS positive in all 10 periods, grew from $1.42 to $6.11"
      },
      "financial_strength": {
        "score": 4,
        "details": "Current ratio: 2.3, Debt ratio: 0.42, Paid dividends 8/10 years"
      },
      "valuation": {
        "score": 4,
        "details": "NCAV/share: $45.20 (67% of price), Graham Number: $125.40 (35% above current price)"
      }
    }
  }
}
```

# Bill Ackman Agent Documentation

## Historical Context
Bill Ackman (b. 1966) is a prominent activist investor and founder of Pershing Square Capital Management. Known for high-profile activist campaigns (e.g., Herbalife short), he focuses on high-quality businesses where operational improvements or activism can unlock value. His style blends deep fundamental analysis with activist positioning.

## Investment Style  
- **Primary Focus**: Fundamental analysis (business quality)
- **Secondary Focus**: Valuation (DCF models) and activism potential
- **Uses Selectively**: Market sentiment for timing activist campaigns
- **Ignores**: Technical analysis
- **Key Principle**: Invest in simple, predictable, free cash flow generative businesses

## Overview
The Bill Ackman Agent implements the investment principles of activist investor Bill Ackman, focusing on:
1. High-quality businesses with durable competitive advantages
2. Consistent free cash flow and growth potential
3. Financial discipline and capital allocation
4. Valuation with margin of safety
5. Activism potential where improvements can unlock value

## Core Methodology

### 1. Business Quality Analysis (Max 5 points)
- **Revenue Growth**: Points for multi-period growth trends
- **Operating Margins**: Points for consistent profitability
- **Free Cash Flow**: Points for positive cash generation
- **Return on Equity**: Points for high ROE indicating moat

### 2. Financial Discipline Analysis (Max 5 points)
- **Debt Levels**: Points for reasonable leverage
- **Capital Returns**: Points for dividends/buybacks
- **Share Count**: Points for decreasing shares (buybacks)

### 3. Activism Potential Analysis (Max 2 points)
- **Revenue vs Margins**: Points for growth with subpar margins
- **Operational Upside**: Identifies potential improvements

### 4. Valuation Analysis (Max 8 points)
- **DCF Valuation**: Discounted cash flow analysis
- **Margin of Safety**: Points for significant undervaluation

### Scoring Summary
- Maximum possible score: 20 points
- Signal thresholds:
  - Bullish: ≥70% of max score (≥14 points)
  - Bearish: ≤30% of max score (≤6 points)
  - Neutral: Between 6-14 points

## Key Metrics
- **Free Cash Flow**: 
  ```
  FCF = Operating Cash Flow - Capital Expenditures
  ```
- **Debt-to-Equity**:
  ```
  Debt/Equity = Total Liabilities / Shareholders' Equity
  ```
- **Intrinsic Value**:
  ```
  DCF = Σ(FCF projections) + Terminal Value
  ```
- **Margin of Safety**:
  ```
  MOS = (Intrinsic Value - Market Cap) / Market Cap
  ```

## Signal Generation Process
1. For each ticker:
   - Fetch financial metrics and line items
   - Calculate business quality score
   - Calculate financial discipline score
   - Assess activism potential
   - Perform DCF valuation
   - Sum scores and determine signal based on thresholds
   - Generate detailed reasoning using LLM in Ackman's style

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the quantitative analysis into Ackman-style reasoning:
- Emphasizes brand strength and competitive advantages
- Reviews cash flow and margin trends
- Analyzes capital allocation decisions
- Provides valuation assessment with numbers
- Identifies activism catalysts
- Uses confident, analytical tone

Example prompt:
```
"You are a Bill Ackman AI agent, making investment decisions using his principles:
1. Seek high-quality businesses with durable moats
2. Prioritize consistent free cash flow
3. Advocate financial discipline
4. Target intrinsic value with margin of safety
5. Consider activism potential
6. Concentrate on high-conviction investments

Format this analysis as an Ackman-style recommendation:
{analysis_data}"
```

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 85,
    "reasoning": {
      "quality_analysis": {
        "score": 4,
        "details": "Strong brand, 18% revenue growth, 25% operating margins"
      },
      "financial_discipline": {
        "score": 4,
        "details": "Debt/equity 0.8, $50B in buybacks last 5 years"
      },
      "activism": {
        "score": 1,
        "details": "Limited upside from activism (already well-run)"
      },
      "valuation": {
        "score": 6,
        "details": "DCF value $2.5T vs $2.1T market cap (19% margin)"
      }
    }
  }
}
```

# Cathie Wood Agent Documentation

## Historical Context
Cathie Wood (b. 1955) is the founder and CEO of ARK Invest, known for her focus on disruptive innovation and high-growth technology companies. She pioneered thematic investing in areas like genomics, AI, fintech, and blockchain. Her investment style embraces volatility and focuses on long-term exponential growth potential rather than short-term profitability.

## Investment Style
- **Primary Focus**: Disruptive innovation and exponential growth potential
- **Secondary Focus**: Technology adoption curves and total addressable market (TAM)
- **Uses Selectively**: Market sentiment for entry/exit timing
- **Ignores**: Traditional valuation metrics in favor of long-term growth potential
- **Key Principle**: Invest in companies that can change the world, not just incrementally improve existing industries

## Overview
The Cathie Wood Agent implements her investment philosophy focusing on:
1. Disruptive technologies with exponential growth potential
2. Companies positioned to benefit from technological convergence
3. High R&D investment and innovation pipelines
4. Large total addressable markets (TAM)
5. Willingness to endure short-term volatility for long-term gains

## Core Methodology

### 1. Disruptive Potential Analysis (Max 5 points)
- **Revenue Growth Acceleration**: Points for increasing growth rates
- **Gross Margin Expansion**: Points for improving profitability
- **Operating Leverage**: Points for revenue growing faster than expenses
- **R&D Intensity**: Points for high innovation investment

### 2. Innovation Growth Analysis (Max 5 points)
- **R&D Growth**: Points for increasing research investment
- **Free Cash Flow**: Points for funding innovation capacity  
- **Operating Efficiency**: Points for scalable business models
- **Capital Allocation**: Points for growth-focused spending
- **Reinvestment Rate**: Points for prioritizing growth over dividends

### 3. Exponential Valuation (Max 5 points)
- **High-Growth DCF**: Uses aggressive growth assumptions (20%+)
- **TAM Analysis**: Evaluates market expansion potential
- **Margin of Safety**: Adjusted for growth potential

### Scoring Summary
- Maximum possible score: 15 points
- Signal thresholds:
  - Bullish: ≥70% of max score (≥10.5 points)
  - Bearish: ≤30% of max score (≤4.5 points)  
  - Neutral: Between 4.5-10.5 points

## Key Metrics
- **Exponential Growth Potential**:
  ```
  Growth Score = (Recent Growth Rate / Long-term Growth Rate) * Adoption Curve Factor
  ```
- **Innovation Intensity**:
  ```
  R&D Intensity = R&D Expense / Revenue
  ```
- **Disruptive Valuation**:
  ```
  High-Growth DCF = Σ(FCF * (1+g)^n) + (FCF * (1+g)^n * Terminal Multiple)
  ```

## Signal Generation Process
1. For each ticker:
   - Analyze disruptive potential metrics
   - Evaluate innovation growth factors
   - Calculate exponential valuation
   - Sum scores and determine signal
   - Generate detailed reasoning using LLM in Wood's style

2. Final signal combines:
   - Quantitative scoring (60% weight)
   - Qualitative LLM assessment (40% weight)

## LLM Interaction
The LLM formats the analysis into Wood-style reasoning:
- Identifies specific disruptive technologies
- Highlights exponential growth metrics
- Discusses long-term vision and TAM
- Explains industry disruption potential
- Reviews innovation pipeline
- Uses Wood's optimistic, conviction-driven voice

Example prompt:
```
"You are a Cathie Wood AI agent analyzing {ticker}:
1. What disruptive technologies is the company leveraging?
2. What evidence shows exponential growth potential?  
3. How large is the total addressable market?
4. What innovation pipeline could drive future growth?
5. Format as a Wood-style recommendation with signal and confidence."
```

## Output Example
```json
{
  "TSLA": {
    "signal": "bullish",
    "confidence": 90,
    "reasoning": {
      "disruptive_analysis": {
        "score": 4.5,
        "details": "AI and battery tech leadership, 65% revenue growth acceleration"
      },
      "innovation_analysis": {
        "score": 4.8, 
        "details": "R&D at 18% of revenue, expanding into robotics and energy"
      },
      "valuation": {
        "score": 4.2,
        "details": "$1.2T TAM in EVs/energy, trading at 50% discount to 2028 DCF"
      }
    }
  }
}
```

# Peter Lynch Agent Documentation

## Historical Context
Peter Lynch (b. 1944) managed Fidelity's Magellan Fund from 1977-1990, achieving a 29% annual return. He popularized the "invest in what you know" philosophy and Growth at a Reasonable Price (GARP) investing. His books "One Up On Wall Street" and "Beating the Street" outline his approach of finding "ten-baggers" (stocks that grow 10x) through fundamental analysis of understandable businesses.

## Investment Style
- **Primary Focus**: Growth at a Reasonable Price (PEG ratio)
- **Secondary Focus**: Understandable businesses with steady growth
- **Uses Selectively**: Insider activity and sentiment analysis
- **Ignores**: Overly complex or highly leveraged businesses
- **Key Principle**: "Invest in what you know" - find great companies in everyday life

## Overview
The Peter Lynch Agent implements his GARP investment philosophy focusing on:
1. Consistent revenue and EPS growth
2. Reasonable valuation (especially PEG ratio)
3. Strong fundamentals (margins, cash flow, low debt)
4. Positive insider activity
5. Understandable business models with growth potential

## Core Methodology

### 1. Growth Analysis (30% weight)
- **Revenue Growth**: 
  - 3 points if >25% growth
  - 2 points if >10% growth
  - 1 point if >2% growth
- **EPS Growth**:
  - 3 points if >25% growth
  - 2 points if >10% growth
  - 1 point if >2% growth
- Maximum score: 6 points (scaled to 10)

### 2. Valuation Analysis (25% weight)
- **PEG Ratio**:
  - 3 points if PEG <1
  - 2 points if PEG <2
  - 1 point if PEG <3
- **P/E Ratio**:
  - 2 points if P/E <15
  - 1 point if P/E <25
- Maximum score: 5 points (scaled to 10)

### 3. Fundamentals Analysis (20% weight)
- **Debt/Equity**:
  - 2 points if <0.5
  - 1 point if <1.0
- **Operating Margin**:
  - 2 points if >20%
  - 1 point if >10%
- **Free Cash Flow**:
  - 2 points if positive
- Maximum score: 6 points (scaled to 10)

### 4. Sentiment Analysis (15% weight)
- **News Sentiment**:
  - 8 points if mostly positive
  - 6 points if some negative
  - 3 points if >30% negative
- Maximum score: 8 points (scaled to 10)

### 5. Insider Activity (10% weight)
- **Insider Trading**:
  - 8 points if heavy buying (>70% buys)
  - 6 points if some buying (>40% buys)
  - 4 points if mostly selling
- Maximum score: 8 points (scaled to 10)

### Scoring Summary
- Maximum possible score: 10 points
- Signal thresholds:
  - Bullish: ≥7.5 points
  - Bearish: ≤4.5 points
  - Neutral: Between 4.5-7.5 points

## Key Metrics
- **PEG Ratio**:
  ```
  PEG = (P/E Ratio) / (EPS Growth Rate × 100)
  ```
- **Revenue Growth**:
  ```
  Growth = (Current Revenue - Prior Revenue) / Prior Revenue
  ```
- **Debt-to-Equity**:
  ```
  D/E = Total Debt / Shareholders' Equity
  ```
- **Operating Margin**:
  ```
  Margin = Operating Income / Revenue
  ```

## Signal Generation Process
1. For each ticker:
   - Calculate growth metrics (revenue, EPS)
   - Compute valuation ratios (PEG, P/E)
   - Assess fundamentals (debt, margins, cash flow)
   - Analyze sentiment and insider activity
   - Apply weights and sum scores
   - Generate detailed reasoning using LLM in Lynch's voice

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the analysis into Lynch's folksy, practical style:
- References PEG ratio prominently
- Mentions "ten-bagger" potential if applicable
- Uses everyday analogies ("If my kids love this product...")
- Highlights key positives and negatives
- Concludes with clear stance
- Maintains Lynch's conversational tone

Example prompt:
```
"You are Peter Lynch analyzing {ticker}:
1. What's the PEG ratio and what does it tell us?
2. Is this an understandable business with steady growth?
3. Any 'ten-bagger' potential here?
4. What would I observe about this company in daily life?
5. Format as a Lynch-style recommendation with signal and confidence."
```

## Output Example
```json
{
  "COST": {
    "signal": "bullish",
    "confidence": 85,
    "reasoning": {
      "growth_analysis": {
        "score": 8,
        "details": "Revenue growth 12%, EPS growth 15% - steady as she goes"
      },
      "valuation": {
        "score": 7, 
        "details": "PEG 0.9 - classic GARP opportunity"
      },
      "fundamentals": {
        "score": 9,
        "details": "Debt/equity 0.4, operating margin 18%, strong FCF"
      },
      "sentiment": {
        "score": 8,
        "details": "Members love the stores - my wife shops there weekly"
      },
      "insider": {
        "score": 7,
        "details": "Executives buying shares - they know the business best"
      }
    }
  }
}
```

# Phil Fisher Agent Documentation

## Historical Context
Philip Fisher (1907-2004) was an influential growth investor and author of "Common Stocks and Uncommon Profits." He pioneered the concept of investing in high-quality growth companies with sustainable competitive advantages. His "scuttlebutt" method emphasized deep fundamental research through management interviews, customer feedback, and industry analysis.

## Investment Style
- **Primary Focus**: Long-term growth potential and management quality
- **Secondary Focus**: R&D investment and product pipeline
- **Uses Selectively**: Insider activity and sentiment analysis
- **Ignores**: Short-term market fluctuations and technical indicators
- **Key Principle**: "Buy the best companies and hold them forever"

## Overview
The Phil Fisher Agent implements his growth investing philosophy focusing on:
1. Long-term above-average growth potential
2. Quality of management and R&D investment
3. Strong and consistent margins
4. Reasonable valuation for quality
5. Insider activity as a management signal

## Core Methodology

### 1. Growth & Quality Analysis (30% weight)
- **Revenue Growth**:
  - 3 points if >80% multi-period growth
  - 2 points if >40% growth
  - 1 point if >10% growth
- **EPS Growth**:
  - 3 points if >80% multi-period growth
  - 2 points if >40% growth
  - 1 point if >10% growth
- **R&D Investment**:
  - 3 points if 3-15% of revenue
  - 2 points if >15% of revenue
  - 1 point if positive but <3%
- Maximum score: 9 points (scaled to 10)

### 2. Margins & Stability (25% weight)
- **Operating Margin**:
  - 2 points if stable/improving
  - 1 point if positive but declining
- **Gross Margin**:
  - 2 points if >50%
  - 1 point if >30%
- **Margin Stability**:
  - 2 points if extremely stable (stdev <2%)
  - 1 point if reasonably stable (stdev <5%)
- Maximum score: 6 points (scaled to 10)

### 3. Management Efficiency (20% weight)
- **ROE**:
  - 3 points if >20%
  - 2 points if >10%
  - 1 point if positive
- **Debt/Equity**:
  - 2 points if <0.3
  - 1 point if <1.0
- **FCF Consistency**:
  - 1 point if mostly positive
- Maximum score: 6 points (scaled to 10)

### 4. Valuation (15% weight)
- **P/E Ratio**:
  - 2 points if <20
  - 1 point if <30
- **P/FCF Ratio**:
  - 2 points if <20
  - 1 point if <30
- Maximum score: 4 points (scaled to 10)

### 5. Insider Activity (5% weight)
- **Insider Trading**:
  - 8 points if heavy buying (>70% buys)
  - 6 points if some buying (>40% buys)
  - 4 points if mostly selling
- Maximum score: 8 points (scaled to 10)

### 6. Sentiment (5% weight)
- **News Sentiment**:
  - 8 points if mostly positive
  - 6 points if some negative
  - 3 points if >30% negative
- Maximum score: 8 points (scaled to 10)

### Scoring Summary
- Maximum possible score: 10 points
- Signal thresholds:
  - Bullish: ≥7.5 points
  - Bearish: ≤4.5 points
  - Neutral: Between 4.5-7.5 points

## Key Metrics
- **R&D Ratio**:
  ```
  R&D Ratio = R&D Expense / Revenue
  ```
- **Margin Stability**:
  ```
  Stdev = Standard deviation of operating margins
  ```
- **Return on Equity**:
  ```
  ROE = Net Income / Shareholders' Equity
  ```
- **Debt-to-Equity**:
  ```
  D/E = Total Debt / Shareholders' Equity
  ```

## Signal Generation Process
1. For each ticker:
   - Calculate growth and quality metrics
   - Analyze margin stability
   - Evaluate management efficiency
   - Assess valuation
   - Review insider activity and sentiment
   - Apply weights and sum scores
   - Generate detailed reasoning using LLM in Fisher's style

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the analysis into Fisher's thorough, research-driven style:
- Emphasizes long-term growth potential
- Details R&D investments and product pipeline
- Analyzes management quality and capital allocation
- Uses Fisher's methodical, growth-focused voice
- Provides specific metrics and trends
- Maintains long-term investment horizon

Example prompt:
```
"You are Phil Fisher analyzing {ticker}:
1. What are the company's long-term growth prospects?
2. How does management quality measure up?
3. What R&D investments could drive future growth?
4. Are margins stable and at appropriate levels?
5. Format as a Fisher-style recommendation with signal and confidence."
```

## Output Example
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 88,
    "reasoning": {
      "growth_analysis": {
        "score": 9,
        "details": "Revenue growth 85% over 5 years, R&D at 7% of revenue funding AR/VR pipeline"
      },
      "margins": {
        "score": 8,
        "details": "Operating margins stable at 28-30%, gross margins 42%"
      },
      "management": {
        "score": 9,
        "details": "ROE 35%, debt/equity 0.25, consistent FCF generation"
      },
      "valuation": {
        "score": 7,
        "details": "P/E 28 justified by growth, P/FCF 22 reasonable for quality"
      }
    }
  }
}
```

# Michael Burry Agent Documentation

## Historical Context
Michael Burry (b. 1971) is a physician-turned-investor famous for predicting and profiting from the 2008 financial crisis. Founder of Scion Asset Management, he specializes in deep-value investing with a contrarian approach. His strategy focuses on identifying fundamentally sound but deeply undervalued companies, often those facing temporary headwinds or market overreactions.

## Investment Style
- **Primary Focus**: Deep value metrics (FCF yield, EV/EBIT)
- **Secondary Focus**: Balance sheet strength and insider activity
- **Uses Selectively**: Contrarian sentiment analysis
- **Ignores**: Short-term technical indicators and market momentum
- **Key Principle**: "The more hated the investment, the better the potential returns if the fundamentals hold up"

## Overview
The Michael Burry Agent implements his deep-value, contrarian investment philosophy focusing on:
1. Exceptional free cash flow yields
2. Low EV/EBIT multiples
3. Strong balance sheets with low leverage
4. Insider buying as a catalyst
5. Contrarian opportunities from negative sentiment

## Core Methodology

### 1. Value Analysis (Max 6 points)
- **FCF Yield**: Points for high cash flow returns
  - 4 points if yield ≥15%
  - 3 points if yield ≥12%
  - 2 points if yield ≥8%
- **EV/EBIT**: Points for low enterprise multiples
  - 2 points if multiple <6
  - 1 point if multiple <10

### 2. Balance Sheet Analysis (Max 3 points)
- **Debt/Equity**: Points for low leverage
  - 2 points if ratio <0.5
  - 1 point if ratio <1.0
- **Net Cash Position**: 1 point if cash > total debt

### 3. Insider Activity (Max 2 points)
- **Net Buying**: Points for significant insider purchases
  - 2 points if net buying > shares sold
  - 1 point if some net buying

### 4. Contrarian Sentiment (Max 1 point)
- **Negative News**: 1 point if ≥5 negative headlines (contrarian opportunity)

### Scoring Summary
- Maximum possible score: 12 points
- Signal thresholds:
  - Bullish: ≥70% of max score (≥8.4 points)
  - Bearish: ≤30% of max score (≤3.6 points)
  - Neutral: Between 3.6-8.4 points

## Key Metrics
- **Free Cash Flow Yield**:
  ```
  FCF Yield = Free Cash Flow / Market Cap
  ```
- **EV/EBIT**:
  ```
  EV/EBIT = Enterprise Value / Earnings Before Interest & Taxes
  ```
- **Debt-to-Equity**:
  ```
  D/E = Total Liabilities / Shareholders' Equity
  ```
- **Net Insider Activity**:
  ```
  Net Buying = Shares Bought - Shares Sold
  ```

## Signal Generation Process
1. For each ticker:
   - Calculate value metrics (FCF yield, EV/EBIT)
   - Analyze balance sheet strength
   - Evaluate insider trading activity
   - Assess contrarian sentiment from news
   - Sum scores and determine signal
   - Generate detailed reasoning using LLM in Burry's style

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the analysis into Burry's terse, data-driven style:
- Leads with key metrics and concrete numbers
- Highlights risk factors and catalysts
- References insider activity and sentiment
- Uses Burry's direct, minimalist communication
- Focuses on downside protection first

Example prompt:
```
"You are Michael Burry analyzing {ticker}:
1. What are the key value metrics?
2. What are the biggest risks?
3. Any insider activity or sentiment catalysts?
4. Format as a Burry-style recommendation with signal and confidence."
```

## Output Example
```json
{
  "BBBY": {
    "signal": "bullish",
    "confidence": 85,
    "reasoning": {
      "value_analysis": {
        "score": 5,
        "details": "FCF yield 14.2%. EV/EBIT 5.8."
      },
      "balance_sheet": {
        "score": 2,
        "details": "D/E 0.4. Net cash position."
      },
      "insider_activity": {
        "score": 2,
        "details": "Net insider buying 42k shares."
      },
      "contrarian": {
        "score": 1,
        "details": "8 negative headlines (overdone fear)."
      }
    }
  }
}
```

# Charlie Munger Agent Documentation

## Historical Context
Charlie Munger (1924-2023) was Warren Buffett's longtime partner at Berkshire Hathaway and a legendary investor in his own right. Known for his multidisciplinary approach and mental models, Munger emphasized investing in high-quality businesses with durable competitive advantages at reasonable prices. His philosophy focuses on avoiding mistakes rather than seeking brilliance.

## Investment Style
- **Primary Focus**: Business quality and predictability
- **Secondary Focus**: Management quality and capital allocation
- **Uses Selectively**: Insider activity as management signal
- **Ignores**: Short-term market sentiment and technical analysis
- **Key Principle**: "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price"

## Overview
The Charlie Munger Agent implements his investment philosophy focusing on:
1. Durable competitive advantages (economic moats)
2. High returns on invested capital (ROIC)
3. Predictable business operations
4. Shareholder-friendly management
5. Reasonable valuation with margin of safety

## Core Methodology

### 1. Moat Strength Analysis (Max 10 points)
- **ROIC Consistency**: Points for sustained high returns (>15%)
- **Pricing Power**: Points for stable/improving gross margins
- **Capital Efficiency**: Points for low capital requirements
- **Intangible Assets**: Points for R&D and intellectual property

### 2. Management Quality Analysis (Max 10 points)
- **Capital Allocation**: Points for cash conversion and debt management
- **Insider Activity**: Points for buying vs selling
- **Share Count**: Points for stable/decreasing shares
- **Cash Management**: Points for prudent cash levels

### 3. Business Predictability (Max 10 points)
- **Revenue Stability**: Points for consistent growth patterns
- **Earnings Consistency**: Points for positive operating income
- **Margin Stability**: Points for low margin volatility
- **Cash Flow Reliability**: Points for consistent FCF

### 4. Valuation Analysis (Max 10 points)
- **FCF Yield**: Points for attractive normalized yields
- **Margin of Safety**: Points for upside to reasonable value
- **Earnings Trend**: Points for growing owner earnings

### Scoring Summary
- Maximum possible score: 40 points (weighted to 10)
- Signal thresholds:
  - Bullish: ≥70% of max score (≥28 points)
  - Bearish: ≤30% of max score (≤12 points)
  - Neutral: Between 12-28 points

## Key Metrics
- **Return on Invested Capital**:
  ```
  ROIC = Net Operating Profit After Tax / Invested Capital
  ```
- **Owner Earnings**:
  ```
  Owner Earnings = Net Income + Depreciation - Maintenance Capex
  ```
- **Margin of Safety**:
  ```
  MOS = (Intrinsic Value - Market Price) / Market Price
  ```
- **Capital Efficiency**:
  ```
  Capex/Revenue = Capital Expenditures / Revenue
  ```

## Signal Generation Process
1. For each ticker:
   - Analyze moat strength metrics
   - Evaluate management quality factors
   - Assess business predictability
   - Calculate Munger-style valuation
   - Sum weighted scores and determine signal
   - Generate detailed reasoning using LLM with Munger's mental models

2. Final signal combines:
   - Quantitative scoring (60% weight)
   - Qualitative LLM assessment (40% weight)

## LLM Interaction
The LLM formats the analysis into Munger-style reasoning:
- Applies mental models from multiple disciplines
- Focuses on avoiding mistakes (inversion)
- Emphasizes long-term business quality
- Uses Munger's direct, pithy style
- References specific principles and quotes

Example prompt:
```
"You are a Charlie Munger AI agent analyzing {ticker}:
1. What mental models best explain this business?
2. What are the biggest risks to avoid? 
3. How does management measure up?
4. Is the price right for the quality?
5. Format as a Munger-style recommendation."
```

## Output Example
```json
{
  "COST": {
    "signal": "bullish",
    "confidence": 85,
    "reasoning": {
      "moat_analysis": {
        "score": 9,
        "details": "Exceptional ROIC (22%), pricing power (gross margins 13% and rising)"
      },
      "management_analysis": {
        "score": 8, 
        "details": "Skin in the game (insiders net buyers), prudent capital allocation"
      },
      "predictability": {
        "score": 9,
        "details": "Revenue growth 8% with <5% volatility, consistent FCF"
      },
      "valuation": {
        "score": 7,
        "details": "Fair price at 6% FCF yield, 15% margin of safety"
      }
    }
  }
}
```

# Stanley Druckenmiller Agent Documentation

## Historical Context
Stanley Druckenmiller (b. 1953) is a legendary hedge fund manager who achieved 30%+ annual returns over 30 years. He managed money for George Soros and was famous for his aggressive but disciplined approach. His philosophy focuses on asymmetric risk-reward opportunities, capital preservation, and riding strong trends.

## Investment Style
- **Primary Focus**: Asymmetric risk-reward opportunities
- **Secondary Focus**: Growth, momentum and sentiment analysis
- **Uses Selectively**: Insider activity as confirmation
- **Ignores**: Traditional valuation metrics when growth justifies
- **Key Principle**: "It's not whether you're right or wrong that's important, but how much money you make when you're right and how much you lose when you're wrong"

## Overview
The Stanley Druckenmiller Agent implements his investment philosophy focusing on:
1. Identifying asymmetric risk-reward setups
2. Strong growth and momentum characteristics
3. Favorable market sentiment
4. Insider activity confirmation
5. Willingness to be aggressive when conditions are right

## Core Methodology

### 1. Growth & Momentum Analysis (35% weight)
- **Revenue Growth**:
  - 3 points if >30% growth
  - 2 points if >15% growth
  - 1 point if >5% growth
- **EPS Growth**:
  - 3 points if >30% growth
  - 2 points if >15% growth
  - 1 point if >5% growth
- **Price Momentum**:
  - 3 points if >50% price increase
  - 2 points if >20% increase
  - 1 point if positive
- Maximum score: 9 points (scaled to 10)

### 2. Risk-Reward Analysis (20% weight)
- **Debt-to-Equity**:
  - 3 points if <0.3
  - 2 points if <0.7
  - 1 point if <1.5
- **Price Volatility**:
  - 3 points if very low volatility
  - 2 points if moderate volatility
  - 1 point if high volatility
- Maximum score: 6 points (scaled to 10)

### 3. Valuation Analysis (20% weight)
- **P/E Ratio**:
  - 2 points if <15
  - 1 point if <25
- **P/FCF Ratio**:
  - 2 points if <15
  - 1 point if <25
- **EV/EBIT**:
  - 2 points if <15
  - 1 point if <25
- **EV/EBITDA**:
  - 2 points if <10
  - 1 point if <18
- Maximum score: 8 points (scaled to 10)

### 4. Sentiment Analysis (15% weight)
- **News Sentiment**:
  - 8 points if mostly positive
  - 6 points if some negative
  - 3 points if >30% negative
- Maximum score: 8 points (scaled to 10)

### 5. Insider Activity (10% weight)
- **Insider Trading**:
  - 8 points if heavy buying (>70% buys)
  - 6 points if some buying (>40% buys)
  - 4 points if mostly selling
- Maximum score: 8 points (scaled to 10)

### Scoring Summary
- Maximum possible score: 10 points
- Signal thresholds:
  - Bullish: ≥7.5 points
  - Bearish: ≤4.5 points
  - Neutral: Between 4.5-7.5 points

## Key Metrics
- **Asymmetric Risk-Reward**:
  ```
  Upside Potential / Downside Risk > 3:1
  ```
- **Growth-Adjusted Valuation**:
  ```
  PEG Ratio = P/E / (EPS Growth × 100)
  ```
- **Momentum Strength**:
  ```
  Price Change % over 3 months
  ```
- **Volatility**:
  ```
  Standard Deviation of Daily Returns
  ```

## Signal Generation Process
1. For each ticker:
   - Calculate growth and momentum metrics
   - Assess risk-reward profile
   - Evaluate valuation relative to growth
   - Analyze sentiment and insider activity
   - Apply weights and sum scores
   - Generate detailed reasoning using LLM in Druckenmiller's style

2. Final signal combines:
   - Quantitative scoring (70% weight)
   - Qualitative LLM assessment (30% weight)

## LLM Interaction
The LLM formats the analysis into Druckenmiller's decisive, conviction-driven style:
- Emphasizes asymmetric risk-reward opportunities
- Highlights growth momentum and catalysts
- Discusses capital preservation considerations
- Uses Druckenmiller's aggressive but disciplined voice
- Provides specific upside/downside estimates
- Maintains focus on position sizing and risk management

Example prompt:
```
"You are Stanley Druckenmiller analyzing {ticker}:
1. What is the asymmetric risk-reward setup?
2. How strong are the growth and momentum characteristics?
3. What sentiment and insider signals confirm the thesis?
4. Format as a Druckenmiller-style recommendation with signal and confidence."
```

## Output Example
```json
{
  "NVDA": {
    "signal": "bullish",
    "confidence": 92,
    "reasoning": {
      "growth_momentum": {
        "score": 9,
        "details": "Revenue growth 65%, EPS growth 82%, stock up 120% YTD"
      },
      "risk_reward": {
        "score": 8,
        "details": "3:1 upside/downside ratio, low volatility given growth"
      },
      "valuation": {
        "score": 7,
        "details": "PEG 1.2 reasonable for growth, EV/EBITDA 25 stretched but justified"
      },
      "sentiment": {
        "score": 9,
        "details": "Overwhelmingly positive sentiment on AI leadership"
      }
    }
  }
}
```

# Warren Buffett Agent Documentation

## Historical Context
Warren Buffett (b. 1930) is chairman of Berkshire Hathaway and one of the most successful investors of all time. He evolved from pure Graham-style value investing to focus more on business quality under Charlie Munger's influence. His approach combines quantitative valuation with qualitative assessment of competitive advantages.

## Investment Style
- **Primary Focus**: Fundamental analysis (economic moats)
- **Secondary Focus**: Valuation (owner earnings)
- **Uses Selectively**: Management quality assessment  
- **Ignores**: Technical analysis and short-term sentiment
- **Key Principle**: Buy wonderful businesses at fair prices rather than fair businesses at wonderful prices

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
