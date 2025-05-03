import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Style, init

from agents.portfolio_manager import portfolio_management_agent
from agents.risk_manager import risk_management_agent
from graph.state import AgentState
from utils.display import print_trading_output
from utils.analysts import ANALYST_CONFIG, get_analyst_nodes
from utils.progress import progress
from llm.models import ModelProvider
from utils.logging import configure_logging

# Import the services instead of direct API functions
from tools.price_service import get_prices, get_price_data
from tools.financial_metrics_service import get_financial_metrics, get_financial_metrics_df
from tools.company_news_service import get_company_news, get_company_news_df
from tools.insider_trades_service import get_insider_trades, get_insider_trades_df
from tools.line_items_service import search_line_items, get_line_items_df
from tools.setup_database import get_db_connection

from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)

# Hardcoded parameters
TICKERS = [ "AAPL", "NVDA", "MSFT" ]
MODEL_NAME = "deepseek-chat"
MODEL_PROVIDER = ModelProvider.DEEPSEEK.value
INITIAL_CASH = 100000.0
MARGIN_REQUIREMENT = 0.0
SHOW_REASONING = True
SHOW_AGENT_GRAPH = True
SAVE_LOGS = True


def parse_hedge_fund_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}\nResponse: {repr(response)}")
        return None


##### Run the Hedge Fund #####
def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict,
    show_reasoning: bool = False,
    selected_analysts: list[str] = None,
    model_name: str = "deepseek-chat",
    model_provider: str = "DeepSeek",
):
    # Start progress tracking
    progress.start()

    try:
        # Create a new workflow with all analysts
        workflow = create_workflow(selected_analysts)
        agent = workflow.compile()

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "tickers": tickers,
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        result = {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }

        # Save valuation data to database if valuation agent was run
        if "valuation_agent" in result["analyst_signals"]:
            save_valuation_data(result["analyst_signals"]["valuation_agent"])

        return result
    finally:
        # Stop progress tracking
        progress.stop()


def start(state: AgentState):
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration    
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())
    
    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_management_agent", portfolio_management_agent)

    # Connect selected analysts to risk management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_management_agent")
    workflow.add_edge("portfolio_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


def save_valuation_data(valuation_data: dict):
    """Save valuation data to the database with UPSERT functionality."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for ticker, data in valuation_data.items():
            for method in data["detail"]:
                cursor.execute(
                    """
                    INSERT INTO valuation (
                        ticker,
                        valuation_method,
                        intrinsic_value,
                        market_cap,
                        gap,
                        signal,
                        biz_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, valuation_method, biz_date) 
                    DO UPDATE SET
                        intrinsic_value = EXCLUDED.intrinsic_value,
                        market_cap = EXCLUDED.market_cap,
                        gap = EXCLUDED.gap,
                        signal = EXCLUDED.signal,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        ticker,
                        method["valuation_method"],
                        method["intrinsic_value"],
                        method["market_cap"],
                        method["gap"],
                        method["signal"],
                        method["biz_date"]
                    )
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving valuation data: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Configure logging
    configure_logging(save_logs=SAVE_LOGS)

    # Hardcoded ticker
    tickers = TICKERS
    
    # Use all analysts
    #selected_analysts = list(ANALYST_CONFIG.keys())
    selected_analysts = ['valuation_analyst'] 
    
    print(f"\nUsing all analysts: {', '.join(Fore.GREEN + ANALYST_CONFIG[choice]['display_name'] + Style.RESET_ALL for choice in selected_analysts)}\n")
    
    # Using DeepSeek v3 model
    print(f"\nUsing {Fore.CYAN}DeepSeek{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}deepseek-v3{Style.RESET_ALL}\n")

    # Create the workflow with all analysts
    workflow = create_workflow(selected_analysts)
    app = workflow.compile()

    # Set the start and end dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    # Calculate 3 months before end_date
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date = (end_date_obj - relativedelta(months=12)).strftime("%Y-%m-%d")

    # Initialize portfolio with cash amount and stock positions
    portfolio = {
        "cash": INITIAL_CASH,  # Initial cash amount
        "margin_requirement": MARGIN_REQUIREMENT,  # Initial margin requirement
        "margin_used": 0.0,  # total margin usage across all short positions
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            }
            for ticker in tickers
        },
    }

    # Run the hedge fund
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=SHOW_REASONING,
        selected_analysts=selected_analysts,
        model_name=MODEL_NAME,
        model_provider=MODEL_PROVIDER,
    )
    print_trading_output(result)
