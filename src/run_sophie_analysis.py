from src.agents.sophie import sophie_agent, save_prompt_to_log
from tools.api_db import save_sophie_analysis
from src.graph.state import AgentState
from src.llm.models import ModelProvider
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description='Run Sophie analysis on stocks')
    parser.add_argument('--tickers', type=str, required=True, 
                      help='Comma-separated list of stock ticker symbols')
    parser.add_argument('--savelog', action='store_true', default=False,
                      help='Save the full prompt/response to log file (default: False)')
    args = parser.parse_args()

    # Parse tickers from comma-separated string
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]
    
    # Create minimal agent state
    state = AgentState(
        data={
            "tickers": tickers,
            "end_date": None,  # Will use latest available
            "analyst_signals": {}
        },
        metadata={
            "model_name": "deepseek-chat",
            "model_provider": ModelProvider.DEEPSEEK.value,
            "show_reasoning": True
        }
    )

    # Run analysis
    result = sophie_agent(state)
    
    # Process each ticker's analysis
    save_success = True
    for ticker in tickers:
        analysis = result["data"]["analyst_signals"]["sophie_agent"][ticker]
        
        # Save to database
        success = save_sophie_analysis(
            ticker=ticker,
        signal=analysis["signal"],
        confidence=analysis["confidence"],
        overall_score=analysis["overall_score"],
        reasoning=analysis["reasoning"],
        time_horizon_analysis=analysis["time_horizon_analysis"],
        bullish_factors=analysis["bullish_factors"],
        bearish_factors=analysis["bearish_factors"],
        risks=analysis["risks"],
        model_name=state["metadata"]["model_name"],
        model_display_name=ModelProvider(state["metadata"]["model_provider"]).name
    )

    # Save to log if savelog is True
    if args.savelog:
        for ticker in tickers:
            filename = save_prompt_to_log(ticker)
            print(f"Analysis log for {ticker} saved to: {filename}")
    
    # Print overall status
    print(f"Database save {'succeeded' if save_success else 'failed'}")

    # Print results for each ticker
    print("\nAnalysis Results:")
    for ticker in tickers:
        print(f"\n{ticker}:")
        print(json.dumps(result["data"]["analyst_signals"]["sophie_agent"][ticker], indent=2))

if __name__ == "__main__":
    main()
