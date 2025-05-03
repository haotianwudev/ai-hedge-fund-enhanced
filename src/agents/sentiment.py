from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import pandas as pd
import numpy as np
import json

from tools.insider_trades_service import get_insider_trades
from tools.company_news_service import get_company_news


##### Sentiment Agent #####
def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals for multiple tickers."""
    data = state.get("data", {})
    end_date = data.get("end_date")
    tickers = data.get("tickers")

    # Initialize sentiment analysis for each ticker
    sentiment_analysis = {}

    for ticker in tickers:
        progress.update_status("sentiment_agent", ticker, "Fetching insider trades")

        # Get the insider trades using the service
        insider_trades = get_insider_trades(
            ticker=ticker,
            end_date=end_date,
            limit=1000,
        )

        progress.update_status("sentiment_agent", ticker, "Analyzing trading patterns")

        # Get the signals and values from the insider trades
        transaction_shares = pd.Series([t.transaction_shares for t in insider_trades]).dropna()
        transaction_values = pd.Series([t.transaction_value for t in insider_trades]).dropna()
        insider_signals = np.where(transaction_shares < 0, "bearish", "bullish").tolist()
        
        # Calculate insider value metrics (bearish values are negative)
        insider_value_bullish = transaction_values[transaction_shares > 0].sum()
        insider_value_bearish = -transaction_values[transaction_shares < 0].sum()  # Negative for sells
        insider_value_total = insider_value_bullish + insider_value_bearish  # Net of buys and sells

        progress.update_status("sentiment_agent", ticker, "Fetching company news")

        # Get the company news using the service
        company_news = get_company_news(ticker, end_date, limit=100)

        # Get the sentiment from the company news
        sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
        news_signals = np.where(sentiment == "negative", "bearish", 
                              np.where(sentiment == "positive", "bullish", "neutral")).tolist()
        
        progress.update_status("sentiment_agent", ticker, "Combining signals")
        # Combine signals from both sources with weights
        insider_weight = 0.3
        news_weight = 0.7
        
        # Calculate weighted signal counts
        bullish_signals = (
            insider_signals.count("bullish") * insider_weight +
            news_signals.count("bullish") * news_weight
        )
        bearish_signals = (
            insider_signals.count("bearish") * insider_weight +
            news_signals.count("bearish") * news_weight
        )

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Calculate confidence level based on the weighted proportion
        total_weighted_signals = len(insider_signals) * insider_weight + len(news_signals) * news_weight
        confidence = 0  # Default confidence when there are no signals
        if total_weighted_signals > 0:
            confidence = round(max(bullish_signals, bearish_signals) / total_weighted_signals, 2) * 100
        reasoning = f"Weighted Bullish signals: {bullish_signals:.1f}, Weighted Bearish signals: {bearish_signals:.1f}"

        sentiment_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "detail": {
                "insider_total": len(insider_signals),
                "insider_bullish": insider_signals.count("bullish"),
                "insider_bearish": insider_signals.count("bearish"),
                "insider_value_total": float(insider_value_total),
                "insider_value_bullish": float(insider_value_bullish),
                "insider_value_bearish": float(insider_value_bearish),
                "insider_weight": 0.3,
                "news_total": len(news_signals),
                "news_bullish": news_signals.count("bullish"),
                "news_bearish": news_signals.count("bearish"),
                "news_neutral": news_signals.count("neutral"),
                "news_weight": 0.7,
                "weighted_bullish": bullish_signals,
                "weighted_bearish": bearish_signals,
                "biz_date": end_date
            }
        }

        progress.update_status("sentiment_agent", ticker, "Done")

    # Create the sentiment message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_agent",
    )

    # Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["sentiment_agent"] = sentiment_analysis

    return {
        "messages": [message],
        "data": data,
    }
