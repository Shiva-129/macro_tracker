import argparse
import sys
from datetime import datetime, timedelta
import pandas as pd
import pytz
import config
from data_loader import fetch_economic_calendar
from analyzer import calculate_impact
from visualizer import plot_event_impact

def main():
    parser = argparse.ArgumentParser(description="Real-time Macro Event Impact Tracker")
    parser.add_argument("--event", type=str, help="Filter by specific event name (e.g., 'CPI')")
    parser.add_argument("--date", type=str, help="Date of the event (YYYY-MM-DD). If not specified, shows all events.", default=None)
    parser.add_argument("--days", type=int, help="Number of days to look back/forward if no specific date", default=0)
    
    args = parser.parse_args()
    
    # Determine date range (only if date is specified)
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
        start_date = (target_date - timedelta(days=args.days)).strftime('%Y-%m-%d')
        end_date = (target_date + timedelta(days=args.days)).strftime('%Y-%m-%d')
    else:
        start_date = None
        end_date = None
    
    # Check if we have an API key
    api_key = config.FMP_API_KEY
    
    if not api_key:
        print("\n--- API Setup ---")
        use_api = input("Do you have an FMP API key? (y/n): ").lower().strip()
        if use_api == 'y':
            api_key = input("Enter your FMP API key: ").strip()
    
    if api_key:
        print(f"Using API Key: {api_key[:5]}...")
    else:
        print("No API key provided. Using local CSV file.")

    print(f"Loading economic events...")
    calendar_df = fetch_economic_calendar(start_date=start_date, end_date=end_date, api_key=api_key)
    
    if calendar_df.empty:
        print("No events found in events.csv")
        return

    # Filter by date if user asked for a specific day
    if args.date:
        calendar_df = calendar_df[calendar_df['date'].dt.strftime('%Y-%m-%d') == args.date]
        print(f"Filtering for events on {args.date}...")
    
    # Filter by event name if provided
    if args.event:
        calendar_df = calendar_df[calendar_df['event'].str.contains(args.event, case=False, na=False)]
        
    if calendar_df.empty:
        print(f"No events matching your criteria.")
        return
        
    print(f"Found {len(calendar_df)} events.")
    
    # Loop through each event found
    try:
        for index, row in calendar_df.iterrows():
            print(f"\n--- Processing {row['country']} {row['event']} ({row['date']} UTC) ---")
            
            # We can't analyze future events because market data doesn't exist yet
            if row['date'] > datetime.now(pytz.utc):
                print("Event is in the future. Cannot fetch market impact yet.")
                continue
                
            impact_data = calculate_impact(row)
            
            if not impact_data:
                print("No market data available for this event.")
                continue
                
            # Create and show the interactive chart
            fig, config_options = plot_event_impact(row, impact_data)
            fig.show(config=config_options)
            
            # If there are more events, ask before showing the next one
            if len(calendar_df) > 1:
                cont = input("Press Enter to see next event, or 'q' to quit: ")
                if cont.lower() == 'q':
                    break
    except KeyboardInterrupt:
        print("\n\nExiting program... Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
