import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import config
import os
import requests
import json
import contextlib
import io

def fetch_from_fmp(api_key, start_date=None, end_date=None):
    """
    Fetches economic calendar from Financial Modeling Prep API.
    """
    if not start_date:
        start_date = datetime.now().strftime('%Y-%m-%d')
    if not end_date:
        end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
    url = f"https://financialmodelingprep.com/api/v3/economic_calendar?from={start_date}&to={end_date}&apikey={api_key}"
    
    print(f"Fetching from FMP API ({start_date} to {end_date})...")
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
        
    data = response.json()
    
    if not data:
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    
    # Rename columns to match our schema
    # FMP returns: event, date, country, impact, actual, estimate, previous
    df = df.rename(columns={'currency': 'country'})
    
    # Parse date
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert to UTC (FMP dates are usually UTC, but let's ensure)
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('UTC')
    else:
        df['date'] = df['date'].dt.tz_convert('UTC')
        
    return df

def fetch_economic_calendar(start_date=None, end_date=None, api_key=None):
    """
    Fetches economic calendar data.
    If api_key is provided, tries FMP API first.
    Falls back to local CSV file (events.csv).
    """
    if api_key:
        try:
            df = fetch_from_fmp(api_key, start_date, end_date)
            if not df.empty:
                print(f"Loaded {len(df)} events from FMP API")
                
                # Filter for important events/currencies
                if 'impact' in df.columns:
                    df['impact'] = df['impact'].str.lower()
                
                # Filter logic (same as CSV)
                mask_impact = df['impact'] == 'high' if 'impact' in df.columns else pd.Series([True] * len(df))
                mask_name = df['event'].apply(lambda x: any(important.lower() in str(x).lower() for important in config.IMPORTANT_EVENTS))
                mask_currency = df['country'].isin(config.IMPORTANT_CURRENCIES)
                
                df = df[(mask_impact | mask_name) & mask_currency].copy()
                return df
                
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg and "subscription" in error_msg.lower():
                print("FMP API Notice: Economic Calendar requires a paid subscription.")
            else:
                print(f"API Fetch Failed: {error_msg.split(' - ')[0]}") # Show concise error
            
            print("Falling back to events.csv...")

    # CSV Fallback Logic
    csv_file = os.path.join(os.path.dirname(__file__), 'events.csv')
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        print("Please create events.csv with your economic events.")
        print("Format: event,country,date,time,impact,estimate,previous")
        return pd.DataFrame()
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        if df.empty:
            print("No events found in events.csv")
            return pd.DataFrame()
        
        # Parse date and time
        # Combine date and time columns
        df['datetime_str'] = df['date'] + ' ' + df['time']
        
        # Parse to datetime
        df['date'] = pd.to_datetime(df['datetime_str'], format='%Y-%m-%d %H:%M')
        
        # Convert to UTC (assuming times are in EST)
        est = pytz.timezone('US/Eastern')
        df['date'] = df['date'].apply(lambda x: est.localize(x).astimezone(pytz.utc))
        
        # Drop the temporary column
        df = df.drop('datetime_str', axis=1)
        
        # Filter by date range if provided
        if start_date:
            start_dt = pd.to_datetime(start_date).tz_localize(pytz.utc)
            df = df[df['date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date).tz_localize(pytz.utc)
            df = df[df['date'] <= end_dt]
        
        # Normalize impact to lowercase
        if 'impact' in df.columns:
            df['impact'] = df['impact'].str.lower()
        
        # Filter for important events
        mask_impact = df['impact'] == 'high' if 'impact' in df.columns else pd.Series([True] * len(df))
        mask_name = df['event'].apply(lambda x: any(important.lower() in str(x).lower() for important in config.IMPORTANT_EVENTS))
        mask_currency = df['country'].isin(config.IMPORTANT_CURRENCIES)
        
        df = df[(mask_impact | mask_name) & mask_currency].copy()
        
        # Add 'actual' column if not present (will be filled after release)
        if 'actual' not in df.columns:
            df['actual'] = 'Wait for release'
        
        print(f"Loaded {len(df)} events from CSV file")
        
        return df
        
    except Exception as e:
        print(f"Error reading events.csv: {e}")
        print("Make sure the CSV format is correct:")
        print("event,country,date,time,impact,estimate,previous")
        return pd.DataFrame()

def fetch_market_data(ticker, event_time):
    """
    Fetches 1-minute interval market data from yfinance around the event time.
    """
    # Define window
    start_time = event_time - timedelta(minutes=config.PRE_EVENT_MINUTES)
    end_time = event_time + timedelta(minutes=config.POST_EVENT_MINUTES)
    
    try:
        # Download data from Yahoo Finance
        # We set prepost=True to get data for 8:30 AM events (before market open)
        # We suppress stderr to hide the "1 Failed download" noise for older events
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            df = yf.download(
                ticker, 
                start=start_time, 
                end=end_time, 
                interval="1m", 
                progress=False,
                prepost=True, 
                auto_adjust=True, 
                multi_level_index=False 
            )
        
        if df.empty:
            # Check if the event is older than 29 days (yfinance 1m limit)
            days_diff = (datetime.now(pytz.utc) - start_time).days
            if days_diff > 29:
                print(f"  Event > 30 days old. Switching to 5m interval...")
                df = yf.download(
                    ticker, 
                    start=start_time, 
                    end=end_time, 
                    interval="5m", 
                    progress=False,
                    prepost=True, 
                    auto_adjust=True, 
                    multi_level_index=False 
                )
                if not df.empty:
                    print(f"  Fetched data (5m interval)...")
            
            if df.empty:
                # Still empty? Market might be closed or ticker delisted
                return pd.DataFrame()
            
        return df
        
    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")
        return pd.DataFrame()

