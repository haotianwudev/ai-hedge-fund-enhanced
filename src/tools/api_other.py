"""
Simple API interface for Polygon.io and Yahoo Finance
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

# Try importing yfinance, but don't fail if it's not installed
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# Load environment variables
load_dotenv()

# Get API key from environment
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')


def get_price_polygon(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get historical price data for a ticker from Polygon.io
    
    Args:
        ticker: The ticker symbol (e.g., "AAPL", "SPY")
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD'
        
    Returns:
        DataFrame containing the historical price data
    """
    # Check if API key is available
    if not POLYGON_API_KEY:
        raise ValueError("POLYGON_API_KEY not found in environment variables")
    
    # Build the URL
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&apiKey={POLYGON_API_KEY}"
    
    # Make the request
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    if data.get('status') != 'OK' or 'results' not in data:
        raise ValueError(f"API returned an error: {data}")
    
    if not data['results']:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['results'])
    
    # Convert timestamp to datetime and format as YYYY-MM-DD
    df['biz_date'] = pd.to_datetime(df['t'], unit='ms').dt.strftime('%Y-%m-%d')
    
    # Rename columns
    df = df.rename(columns={
        'o': 'open',
        'h': 'high',
        'l': 'low',
        'c': 'close',
        'v': 'volume',
        'vw': 'vwap',
        'n': 'transactions'
    })
    
    # Set biz_date as index and drop unnecessary columns
    df.set_index('biz_date', inplace=True)
    if 't' in df.columns:
        df = df.drop(['t'], axis=1)
    
    return df


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


if __name__ == "__main__":
    # Example usage
    try:
        # Get last year of SPY data using Polygon
        start = (datetime.now().replace(year=datetime.now().year-1)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        
        print("Fetching data from Polygon.io...")
        try:
            spy_data_polygon = get_price_polygon("SPY", start, end)
            print(f"Fetched {len(spy_data_polygon)} days of SPY data from Polygon")
            print("\nFirst 5 rows:")
            print(spy_data_polygon.head())
        except Exception as e:
            print(f"Polygon API error: {str(e)}")
        
        # Get the same data from Yahoo Finance
        print("\nFetching data from Yahoo Finance...")
        try:
            spy_data_yahoo = get_price_yahoofinance("SPY", start, end)
            print(f"Fetched {len(spy_data_yahoo)} days of SPY data from Yahoo Finance")
            print("\nFirst 5 rows:")
            print(spy_data_yahoo.head())
        except Exception as e:
            print(f"Yahoo Finance error: {str(e)}")
        
    except Exception as e:
        print(f"Error: {str(e)}") 