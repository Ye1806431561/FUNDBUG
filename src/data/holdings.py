
import pandas as pd
import akshare as ak
import datetime
import re
from typing import List, Dict, Optional, Tuple
from src.db import crud
from src.utils.helpers import retry_on_failure

# Month mapping for quarter end dates
QUARTER_END_MONTHS = {
    1: "03-31",
    2: "06-30",
    3: "09-30",
    4: "12-31"
}

def _parse_report_date(quarter_str: str) -> Optional[str]:
    """
    Parses '2024年1季度股票投资明细' to '2024-03-31'.
    Returns None if parsing fails.
    """
    try:
        # Regex to find Year and Quarter
        match = re.search(r'(\d{4})年(\d)季度', quarter_str)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            if quarter in QUARTER_END_MONTHS:
                return f"{year}-{QUARTER_END_MONTHS[quarter]}"
        return None
    except Exception:
        return None

@retry_on_failure(max_retries=3, delay=1)
def _fetch_holdings_impl(fund_code: str) -> pd.DataFrame:
    """
    Internal implementation to fetch holdings from AKShare.
    """
    return ak.fund_portfolio_hold_em(symbol=fund_code)

def get_fund_holdings(fund_code: str) -> Optional[List[Dict]]:
    """
    Fetches the LATEST quarterly holdings for the given fund.
    
    Returns:
        List of dicts with keys: fund_code, stock_code, stock_name, weight, report_date
        Returns None if data fetch fails or no data exists.
    """
    try:
        df = _fetch_holdings_impl(fund_code)
        if df is None or df.empty:
            return None
            
        # Standardize columns
        # AKShare columns: 序号, 股票代码, 股票名称, 占净值比例, 持股数, 持仓市值, 季度
        if '季度' not in df.columns or '股票代码' not in df.columns:
            return None
            
        # Parse '季度' to standard date string
        # We want to filter for the latest report date available
        
        # Create a temporary column for parsed date to sort
        df['parsed_date'] = df['季度'].apply(_parse_report_date)
        
        # Drop rows where date parsing failed
        df = df.dropna(subset=['parsed_date'])
        
        if df.empty:
            return None
            
        # Find the latest date
        latest_date = df['parsed_date'].max()
        
        # Filter for only the latest quarter
        latest_df = df[df['parsed_date'] == latest_date].copy()
        
        # Rename and select columns to match DB schema
        # DB schema: fund_code, stock_code, stock_name, weight, report_date
        result = []
        for _, row in latest_df.iterrows():
            item = {
                "fund_code": fund_code,
                "stock_code": str(row['股票代码']),
                "stock_name": str(row['股票名称']),
                "weight": float(row['占净值比例']), # Already in percentage e.g. 3.46
                "report_date": latest_date
            }
            result.append(item)
            
        return result

    except Exception as e:
        print(f"Error fetching holdings for {fund_code}: {e}")
        return None

def save_fund_holdings(fund_code: str) -> bool:
    """
    Fetches and saves holdings for a fund.
    Calculates and prints the total weight of disclosed holdings.
    """
    holdings = get_fund_holdings(fund_code)
    
    if not holdings:
        print(f"No holdings data found for {fund_code}")
        return False
        
    # Calculate stats
    total_weight = sum(h['weight'] for h in holdings)
    report_date = holdings[0]['report_date']
    
    print(f"Fund {fund_code} ({report_date}): Found {len(holdings)} stocks.")
    print(f"Total disclosed weight: {total_weight:.2f}% (Undisclosed/Cash: {100 - total_weight:.2f}%)")
    
    # Save to DB
    try:
        crud.insert_holdings(holdings)
        return True
    except Exception as e:
        print(f"Error saving holdings for {fund_code}: {e}")
        return False
