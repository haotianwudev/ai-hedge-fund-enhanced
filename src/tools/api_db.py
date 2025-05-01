"""
API functions that use the PostgreSQL database instead of external APIs.
These functions can be used as replacements or fallbacks for the original API functions.
"""

import os
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from src.data.models import CompanyFacts
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

def get_market_cap_db(ticker: str, end_date: str) -> float | None:
    """Fetch market cap from the PostgreSQL database."""
    # Check if end_date is today
    if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
        # Get market cap from company_facts table
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
    
    # For historical data, we would need a different approach
    # This is a placeholder for future implementation
    print(f"Historical market cap data for {ticker} on {end_date} not available in database")
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