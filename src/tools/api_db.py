"""
API functions that use the PostgreSQL database instead of external APIs.
These functions can be used as replacements or fallbacks for the original API functions.
"""

import os
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from src.data.models import CompanyFacts, Price
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    # Get database connection parameters from environment variables
    db_user = os.environ.get("DB_USER", "")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "")
    db_name = os.environ.get("DB_NAME", "")
    db_sslmode = os.environ.get("DB_SSLMODE", "require")
    
    # Build connection string
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}?sslmode={db_sslmode}"
    
    # Fallback to direct connection string if provided (for backward compatibility)
    connection_string = os.environ.get("DATABASE_URL", connection_string)
    
    return psycopg2.connect(connection_string)

def get_company_facts_db(ticker: str) -> CompanyFacts | None:
    """Fetch company facts from the PostgreSQL database."""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query the database
        cursor.execute("SELECT * FROM company_facts WHERE ticker = %s", (ticker,))
        result = cursor.fetchone()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        # Return None if no data found
        if not result:
            return None
        
        # Convert date strings to the format expected by the model
        if result.get('listing_date'):
            result['listing_date'] = result['listing_date'].isoformat()
            
        # Convert the result to a CompanyFacts object
        return CompanyFacts(**result)
        
    except Exception as e:
        print(f"Error fetching company facts from database: {e}")
        return None

def get_market_cap_db(ticker: str) -> float | None:
    """Fetch market cap from the PostgreSQL database."""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query the database
        cursor.execute("SELECT market_cap FROM company_facts WHERE ticker = %s", (ticker,))
        result = cursor.fetchone()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        # Return None if no data found
        if not result:
            return None
        
        return result[0]
        
    except Exception as e:
        print(f"Error fetching market cap from database: {e}")
        return None

def save_company_facts(company_facts: CompanyFacts) -> bool:
    """Save company facts to the PostgreSQL database."""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prepare data for insert/update
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
        print(f"Error saving company facts to database: {e}")
        return False

def get_prices_db(ticker: str, start_date: str, end_date: str) -> list[Price] | None:
    """Fetch price data from the PostgreSQL database for a specific date range."""
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query the database
        cursor.execute(
            "SELECT * FROM prices WHERE ticker = %s AND biz_date >= %s AND biz_date <= %s ORDER BY time DESC", 
            (ticker, start_date, end_date)
        )
        results = cursor.fetchall()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        # Return None if no data found
        if not results:
            return None
        
        # Format dates and convert to Price objects
        prices = []
        for result in results:
            # Convert datetime to ISO format string
            result['time'] = result['time'].isoformat()
            # Create a Price object
            prices.append(Price(**{
                'open': float(result['open']),
                'close': float(result['close']),
                'high': float(result['high']),
                'low': float(result['low']),
                'volume': int(result['volume']),
                'time': result['time']
            }))
        
        return prices
        
    except Exception as e:
        print(f"Error fetching price data from database: {e}")
        return None

def save_prices(ticker: str, prices: list[Price]) -> bool:
    """Save price data to the PostgreSQL database."""
    if not prices:
        return False
        
    try:
        # Connect to PostgreSQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert records
        insert_count = 0
        for price in prices:
            try:
                # Extract date from time for biz_date
                time_obj = datetime.datetime.fromisoformat(price.time.replace('Z', '+00:00'))
                biz_date = time_obj.date()
                
                sql = """
                INSERT INTO prices (ticker, time, biz_date, open, close, high, low, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, biz_date) DO UPDATE SET
                    time = EXCLUDED.time,
                    open = EXCLUDED.open,
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    volume = EXCLUDED.volume,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                cursor.execute(sql, (
                    ticker,
                    price.time,
                    biz_date,
                    price.open,
                    price.close,
                    price.high,
                    price.low,
                    price.volume
                ))
                insert_count += 1
            except Exception as inner_e:
                print(f"Error inserting price for {ticker} on {price.time}: {inner_e}")
        
        # Commit the transaction
        conn.commit()
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        print(f"Successfully saved {insert_count} price records for {ticker}")
        return True
        
    except Exception as e:
        print(f"Error saving price data to database: {e}")
        return False 