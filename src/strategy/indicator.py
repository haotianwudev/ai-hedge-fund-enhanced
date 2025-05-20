import pandas as pd
import numpy as np
import ta

def get_indicator_list():
    """
    Returns a list of all available indicators.
    
    Returns:
        list: List of indicator names
    """
    return [
        # Return-based indicators
        'return_1d',
        'return_5d',
        'drawdown',
        
        # Volume indicators
        'volume',
        'volume_3m_ratio',
        
        # VIX-based indicators
        'vix',
        'vix_change',
        'vix_rank',
        
        # VVIX-based indicators
        'vvix',
        'vvix_change',
        'vvix_zscore',
        'vix_vvix_ratio',
        
        # Moving Average indicators
        'sma_20',
        'sma_50',
        'sma_200',
        'sma_20_50_cross',
        'sma_20_200_cross',
        'sma_50_200_cross',
        'sma_20_50_crossover',
        'sma_20_200_crossover',
        'sma_50_200_crossover',
        'sma_20_50_distance',
        'sma_20_200_distance',
        'sma_50_200_distance',
        'dist_from_200sma',
        
        # Technical indicators
        'rsi',
        'macd',
        'macd_signal',
        'macd_diff',
        'atr',
        
        # Volatility indicators
        'spy_vol',
        'spy_vol_zscore'
    ]

def calculate_stock_indicators(stock_data):
    """
    Calculate stock-specific technical indicators.
    
    Args:
        stock_data (DataFrame): Stock price data with columns ['open', 'high', 'low', 'close', 'volume']
        
    Returns:
        DataFrame: Features dataframe with stock indicators
    """
    features = stock_data.copy()
    
    # Add returns and drawdown
    features['return_1d'] = stock_data['close'].pct_change(1)
    features['return_5d'] = stock_data['close'].pct_change(5)
    
    # Add drawdown feature
    roll_max = stock_data['close'].rolling(window=252, min_periods=1).max()
    drawdown = stock_data['close']/roll_max - 1.0
    features['drawdown'] = drawdown
    
    # Add volume indicators
    features['volume'] = stock_data['volume']
    features['volume_3m_ratio'] = stock_data['volume'] / stock_data['volume'].rolling(window=63).mean()
    
    # Calculate technical indicators
    # Simple Moving Averages
    features['sma_20'] = stock_data['close'].rolling(window=20).mean()
    features['sma_50'] = stock_data['close'].rolling(window=50).mean()
    features['sma_200'] = stock_data['close'].rolling(window=200).mean()

    # Crossover signals
    features['sma_20_50_cross'] = (features['sma_20'] > features['sma_50']).astype(int)
    features['sma_20_200_cross'] = (features['sma_20'] > features['sma_200']).astype(int)
    features['sma_50_200_cross'] = (features['sma_50'] > features['sma_200']).astype(int)
    
    # Signal changes (crossover events)
    features['sma_20_50_crossover'] = features['sma_20_50_cross'].diff().fillna(0)
    features['sma_20_200_crossover'] = features['sma_20_200_cross'].diff().fillna(0)
    features['sma_50_200_crossover'] = features['sma_50_200_cross'].diff().fillna(0)
    
    # Distance between SMAs (percentage)
    features['sma_20_50_distance'] = (features['sma_20'] / features['sma_50'] - 1) * 100
    features['sma_20_200_distance'] = (features['sma_20'] / features['sma_200'] - 1) * 100
    features['sma_50_200_distance'] = (features['sma_50'] / features['sma_200'] - 1) * 100
    
    # Distance from 200-day trend (%)
    features['dist_from_200sma'] = (stock_data['close'] / features['sma_200'] - 1) * 100
    
    # RSI (Relative Strength Index)
    features['rsi'] = ta.momentum.RSIIndicator(stock_data['close'], window=14).rsi()
    
    # MACD (Moving Average Convergence Divergence)
    macd = ta.trend.MACD(stock_data['close'])
    features['macd'] = macd.macd()
    features['macd_signal'] = macd.macd_signal()
    features['macd_diff'] = macd.macd_diff()
    
    # ATR (Average True Range) - volatility indicator
    features['atr'] = ta.volatility.AverageTrueRange(
        stock_data['high'], stock_data['low'], stock_data['close'], window=14
    ).average_true_range()
    
    # Stock volatility (20-day rolling)
    vol_window = 20
    features['spy_vol'] = stock_data['daily_return'].rolling(window=vol_window).std() * np.sqrt(252)  # Annualize
    
    # Stock volatility z-score (standardize against 252-day history)
    vol_hist_window = 252
    features['spy_vol_mean'] = features['spy_vol'].rolling(window=vol_hist_window).mean()
    features['spy_vol_std'] = features['spy_vol'].rolling(window=vol_hist_window).std()
    features['spy_vol_zscore'] = (features['spy_vol'] - features['spy_vol_mean']) / features['spy_vol_std']
    
    return features

