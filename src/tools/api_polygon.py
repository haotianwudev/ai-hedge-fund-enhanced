"""
Polygon.io API Module

This module provides functions to interact with the Polygon.io API to fetch historical market data.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import pandas as pd
import requests
from dotenv import load_dotenv

# Try to import the polygon client, but don't fail if it's not available
try:
    from polygon import RESTClient
    HAS_POLYGON_CLIENT = True
except ImportError:
    HAS_POLYGON_CLIENT = False

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Polygon API key from environment
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
if not POLYGON_API_KEY:
    logger.warning("POLYGON_API_KEY not found in environment variables or .env file.")


def get_spy_data_with_client(
    api_key: str, 
    from_date: str, 
    to_date: str, 
    timespan: str = "day"
) -> pd.DataFrame:
    """
    Query SPY historical data using the polygon-api-client library.
    
    Args:
        api_key: Polygon API key
        from_date: Start date in format 'YYYY-MM-DD'
        to_date: End date in format 'YYYY-MM-DD'
        timespan: Time span for aggregates (day, minute, hour, week, month, quarter, year)
        
    Returns:
        DataFrame containing the historical data
        
    Raises:
        ImportError: If polygon-api-client is not installed
        ValueError: If API key is invalid or other API errors
    """
    if not HAS_POLYGON_CLIENT:
        raise ImportError(
            "polygon-api-client is not installed. "
            "Install it with 'pip install polygon-api-client'"
        )
    
    if not api_key:
        raise ValueError("API key is required")
    
    client = RESTClient(api_key)
    
    # Query aggregates (bars)
    aggs = client.get_aggs(
        ticker="SPY",
        multiplier=1,
        timespan=timespan,
        from_=from_date,
        to=to_date,
        limit=50000
    )
    
    # Convert to DataFrame
    data = []
    for agg in aggs:
        data.append({
            'timestamp': datetime.fromtimestamp(agg.timestamp / 1000),
            'open': agg.open,
            'high': agg.high,
            'low': agg.low,
            'close': agg.close,
            'volume': agg.volume,
            'vwap': agg.vwap,
            'transactions': agg.transactions
        })
    
    if not data:
        logger.warning(f"No data returned for SPY from {from_date} to {to_date}")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def get_spy_data_with_requests(
    api_key: str, 
    from_date: str, 
    to_date: str, 
    multiplier: int = 1, 
    timespan: str = "day"
) -> pd.DataFrame:
    """
    Query SPY historical data using direct API calls.
    
    Args:
        api_key: Polygon API key
        from_date: Start date in format 'YYYY-MM-DD'
        to_date: End date in format 'YYYY-MM-DD'
        multiplier: The size of the timespan multiplier
        timespan: Time span for aggregates (day, minute, hour, week, month, quarter, year)
        
    Returns:
        DataFrame containing the historical data
        
    Raises:
        ValueError: If API key is invalid, API request fails, or other errors
    """
    if not api_key:
        raise ValueError("API key is required")
    
    url = f"https://api.polygon.io/v2/aggs/ticker/SPY/range/{multiplier}/{timespan}/{from_date}/{to_date}?apiKey={api_key}"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    if data.get('status') != 'OK' or 'results' not in data:
        raise ValueError(f"API returned an error: {data}")
    
    if not data['results']:
        logger.warning(f"No data returned for SPY from {from_date} to {to_date}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['results'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
    
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
    
    # Set timestamp as index and drop unnecessary columns
    df.set_index('timestamp', inplace=True)
    df = df.drop(['t'], axis=1)
    
    return df


def get_ticker_data(
    ticker: str,
    from_date: str,
    to_date: str,
    api_key: Optional[str] = None,
    multiplier: int = 1,
    timespan: str = "day",
    adjusted: bool = True,
    use_client: bool = True
) -> pd.DataFrame:
    """
    Get historical data for any ticker from Polygon.io API.
    
    Args:
        ticker: The ticker symbol (e.g., "AAPL", "SPY")
        from_date: Start date in format 'YYYY-MM-DD'
        to_date: End date in format 'YYYY-MM-DD'
        api_key: Polygon API key (defaults to environment variable)
        multiplier: The size of the timespan multiplier
        timespan: Time span for aggregates (day, minute, hour, week, month, quarter, year)
        adjusted: Whether to use adjusted stock data
        use_client: Whether to try using the polygon client library first
        
    Returns:
        DataFrame containing the historical data
    """
    # Use the provided API key or the one from environment
    api_key = api_key or POLYGON_API_KEY
    
    if not api_key:
        raise ValueError("API key is required. Provide it as an argument or set POLYGON_API_KEY environment variable.")
    
    if ticker == "SPY" and use_client and HAS_POLYGON_CLIENT:
        try:
            logger.info(f"Fetching {ticker} data using polygon-api-client")
            return get_spy_data_with_client(api_key, from_date, to_date, timespan)
        except Exception as e:
            logger.warning(f"Error using polygon-api-client: {e}. Falling back to direct API calls.")
    
    # Use direct API calls
    logger.info(f"Fetching {ticker} data using direct API calls")
    
    # Build the URL
    url_params = f"adjusted={str(adjusted).lower()}"
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}?{url_params}&apiKey={api_key}"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}: {response.text}")
    
    data = response.json()
    
    if data.get('status') != 'OK' or 'results' not in data:
        raise ValueError(f"API returned an error: {data}")
    
    if not data['results']:
        logger.warning(f"No data returned for {ticker} from {from_date} to {to_date}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['results'])
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
    
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
    
    # Set timestamp as index and drop unnecessary columns
    df.set_index('timestamp', inplace=True)
    if 't' in df.columns:
        df = df.drop(['t'], axis=1)
    
    return df


def get_last_year_data(ticker: str = "SPY") -> pd.DataFrame:
    """
    Get the last year of daily data for a ticker.
    
    Args:
        ticker: The ticker symbol to fetch data for
        
    Returns:
        DataFrame containing the historical data
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    return get_ticker_data(ticker, start_date, end_date)


