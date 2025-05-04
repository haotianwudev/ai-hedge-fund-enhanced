# Hedge Fund AI Agents Documentation

## Table of Contents
1. [Valuation Agent](#valuation-agent-documentation)
2. [Fundamental Analysis Agent](#fundamental-analysis-agent-documentation)  
3. [Sentiment Agent](#sentiment-agent-documentation)
4. [Technical Analysis Agent](#technical-analysis-agent-documentation)
5. [Benjamin Graham Agent](#benjamin-graham-agent-documentation)
6. [Bill Ackman Agent](#bill-ackman-agent-documentation)
7. [Cathie Wood Agent](#cathie-wood-agent-documentation)
8. [Warren Buffett Agent](#warren-buffett-agent-documentation)

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
