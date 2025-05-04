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
ANALYSTS = ['warren_buffett', 'charlie_munger'] 


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

        # Save analyst data to database
        for agent_name, agent_data in result["analyst_signals"].items():
            # Save AI agents to unified table
            agent_key = agent_name.replace("_agent", "")
            if ANALYST_CONFIG.get(agent_key, {}).get("is_ai_agent", False):
                save_ai_analysis_data(agent_name, agent_data, end_date, final_state)
            # Save specialized agents to their own tables
            elif agent_name == "valuation_agent":
                save_valuation_data(agent_data)
            elif agent_name == "fundamentals_agent":
                save_fundamentals_data(agent_data, end_date)
            elif agent_name == "sentiment_agent":
                save_sentiment_data(agent_data)
            elif agent_name == "technical_analyst_agent":
                save_technical_data(agent_data, end_date)

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


def save_ai_analysis_data(agent_name: str, analysis_data: dict, biz_date: str, state: dict = None):
    """Save AI agent analysis data to unified ai_analysis table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for ticker, data in analysis_data.items():
            cursor.execute(
                """
                INSERT INTO ai_analysis (
                    ticker, agent, signal, confidence, reasoning, 
                    model_name, model_display_name, biz_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker, agent, biz_date, model_display_name) 
                DO UPDATE SET
                    signal = EXCLUDED.signal,
                    confidence = EXCLUDED.confidence,
                    reasoning = EXCLUDED.reasoning,
                    model_name = EXCLUDED.model_name,
                    model_display_name = EXCLUDED.model_display_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    ticker,
                    agent_name.replace("_agent", ""),  # Remove '_agent' suffix
                    data["signal"],
                    data["confidence"],
                    json.dumps(data["reasoning"]) if isinstance(data["reasoning"], dict) else data["reasoning"],
                    state["metadata"]["model_name"] if state else None,
                    state["metadata"]["model_provider"] if state else None,
                    biz_date
                )
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving AI analysis data: {e}")
    finally:
        cursor.close()
        conn.close()

def save_fundamentals_data(fundamentals_data: dict, biz_date: str):
    """Save fundamentals analysis data to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for ticker, data in fundamentals_data.items():
            detail = data["detail"]
            cursor.execute(
                """
                INSERT INTO fundamentals (
                    ticker, biz_date, overall_signal, confidence,
                    return_on_equity, net_margin, operating_margin,
                    profitability_score, profitability_signal,
                    revenue_growth, earnings_growth, book_value_growth,
                    growth_score, growth_signal,
                    current_ratio, debt_to_equity, free_cash_flow_per_share, earnings_per_share,
                    health_score, health_signal,
                    pe_ratio, pb_ratio, ps_ratio,
                    valuation_score, valuation_signal
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                ON CONFLICT (ticker, biz_date) 
                DO UPDATE SET
                    overall_signal = EXCLUDED.overall_signal,
                    confidence = EXCLUDED.confidence,
                    return_on_equity = EXCLUDED.return_on_equity,
                    net_margin = EXCLUDED.net_margin,
                    operating_margin = EXCLUDED.operating_margin,
                    profitability_score = EXCLUDED.profitability_score,
                    profitability_signal = EXCLUDED.profitability_signal,
                    revenue_growth = EXCLUDED.revenue_growth,
                    earnings_growth = EXCLUDED.earnings_growth,
                    book_value_growth = EXCLUDED.book_value_growth,
                    growth_score = EXCLUDED.growth_score,
                    growth_signal = EXCLUDED.growth_signal,
                    current_ratio = EXCLUDED.current_ratio,
                    debt_to_equity = EXCLUDED.debt_to_equity,
                    free_cash_flow_per_share = EXCLUDED.free_cash_flow_per_share,
                    earnings_per_share = EXCLUDED.earnings_per_share,
                    health_score = EXCLUDED.health_score,
                    health_signal = EXCLUDED.health_signal,
                    pe_ratio = EXCLUDED.pe_ratio,
                    pb_ratio = EXCLUDED.pb_ratio,
                    ps_ratio = EXCLUDED.ps_ratio,
                    valuation_score = EXCLUDED.valuation_score,
                    valuation_signal = EXCLUDED.valuation_signal,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    ticker, biz_date, data["signal"], data["confidence"],
                    detail["profitability"]["return_on_equity"],
                    detail["profitability"]["net_margin"],
                    detail["profitability"]["operating_margin"],
                    detail["profitability"]["score"],
                    detail["profitability"]["signal"],
                    detail["growth"]["revenue_growth"],
                    detail["growth"]["earnings_growth"],
                    detail["growth"]["book_value_growth"],
                    detail["growth"]["score"],
                    detail["growth"]["signal"],
                    detail["financial_health"]["current_ratio"],
                    detail["financial_health"]["debt_to_equity"],
                    detail["financial_health"]["free_cash_flow_per_share"],
                    detail["financial_health"]["earnings_per_share"],
                    detail["financial_health"]["score"],
                    detail["financial_health"]["signal"],
                    detail["valuation"]["pe_ratio"],
                    detail["valuation"]["pb_ratio"],
                    detail["valuation"]["ps_ratio"],
                    detail["valuation"]["score"],
                    detail["valuation"]["signal"]
                )
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving fundamentals data: {e}")
    finally:
        cursor.close()
        conn.close()


