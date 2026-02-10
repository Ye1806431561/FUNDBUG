
import akshare as ak
import pandas as pd
import sys

# Set encoding for Chinese output
sys.stdout.reconfigure(encoding='utf-8')

try:
    print("Fetching fund holdings for 000001...")
    # Using 'fund_portfolio_hold_em' as planned
    df = ak.fund_portfolio_hold_em(symbol="000001", date="2023") # Need to specify year? It usually returns all history or latest. Let's try without date first if possible, but the doc says 'date' is optional or specific. Let's try without date to get latest.
    # Actually, let's just try obtaining without date first, maybe it defaults to latest.
    # The common usage is `fund_portfolio_hold_em(symbol="000001")` returns all history?
    # Or maybe it requires a specific year. Let's check.
    
    # Attempt 1: Just symbol
    try:
        df = ak.fund_portfolio_hold_em(symbol="000001")
        print("Fetched with symbol only.")
    except Exception as e:
        print(f"Failed with symbol only: {e}")
        # Attempt 2: With latest year
        print("Trying with date='2024'...")
        df = ak.fund_portfolio_hold_em(symbol="000001", date="2024")
    
    if df is not None and not df.empty:
        print("Columns:", df.columns.tolist())
        print("First 2 rows:")
        print(df.head(2).to_markdown())
        print("Data Types:")
        print(df.dtypes)
    else:
        print("DataFrame is empty or None")

except Exception as e:
    print(f"An error occurred: {e}")
