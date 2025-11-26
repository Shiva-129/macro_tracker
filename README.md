# Macro Event Tracker 

**A real-time tool to analyze how financial markets react to major economic news.**

---

## What is this?

Have you ever wondered: *"What actually happens to the S&P 500 when inflation comes in hot?"* or *"Does Gold really go up when the Fed cuts rates?"*

This tool answers those questions instantly. It takes an economic event (like CPI or Jobless Claims) and automatically fetches minute-by-minute price data for Stocks, Forex, Bonds, and Sectors to show you the exact market reaction.

## Why use it?

*   **Automated Analysis:** No more manually checking 5 different charts after news drops.
*   **Sector Deep Dive:** See if Tech crashed while Energy rallied.
*   **Free to Use:** Uses free data sources (Yahoo Finance) and a local CSV file. No expensive subscriptions needed.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Add Your Events
Open `events.csv` and add the events you want to track.
*Format: Event Name, Country, Date, Time, Impact, Forecast, Previous*
```csv
US CPI,USD,2025-11-21,08:30,High,3.2%,3.1%
```
*(Note: Ensure the date is within the last 30 days)*

### 3. Run the Tracker
```bash
python main.py
```
That's it! The tool will process your events and open interactive charts in your browser.

---

##  How it Works

1.  **Read Event:** The tool reads the date and time from your `events.csv`.
2.  **Fetch Data:** It downloads 1-minute price candles for SPY, EUR/USD, 10Y Yields, and 11 Sector ETFs.
3.  **Normalize:** It sets the price of every asset to 0% at the exact minute of the news release.
4.  **Visualize:** It plots the percentage change so you can compare everything on one chart.

---

##  Customization

Want to track Bitcoin? Or change the analysis window?
Check out `config.py`! It's designed to be easily changed.

```python
# Example: Adding Bitcoin to config.py
ASSETS = {
    ...
    "Bitcoin": "BTC-USD"
}
```

