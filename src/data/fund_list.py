import akshare as ak
import pandas as pd
import logging
from typing import Optional, Tuple, Dict, Any
from src.db.crud import insert_fund
from src.utils.helpers import retry_on_failure

logger = logging.getLogger(__name__)

@retry_on_failure(max_retries=3, delay=1.0)
def _fetch_fund_info_impl(fund_code: str) -> Dict[str, Any]:
    """Inner function with retry logic."""
    # 1. Get basic info (Name, Type)
    basic_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
    # basic_info_df columns: item, value
    # We need to parse it.
    info_dict = dict(zip(basic_info_df['item'], basic_info_df['value']))
    
    fund_name = info_dict.get('基金名称')
    fund_type = info_dict.get('基金类型')
    
    if not fund_name:
        raise ValueError(f"Could not find fund name for {fund_code}")

    # 2. Get latest NAV (Optional, but good to have)
    latest_nav = None
    nav_date = None
    try:
        nav_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if not nav_df.empty:
            last_row = nav_df.iloc[-1]
            # nav_df columns: 净值日期, 单位净值, 日增长率
            nav_date = str(last_row['净值日期'])
            latest_nav = float(last_row['单位净值'])
    except Exception as e:
        logger.warning(f"Failed to get NAV for {fund_code}: {e}")
        # Continue even if NAV fails, as we have name and type
        
    return {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "fund_type": fund_type,
        "latest_nav": latest_nav,
        "nav_date": nav_date
    }

def get_fund_info(fund_code: str) -> Optional[Dict[str, Any]]:
    """
    Get fund basic info and latest NAV.
    
    Returns:
        Dict with keys: fund_name, fund_type, latest_nav, nav_date
        Or None if failed.
    """
    try:
        return _fetch_fund_info_impl(fund_code)
    except Exception as e:
        logger.error(f"Error fetching fund info for {fund_code}: {e}")
        return None

def validate_fund_code(fund_code: str) -> bool:
    """
    Validate if a fund code is valid.
    
    Rules:
    1. Must be 6 digits.
    2. Must exist in external source (by calling get_fund_info).
    """
    if not fund_code or not fund_code.isdigit() or len(fund_code) != 6:
        return False
    
    info = get_fund_info(fund_code)
    return info is not None

def save_fund_info(fund_code: str) -> bool:
    """
    Fetch fund info and save to database.
    """
    info = get_fund_info(fund_code)
    if not info:
        return False
    
    return insert_fund(
        fund_code=info['fund_code'],
        fund_name=info['fund_name'],
        fund_type=info['fund_type'],
        latest_nav=info['latest_nav'],
        nav_date=info['nav_date']
    )