def calculate_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate basic financial metrics from price data.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Dictionary of metrics
    """
    if df.empty:
        return {}
    
    # Calculate daily returns
    df_copy = df.copy()
    df_copy['daily_return'] = df_copy['close'].pct_change() * 100
    
    # Calculate metrics
    total_return = (df_copy['close'].iloc[-1] / df_copy['close'].iloc[0] - 1) * 100
    annualized_volatility = df_copy['daily_return'].std() * (252 ** 0.5)  # Assuming 252 trading days in a year
    sharpe_ratio = (df_copy['daily_return'].mean() / df_copy['daily_return'].std()) * (252 ** 0.5)  # Simplified Sharpe ratio
    
    # Find best and worst days
    best_day = df_copy['daily_return'].idxmax()
    worst_day = df_copy['daily_return'].idxmin()
    
    return {
        'total_return': total_return,
        'annualized_volatility': annualized_volatility,
        'sharpe_ratio': sharpe_ratio,
        'best_day': best_day.strftime('%Y-%m-%d') if not pd.isna(best_day) else None,
        'best_day_return': df_copy.loc[best_day, 'daily_return'] if not pd.isna(best_day) else None,
        'worst_day': worst_day.strftime('%Y-%m-%d') if not pd.isna(worst_day) else None,
        'worst_day_return': df_copy.loc[worst_day, 'daily_return'] if not pd.isna(worst_day) else None
    }


if __name__ == "__main__":
    # Example usage
    try:
        # Get last year of SPY data
        spy_data = get_last_year_data("SPY")
        
        # Print basic info
        print(f"Fetched {len(spy_data)} days of SPY data")
        print("\nFirst 5 rows:")
        print(spy_data.head())
        
        # Calculate and print metrics
        metrics = calculate_metrics(spy_data)
        print("\nSPY Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}") 