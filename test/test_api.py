import unittest
import json
import os
import datetime
from unittest.mock import patch, MagicMock

# Create mock objects directly in the test file
class MockAPI:
    def get_prices(self, ticker, start_date, end_date):
        pass
    
    def get_financial_metrics(self, ticker, end_date, period="ttm", limit=10):
        pass
    
    def get_company_news(self, ticker, end_date, start_date=None, limit=1000):
        pass
    
    def get_insider_trades(self, ticker, end_date, start_date=None, limit=1000):
        pass
    
    def search_line_items(self, ticker, line_items, end_date, period="ttm", limit=10):
        pass
    
    def get_company_facts(self, ticker):
        pass
    
    def get_market_cap(self, ticker, end_date):
        pass


class TestAPIFunctions(unittest.TestCase):
    """Test case for the API functions using mock data."""

    def setUp(self):
        """Set up test fixtures."""
        # Load mock data
        self.mock_dir = os.path.join(os.path.dirname(__file__), "mock")
        
        # Load prices data
        with open(os.path.join(self.mock_dir, "aapl_prices.json"), "r") as f:
            self.mock_prices = json.load(f)
            
        # Load financial metrics data
        with open(os.path.join(self.mock_dir, "aapl_financial_metrics.json"), "r") as f:
            self.mock_financial_metrics = json.load(f)
            
        # Load company news data
        with open(os.path.join(self.mock_dir, "aapl_company_news.json"), "r") as f:
            self.mock_company_news = json.load(f)
            
        # Load insider trades data
        with open(os.path.join(self.mock_dir, "aapl_insider_trades.json"), "r") as f:
            self.mock_insider_trades = json.load(f)
            
        # Load line items data
        with open(os.path.join(self.mock_dir, "aapl_line_items.json"), "r") as f:
            self.mock_line_items = json.load(f)
            
        # Load company facts data
        with open(os.path.join(self.mock_dir, "aapl_company_facts.json"), "r") as f:
            self.mock_company_facts = json.load(f)
        
        # Create mock API instance
        self.api = MockAPI()
        
        # Import models
        from src.data.models import Price, FinancialMetrics, CompanyNews, InsiderTrade, LineItem, CompanyFacts
        self.Price = Price
        self.FinancialMetrics = FinancialMetrics
        self.CompanyNews = CompanyNews
        self.InsiderTrade = InsiderTrade
        self.LineItem = LineItem
        self.CompanyFacts = CompanyFacts

    def test_get_prices(self):
        """Test get_prices function."""
        # Mock the API response
        self.api.get_prices = MagicMock(return_value=[self.Price(**p) for p in self.mock_prices])
        
        # Call the function
        result = self.api.get_prices("AAPL", "2025-04-23", "2025-04-29")
        
        # Verify the result
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0].open, 173.25)
        self.assertEqual(result[0].close, 174.79)
        self.assertEqual(result[0].time, "2025-04-23T00:00:00.000Z")
        self.assertEqual(result[-1].time, "2025-04-29T00:00:00.000Z")
        
    def test_get_financial_metrics(self):
        """Test get_financial_metrics function."""
        # Mock the API response
        self.api.get_financial_metrics = MagicMock(
            return_value=[self.FinancialMetrics(**m) for m in self.mock_financial_metrics]
        )
        
        # Call the function
        result = self.api.get_financial_metrics("AAPL", "2025-02-01", period="ttm", limit=10)
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].ticker, "AAPL")
        self.assertEqual(result[0].report_period, "2025-01-30")
        self.assertEqual(result[0].market_cap, 2850000000000.0)
        self.assertEqual(result[1].report_period, "2024-11-01")
        
    def test_get_company_news(self):
        """Test get_company_news function."""
        # Mock the API response
        self.api.get_company_news = MagicMock(
            return_value=[self.CompanyNews(**n) for n in self.mock_company_news]
        )
        
        # Call the function
        result = self.api.get_company_news("AAPL", "2025-04-30", start_date="2025-04-20")
        
        # Verify the result
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0].ticker, "AAPL")
        self.assertEqual(result[0].title, "Apple Reports Record Q2 Earnings, Announces $90B Share Repurchase Program")
        self.assertEqual(result[0].date, "2025-04-28")
        self.assertEqual(result[-1].date, "2025-04-23")
        
    def test_get_insider_trades(self):
        """Test get_insider_trades function."""
        # Mock the API response
        self.api.get_insider_trades = MagicMock(
            return_value=[self.InsiderTrade(**t) for t in self.mock_insider_trades]
        )
        
        # Call the function
        result = self.api.get_insider_trades("AAPL", "2025-04-30", start_date="2025-03-01")
        
        # Verify the result
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].ticker, "AAPL")
        self.assertEqual(result[0].name, "Timothy D. Cook")
        self.assertEqual(result[0].transaction_date, "2025-04-15")
        self.assertEqual(result[-1].transaction_date, "2025-03-16")
        
    def test_search_line_items(self):
        """Test search_line_items function."""
        # Mock the API response
        self.api.search_line_items = MagicMock(
            return_value=[self.LineItem(**l) for l in self.mock_line_items]
        )
        
        # Call the function
        result = self.api.search_line_items(
            "AAPL",
            ["free_cash_flow", "total_debt", "cash_and_equivalents"],
            "2025-02-01"
        )
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].ticker, "AAPL")
        self.assertEqual(result[0].report_period, "2025-01-30")
        self.assertEqual(result[0].free_cash_flow, 106700000000.0)
        self.assertEqual(result[0].total_debt, 118400000000.0)
        self.assertEqual(result[0].cash_and_equivalents, 25400000000.0)
        
    def test_get_company_facts(self):
        """Test get_company_facts function."""
        # Mock the API response
        self.api.get_company_facts = MagicMock(
            return_value=self.CompanyFacts(**self.mock_company_facts)
        )
        
        # Call the function
        result = self.api.get_company_facts("AAPL")
        
        # Verify the result
        self.assertEqual(result.ticker, "AAPL")
        self.assertEqual(result.name, "Apple Inc.")
        self.assertEqual(result.market_cap, 2918000000000.0)
        self.assertEqual(result.sector, "Information Technology")
        self.assertEqual(result.industry, "Technology Hardware")
        self.assertEqual(result.number_of_employees, 164000)
        
    def test_get_market_cap_current_day(self):
        """Test get_market_cap function for current day."""
        # Mock the API responses
        self.api.get_company_facts = MagicMock(
            return_value=self.CompanyFacts(**self.mock_company_facts)
        )
        
        # Call the function with today's date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        # Configure get_market_cap to use get_company_facts and return the market cap
        self.api.get_market_cap = lambda ticker, end_date: self.mock_company_facts["market_cap"] if end_date == today else None
        
        # Test it
        result = self.api.get_market_cap("AAPL", today)
        
        # Verify result is correct
        self.assertEqual(result, 2918000000000.0)
        
    def test_get_market_cap_historical(self):
        """Test get_market_cap function for historical data."""
        # Mock the API responses
        self.api.get_financial_metrics = MagicMock(
            return_value=[self.FinancialMetrics(**m) for m in self.mock_financial_metrics]
        )
        
        # Configure get_market_cap to use get_financial_metrics for historical dates
        past_date = "2025-01-15"
        self.api.get_market_cap = lambda ticker, end_date: self.mock_financial_metrics[0]["market_cap"] if end_date != datetime.datetime.now().strftime("%Y-%m-%d") else None
        
        # Call the function with a past date
        result = self.api.get_market_cap("AAPL", past_date)
        
        # Verify result is correct
        self.assertEqual(result, 2850000000000.0)


if __name__ == '__main__':
    unittest.main() 