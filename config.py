import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
FMP_API_KEY = os.getenv("FMP_API_KEY")


# Assets to track
ASSETS = {
    "Equities": "SPY",      # S&P 500 ETF
    "FX": "EURUSD=X",       # Euro/USD
    "Rates": "^TNX",        # 10-Year Treasury Yield
    "Volatility": "^VIX",   # CBOE Volatility Index
    
    # Sectors
    "Tech": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Cons. Disc": "XLY",    # Discretionary (Amazon, Tesla)
    "Cons. Staples": "XLP", # Staples (Walmart, Coke)
    "Energy": "XLE",
    "Utilities": "XLU",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Comm. Svcs": "XLC"     # Communication (Google, Meta)
}

# Impact Window (minutes)
PRE_EVENT_MINUTES = 15
POST_EVENT_MINUTES = 60

# Important Events to Filter (ForexFactory naming convention)
IMPORTANT_EVENTS = [
    "CPI",
    "Non-Farm Employment Change",
    "Fed Interest Rate Decision",
    "ISM Manufacturing PMI",
    "ISM Services PMI",
    "GDP",
    "FOMC Statement"
]

# Filter by Currency/Country (ForexFactory uses 'USD', 'EUR', etc.)
# Since our assets (SPY, TNX, VIX) are US-centric, we default to USD.
IMPORTANT_CURRENCIES = ["USD"]
