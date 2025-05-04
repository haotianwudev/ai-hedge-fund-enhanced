from src.agents.sophie import sophie_agent, save_prompt_to_log
from src.graph.state import AgentState
from src.llm.models import ModelProvider
import argparse
import json

def main():
    parser = argparse.ArgumentParser(description='Run Sophie analysis on a stock')
    parser.add_argument('ticker', type=str, help='Stock ticker to analyze')
    args = parser.parse_args()

    # Create minimal agent state
    state = AgentState(
        data={
            "tickers": [args.ticker],
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
    
    # Save to log
    filename = save_prompt_to_log(args.ticker)
    print(f"Analysis saved to: {filename}")

    # Print results
    print("\nAnalysis Results:")
    print(json.dumps(result["data"]["analyst_signals"]["sophie_agent"], indent=2))

if __name__ == "__main__":
    main()
