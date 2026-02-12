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
    # 1. Try to get basic info from XQ (Snowball)
    fund_name = None
    fund_type = None

    try:
        basic_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
        info_dict = dict(zip(basic_info_df['item'], basic_info_df['value']))
        fund_name = info_dict.get('基金名称')
        fund_type = info_dict.get('基金类型')
    except Exception as e:
        logger.warning(f"Failed to fetch XQ info for {fund_code}: {e}")

    # 2. Try EM (EastMoney) interface if XQ failed or just to get NAV
    latest_nav = None
    nav_date = None
    
    try:
        # 这个接口也能返回基金名称，虽然主要用于净值
        nav_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if not nav_df.empty:
            last_row = nav_df.iloc[-1]
            nav_date = str(last_row['净值日期'])
            latest_nav = float(last_row['单位净值'])
            
            # 如果 XQ 没拿到名字，尝试从这里补救？
            # ak.fund_open_fund_info_em 本身不返回名称，需要另一个接口
            # 尝试 ak.fund_em_open_fund_info (或者 ak.fund_name_em 并不存在)
            pass
    except Exception as e:
        logger.warning(f"Failed to fetch EM NAV for {fund_code}: {e}")

    # 3. Fallback for Name: Try to find in all funds list (Heavy but reliable)
    if not fund_name:
        try:
             # ak.fund_name_em() returns all funds. We can filter.
             # This is slow, so only use as last resort.
             all_funds = ak.fund_name_em()
             # Columns: 基金代码, 基金简称
             match = all_funds[all_funds['基金代码'] == fund_code]
             if not match.empty:
                 fund_name = match.iloc[0]['基金简称']
                 # Ensure we have a type, or set default
                 if not fund_type:
                     fund_type = "未知类型"
        except Exception as e:
            logger.warning(f"Failed to fetch name from all funds list: {e}")

    if not fund_name:
         raise ValueError(f"Could not find fund name for {fund_code} from primary sources")

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
