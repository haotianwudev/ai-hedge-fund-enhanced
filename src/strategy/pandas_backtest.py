import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any

def estimate_put_option_price(S: float, K: float, T: float, r: float, sigma: float, dividend_yield: float = 0.0) -> float:
    """
    Estimate the price of a put option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years (e.g., 21/252 for 21 trading days)
        r: Risk-free interest rate (as a decimal)
        sigma: Implied volatility (VIX/100 for SPY options)
        dividend_yield: Annual dividend yield of the underlying asset (as a decimal)
        
    Returns:
        Put option price
    """
    # Black-Scholes formula for put option
    d1 = (np.log(S / K) + (r - dividend_yield + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    put_price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * np.exp(-dividend_yield * T) * stats.norm.cdf(-d1)
    
    return put_price

