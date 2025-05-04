# Valuation Agent Documentation

[Previous Valuation Agent content remains unchanged...]

# Fundamental Analysis Agent Documentation

[Previous Fundamental Analysis content remains unchanged...]

# Sentiment Agent Documentation

[Previous Sentiment Agent content remains unchanged...]

# Technical Analysis Agent Documentation

[Previous Technical Analysis content remains unchanged...]

# Warren Buffett Agent Documentation

[Previous Warren Buffett content remains unchanged...]

# Ben Graham Agent Documentation

## Overview
The Ben Graham Agent implements classic value investing principles focusing on:
- Earnings stability
- Financial strength
- Discount to intrinsic value
- Margin of safety

## Core Methodology

1. **Earnings Stability**:
   - Multiple years of positive EPS
   - EPS growth from first to last period
   - Scores based on consistency

2. **Financial Strength**:
   - Current ratio >= 2.0
   - Debt ratio < 0.5  
   - Dividend track record
   - Scores based on conservative metrics

3. **Valuation**:
   - Graham Number: sqrt(22.5 * EPS * Book Value)
   - Net-Net Current Asset Value
   - Scores based on margin of safety

## Signal Generation
1. Scores each category (0-5 points)
2. Calculates total score (max 15)
3. Determines signal:
   - Bullish: >=70% (10.5+)
   - Bearish: <=30% (4.5-)
   - Neutral: Between

## Example Output
```json
{
  "AAPL": {
    "signal": "bullish",
    "confidence": 85,
    "reasoning": {
      "earnings": "EPS positive all periods, growing 12%",
      "financials": "Current ratio 2.5, debt ratio 0.3",
      "valuation": "Graham Number $150 vs price $120 (25% margin)"
    }
  }
}
```

# Bill Ackman Agent Documentation

## Overview
The Bill Ackman Agent evaluates:
- Business quality
- Financial discipline  
- Activism potential
- Valuation with margin of safety

## Core Methodology

1. **Business Quality**:
   - Revenue growth acceleration
   - Operating margin consistency
   - R&D intensity

2. **Financial Discipline**:
   - Debt-to-equity trends  
   - Capital allocation
   - Share buybacks

3. **Activism Potential**:
   - Revenue growth vs margins
   - Operational improvements needed

4. **Valuation**:
   - DCF with conservative assumptions
   - Margin of safety calculation

## Signal Generation
1. Scores each category (0-5 points)
2. Total score (max 20)
3. Signal:
   - Bullish: >=70% (14+)
   - Bearish: <=30% (6-)
   - Neutral: Between

## Example Output
```json
{
  "TGT": {
    "signal": "bullish", 
    "confidence": 80,
    "reasoning": {
      "quality": "Strong brand, 15% revenue growth",
      "discipline": "Reduced debt, buying back shares",
      "activism": "Margin improvement potential",
      "valuation": "35% margin of safety"
    }
  }
}
```

# Cathie Wood Agent Documentation

## Overview
The Cathie Wood Agent focuses on:
- Disruptive innovation
- Exponential growth potential  
- Large TAM
- High R&D investment

## Core Methodology

1. **Disruptive Potential**:
   - Revenue growth acceleration
   - Gross margin expansion  
   - R&D intensity (>15% of revenue)

2. **Innovation Growth**:
   - R&D investment trends
   - Free cash flow generation
   - Operating efficiency

3. **Valuation**:
   - High-growth DCF model
   - 20% annual growth assumption
   - Large terminal multiple

## Signal Generation
1. Scores each category (0-5 points)
2. Total score (max 15)  
3. Signal:
   - Bullish: >=70% (10.5+)
   - Bearish: <=30% (4.5-)
   - Neutral: Between

## Example Output
```json
{
  "TSLA": {
    "signal": "bullish",
    "confidence": 90,
    "reasoning": {
      "disruption": "EV market leader, 50% revenue growth",
      "innovation": "25% R&D intensity, improving margins",
      "valuation": "Long-term growth potential not priced in"
    }
  }
}
```

[Additional agent sections for Charlie Munger, Michael Burry, Peter Lynch, Phil Fisher, and Stanley Druckenmiller would follow the same format...]
