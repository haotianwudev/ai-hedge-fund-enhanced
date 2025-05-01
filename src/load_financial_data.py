#!/usr/bin/env python
"""
Load Financial Data Script

This script fetches company facts data for specified tickers and saves it to the PostgreSQL database.
It uses the API functions in tools/api.py to get the data and stores it in the company_facts table.

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
from tools.api import get_company_facts

# Database connection string
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_IjoHW5gl8AYZ@ep-billowing-wildflower-a4222ksm-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Initialize colorama
init(autoreset=True)

def save_company_facts_to_db(company_facts):
    """Save company facts to the PostgreSQL database."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DB_CONNECTION_STRING)
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
        "failed": []
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
                    print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    
                    if verbose:
                        print(f"  Market Cap: ${company_facts.market_cap:,.2f}")
                        print(f"  Industry: {company_facts.industry}")
                        print(f"  Sector: {company_facts.sector}")
                    
                    results["success"].append(ticker)
                else:
                    print(f"{Fore.RED}Failed to save to database{Style.RESET_ALL}")
                    results["failed"].append(ticker)
            else:
                print(f"{Fore.RED}No data available{Style.RESET_ALL}")
                results["failed"].append(ticker)
                
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            results["failed"].append(ticker)
    
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
    print(f"  {Fore.GREEN}Successful:{Style.RESET_ALL} {len(results['success'])} ({', '.join(results['success']) if results['success'] else 'None'})")
    print(f"  {Fore.RED}Failed:{Style.RESET_ALL} {len(results['failed'])} ({', '.join(results['failed']) if results['failed'] else 'None'})")

if __name__ == "__main__":
    main() 