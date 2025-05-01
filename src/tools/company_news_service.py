"""
Company News Service that integrates cache and database functions.
This service provides a unified interface for retrieving company news data,
with automatic caching to both memory and database.
"""

import pandas as pd
from src.data.models import CompanyNews
from src.data.cache import get_cache
from src.tools.api import get_company_news as get_company_news_api
from src.tools.api_db import get_company_news_db, save_company_news

class CompanyNewsService:
    """Service for retrieving and managing company news data."""
    
    def __init__(self):
        """Initialize the service with cache."""
        self._cache = get_cache()
    
    def get_company_news(
        self, 
        ticker: str, 
        end_date: str,
        start_date: str | None = None,
        limit: int = 1000
    ) -> list[CompanyNews]:
        """
        Get company news data for the given ticker.
        
        This function implements a three-level caching strategy:
        1. First, check in-memory cache
        2. Then, check the database
        3. Finally, fall back to the API
        
        Args:
            ticker: The stock ticker symbol
            end_date: The end date for filtering news
            start_date: Optional start date for filtering news
            limit: Maximum number of records to return
            
        Returns:
            A list of CompanyNews objects for the specified ticker and date range
        """
        ticker = ticker.upper()
        
        # 1. Check in-memory cache first (fastest)
        if cached_data := self._cache.get_company_news(ticker):
            # Filter cached data by date range and convert to CompanyNews objects
            filtered_data = [
                CompanyNews(**news) 
                for news in cached_data 
                if ((start_date is None or news.get("date") >= start_date) and
                    news.get("date") <= end_date)
            ]
            
            # Sort by date in descending order
            filtered_data.sort(key=lambda x: x.date, reverse=True)
            
            if filtered_data:
                return filtered_data[:limit]
        
        # 2. Check the database (slower than memory, faster than API)
        if db_data := get_company_news_db(ticker, end_date, start_date, limit):
            # Cache in memory for future requests
            news_to_cache = [news.model_dump() for news in db_data]
            self._cache.set_company_news(ticker, news_to_cache)
            return db_data
        
        # 3. If not in cache or database, fetch from API (slowest)
        api_data = get_company_news_api(ticker, end_date, start_date, limit)
        
        if api_data:
            # Save to database
            save_company_news(api_data)
            
            # Cache in memory
            news_to_cache = [news.model_dump() for news in api_data]
            self._cache.set_company_news(ticker, news_to_cache)
            
            return api_data
        
        # If data is not found anywhere, return empty list
        return []
    
    def company_news_to_df(self, news_list: list[CompanyNews]) -> pd.DataFrame:
        """Convert company news to a DataFrame."""
        # Check if we have any news
        if not news_list:
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame([news.model_dump() for news in news_list])
        
        # Format the dataframe
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
        # Sort by date (newest to oldest)
        df.sort_index(ascending=False, inplace=True)
        
        return df

# Create a singleton instance
company_news_service = CompanyNewsService()

# Convenience functions that use the service
def get_company_news(
    ticker: str, 
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000
) -> list[CompanyNews]:
    """Get company news for the given ticker and date range."""
    return company_news_service.get_company_news(ticker, end_date, start_date, limit)

def get_company_news_df(
    ticker: str, 
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000
) -> pd.DataFrame:
    """Get company news as a DataFrame."""
    news_list = company_news_service.get_company_news(ticker, end_date, start_date, limit)
    return company_news_service.company_news_to_df(news_list) 