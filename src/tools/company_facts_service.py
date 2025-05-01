"""
Company Facts Service that integrates API and database functions.
This service provides a unified interface for retrieving company facts,
with automatic caching to both memory and database.
"""

import datetime
from data.models import CompanyFacts
from data.cache import get_cache
from src.tools.api import get_company_facts as get_company_facts_api
from src.tools.api_db import get_company_facts_db, save_company_facts

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
        For current date, uses company facts.
        For historical dates, falls back to financial metrics.
        """
        ticker = ticker.upper()
        
        # Use today's date if no date is provided
        if end_date is None:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Get company facts if end_date is today
        if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
            facts = self.get_company_facts(ticker)
            if facts:
                return facts.market_cap
        
        # For historical data, use the API's get_market_cap function
        # which already handles both current and historical requests
        from src.tools.api import get_market_cap as get_market_cap_api
        return get_market_cap_api(ticker, end_date)

# Create a singleton instance
company_facts_service = CompanyFactsService()

# Convenience functions that use the service
def get_company_facts(ticker: str) -> CompanyFacts | None:
    """Get company facts for the given ticker."""
    return company_facts_service.get_company_facts(ticker)

def get_market_cap(ticker: str, end_date: str = None) -> float | None:
    """Get market cap for the given ticker and date."""
    return company_facts_service.get_market_cap(ticker, end_date) 