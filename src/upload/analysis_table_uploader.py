import sys
import os
import argparse
from dotenv import load_dotenv

# Add src directory to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_dir = os.path.join(project_root, 'src')
if os.path.exists(src_dir):
    sys.path.insert(0, src_dir)
else:
    print(f"Warning: Could not find src directory at {src_dir}")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Style, init
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from agents.portfolio_manager import portfolio_management_agent
from agents.risk_manager import risk_management_agent
from graph.state import AgentState
from utils.display import print_trading_output
from utils.analysts import ANALYST_CONFIG, get_analyst_nodes
from utils.progress import progress
from llm.models import ModelProvider
from utils.logging import configure_logging
from tools.db_upload import save_to_db
from cfg.sql_table_upload import TABLE_UPLOAD_CONFIG

# Load environment variables from .env file
load_dotenv()
init(autoreset=True)

# Hardcoded parameters
MODEL_NAME = "deepseek-chat"
MODEL_PROVIDER = ModelProvider.DEEPSEEK.value
INITIAL_CASH = 100000.0
MARGIN_REQUIREMENT = 0.0
SHOW_AGENT_GRAPH = True

def parse_hedge_fund_response(response):
    """Parse JSON response from hedge fund agent."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}")
        return None

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
    """Run hedge fund analysis and save results to database."""
    progress.start()
    try:
        workflow = create_workflow(selected_analysts)
        agent = workflow.compile()

        final_state = agent.invoke({
            "messages": [HumanMessage(content="Make trading decisions based on the provided data.")],
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
        })

        result = {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }

        # Save analysis data to database
        for agent_name, agent_data in result["analyst_signals"].items():
            agent_key = agent_name.replace("_agent", "")
            table_name = agent_key if agent_key in TABLE_UPLOAD_CONFIG else "ai_analysis"
            
            if table_name == 'ai_analysis':
                save_ai_analysis_data(
                    agent_name=agent_name,
                    analysis_data=agent_data,
                    biz_date=end_date,
                    state={'metadata': {'model_name': model_name, 'model_provider': model_provider}}
                )
            else:
                # Handle other table types if needed
                pass

        return result
    finally:
        progress.stop()

def create_workflow(selected_analysts=None):
    """Create workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", lambda state: state)
    
    analyst_nodes = get_analyst_nodes()
    selected_analysts = selected_analysts or list(analyst_nodes.keys())
    
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_management_agent", portfolio_management_agent)
    
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_management_agent")
    workflow.add_edge("portfolio_management_agent", END)
    workflow.set_entry_point("start_node")
    
    return workflow

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run hedge fund analysis and save results")
    parser.add_argument("--tickers", type=str, required=True, 
                      help="Comma-separated list of stock tickers")
    parser.add_argument("--verbose", action="store_true", default=False,
                      help="Show detailed reasoning output (default: False)")
    parser.add_argument("--savelog", action="store_true", default=False,
                      help="Save logs to file (default: False)")
    args = parser.parse_args()

    configure_logging(save_logs=args.savelog)
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    selected_analysts = list(get_analyst_nodes().keys())
    
    print(f"\nUsing analysts: {', '.join(Fore.GREEN + ANALYST_CONFIG[choice]['display_name'] + Style.RESET_ALL for choice in selected_analysts)}")
    print(f"\nUsing {Fore.CYAN}DeepSeek{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}deepseek-v3{Style.RESET_ALL}\n")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.strptime(end_date, "%Y-%m-%d") - relativedelta(months=12)).strftime("%Y-%m-%d")

    portfolio = {
        "cash": INITIAL_CASH,
        "margin_requirement": MARGIN_REQUIREMENT,
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            }
            for ticker in tickers
        },
    }

    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=args.verbose,
        selected_analysts=selected_analysts,
        model_name=MODEL_NAME,
        model_provider=MODEL_PROVIDER,
    )
    print_trading_output(result)
