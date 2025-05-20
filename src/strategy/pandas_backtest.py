import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any

def estimate_put_option_price(S: float, K: float, T: float, r: float, sigma: float, dividend_yield: float = 0.0) -> float:
    """
    Estimate the price of a put option using the Black-Scholes model.
    
    Args:
        S: Current price of the underlying asset
        K: Strike price of the option
        T: Time to expiration in years (e.g., 21/252 for 21 trading days)
        r: Risk-free interest rate (as a decimal)
        sigma: Implied volatility (VIX/100 for SPY options)
        dividend_yield: Annual dividend yield of the underlying asset (as a decimal)
        
    Returns:
        Put option price
    """
    # Black-Scholes formula for put option
    d1 = (np.log(S / K) + (r - dividend_yield + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    put_price = K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * np.exp(-dividend_yield * T) * stats.norm.cdf(-d1)
    
    return put_price

def backtest_option_strategy(model_probs, actual_crashes, spy_prices, vix_values, threshold=0.5, strike_pct=0.95, option_expiry_days=int(252 / 12)):
    """
    Backtest a strategy that buys put options when crash probability exceeds threshold.
    
    Strategy:
    - When crash probability exceeds threshold AND we don't already have an active option,
      buy a put option with strike at strike_pct of current price
    - Sell option when probability falls below threshold (or at expiration)
    - Option is valued at each time step using Black-Scholes pricing
    
    Args:
        model_probs: Series of model crash probabilities
        actual_crashes: Series of actual crash labels
        spy_prices: Series of SPY prices
        vix_values: Series of VIX values (used for implied volatility)
        threshold: Probability threshold for buying options (default: 0.5)
        strike_pct: Strike price as percentage of current price (default: 0.9 = 10% OTM)
        option_expiry_days: Days until option expiration (default: 21 trading days)
        
    Returns:
        DataFrame: Strategy results
    """
    # model_probs = pd.Series(rf_probs, index=X_test.index)
    # actual_crashes = y_test
    # spy_prices = spy_prices
    # threshold=0.6
    # strike_pct=0.9
    # option_expiry_days= int(252 / 12)
    
    # Interest rate assumption
    risk_free_rate = 0.02
    # Option coverage
    option_coverage = 1.0  # Protect 30% of the portfolio
    
    # Initialize strategy DataFrame
    strategy = pd.DataFrame({
        'date': model_probs.index,
        'spy_price': spy_prices,
        'spy_return': spy_prices.pct_change(),
        'vix': vix_values,
        'prob': model_probs,
        'actual_crash': actual_crashes,
        'signal': (model_probs >= threshold).astype(int),
        'stock_balance': spy_prices,
    })
    strategy['has_active_option'] = False
    strategy['option_start_idx'] = -1
    strategy['option_expiry_idx'] = -1
    strategy['strike_price'] = np.nan
    strategy['option_price'] = np.nan
    strategy['option_cost'] = np.nan
    strategy['option_balance'] = 0.0
    strategy['cash_balance'] = 0.0 # cash to track option PNL, given no stock trade
    strategy['exit_type'] = ""  # "expiry", "threshold_exit", "still_active"
    strategy['strategy_balance'] = 0.0
    strategy['strategy_return'] = 0.0
    strategy['cum_strategy_dollar_return'] = 0.0
    strategy['cum_strategy_return'] = 0.0
    
    # Simulate the strategy
    active_option = False
    option_start_idx = -1
    option_expiry_idx = -1
    strike_price = np.nan
    entry_option_price = np.nan
    
    for i in range(len(strategy)):
        current_date = strategy.iloc[i].date
        current_price = strategy.iloc[i]['spy_price']
        current_prob = strategy.iloc[i]['prob']

        if i > 0:
            # initial position of cash balance for every day may change later
            strategy.iloc[i, strategy.columns.get_loc('cash_balance')] = strategy.iloc[i-1]['cash_balance']
        
        # Check if we have an active option
        if active_option:
            # Mark this day as having an active option
            strategy.iloc[i, strategy.columns.get_loc('has_active_option')] = True
            strategy.iloc[i, strategy.columns.get_loc('option_start_idx')] = option_start_idx
            strategy.iloc[i, strategy.columns.get_loc('option_expiry_idx')] = option_expiry_idx
            strategy.iloc[i, strategy.columns.get_loc('strike_price')] = strike_price
            strategy.iloc[i, strategy.columns.get_loc('option_cost')] = option_cost
            
            # Calculate current option value using Black-Scholes
            remaining_days = option_expiry_idx - i
            if remaining_days > 0:
                # Option still has time value
                days_to_expiry = remaining_days / 252  # Convert to years
                implied_vol = strategy.iloc[i]['vix'] / 100
                
                # Calculate current option price
                current_option_price = estimate_put_option_price(
                    S=current_price,
                    K=strike_price,
                    T=days_to_expiry,
                    r=risk_free_rate,
                    sigma=implied_vol
                )
                
                strategy.iloc[i, strategy.columns.get_loc('option_price')] = current_option_price
                strategy.iloc[i, strategy.columns.get_loc('option_balance')] = current_option_price * option_coverage    
                                
                # Check if we should exit based on threshold
                if current_prob < threshold and current_option_price > option_cost:
                    # Exit the position as probability is below threshold                
                    strategy.iloc[i, strategy.columns.get_loc('exit_type')] = "threshold_exit"
                    strategy.iloc[i, strategy.columns.get_loc('cash_balance')] += current_option_price * option_coverage
                    strategy.iloc[i, strategy.columns.get_loc('option_balance')] = 0 
                    active_option = False
                    continue  
            
            # Check if option is expiring today
            if i == option_expiry_idx:
                # Calculate payoff at expiration (intrinsic value only)
                payoff = max(0, strike_price - current_price)
                
                # Record the final payoff
                strategy.iloc[i, strategy.columns.get_loc('option_price')] = payoff # this is daily backtesting, so no time value
                strategy.iloc[i, strategy.columns.get_loc('cash_balance')] += payoff * option_coverage
                strategy.iloc[i, strategy.columns.get_loc('option_balance')] = 0
                strategy.iloc[i, strategy.columns.get_loc('exit_type')] = "expiry"
                
                # Close the position
                active_option = False
        
        # Check if we should open a new position (only if no active option)
        elif strategy.iloc[i]['signal'] == 1:
            # Calculate option parameters
            implied_vol = strategy.iloc[i]['vix'] / 100
            strike_price = current_price * strike_pct
            
            # Calculate option price
            entry_option_price = estimate_put_option_price(
                S=current_price,
                K=strike_price,
                T=option_expiry_days/252,  # Convert to years
                r=risk_free_rate,
                sigma=implied_vol
            )
            
            # Calculate cost as percentage of portfolio
            option_cost = entry_option_price * option_coverage
            
            # Record option details
            active_option = True
            option_start_idx = i
            option_expiry_idx = i + option_expiry_days
            
            # Record in the strategy DataFrame
            strategy.iloc[i, strategy.columns.get_loc('has_active_option')] = True
            strategy.iloc[i, strategy.columns.get_loc('option_start_idx')] = option_start_idx
            strategy.iloc[i, strategy.columns.get_loc('option_expiry_idx')] = option_expiry_idx
            strategy.iloc[i, strategy.columns.get_loc('strike_price')] = strike_price
            strategy.iloc[i, strategy.columns.get_loc('option_price')] = entry_option_price
            strategy.iloc[i, strategy.columns.get_loc('option_cost')] = option_cost
            strategy.iloc[i, strategy.columns.get_loc('option_balance')] = option_cost
            strategy.iloc[i, strategy.columns.get_loc('cash_balance')] -= option_cost
    
    # Calculate strategy returns
    initial_balance = strategy.iloc[0]['stock_balance']
    
    for i in range(len(strategy)):
        strategy.iloc[i, strategy.columns.get_loc('strategy_balance')] = strategy.iloc[i]['stock_balance'] + strategy.iloc[i]['option_balance'] + strategy.iloc[i]['cash_balance']
        strategy.iloc[i, strategy.columns.get_loc('cum_strategy_dollar_return')] = strategy.iloc[i]['strategy_balance'] - initial_balance
        strategy.iloc[i, strategy.columns.get_loc('cum_strategy_return')] = strategy.iloc[i]['cum_strategy_dollar_return'] / initial_balance
        if i > 0:
            strategy.iloc[i, strategy.columns.get_loc('strategy_return')] = strategy.iloc[i]['strategy_balance'] / strategy.iloc[i - 1]['strategy_balance'] - 1
    
    strategy['benchmark_balance'] = strategy['stock_balance']
    strategy['cum_benchmark_dollar_return'] = 0
    strategy['cum_benchmark_return'] = 0
    strategy['benchmark_return'] = 0
    for i in range(len(strategy)):
        strategy.iloc[i, strategy.columns.get_loc('cum_benchmark_dollar_return')] = strategy.iloc[i]['benchmark_balance'] - initial_balance
        strategy.iloc[i, strategy.columns.get_loc('cum_benchmark_return')] = strategy.iloc[i]['cum_benchmark_dollar_return'] / initial_balance
        if i > 0:
            strategy.iloc[i, strategy.columns.get_loc('benchmark_return')] = strategy.iloc[i]['benchmark_balance'] / strategy.iloc[i - 1]['benchmark_balance'] - 1
    
    
    # Calculate drawdowns
    strategy['strategy_peak'] = strategy['cum_strategy_return'].cummax()
    strategy['benchmark_peak'] = strategy['cum_benchmark_return'].cummax()
    
    strategy['strategy_drawdown'] = (strategy['cum_strategy_return'] - strategy['strategy_peak'])
    strategy['benchmark_drawdown'] = (strategy['cum_benchmark_return'] - strategy['benchmark_peak'])
    
    # Calculate drawdown duration
    strategy['strategy_drawdown_duration'] = 0
    strategy['benchmark_drawdown_duration'] = 0
    current_drawdown_duration = 0
    current_benchmark_drawdown_duration = 0
    
    for i in range(1, len(strategy)):
        if strategy.iloc[i]['strategy_drawdown'] < 0:
            current_drawdown_duration += 1
        else:
            current_drawdown_duration = 0
        if strategy.iloc[i]['benchmark_drawdown'] < 0:
            current_benchmark_drawdown_duration += 1
        else:
            current_benchmark_drawdown_duration = 0
            
        strategy.iloc[i, strategy.columns.get_loc('strategy_drawdown_duration')] = current_drawdown_duration
        strategy.iloc[i, strategy.columns.get_loc('benchmark_drawdown_duration')] = current_benchmark_drawdown_duration
    
    # Calculate performance metrics
    total_periods = len(strategy)
    option_periods = strategy[strategy['has_active_option']].shape[0]
    option_entries = len(strategy[strategy['option_start_idx'] == range(len(strategy))])
    option_pct = option_periods / total_periods
    
    # Count exit types
    expiry_exits = len(strategy[strategy['exit_type'] == "expiry"])
    threshold_exits = len(strategy[strategy['exit_type'] == "threshold_exit"])
    still_active = len(strategy[strategy['exit_type'] == "still_active"])
    
    strategy_return = strategy['cum_strategy_return'].iloc[-1]
    benchmark_return = strategy['cum_benchmark_return'].iloc[-1]
    
    strategy_max_drawdown = strategy['strategy_drawdown'].min()
    benchmark_max_drawdown = strategy['benchmark_drawdown'].min()
    
    # Calculate average drawdown
    strategy_avg_drawdown = strategy[strategy['strategy_drawdown'] < 0]['strategy_drawdown'].mean()
    benchmark_avg_drawdown = strategy[strategy['benchmark_drawdown'] < 0]['benchmark_drawdown'].mean()
    
    # Calculate max drawdown duration
    strategy_max_drawdown_duration = strategy['strategy_drawdown_duration'].max()
    benchmark_max_drawdown_duration = strategy['benchmark_drawdown_duration'].max()
    
    strategy_volatility = strategy['strategy_return'].std() * np.sqrt(252)  # Annualized
    benchmark_volatility = strategy['benchmark_return'].std() * np.sqrt(252)  # Annualized
    
    strategy_sharpe = strategy_return / strategy_volatility if strategy_volatility > 0 else 0
    benchmark_sharpe = benchmark_return / benchmark_volatility if benchmark_volatility > 0 else 0
    
    # Calculate option-specific metrics
    total_option_cost = strategy[~strategy['exit_type'].isnull()]['option_balance'].sum()
    
    # Display metrics
    print(f"Option Strategy Performance (threshold = {threshold}):")
    print(f"Option positions opened: {option_entries}")
    print(f"Exit types - Expiry: {expiry_exits}, Threshold exits: {threshold_exits}, Still active: {still_active}")
    print(f"SPY Return: {benchmark_return:.2%}, Strategy Return: {strategy_return:.2%}")
    print(f"SPY Max Drawdown: {benchmark_max_drawdown:.2%}, Strategy Max Drawdown: {strategy_max_drawdown:.2%}")
    print(f"SPY Max Drawdown Duration: {benchmark_max_drawdown_duration} days, Strategy Max Drawdown Duration: {strategy_max_drawdown_duration} days")
    print(f"SPY Volatility: {benchmark_volatility:.2%}, Strategy Volatility: {strategy_volatility:.2%}")
    print(f"SPY Sharpe: {benchmark_sharpe:.2f}, Strategy Sharpe: {strategy_sharpe:.2f}")
    print(f"Total option cost: {total_option_cost}")
    
    # Plot performance
    plt.figure(figsize=(14, 10))
    
    # Plot 1: Cumulative Returns
    plt.subplot(2, 1, 1)
    plt.plot(strategy['date'], strategy['cum_benchmark_return'], 'b-', label='SPY')
    plt.plot(strategy['date'], strategy['cum_strategy_return'], 'r-', label='Option Strategy')
    
    # Highlight periods when options were active
    option_periods = strategy[strategy['has_active_option']]
    option_starts = strategy[strategy['option_start_idx'] >= 0]
    
    for i in range(len(option_starts)):
        start_idx = option_starts.iloc[i]['option_start_idx']
        end_idx = option_starts.iloc[i]['option_expiry_idx']
        if end_idx >= len(strategy):
            end_idx = len(strategy) - 1
            
        start_date = strategy.iloc[int(start_idx)]['date']
        
        # Find actual end date (might be earlier than expiry due to threshold exit)
        actual_end_idx = end_idx
        for j in range(int(start_idx), int(end_idx) + 1):
            if strategy.iloc[j]['exit_type'] in ["expiry", "threshold_exit"]:
                actual_end_idx = j
                break
                
        end_date = strategy.iloc[int(actual_end_idx)]['date']
        
        plt.axvspan(start_date, end_date, color='lightgreen', alpha=0.5)
    
    # Mark crash events
    crash_dates = strategy[strategy['actual_crash'] == 1].date
    for date in crash_dates:
        plt.axvline(x=date, color='red', linestyle='--', alpha=0.5)
    
    plt.title('Cumulative Returns: SPY vs Option Strategy')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Drawdowns
    plt.subplot(2, 1, 2)
    plt.plot(strategy['date'], strategy['benchmark_drawdown'], 'b-', label='SPY Drawdown')
    plt.plot(strategy['date'], strategy['strategy_drawdown'], 'r-', label='Option Strategy Drawdown')
    plt.fill_between(strategy['date'], strategy['strategy_drawdown'], 0, color='red', alpha=0.1)
    
    plt.title('Drawdowns: SPY vs Option Strategy')
    plt.ylabel('Drawdown')
    plt.ylim(min(strategy_max_drawdown, benchmark_max_drawdown) * 1.1, 0.05)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    plt.close()
    return strategy