def save_sentiment_data(sentiment_data: dict):
    """Save sentiment data to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for ticker, data in sentiment_data.items():
            detail = data["detail"]
            cursor.execute(
                """
                INSERT INTO sentiment (
                    ticker, biz_date, overall_signal, confidence,
                    insider_total, insider_bullish, insider_bearish,
                    insider_value_total, insider_value_bullish, insider_value_bearish,
                    insider_weight, news_total, news_bullish, news_bearish, news_neutral,
                    news_weight, weighted_bullish, weighted_bearish
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                ON CONFLICT (ticker, biz_date) 
                DO UPDATE SET
                    overall_signal = EXCLUDED.overall_signal,
                    confidence = EXCLUDED.confidence,
                    insider_total = EXCLUDED.insider_total,
                    insider_bullish = EXCLUDED.insider_bullish,
                    insider_bearish = EXCLUDED.insider_bearish,
                    insider_value_total = EXCLUDED.insider_value_total,
                    insider_value_bullish = EXCLUDED.insider_value_bullish,
                    insider_value_bearish = EXCLUDED.insider_value_bearish,
                    news_total = EXCLUDED.news_total,
                    news_bullish = EXCLUDED.news_bullish,
                    news_bearish = EXCLUDED.news_bearish,
                    news_neutral = EXCLUDED.news_neutral,
                    weighted_bullish = EXCLUDED.weighted_bullish,
                    weighted_bearish = EXCLUDED.weighted_bearish,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    ticker, detail["biz_date"], data["signal"], data["confidence"],
                    detail["insider_total"], detail["insider_bullish"], detail["insider_bearish"],
                    detail["insider_value_total"], detail["insider_value_bullish"], detail["insider_value_bearish"],
                    detail["insider_weight"], detail["news_total"], detail["news_bullish"], detail["news_bearish"], detail["news_neutral"],
                    detail["news_weight"], detail["weighted_bullish"], detail["weighted_bearish"]
                )
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving sentiment data: {e}")
    finally:
        cursor.close()
        conn.close()

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


