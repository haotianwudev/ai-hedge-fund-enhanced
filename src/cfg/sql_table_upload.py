"""
SQL Table Upload Configuration

Contains configuration for financial data uploads including:
- Upload function to call
- Target SQL table name
- API function to get data
- Required parameters
"""

from src.tools.db_upload import (
    load_company_facts_to_db,
    load_prices_to_db,
    load_company_news_to_db,
    load_financial_metrics_to_db,
    load_insider_trades_to_db,
    load_line_items_to_db
)

TABLE_UPLOAD_CONFIG = {
    'company_facts': {
        'upload_function': load_company_facts_to_db,
        'sql_table_name': 'company_facts',
        'params': {}
    },
    'prices': {
        'upload_function': load_prices_to_db,
        'sql_table_name': 'prices',
        'params': ['start_date', 'end_date']
    },
    'company_news': {
        'upload_function': load_company_news_to_db,
        'sql_table_name': 'company_news',
        'params': ['end_date']
    },
    'financial_metrics': {
        'upload_function': load_financial_metrics_to_db,
        'sql_table_name': 'financial_metrics',
        'params': ['end_date']
    },
    'insider_trades': {
        'upload_function': load_insider_trades_to_db,
        'sql_table_name': 'insider_trades',
        'params': ['end_date']
    },
    'line_items': {
        'upload_function': load_line_items_to_db,
        'sql_table_name': 'line_items',
        'params': ['end_date']
    }
}
