"""
Company Facts Service that integrates API and database functions.
This service provides a unified interface for retrieving company facts,
with automatic caching to both memory and database.
"""

import datetime
from src.data.models import CompanyFacts
from src.data.cache import get_cache
from src.tools.api import get_company_facts as get_company_facts_api
from tools.api_db import get_company_facts_db, get_market_cap_db, save_company_facts

class CompanyFactsService:
    """Service for retrieving and managing company facts."""
    
    def __init__(self):
        """Initialize the service with cache."""
        self._cache = get_cache()
    
    def get_company_facts(self, ticker: str) -> CompanyFacts | None:
        """
        Get company facts for the given ticker.
        
        This function implements a multi-level caching strategy:
        1. First, check in-memory cache
        2. Then, check the database
        3. Finally, fetch from the external API
        4. Store results in both memory cache and database for future use
        """
        ticker = ticker.upper()
        
        # 1. Check in-memory cache first (fastest)
        if cached_data := self._cache.get_company_facts(ticker):
            return CompanyFacts(**cached_data)
        
        # 2. Check the database (slower than memory, faster than API)
        if db_data := get_company_facts_db(ticker):
            # Cache in memory for future requests
            self._cache.set_company_facts(ticker, db_data.model_dump())
            return db_data
        
        # 3. If not in database, fetch from API
        if api_data := get_company_facts_api(ticker):
            # Cache in memory for future requests
            self._cache.set_company_facts(ticker, api_data.model_dump())
            
            # Store in database for persistence
            save_company_facts(api_data)
            
            return api_data
        
        # If we reach here, data couldn't be found anywhere
        return None
    
    def get_market_cap(self, ticker: str, end_date: str = None) -> float | None:
        """
        Get market cap for the given ticker and date.
        Only uses cache or database, never calls the API directly.
        
        For current date, retrieves from company facts (cache or DB).
        For historical dates, tries the database.
        
        Args:
            ticker: The stock ticker symbol
            end_date: The date for which to get market cap (defaults to today)
            
        Returns:
            The market cap value if found, None otherwise
        """
        ticker = ticker.upper()
        
        # Use today's date if no date is provided
        if end_date is None:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Check if it's today's date
        if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
            # Try to get from company facts (which will check cache then database)
            facts = self.get_company_facts(ticker)
            if facts and facts.market_cap is not None:
                return facts.market_cap
        
        # Try to get directly from database
        market_cap = get_market_cap_db(ticker, end_date)
        if market_cap is not None:
            return market_cap
            
        # If we get here, the data isn't available in cache or database
        return None

# Create a singleton instance
company_facts_service = CompanyFactsService()

# Convenience functions that use the service
def get_company_facts(ticker: str) -> CompanyFacts | None:
    """Get company facts for the given ticker."""
    return company_facts_service.get_company_facts(ticker)

def get_market_cap(ticker: str, end_date: str = None) -> float | None:
    """
    Get market cap for the given ticker and date.
    Only retrieves from cache or database, never calls the API directly.
    """
    return company_facts_service.get_market_cap(ticker, end_date) 