def calculate_vix_indicators(vix_data):
    """
    Calculate VIX-specific indicators.
    
    Args:
        vix_data (DataFrame): VIX price data with columns ['open', 'high', 'low', 'close', 'volume']
        
    Returns:
        DataFrame: Features dataframe with VIX indicators
    """
    features = pd.DataFrame(index=vix_data.index)
    
    # Add VIX data
    features['vix'] = vix_data['close']
    features['vix_change'] = vix_data['close'].pct_change()
    
    # Calculate VIX rank (percentile over trailing year)
    vix_lookback = 252  # Trading days in a year
    features['vix_rank'] = vix_data['close'].rolling(window=vix_lookback).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1]
    )
    
    return features

def calculate_vvix_indicators(vvix_data, vix_data):
    """
    Calculate VVIX-specific indicators.
    
    Args:
        vvix_data (DataFrame): VVIX price data with columns ['open', 'high', 'low', 'close', 'volume']
        vix_data (DataFrame): VIX price data with columns ['open', 'high', 'low', 'close', 'volume']
        
    Returns:
        DataFrame: Features dataframe with VVIX indicators
    """
    features = pd.DataFrame(index=vvix_data.index)
    
    # Add VVIX data
    features['vvix'] = vvix_data['close']
    features['vvix_change'] = vvix_data['close'].pct_change()
    
    # Calculate VVIX z-score (60-day rolling)
    vvix_lookback = 60
    features['vvix_mean'] = vvix_data['close'].rolling(window=vvix_lookback).mean()
    features['vvix_std'] = vvix_data['close'].rolling(window=vvix_lookback).std()
    features['vvix_zscore'] = (vvix_data['close'] - features['vvix_mean']) / features['vvix_std']
    
    # Calculate VIX/VVIX ratio
    features['vix_vvix_ratio'] = vix_data['close'] / vvix_data['close']
    
    return features

def calculate_indicators(spy_data, vix_data, vvix_data):
    """
    Calculate all technical indicators for market crash prediction.
    
    Args:
        spy_data (DataFrame): SPY price data with columns ['open', 'high', 'low', 'close', 'volume']
        vix_data (DataFrame): VIX price data with columns ['open', 'high', 'low', 'close', 'volume']
        vvix_data (DataFrame): VVIX price data with columns ['open', 'high', 'low', 'close', 'volume']
        
    Returns:
        DataFrame: Features dataframe with all calculated indicators
    """
    # Calculate indicators for each component
    stock_features = calculate_stock_indicators(spy_data)
    vix_features = calculate_vix_indicators(vix_data)
    vvix_features = calculate_vvix_indicators(vvix_data, vix_data)
    
    # Combine all features
    features = pd.concat([stock_features, vix_features, vvix_features], axis=1)
    
    # Drop any rows with NaN values from the calculations
    features = features.replace([np.inf, -np.inf], np.nan).dropna()
    
    return features

def create_crash_labels(price_data, threshold=-0.05, forward_days=21):
    """
    Create crash labels based on forward returns.
    
    A crash is defined as a decline of 'threshold' percent or more within the next 'forward_days' trading days.
    For example, with threshold=-0.05 and forward_days=21, a crash is defined as a 5% or greater decline
    within the next month of trading.
    
    Args:
        price_data (DataFrame): Price data with 'close' column
        threshold (float): Decline threshold that defines a crash (default: -0.05 for 5% decline)
        forward_days (int): Number of forward trading days to look for a crash (default: 21 for 1 month)
        
    Returns:
        Series: Binary labels where 1 indicates a crash occurred within the forward window
    """
    if not isinstance(price_data, pd.DataFrame):
        raise TypeError("price_data must be a pandas DataFrame")
    if 'close' not in price_data.columns:
        raise ValueError("price_data must contain a 'close' column")
    if not isinstance(forward_days, int) or forward_days <= 0:
        raise ValueError("forward_days must be a positive integer")
    if not isinstance(threshold, (int, float)) or threshold >= 0:
        raise ValueError("threshold must be a negative number")
    
    # Get the closing prices
    close_prices = price_data['close']
    
    # Calculate forward returns for each day using shift
    forward_returns = pd.DataFrame(index=close_prices.index)
    for i in range(1, forward_days + 1):
        forward_returns[f'return_{i}d'] = close_prices.shift(-i) / close_prices - 1
    
    # Find the minimum return in the forward window for each day
    min_forward_returns = forward_returns.min(axis=1)
    
    # Create crash labels (1 if crash occurs, 0 otherwise)
    crash_labels = (min_forward_returns <= threshold).astype(int)
    
    # The last 'forward_days' days don't have complete forward windows
    # Set them to NaN to exclude from analysis
    crash_labels.iloc[-forward_days:] = np.nan
    
    return crash_labels.dropna() 