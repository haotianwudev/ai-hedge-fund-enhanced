# Example Session: DCF Valuation Analysis for AAPL (with Actual Numbers)

## Step 1: Gather Inputs (as of 2025-03-29)

- **free_cash_flow**: $98,486,000,000
- **growth_rate**: 0.0119 (1.19% annual, from recent earnings growth)
- **discount_rate**: 0.10 (10% required return, default)
- **terminal_growth_rate**: 0.03 (3% perpetual growth, default)
- **num_years**: 5 (default projection period)
- **market_cap**: $3,155,342,600,760 (from company_facts table)

## Step 2: Project Future FCFs

For each year, calculate:
```
FCF_year = free_cash_flow * (1 + growth_rate) ** year
```

- Year 1: 98,486,000,000 * (1 + 0.0119)^1 = $99,655,533,400
- Year 2: 98,486,000,000 * (1 + 0.0119)^2 = $100,834,062,748
- Year 3: 98,486,000,000 * (1 + 0.0119)^3 = $102,021,661,489
- Year 4: 98,486,000,000 * (1 + 0.0119)^4 = $103,218,413,187
- Year 5: 98,486,000,000 * (1 + 0.0119)^5 = $104,424,401,573

## Step 3: Discount Future FCFs

For each year, calculate:
```
PV_year = FCF_year / (1 + discount_rate) ** year
```

- Year 1: $99,655,533,400 / 1.10 = $90,595,030,364
- Year 2: $100,834,062,748 / 1.21 = $83,370,940,121
- Year 3: $102,021,661,489 / 1.331 = $76,663,073,964
- Year 4: $103,218,413,187 / 1.4641 = $70,515,964,073
- Year 5: $104,424,401,573 / 1.61051 = $64,877,073,964

## Step 4: Calculate Terminal Value

```
Terminal Value = (FCF_5 * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
```
- FCF_5 = $104,424,401,573
- Terminal Value = ($104,424,401,573 * 1.03) / (0.10 - 0.03) = $107,557,133,620 / 0.07 = $1,536,530,480,286

Discount terminal value to present:
```
PV_Terminal = Terminal Value / (1 + discount_rate) ** 5
```
- PV_Terminal = $1,536,530,480,286 / 1.61051 = $954,420,000,000

## Step 5: Sum Present Values

```
Intrinsic Value = sum(PV_years) + PV_Terminal
```
- Sum of PV_years = $90,595,030,364 + $83,370,940,121 + $76,663,073,964 + $70,515,964,073 + $64,877,073,964 = $385,022,082,486
- Intrinsic Value = $385,022,082,486 + $954,420,000,000 = $1,339,442,082,486

## Step 6: Compare to Market Cap

- **market_cap**: $3,155,342,600,760
- **gap**: (Intrinsic Value - Market Cap) / Market Cap = ($1,339,442,082,486 - $3,155,342,600,760) / $3,155,342,600,760 ≈ -0.575
- **signal**: "bearish" (since gap < -15%)

## Step 7: Output

```json
{
  "valuation_method": "dcf",
  "intrinsic_value": 1339442082486,
  "market_cap": 3155342600760,
  "gap": -0.575,
  "signal": "bearish",
  "biz_date": "2025-03-29"
}
```

---

**Note:**
- All numbers are rounded for clarity. Use full precision for actual calculations.
- This session demonstrates the DCF process with real AAPL data as of 2025-03-29, using the market cap from the company_facts table. 