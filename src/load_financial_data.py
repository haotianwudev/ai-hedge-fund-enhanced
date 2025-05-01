#!/usr/bin/env python
"""
Load Financial Data Script

This script fetches company facts and price data for specified tickers and saves it to the PostgreSQL database.
It uses the API functions in tools/api.py to get the data and stores it in the company_facts and prices tables.

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

# Import API functions
from tools.api import get_company_facts, get_prices

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
    """Save price data to the PostgreSQL database."""
    if not prices:
        return False
        
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print(f"{Fore.RED}Error: DATABASE_URL environment variable not set{Style.RESET_ALL}")
            return False

        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Fields to insert/update
        fields = [
            'ticker', 'time', 'biz_date', 'open', 'close', 'high', 'low', 'volume'
        ]
        
        # Prepare data for insert
        values = []
        for price in prices:
            data = price.model_dump()
            # Extract date from time for biz_date
            time_str = data['time']
            date_part = time_str.split('T')[0] if 'T' in time_str else time_str.split(' ')[0]
            
            values.append([
                ticker, 
                data['time'], 
                date_part,  # biz_date
                data['open'], 
                data['close'], 
                data['high'], 
                data['low'], 
                data['volume']
            ])
        
        # Build the SQL query
        field_list = ', '.join(fields)
        update_list = ', '.join([f"{field} = EXCLUDED.{field}" for field in fields if field != 'ticker' and field != 'biz_date'])
        update_list += ", updated_at = CURRENT_TIMESTAMP"
        
        sql = f"""
        INSERT INTO prices ({field_list})
        VALUES %s
        ON CONFLICT (ticker, biz_date) DO UPDATE SET {update_list}
        """
        
        # Execute the query with multiple rows
        execute_values(cursor, sql, values, template=None, page_size=100)
        
        # Commit the transaction
        conn.commit()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}Error saving price data to database: {e}{Style.RESET_ALL}")
        return False

def load_financial_data(tickers, start_date, end_date, verbose=False):
    """
    Load financial data for the specified tickers and date range.
    
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
        "prices_failed": []
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
            
            # Get price data
            print(f"Fetching price data for {Fore.YELLOW}{ticker}{Style.RESET_ALL}... ", end="", flush=True)
            prices = get_prices(ticker, start_date, end_date)
            
            if prices:
                # Save to database
                if save_prices_to_db(ticker, prices):
                    print(f"{Fore.GREEN}Prices saved successfully ({len(prices)} records){Style.RESET_ALL}")
                    results["prices_success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save price data to database{Style.RESET_ALL}")
                    results["prices_failed"].append(ticker)
            else:
                print(f"{Fore.RED}No price data available{Style.RESET_ALL}")
                results["prices_failed"].append(ticker)
                
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
        start_dt = end_dt - timedelta(days=90)
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
        help="Start date (YYYY-MM-DD). Defaults to 3 months before end date",
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

if __name__ == "__main__":
    main() 