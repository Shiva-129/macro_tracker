import pandas as pd
import config
from data_loader import fetch_market_data

def calculate_impact(event_row):
    """
    Calculates the impact of an event on all configured assets.
    Returns a dictionary of DataFrames, one for each asset, normalized to 0% at event time.
    """
    event_time = event_row['date']
    event_name = event_row['event']
    
    print(f"Analyzing impact for: {event_name} at {event_time} (UTC)")
    
    impact_data = {}
    
    for asset_name, ticker in config.ASSETS.items():
        print(f"  Fetching data for {asset_name} ({ticker})...")
        df = fetch_market_data(ticker, event_time)
        
        if df.empty:
            continue
            
        # Normalize data
        # Find the price closest to the event time to use as baseline
        # We use 'Close' price
        
        # Ensure index is timezone aware/unaware matching event_time if needed.
        # yfinance returns timezone-aware timestamps (usually America/New_York).
        # FMP event_time is usually UTC (or we need to check). 
        # Let's assume we need to handle timezone conversion.
        
        if df.index.tz is None:
             # If data has no timezone, assume it's local time
             pass
        else:
            # Make sure event time matches the market data timezone
            if event_time.tzinfo is None:
                event_time_tz = event_time.tz_localize('UTC').tz_convert(df.index.tz)
            else:
                event_time_tz = event_time.tz_convert(df.index.tz)
            
        # Find the price at the exact minute the event happened
        try:
            idx_loc = df.index.get_indexer([event_time_tz], method='nearest')[0]
            baseline_price = df.iloc[idx_loc]['Close']
            
            # Handle case where 'Close' is a Series (rare yfinance quirk)
            if isinstance(baseline_price, pd.Series):
                baseline_price = baseline_price.iloc[0]
            
            # Calculate percentage change: (Current Price - Baseline) / Baseline * 100
            # This makes all assets start at 0% so we can compare them easily
            
            # Calculate minutes relative to event (e.g., -15, 0, +60)
            minutes_relative = (df.index - event_time_tz).total_seconds() / 60
            
            pct_change = ((df['Close'] - baseline_price) / baseline_price) * 100
            
            # If pct_change is a DataFrame (yfinance quirk), squeeze it
            if isinstance(pct_change, pd.DataFrame):
                pct_change = pct_change.squeeze()
            
            asset_impact_df = pd.DataFrame({
                'time': df.index,
                'minutes_relative': minutes_relative,
                'pct_change': pct_change
            })
            
            impact_data[asset_name] = asset_impact_df
            
        except Exception as e:
            print(f"  Error normalizing data for {asset_name}: {e}")
            
    return impact_data
