#!/usr/bin/env python
"""
Load Financial Data Script

This script fetches company facts, price data, company news, financial metrics, 
insider trades, and line items for specified tickers and saves it to the PostgreSQL database.
It uses the API functions in tools/api.py to get the data and stores it in the database.

The various service modules can then access this data from the cache and database, but won't
make API calls directly. This script is responsible for populating the database with all financial data.

Example usage:
    poetry run python src/load_financial_data.py --tickers AAPL,MSFT,NVDA
"""

import argparse
import sys
import os
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import API functions to fetch data
from tools.api import get_company_facts, get_prices, get_company_news, get_financial_metrics, get_insider_trades, search_line_items
# Import DB functions to save data
from tools.api_db import (
    save_prices as save_prices_db,
    save_company_news,
    save_financial_metrics,
    save_insider_trades,
    save_line_items
)
from tools.line_items_list import get_all_line_items

# Initialize colorama
init(autoreset=True)

def save_company_facts_to_db(company_facts):
    """Save company facts to the PostgreSQL database."""
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print(f"{Fore.RED}Error: DATABASE_URL environment variable not set{Style.RESET_ALL}")
            return False

        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Convert to dictionary
        data = company_facts.model_dump()
        
        # Fields to insert/update
        fields = [
            'ticker', 'name', 'cik', 'industry', 'sector', 'category', 
            'exchange', 'is_active', 'listing_date', 'location', 'market_cap',
            'number_of_employees', 'sec_filings_url', 'sic_code', 
            'sic_industry', 'sic_sector', 'website_url', 'weighted_average_shares'
        ]
        
        # Build the SQL query
        placeholders = ', '.join(['%s'] * len(fields))
        field_list = ', '.join(fields)
        update_list = ', '.join([f"{field} = EXCLUDED.{field}" for field in fields])
        update_list += ", updated_at = CURRENT_TIMESTAMP"
        
        sql = f"""
        INSERT INTO company_facts ({field_list})
        VALUES ({placeholders})
        ON CONFLICT (ticker) DO UPDATE SET {update_list}
        """
        
        # Execute the query
        cursor.execute(sql, [data.get(field) for field in fields])
        
        # Commit the transaction
        conn.commit()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}Error saving company facts to database: {e}{Style.RESET_ALL}")
        return False

def save_prices_to_db(ticker, prices):
    """
    Save price data to the PostgreSQL database using the api_db module.
    This is a simple wrapper around the api_db.save_prices function.
    """
    if not prices:
        return False
    
    try:
        # Use the save_prices function from api_db
        return save_prices_db(ticker, prices)
    except Exception as e:
        print(f"{Fore.RED}Error saving price data to database: {e}{Style.RESET_ALL}")
        return False

def save_company_news_to_db(ticker, news):
    """Save company news to the PostgreSQL database."""
    if not news:
        return False
    
    try:
        return save_company_news(news)
    except Exception as e:
        print(f"{Fore.RED}Error saving company news to database: {e}{Style.RESET_ALL}")
        return False

def save_financial_metrics_to_db(metrics):
    """Save financial metrics to the PostgreSQL database."""
    if not metrics:
        return False
    
    try:
        return save_financial_metrics(metrics)
    except Exception as e:
        print(f"{Fore.RED}Error saving financial metrics to database: {e}{Style.RESET_ALL}")
        return False

def save_insider_trades_to_db(ticker, trades):
    """Save insider trades to the PostgreSQL database."""
    if not trades:
        return False
    
    try:
        return save_insider_trades(trades)
    except Exception as e:
        print(f"{Fore.RED}Error saving insider trades to database: {e}{Style.RESET_ALL}")
        return False

def save_line_items_to_db(ticker, line_items):
    """Save line items to the PostgreSQL database."""
    if not line_items:
        return False
    
    try:
        return save_line_items(ticker, line_items)
    except Exception as e:
        print(f"{Fore.RED}Error saving line items to database: {e}{Style.RESET_ALL}")
        return False