def save_technical_data(technical_data: dict, biz_date: str):
    """Save technical analysis data to database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for ticker, data in technical_data.items():
            strategies = data["strategy_signals"]
            
            cursor.execute(
                """
                INSERT INTO technicals (
                    ticker, biz_date, signal, confidence,
                    -- Trend Following
                    trend_signal, trend_confidence, trend_score,
                    trend_adx_threshold, trend_ema_crossover_threshold,
                    ema_8, ema_21, ema_55, adx, di_plus, di_minus,
                    -- Mean Reversion
                    mr_signal, mr_confidence, mr_score,
                    mr_z_score_threshold, mr_rsi_low_threshold, mr_rsi_high_threshold,
                    z_score, bb_upper, bb_lower, rsi_14, rsi_28,
                    -- Momentum
                    momentum_signal, momentum_confidence, momentum_score,
                    momentum_min_strength, momentum_volume_ratio_threshold,
                    mom_1m, mom_3m, mom_6m, volume_ratio,
                    -- Volatility
                    volatility_signal, volatility_confidence, volatility_score,
                    volatility_low_regime, volatility_high_regime, volatility_z_threshold,
                    hist_vol_21d, vol_regime, vol_z_score, atr_ratio,
                    -- Statistical Arbitrage
                    stat_arb_signal, stat_arb_confidence, stat_arb_score,
                    stat_arb_hurst_threshold, stat_arb_skew_threshold,
                    hurst_exp, skewness, kurtosis
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (ticker, biz_date) 
                DO UPDATE SET
                    signal = EXCLUDED.signal,
                    confidence = EXCLUDED.confidence,
                    -- Trend Following
                    trend_signal = EXCLUDED.trend_signal,
                    trend_confidence = EXCLUDED.trend_confidence,
                    trend_score = EXCLUDED.trend_score,
                    ema_8 = EXCLUDED.ema_8,
                    ema_21 = EXCLUDED.ema_21,
                    ema_55 = EXCLUDED.ema_55,
                    adx = EXCLUDED.adx,
                    di_plus = EXCLUDED.di_plus,
                    di_minus = EXCLUDED.di_minus,
                    -- Mean Reversion
                    mr_signal = EXCLUDED.mr_signal,
                    mr_confidence = EXCLUDED.mr_confidence,
                    mr_score = EXCLUDED.mr_score,
                    z_score = EXCLUDED.z_score,
                    bb_upper = EXCLUDED.bb_upper,
                    bb_lower = EXCLUDED.bb_lower,
                    rsi_14 = EXCLUDED.rsi_14,
                    rsi_28 = EXCLUDED.rsi_28,
                    -- Momentum
                    momentum_signal = EXCLUDED.momentum_signal,
                    momentum_confidence = EXCLUDED.momentum_confidence,
                    momentum_score = EXCLUDED.momentum_score,
                    mom_1m = EXCLUDED.mom_1m,
                    mom_3m = EXCLUDED.mom_3m,
                    mom_6m = EXCLUDED.mom_6m,
                    volume_ratio = EXCLUDED.volume_ratio,
                    -- Volatility
                    volatility_signal = EXCLUDED.volatility_signal,
                    volatility_confidence = EXCLUDED.volatility_confidence,
                    volatility_score = EXCLUDED.volatility_score,
                    hist_vol_21d = EXCLUDED.hist_vol_21d,
                    vol_regime = EXCLUDED.vol_regime,
                    vol_z_score = EXCLUDED.vol_z_score,
                    atr_ratio = EXCLUDED.atr_ratio,
                    -- Statistical Arbitrage
                    stat_arb_signal = EXCLUDED.stat_arb_signal,
                    stat_arb_confidence = EXCLUDED.stat_arb_confidence,
                    stat_arb_score = EXCLUDED.stat_arb_score,
                    hurst_exp = EXCLUDED.hurst_exp,
                    skewness = EXCLUDED.skewness,
                    kurtosis = EXCLUDED.kurtosis,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    ticker, biz_date, data["signal"], data["confidence"],
                    # Trend Following
                    strategies["trend_following"]["signal"],
                    strategies["trend_following"]["confidence"],
                    strategies["trend_following"]["metrics"].get("trend_strength", 0),
                    25.0, True,  # Default thresholds
                    strategies["trend_following"]["metrics"].get("ema_8", 0),
                    strategies["trend_following"]["metrics"].get("ema_21", 0),
                    strategies["trend_following"]["metrics"].get("ema_55", 0),
                    strategies["trend_following"]["metrics"].get("adx", 0),
                    strategies["trend_following"]["metrics"].get("di_plus", 0),
                    strategies["trend_following"]["metrics"].get("di_minus", 0),
                    # Mean Reversion
                    strategies["mean_reversion"]["signal"],
                    strategies["mean_reversion"]["confidence"],
                    strategies["mean_reversion"]["metrics"].get("z_score", 0),
                    2.0, 30.0, 70.0,  # Default thresholds
                    strategies["mean_reversion"]["metrics"].get("z_score", 0),
                    strategies["mean_reversion"]["metrics"].get("bb_upper", 0),
                    strategies["mean_reversion"]["metrics"].get("bb_lower", 0),
                    strategies["mean_reversion"]["metrics"].get("rsi_14", 0),
                    strategies["mean_reversion"]["metrics"].get("rsi_28", 0),
                    # Momentum
                    strategies["momentum"]["signal"],
                    strategies["momentum"]["confidence"],
                    strategies["momentum"]["metrics"].get("momentum_6m", 0),
                    0.05, 1.0,  # Default thresholds
                    strategies["momentum"]["metrics"].get("momentum_1m", 0),
                    strategies["momentum"]["metrics"].get("momentum_3m", 0),
                    strategies["momentum"]["metrics"].get("momentum_6m", 0),
                    strategies["momentum"]["metrics"].get("volume_momentum", 0),
                    # Volatility
                    strategies["volatility"]["signal"],
                    strategies["volatility"]["confidence"],
                    strategies["volatility"]["metrics"].get("volatility_z_score", 0),
                    0.8, 1.2, 1.0,  # Default thresholds
                    strategies["volatility"]["metrics"].get("historical_volatility", 0),
                    strategies["volatility"]["metrics"].get("volatility_regime", 0),
                    strategies["volatility"]["metrics"].get("volatility_z_score", 0),
                    strategies["volatility"]["metrics"].get("atr_ratio", 0),
                    # Statistical Arbitrage
                    strategies["statistical_arbitrage"]["signal"],
                    strategies["statistical_arbitrage"]["confidence"],
                    strategies["statistical_arbitrage"]["metrics"].get("hurst_exponent", 0.5),
                    0.4, 1.0,  # Default thresholds
                    strategies["statistical_arbitrage"]["metrics"].get("hurst_exponent", 0.5),
                    strategies["statistical_arbitrage"]["metrics"].get("skewness", 0),
                    strategies["statistical_arbitrage"]["metrics"].get("kurtosis", 0)
                )
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving technical data: {e}")
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
    selected_analysts = ANALYSTS
    
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
