#!/usr/bin/env python
"""
Database setup script to create tables in PostgreSQL.
This script executes the SQL file to create the company_facts table.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection string
DB_CONNECTION_STRING = "postgresql://neondb_owner:npg_IjoHW5gl8AYZ@ep-billowing-wildflower-a4222ksm-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

def execute_sql_file(file_path):
    """Execute SQL commands from a file."""
    print(f"Executing SQL file: {file_path}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read SQL file content
        with open(file_path, 'r') as sql_file:
            sql_script = sql_file.read()
        
        # Execute SQL commands
        cursor.execute(sql_script)
        
        print("SQL execution completed successfully")
        
    except Exception as e:
        print(f"Error executing SQL: {e}")
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to SQL file (one directory up from util, then into sql directory)
    sql_file_path = os.path.join(script_dir, '..', 'sql', 'create_company_facts_table.sql')
    
    # Execute SQL file
    execute_sql_file(sql_file_path)

if __name__ == "__main__":
    main() 