def load_financial_data(tickers, start_date, end_date, verbose=False):
    """
    Load financial data for the specified tickers and date range.
    This function is responsible for fetching data from the API and saving it to the database.
    
    Args:
        tickers (list): List of ticker symbols
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        verbose (bool): Whether to print verbose output
    
    Returns:
        dict: Results of data loading
    """
    results = {
        "success": [],
        "failed": [],
        "prices_success": [],
        "prices_failed": [],
        "news_success": [],
        "news_failed": [],
        "metrics_success": [],
        "metrics_failed": [],
        "trades_success": [],
        "trades_failed": [],
        "line_items_success": [],
        "line_items_failed": []
    }
    
    print(f"\n{Fore.CYAN}Loading financial data for {len(tickers)} tickers: {', '.join(tickers)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Date range: {start_date} to {end_date}{Style.RESET_ALL}\n")
    
    for ticker in tickers:
        try:
            print(f"Processing {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            
            # Get company facts data
            company_facts = get_company_facts(ticker)
            
            if company_facts:
                # Save to database
                if save_company_facts_to_db(company_facts):
                    print(f"{Fore.GREEN}Company facts saved successfully{Style.RESET_ALL}")
                    
                    if verbose:
                        print(f"  Market Cap: ${company_facts.market_cap:,.2f}")
                        print(f"  Industry: {company_facts.industry}")
                        print(f"  Sector: {company_facts.sector}")
                    
                    results["success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save company facts to database{Style.RESET_ALL}")
                    results["failed"].append(ticker)
            else:
                print(f"{Fore.RED}No company facts data available{Style.RESET_ALL}")
                results["failed"].append(ticker)
            
            # Fetch price data from API
            print(f"Fetching price data for {Fore.YELLOW}{ticker}{Style.RESET_ALL} from API... ", end="", flush=True)
            prices = get_prices(ticker, start_date, end_date)
            
            if prices:
                # Save to database using the function from api_db
                if save_prices_to_db(ticker, prices):
                    print(f"{Fore.GREEN}Prices saved successfully ({len(prices)} records){Style.RESET_ALL}")
                    results["prices_success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save price data to database{Style.RESET_ALL}")
                    results["prices_failed"].append(ticker)
            else:
                print(f"{Fore.RED}No price data available from API{Style.RESET_ALL}")
                results["prices_failed"].append(ticker)

            # Fetch company news
            print(f"Fetching company news for {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            news = get_company_news(ticker, end_date)
            if news:
                if save_company_news_to_db(ticker, news):
                    print(f"{Fore.GREEN}News saved successfully ({len(news)} records){Style.RESET_ALL}")
                    results["news_success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save news to database{Style.RESET_ALL}")
                    results["news_failed"].append(ticker)
            else:
                print(f"{Fore.RED}No company news available{Style.RESET_ALL}")
                results["news_failed"].append(ticker)

            # Fetch financial metrics
            print(f"Fetching financial metrics for {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            metrics = get_financial_metrics(ticker, end_date)
            if metrics:
                if save_financial_metrics_to_db(metrics):
                    print(f"{Fore.GREEN}Metrics saved successfully ({len(metrics)} records){Style.RESET_ALL}")
                    results["metrics_success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save metrics to database{Style.RESET_ALL}")
                    results["metrics_failed"].append(ticker)
            else:
                print(f"{Fore.RED}No financial metrics available{Style.RESET_ALL}")
                results["metrics_failed"].append(ticker)

            # Fetch insider trades
            print(f"Fetching insider trades for {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            trades = get_insider_trades(ticker, end_date)
            if trades:
                if save_insider_trades_to_db(ticker, trades):
                    print(f"{Fore.GREEN}Trades saved successfully ({len(trades)} records){Style.RESET_ALL}")
                    results["trades_success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save trades to database{Style.RESET_ALL}")
                    results["trades_failed"].append(ticker)
            else:
                print(f"{Fore.RED}No insider trades available{Style.RESET_ALL}")
                results["trades_failed"].append(ticker)

            # Fetch line items (using all financial metrics defined in line_items_list.py)
            print(f"Fetching line items for {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            try:
                # Get all line items from line_items_list.py
                all_line_items = get_all_line_items()
                line_items = search_line_items(ticker, all_line_items, end_date)
                if line_items:
                    if save_line_items_to_db(ticker, line_items):
                        print(f"{Fore.GREEN}Line items saved successfully ({len(line_items)} records){Style.RESET_ALL}")
                        results["line_items_success"].append(ticker)
                    else:
                        print(f"{Fore.RED}Failed to save line items to database{Style.RESET_ALL}")
                        results["line_items_failed"].append(ticker)
                else:
                    print(f"{Fore.RED}No line items available{Style.RESET_ALL}")
                    results["line_items_failed"].append(ticker)
            except Exception as e:
                print(f"{Fore.RED}Error fetching line items: {e}{Style.RESET_ALL}")
                results["line_items_failed"].append(ticker)
                
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            results["failed"].append(ticker)
            results["prices_failed"].append(ticker)
    
    return results

def get_date_range(start_date, end_date):
    """
    Get the date range for the data fetching.
    If start_date or end_date is not provided, use defaults.
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if not start_date:
        # Default to 3 months before end date
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=1825)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    return start_date, end_date

def main():
    """Main entry point for the script."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Load financial data into the database")
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock ticker symbols")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 5 years before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information")
    
    args = parser.parse_args()
    
    # Parse tickers from comma-separated string
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    # Get date range
    start_date, end_date = get_date_range(args.start_date, args.end_date)
    
    # Load financial data
    results = load_financial_data(tickers, start_date, end_date, args.verbose)
    
    # Print summary
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  Total tickers: {len(tickers)}")
    print(f"  {Fore.GREEN}Company facts - Successful:{Style.RESET_ALL} {len(results['success'])} ({', '.join(results['success']) if results['success'] else 'None'})")
    print(f"  {Fore.RED}Company facts - Failed:{Style.RESET_ALL} {len(results['failed'])} ({', '.join(results['failed']) if results['failed'] else 'None'})")
    print(f"  {Fore.GREEN}Price data - Successful:{Style.RESET_ALL} {len(results['prices_success'])} ({', '.join(results['prices_success']) if results['prices_success'] else 'None'})")
    print(f"  {Fore.RED}Price data - Failed:{Style.RESET_ALL} {len(results['prices_failed'])} ({', '.join(results['prices_failed']) if results['prices_failed'] else 'None'})")
    print(f"  {Fore.GREEN}Company news - Successful:{Style.RESET_ALL} {len(results['news_success'])} ({', '.join(results['news_success']) if results['news_success'] else 'None'})")
    print(f"  {Fore.RED}Company news - Failed:{Style.RESET_ALL} {len(results['news_failed'])} ({', '.join(results['news_failed']) if results['news_failed'] else 'None'})")
    print(f"  {Fore.GREEN}Financial metrics - Successful:{Style.RESET_ALL} {len(results['metrics_success'])} ({', '.join(results['metrics_success']) if results['metrics_success'] else 'None'})")
    print(f"  {Fore.RED}Financial metrics - Failed:{Style.RESET_ALL} {len(results['metrics_failed'])} ({', '.join(results['metrics_failed']) if results['metrics_failed'] else 'None'})")
    print(f"  {Fore.GREEN}Insider trades - Successful:{Style.RESET_ALL} {len(results['trades_success'])} ({', '.join(results['trades_success']) if results['trades_success'] else 'None'})")
    print(f"  {Fore.RED}Insider trades - Failed:{Style.RESET_ALL} {len(results['trades_failed'])} ({', '.join(results['trades_failed']) if results['trades_failed'] else 'None'})")
    print(f"  {Fore.GREEN}Line items - Successful:{Style.RESET_ALL} {len(results['line_items_success'])} ({', '.join(results['line_items_success']) if results['line_items_success'] else 'None'})")
    print(f"  {Fore.RED}Line items - Failed:{Style.RESET_ALL} {len(results['line_items_failed'])} ({', '.join(results['line_items_failed']) if results['line_items_failed'] else 'None'})")

if __name__ == "__main__":
    main()
