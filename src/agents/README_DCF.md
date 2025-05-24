# Valuation Analysis: Discounted Cash Flow (DCF) Method

## Overview

The Discounted Cash Flow (DCF) method is a core valuation approach implemented in the `valuation_agent` (see `valuation.py`). It estimates a company's intrinsic value by projecting its future free cash flows (FCF) and discounting them back to present value using a required rate of return. The DCF result is then compared to the current market capitalization to generate a valuation signal.

---

## Inputs

The DCF method in this codebase requires the following inputs for each ticker:

- **free_cash_flow**: The most recent free cash flow value (from line items).
- **growth_rate**: Projected annual growth rate for FCF (default: recent earnings growth, fallback: 5%).
- **discount_rate**: The required rate of return (default: 10%).
- **terminal_growth_rate**: The perpetual growth rate after the projection period (default: 3%).
- **num_years**: Number of years to project FCF (default: 5).

These are sourced from:
- `get_financial_metrics` (for growth rate and other metrics)
- `search_line_items` (for free cash flow and other line items)

---

## Methodology

The DCF calculation is performed by the function `calculate_intrinsic_value`:

1. **Project Future FCFs**:  
   For each year in the projection period (default 5 years), future FCF is estimated as:
   ```
   FCF_year = free_cash_flow * (1 + growth_rate) ** year
   ```

2. **Discount Future FCFs**:  
   Each projected FCF is discounted to present value:
   ```
   PV_year = FCF_year / (1 + discount_rate) ** year
   ```

3. **Calculate Terminal Value**:  
   After the projection period, a terminal value is calculated using the Gordon Growth Model:
   ```
   Terminal Value = (FCF_n * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
   PV_Terminal = Terminal Value / (1 + discount_rate) ** num_years
   ```

4. **Sum Present Values**:  
   The intrinsic value is the sum of all discounted FCFs and the discounted terminal value:
   ```
   Intrinsic Value = sum(PV_years) + PV_Terminal
   ```

5. **Compare to Market Cap**:  
   The calculated intrinsic value is compared to the current market capitalization to determine the valuation gap and generate a signal (bullish, bearish, or neutral).

---

## Output

For each ticker, the DCF method produces:

- **intrinsic_value**: The estimated present value of the company using DCF.
- **market_cap**: The current market capitalization.
- **gap**: The percentage difference between intrinsic value and market cap.
- **signal**:  
  - `"bullish"` if the intrinsic value is >15% above market cap  
  - `"bearish"` if >15% below  
  - `"neutral"` otherwise
- **detail**: A record of the method, values, and signal for reporting and aggregation.

Example output structure:
```json
{
  "valuation_method": "dcf",
  "intrinsic_value": 123456789.0,
  "market_cap": 100000000.0,
  "gap": 0.2345,
  "signal": "bullish",
  "biz_date": "2024-05-24"
}
```

---

## References

- See `valuation.py` for the main agent logic and aggregation.
- See `calculate_intrinsic_value` in the same file for the DCF implementation.

---

**Advice:**  
- Ensure your FCF and growth rate inputs are reasonable and not outliers.
- Adjust `discount_rate` and `terminal_growth_rate` as needed for your investment philosophy or market conditions.
- The DCF is one of several methods used in your system; results are aggregated for a more robust signal. 