
import logging
import time
from typing import List, Dict, Optional
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

from src.utils.helpers import retry_on_failure

logger = logging.getLogger(__name__)

# Cache structure: {'timestamp': datetime, 'data': pd.DataFrame}
_SC_CACHE: Dict[str, any] = {'timestamp': None, 'data': None}
_CACHE_DURATION_SECONDS = 60

import concurrent.futures

@retry_on_failure(max_retries=3, delay=2.0)
def _get_all_a_share_quotes() -> pd.DataFrame:
    # ... (Keep existing implementation)
    """
    Fetch all A-share real-time quotes from AKShare.
    This function is cached manually to avoid hitting the API too frequently.
    """
    global _SC_CACHE
    now = datetime.now()

    # Check cache
    if _SC_CACHE['data'] is not None and _SC_CACHE['timestamp'] is not None:
        if (now - _SC_CACHE['timestamp']).total_seconds() < _CACHE_DURATION_SECONDS:
            logger.debug("Returning cached real-time quotes")
            return _SC_CACHE['data']

    logger.info("Fetching fresh real-time quotes from AKShare (Batch)...")
    try:
        # stock_zh_a_spot_em returns all A-share stocks:
        start_time = time.time()
        df = ak.stock_zh_a_spot_em()
        elapsed = time.time() - start_time
        logger.info(f"Fetched {len(df)} records in {elapsed:.2f}s")
        
        rename_map = {
            "代码": "stock_code",
            "名称": "name",
            "最新价": "current_price",
            "涨跌幅": "change_percent"
        }
        
        missing_cols = [col for key, col in rename_map.items() if key not in df.columns]
        if missing_cols:
             raise ValueError(f"Missing expected columns from AKShare: {missing_cols}")

        df = df[list(rename_map.keys())].rename(columns=rename_map)
        df['stock_code'] = df['stock_code'].astype(str)
        df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce')
        df['change_percent'] = pd.to_numeric(df['change_percent'], errors='coerce')

        # Update cache
        _SC_CACHE['timestamp'] = now
        _SC_CACHE['data'] = df
        
        return df

    except Exception as e:
        logger.error(f"Error fetching batch real-time quotes: {e}")
        raise e

def _fetch_single_stock(stock_code: str) -> Optional[Dict]:
    """Fetch single stock quote using ak.stock_bid_ask_em"""
    try:
        df = ak.stock_bid_ask_em(symbol=stock_code)
        # df has columns: item, value.
        # Need "最新" (current_price) and "涨幅" (change_percent)
        # Note: "涨幅" might be percent (e.g. -0.09 usually means -0.09%)
        
        price_row = df[df['item'] == '最新']
        change_row = df[df['item'] == '涨幅']
        
        if price_row.empty:
            return None
            
        current_price = float(price_row['value'].values[0])
        change_percent = float(change_row['value'].values[0]) if not change_row.empty else 0.0
        
        # We don't have name easily here? 
        # Actually stock_bid_ask_em doesn't return name in rows?
        # Let's assume name is unknown or fetch separately? 
        # For performance, maybe just use stock_code as name or empty string if fallback.
        # Or try ak.stock_individual_info_em(symbol=stock_code) for name? Too slow.
        
        return {
            "stock_code": stock_code,
            "name": "", # Name not available in bid_ask api
            "current_price": current_price,
            "change_percent": change_percent
        }
    except Exception as e:
        logger.warning(f"Failed to fetch single stock {stock_code}: {e}")
        return None

def _get_quotes_by_symbols(stock_codes: List[str]) -> pd.DataFrame:
    """Fallback: Fetch quotes one by one using ThreadPoolExecutor"""
    logger.info(f"Fallback: Fetching {len(stock_codes)} stocks individually...")
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_code = {executor.submit(_fetch_single_stock, code): code for code in stock_codes}
        for future in concurrent.futures.as_completed(future_to_code):
            data = future.result()
            if data:
                results.append(data)
                
    if not results:
        return pd.DataFrame(columns=["stock_code", "name", "current_price", "change_percent"])
        
    return pd.DataFrame(results)

def get_realtime_quotes(stock_codes: List[str]) -> pd.DataFrame:
    """
    Get real-time quotes for a list of stock codes.
    Tries batch fetch first, then falls back to individual fetch.
    """
    if not stock_codes:
        return pd.DataFrame(columns=["stock_code", "name", "current_price", "change_percent"])

    try:
        # Try batch fetch
        all_quotes = _get_all_a_share_quotes()
        filtered_df = all_quotes[all_quotes['stock_code'].isin(stock_codes)].copy()
        filtered_df.reset_index(drop=True, inplace=True)
        return filtered_df
        
    except Exception as e:
        logger.warning(f"Batch fetch failed ({e}). Switching to individual fetch fallback.")
        return _get_quotes_by_symbols(stock_codes)

def clear_cache():
    """Manually clear the cache (useful for testing)"""
    global _SC_CACHE
    _SC_CACHE = {'timestamp': None, 'data': None}
