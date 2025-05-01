# Database Setup and Management

This directory contains SQL scripts for creating and managing the database tables for the AI Hedge Fund project.

## Connection Information

The database is hosted on Neon PostgreSQL:

```
Connection string: postgresql://neondb_owner:npg_IjoHW5gl8AYZ@ep-billowing-wildflower-a4222ksm-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
```

## Available SQL Scripts

- `create_company_facts_table.sql`: Creates the company_facts table for storing company information including market cap.

## Setup Instructions

### Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

### Running Setup Script

To set up the database tables, run:

```bash
python scripts/setup_database.py
```

This will create the company_facts table if it doesn't exist, or update it if it already exists.

## Schema Information

### Company Facts Table

The company_facts table stores information about companies including:

- Basic identification (ticker, name, CIK)
- Sector and industry classification
- Market information (market cap, exchange)
- Company details (employees, location, website)
- SIC information

The table includes a unique constraint on ticker to prevent duplicate entries.

## Using PostgreSQL with Python

Example code to connect to the database from Python:

```python
import psycopg2

# Connect to the database
conn = psycopg2.connect("postgresql://neondb_owner:npg_IjoHW5gl8AYZ@ep-billowing-wildflower-a4222ksm-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require")
cursor = conn.cursor()

# Example: Fetch a company's market cap
cursor.execute("SELECT market_cap FROM company_facts WHERE ticker = %s", ("AAPL",))
market_cap = cursor.fetchone()[0]
print(f"Apple's market cap: {market_cap}")

# Don't forget to close the connection
cursor.close()
conn.close()
``` 