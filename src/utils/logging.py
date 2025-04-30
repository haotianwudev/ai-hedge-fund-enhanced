import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger for LLM interactions
llm_logger = logging.getLogger("llm")
llm_logger.setLevel(logging.INFO)

# Create a logger for portfolio management errors
portfolio_logger = logging.getLogger("portfolio")
portfolio_logger.setLevel(logging.INFO)

# Global variable to control whether logs are displayed to console
show_logs_to_console = False

def configure_logging(show_logs: bool = False):
    """Configure logging settings
    
    Args:
        show_logs: Whether to display logs to console
    """
    global show_logs_to_console
    show_logs_to_console = show_logs
    
    # Set log level based on whether we're showing logs
    log_level = logging.INFO if show_logs else logging.ERROR
    
    # Update handler levels
    for handler in logging.root.handlers:
        handler.setLevel(log_level)

def log_llm_interaction(
    model_name: str, 
    model_provider: str, 
    prompt: Any, 
    response: Any, 
    agent_name: Optional[str] = None,
    error: Optional[Exception] = None
):
    """Log an LLM interaction
    
    Args:
        model_name: The name of the LLM model
        model_provider: The provider of the LLM model
        prompt: The prompt sent to the LLM
        response: The response received from the LLM
        agent_name: Optional name of the agent making the request
        error: Optional exception if an error occurred
    """
    if not show_logs_to_console:
        return
    
    agent_info = f" by {agent_name}" if agent_name else ""
    
    if error:
        llm_logger.error(f"LLM Error with {model_provider} {model_name}{agent_info}: {error}")
        return
    
    llm_logger.info(f"LLM Request to {model_provider} {model_name}{agent_info}")
    llm_logger.info(f"Prompt: {truncate_str(str(prompt), 500)}")
    llm_logger.info(f"Response: {truncate_str(str(response), 500)}")

def log_portfolio_error(error_message: str, ticker: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Log portfolio management errors
    
    Args:
        error_message: The error message
        ticker: Optional ticker symbol related to the error
        details: Optional dictionary with additional error details
    """
    ticker_info = f" for {ticker}" if ticker else ""
    details_str = f": {details}" if details else ""
    
    portfolio_logger.error(f"Portfolio error{ticker_info} - {error_message}{details_str}")

def truncate_str(s: str, max_length: int = 100) -> str:
    """Truncate a string to a maximum length
    
    Args:
        s: The string to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length] + "..." 