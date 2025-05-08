import os
import logging
import requests
import csv
import argparse
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

def get_news_sentiment(ticker: str, time_from: Optional[str] = None, 
                      time_to: Optional[str] = None, limit: int = 5) -> Optional[Dict]:
    """Fetch news sentiment data for a ticker from Alpha Vantage API.
    
    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
        time_from: Start time in YYYYMMDDTHHMM format (optional)
        time_to: End time in YYYYMMDDTHHMM format (optional)
        limit: Maximum number of results (default 50, max 1000)
    
    Returns:
        Dictionary containing news sentiment data or None if request fails
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
        return None

    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&limit={limit}&apikey={api_key}"
    
    if time_from:
        url += f"&time_from={time_from}"
    if time_to:
        url += f"&time_to={time_to}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch news sentiment for {ticker}: {str(e)}")
        return None

def save_news_to_csv(data: Dict, ticker: str):
    """Save sentiment data to CSV file in logs directory with expanded fields.
    
    Args:
        data: Sentiment data dictionary from API
        ticker: Ticker symbol processed
    
    CSV Format:
    - One row per article-ticker combination
    - Includes article metadata, overall sentiment, ticker sentiment, and topics
    """
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/news_sentiment_{ticker}_{timestamp}.csv"
    
    fieldnames = [
        'ticker', 'title', 'url', 'time_published', 'date', 'source',
        'author', 'summary', 'overall_sentiment_score',
        'overall_sentiment_label', 'ticker_sentiment_score', 
        'ticker_relevance_score', 'sentiment'
    ]
    
    def format_time(time_str: str) -> str:
        """Convert API time format (YYYYMMDDTHHMM) to readable format"""
        try:
            dt = datetime.strptime(time_str, "%Y%m%dT%H%M")
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return time_str
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        if data and 'feed' in data:
            for item in data['feed']:
                # Process each ticker sentiment in the article
                ticker_sentiments = item.get('ticker_sentiment', [])
                if not ticker_sentiments:  # If no ticker sentiments, include with empty values
                    writer.writerow({
                        'ticker': ticker,
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'time_published': format_time(item.get('time_published', '')),
                        'date': datetime.strptime(item.get('time_published', ''), "%Y%m%dT%H%M").strftime("%Y-%m-%d") if item.get('time_published') else '',
                        'source': item.get('source', ''),
                        'author': "; ".join(item.get('authors', [])),
                        'summary': item.get('summary', ''),
                        'overall_sentiment_score': item.get('overall_sentiment_score', 0),
                        'overall_sentiment_label': item.get('overall_sentiment_label', ''),
                        'ticker_sentiment_score': 0,
                        'ticker_relevance_score': 0,
                        'sentiment': '',
                    })
                else:
                    for ticker_sent in ticker_sentiments:
                        if ticker_sent['ticker'] == ticker:
                            writer.writerow({
                                'ticker': ticker_sent['ticker'],
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'time_published': format_time(item.get('time_published', '')),
                                'date': datetime.strptime(item.get('time_published', ''), "%Y%m%dT%H%M").strftime("%Y-%m-%d") if item.get('time_published') else '',
                                'source': item.get('source', ''),
                                'author': "; ".join(item.get('authors', [])),
                                'summary': item.get('summary', ''),
                                'overall_sentiment_score': float(item.get('overall_sentiment_score', 0)),
                                'overall_sentiment_label': item.get('overall_sentiment_label', ''),
                                'ticker_sentiment_score': float(ticker_sent.get('ticker_sentiment_score', '0')),
                                'ticker_relevance_score': float(ticker_sent.get('relevance_score', '0')),
                                'sentiment': ticker_sent.get('ticker_sentiment_label', ''),
                            })

def get_daily_prices(ticker: str, outputsize: str = 'compact') -> Optional[Dict]:
    """Fetch daily price data for a ticker from Alpha Vantage API.
    
    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
        outputsize: 'compact' (latest 100 points) or 'full' (20+ years history)
    
    Returns:
        Dictionary containing price data or None if request fails
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
        return None

    if outputsize not in ['compact', 'full']:
        logger.error("outputsize must be either 'compact' or 'full'")
        return None

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize={outputsize}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch prices for {ticker}: {str(e)}")
        return None

def save_prices_to_csv(data: Dict, ticker: str):
    """Save price data to CSV file in logs directory.
    
    Args:
        data: Dictionary containing price data
        ticker: Ticker symbol processed
    """
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/daily_prices_{ticker}_{timestamp}.csv"
    
    fieldnames = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        if data and 'Time Series (Daily)' in data:
            for date, prices in data['Time Series (Daily)'].items():
                writer.writerow({
                    'date': date,
                    'open': prices['1. open'],
                    'high': prices['2. high'],
                    'low': prices['3. low'],
                    'close': prices['4. close'],
                    'volume': prices['5. volume']
                })

if __name__ == "__main__":
    ticker = "AAPL"
    data = get_daily_prices(ticker)
    if data:
        save_prices_to_csv(data, ticker)
        logger.info(f"Saved price data for {ticker} to CSV in logs directory")

    # Process first ticker for sentiment
    logger.info(f"Fetching news sentiment for {ticker}")
    data = get_news_sentiment(ticker)
    if data:
        save_news_to_csv(data, ticker)
        logger.info(f"Saved sentiment data for {ticker} to CSV in logs directory")
