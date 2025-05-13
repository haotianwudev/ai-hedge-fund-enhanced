"""
Simple API interface for Polygon.io and Yahoo Finance
"""

import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Try importing yfinance, but don't fail if it's not installed
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


def get_price_yahoofinance(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get historical price data for a ticker from Yahoo Finance
    
    Args:
        ticker: The ticker symbol (e.g., "AAPL", "SPY")
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD'
        
    Returns:
        DataFrame containing the historical price data
    """
    if not HAS_YFINANCE:
        raise ImportError("yfinance is not installed. Install it with 'pip install yfinance'")
    
    # Download data from Yahoo Finance
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        return pd.DataFrame()
    
    # Rename columns to match our convention (lower case)
    df.columns = [col.lower() for col in df.columns]
    
    # Reset index to make date a column called biz_date in YYYY-MM-DD format
    df = df.reset_index()
    df['biz_date'] = df['date'].dt.strftime('%Y-%m-%d')
    df = df.drop(['date'], axis=1)
    
    # Set biz_date as index
    df.set_index('biz_date', inplace=True)
    
    return df
