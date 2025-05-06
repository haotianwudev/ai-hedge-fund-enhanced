#!/usr/bin/env python
"""
Database Upload Functions

This module contains all functions related to uploading financial data to the PostgreSQL database.
Moved from src/upload/load_financial_data.py as part of refactoring.
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from colorama import Fore, Style
from datetime import datetime
from src.cfg.line_items_list import LINE_ITEMS

def save_to_db(data, upload_func, table_name=None, verbose=False):
    """Generic function to save data to database with standardized logging"""
    try:
        if verbose:
            print(f"Saving data to {table_name or 'default'} table...")
        
        result = upload_func(data, table_name=table_name)
        
        if verbose:
            record_count = len(data) if hasattr(data, '__len__') else 1
            print(f"Successfully saved {record_count} records to {table_name or 'default'} table")
            
        return result
    except Exception as e:
        if verbose:
            print(f"{Fore.RED}Failed to save data: {e}{Style.RESET_ALL}")
        return False

def load_company_facts_to_db(tickers, verbose=False):
    """Load and save company facts for multiple tickers to the PostgreSQL database."""
    if not tickers:
        return False
        
    try:
        from tools.api import get_company_facts
        
        success = []
        failed = []
        
        for ticker in tickers:
            if verbose:
                print(f"Loading company facts for {ticker}...", end=" ", flush=True)
            
            try:
                facts = get_company_facts(ticker)
                if not facts:
                    if verbose:
                        print(f"{Fore.YELLOW}No data{Style.RESET_ALL}")
                    failed.append(ticker)
                    continue
                    
                if save_company_facts_to_db(facts):
                    if verbose:
                        print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    success.append(ticker)
                else:
                    if verbose:
                        print(f"{Fore.RED}Failed to save{Style.RESET_ALL}")
                    failed.append(ticker)
            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                failed.append(ticker)
                
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in batch company facts loading: {e}{Style.RESET_ALL}")
        return False

def save_company_facts_to_db(company_facts, table_name=None):
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

def load_prices_to_db(tickers, start_date, end_date, verbose=False):
    """Load and save price data for multiple tickers to the PostgreSQL database."""
    if not tickers:
        return False
        
    try:
        from tools.api import get_prices
        
        success = []
        failed = []
        
        for ticker in tickers:
            if verbose:
                print(f"Loading prices for {ticker}...", end=" ", flush=True)
            
            try:
                prices = get_prices(ticker, start_date, end_date)
                if not prices:
                    if verbose:
                        print(f"{Fore.YELLOW}No data{Style.RESET_ALL}")
                    failed.append(ticker)
                    continue
                    
                if save_prices_to_db(ticker, prices):
                    if verbose:
                        print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    success.append(ticker)
                else:
                    if verbose:
                        print(f"{Fore.RED}Failed to save{Style.RESET_ALL}")
                    failed.append(ticker)
            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                failed.append(ticker)
                
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in batch price loading: {e}{Style.RESET_ALL}")
        return False

def save_prices_to_db(ticker, prices):
    """
    Save price data to the PostgreSQL database using the api_db module.
    This is a simple wrapper around the api_db.save_prices function.
    """
    if not prices:
        return False
    
    try:
        from tools.api_db import save_prices
        return save_prices(ticker, prices)
    except Exception as e:
        print(f"{Fore.RED}Error saving price data to database: {e}{Style.RESET_ALL}")
        return False

def load_company_news_to_db(tickers, end_date, verbose=False):
    """Load and save company news for multiple tickers to the PostgreSQL database."""
    if not tickers:
        return False
        
    try:
        from tools.api import get_company_news
        
        success = []
        failed = []
        
        for ticker in tickers:
            if verbose:
                print(f"Loading news for {ticker}...", end=" ", flush=True)
            
            try:
                news = get_company_news(ticker, end_date)
                if not news:
                    if verbose:
                        print(f"{Fore.YELLOW}No data{Style.RESET_ALL}")
                    failed.append(ticker)
                    continue
                    
                if save_company_news_to_db(ticker, news):
                    if verbose:
                        print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    success.append(ticker)
                else:
                    if verbose:
                        print(f"{Fore.RED}Failed to save{Style.RESET_ALL}")
                    failed.append(ticker)
            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                failed.append(ticker)
                
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in batch news loading: {e}{Style.RESET_ALL}")
        return False

def save_company_news_to_db(ticker, news):
    """Save company news to the PostgreSQL database using the api_db module."""
    if not news:
        return False
    
    try:
        from tools.api_db import save_company_news
        return save_company_news(news)
    except Exception as e:
        print(f"{Fore.RED}Error saving company news to database: {e}{Style.RESET_ALL}")
        return False

def load_financial_metrics_to_db(tickers, end_date, verbose=False):
    """Load and save financial metrics for multiple tickers to the PostgreSQL database."""
    if not tickers:
        return False
        
    try:
        from tools.api import get_financial_metrics
        
        success = []
        failed = []
        
        for ticker in tickers:
            if verbose:
                print(f"Loading metrics for {ticker}...", end=" ", flush=True)
            
            try:
                metrics = get_financial_metrics(ticker, end_date)
                if not metrics:
                    if verbose:
                        print(f"{Fore.YELLOW}No data{Style.RESET_ALL}")
                    failed.append(ticker)
                    continue
                    
                if save_financial_metrics_to_db(metrics):
                    if verbose:
                        print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    success.append(ticker)
                else:
                    if verbose:
                        print(f"{Fore.RED}Failed to save{Style.RESET_ALL}")
                    failed.append(ticker)
            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                failed.append(ticker)
                
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in batch metrics loading: {e}{Style.RESET_ALL}")
        return False

def save_financial_metrics_to_db(metrics):
    """Save financial metrics to the PostgreSQL database using the api_db module."""
    if not metrics:
        return False
    
    try:
        from tools.api_db import save_financial_metrics
        return save_financial_metrics(metrics)
    except Exception as e:
        print(f"{Fore.RED}Error saving financial metrics to database: {e}{Style.RESET_ALL}")
        return False

def load_insider_trades_to_db(tickers, end_date, verbose=False):
    """Load and save insider trades for multiple tickers to the PostgreSQL database."""
    if not tickers:
        return False
        
    try:
        from tools.api import get_insider_trades
        
        success = []
        failed = []
        
        for ticker in tickers:
            if verbose:
                print(f"Loading insider trades for {ticker}...", end=" ", flush=True)
            
            try:
                trades = get_insider_trades(ticker, end_date)
                if not trades:
                    if verbose:
                        print(f"{Fore.YELLOW}No data{Style.RESET_ALL}")
                    failed.append(ticker)
                    continue
                    
                if save_insider_trades_to_db(ticker, trades):
                    if verbose:
                        print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                    success.append(ticker)
                else:
                    if verbose:
                        print(f"{Fore.RED}Failed to save{Style.RESET_ALL}")
                    failed.append(ticker)
            except Exception as e:
                if verbose:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                failed.append(ticker)
                
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in batch insider trades loading: {e}{Style.RESET_ALL}")
        return False

def save_insider_trades_to_db(ticker, trades):
    """Save insider trades to the PostgreSQL database using the api_db module."""
    if not trades:
        return False
    
    try:
        from tools.api_db import save_insider_trades
        return save_insider_trades(trades)
    except Exception as e:
        print(f"{Fore.RED}Error saving insider trades to database: {e}{Style.RESET_ALL}")
        return False

def load_line_items_to_db(tickers, end_date, verbose=False):
    """Batch load line items for multiple tickers to PostgreSQL database."""
    if not tickers:
        return {'success': [], 'failed': []}
        
    try:
        from tools.api import search_line_items
        
        if verbose:
            print(f"Loading line items for {len(tickers)} tickers...")
        
        all_line_items = search_line_items(
            tickers=tickers,
            line_items=LINE_ITEMS,
            end_date=end_date
        )

        if not all_line_items:
            if verbose:
                print(f"{Fore.YELLOW}No line items found{Style.RESET_ALL}")
            return {'success': [], 'failed': tickers}
        
        # Group by ticker
        ticker_items = {}
        for item in all_line_items:
            ticker_items.setdefault(item.ticker, []).append(item)
        
        # Process results
        success = []
        failed = []
        
        for ticker in tickers:
            items = ticker_items.get(ticker, [])
            if not items:
                if verbose:
                    print(f"{Fore.YELLOW}No items for {ticker}{Style.RESET_ALL}")
                failed.append(ticker)
                continue
                
            if save_line_items_to_db(ticker, items):
                success.append(ticker)
            else:
                failed.append(ticker)
                
        if verbose:
            print(f"{Fore.GREEN}Saved line items for {len(success)}/{len(tickers)} tickers{Style.RESET_ALL}")
            
        return {'success': success, 'failed': failed}
        
    except Exception as e:
        print(f"{Fore.RED}Error in line items batch load: {e}{Style.RESET_ALL}")
        return {'success': [], 'failed': tickers}

def save_line_items_to_db(ticker, line_items):
    """Save line items to the PostgreSQL database using the api_db module."""
    if not line_items:
        return False
    
    try:
        from tools.api_db import save_line_items
        return save_line_items(ticker, line_items)
    except Exception as e:
        print(f"{Fore.RED}Error saving line items to database: {e}{Style.RESET_ALL}")
        return False
