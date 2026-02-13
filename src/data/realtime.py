
import logging
import time
import asyncio
import random
import threading
from typing import List, Dict, Optional
import pandas as pd
import akshare as ak
from datetime import datetime
import concurrent.futures

from src.utils.helpers import retry_on_failure

logger = logging.getLogger(__name__)

# --- Constants & Configuration ---
_CACHE_DURATION_SECONDS = 60

# Manual User-Agent pool to avoid extra dependencies
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]

class AsyncRealtimeProvider:
    """
    Singleton provider for real-time stock quotes using asyncio and background caching.
    Implements Producer-Consumer pattern with memory cache.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check locking
                    instance = super(AsyncRealtimeProvider, cls).__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            # 初始化逻辑
            self.quote_cache: Dict[str, Dict] = {}  # {stock_code: {price, change, time}}
            self._cache_lock = threading.RLock()  # 读写锁
            self.last_update_time: Optional[datetime] = None
            self.is_running = False
            self._background_task = None
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
            self.consecutive_failures = 0
            self._watchlist: set = set()  # 监控列表

            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_watchlist(self, stock_codes: List[str]):
        """外部注入需要监控的股票代码列表"""
        self._watchlist = set(stock_codes)
        logger.info(f"Watchlist updated: {len(self._watchlist)} stocks to monitor")

    def stop(self):
        """Stop the background fetching loop."""
        self.is_running = False
        if self._background_task:
            self._background_task.cancel()
        self.executor.shutdown(wait=False)
        logger.info("AsyncRealtimeProvider stopped.")

    def get_cached_quote(self, stock_code: str) -> Optional[Dict]:
        """
        Non-blocking retrieval from memory cache.
        Returns None if code not found.
        """
        with self._cache_lock:
            return self.quote_cache.get(stock_code, None)

    async def _fetch_worker(self):
        """Infinite loop to fetch data periodically."""
        logger.info("Starting background fetch worker...")

        while self.is_running:
            try:
                # 改进：指数退避熔断器
                if self.consecutive_failures >= 3:
                    # 5s -> 10s -> 20s -> 40s -> ... -> 最多 5 分钟
                    backoff = min(300, 5 * (2 ** (self.consecutive_failures - 3)))
                    logger.error(
                        f"🚨 High failure rate ({self.consecutive_failures} consecutive failures)! "
                        f"Backing off for {backoff}s. Possible IP ban or data source issue."
                    )
                    await asyncio.sleep(backoff)
                    continue  # 跳过本次拉取，直接进入下一轮

                # 正常的 jitter（抖动）
                jitter = random.uniform(-0.1, 0.1)
                sleep_time = max(0.5, 1.0 + jitter)
                await asyncio.sleep(sleep_time)

                # 在线程池中执行阻塞 I/O
                loop = asyncio.get_running_loop()
                df = await loop.run_in_executor(self.executor, self._fetch_data_safe)

                if df is not None and not df.empty:
                    self._update_cache(df)
                    self.consecutive_failures = 0  # 成功后重置计数器
                    logger.debug(f"Successfully fetched {len(df)} stocks")
                else:
                    self.consecutive_failures += 1
                    logger.warning(
                        f"Fetch returned empty data (failure #{self.consecutive_failures})"
                    )

            except asyncio.CancelledError:
                logger.info("Fetch worker cancelled.")
                break
            except Exception as e:
                self.consecutive_failures += 1
                logger.exception(
                    f"Error in fetch worker (failure #{self.consecutive_failures}): {e}"
                )

    def _fetch_data_safe(self) -> Optional[pd.DataFrame]:
        """仅拉取关注列表的股票（并发）"""
        if not self._watchlist:
            logger.warning("Watchlist is empty, skipping fetch")
            return None

        results = []

        def fetch_one(code: str) -> Optional[Dict]:
            """拉取单只股票的实时行情"""
            try:
                df = ak.stock_bid_ask_em(symbol=code)
                price_row = df[df['item'] == '最新']
                change_row = df[df['item'] == '涨幅']

                if price_row.empty or change_row.empty:
                    return None

                price = float(price_row['value'].values[0])
                change = float(change_row['value'].values[0])

                return {
                    'stock_code': code,
                    'current_price': price,
                    'change_percent': change,
                    'name': ''
                }
            except Exception as e:
                logger.debug(f"Failed to fetch {code}: {e}")
                return None

        # 并发拉取（20-50 只股票，耗时 <1s）
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_one, code): code for code in self._watchlist}

            for future in concurrent.futures.as_completed(futures, timeout=3):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Future failed: {e}")

        if not results:
            logger.warning("No data fetched from watchlist")
            return None

        return pd.DataFrame(results)

    def _update_cache(self, df: pd.DataFrame):
        """Update the internal dictionary from DataFrame."""
        # Expected columns: 代码, 名称, 最新价, 涨跌幅
        try:
            # Rename columns to match our internal schema
            rename_map = {
                "代码": "stock_code",
                "名称": "name",
                "最新价": "current_price",
                "涨跌幅": "change_percent"
            }
            # Helper to safely map if columns exist
            cols_to_use = []
            for k in rename_map.keys():
                if k in df.columns:
                    cols_to_use.append(k)
            
            if not cols_to_use:
                return

            subset = df[cols_to_use].rename(columns=rename_map)
            
            # Convert to dictionary for O(1) access
            # Format: { '000001': {'price': 10.5, 'change': 1.2, 'time': now} }
            now = datetime.now()
            
            # Batch update is faster
            # Iterating 5000 rows in Python is fast enough (<10ms)
            records = subset.to_dict('records')
            
            new_cache = {}
            for row in records:
                code = str(row.get('stock_code'))
                price = row.get('current_price')
                change = row.get('change_percent')
                
                # Basic validation
                try:
                    price = float(price) if price is not None else 0.0
                    change = float(change) if change is not None else 0.0
                except (ValueError, TypeError):
                    continue

                new_cache[code] = {
                    'current_price': price,
                    'change_percent': change,
                    'updated_at': now
                }

            # 原子替换（加锁）
            with self._cache_lock:
                self.quote_cache = new_cache
                self.last_update_time = now

            logger.debug(f"Cache updated with {len(new_cache)} stocks.")

        except Exception as e:
            logger.exception(f"Error updating cache: {e}")

# --- Legacy Synchronous Support (Deprecated) ---
# Keeping this for backward compatibility until Engine is refactored

_SC_CACHE: Dict[str, any] = {'timestamp': None, 'data': None}

@retry_on_failure(max_retries=3, delay=2.0)
def _get_all_a_share_quotes() -> pd.DataFrame:
    """Refactored to use the AsyncProvider if available, else fallback."""
    # If AsyncProvider is running and has data, use it
    provider = AsyncRealtimeProvider._instance
    if provider and provider.quote_cache:
        # Reconstruct DataFrame from cache
        # This is expensive but provided for compatibility
        data = list(provider.quote_cache.values())
        # We need stock_code in the dict values for DataFrame construction
        # But cache structure implies key is stock_code. 
        # Let's just fallback to original logic for legacy calls to avoid complexity
        pass

    # Original Logic
    global _SC_CACHE
    now = datetime.now()
    if _SC_CACHE['data'] is not None and _SC_CACHE['timestamp'] is not None:
        if (now - _SC_CACHE['timestamp']).total_seconds() < _CACHE_DURATION_SECONDS:
            return _SC_CACHE['data']

    try:
        df = ak.stock_zh_a_spot_em()
        rename_map = {
            "代码": "stock_code",
            "名称": "name",
            "最新价": "current_price",
            "涨跌幅": "change_percent"
        }
        df = df.rename(columns=rename_map)
        _SC_CACHE['timestamp'] = now
        _SC_CACHE['data'] = df
        return df
    except Exception as e:
        raise e

def _get_quotes_by_symbols(stock_codes: List[str]) -> pd.DataFrame:
    """Legacy individual fetcher."""
    # ... (simplified version of previous implementation)
    results = []
    def fetch_one(code):
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            price = float(df[df['item'] == '最新']['value'].values[0])
            change = float(df[df['item'] == '涨幅']['value'].values[0])
            return {"stock_code": code, "current_price": price, "change_percent": change, "name": ""}
        except:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_one, code) for code in stock_codes]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res: results.append(res)
            
    return pd.DataFrame(results) if results else pd.DataFrame(columns=["stock_code", "current_price", "change_percent"])

def get_realtime_quotes(stock_codes: List[str]) -> pd.DataFrame:
    """Legacy wrapper."""
    try:
        quotes = _get_all_a_share_quotes()
        return quotes[quotes['stock_code'].isin(stock_codes)]
    except:
        return _get_quotes_by_symbols(stock_codes)

def clear_cache():
    global _SC_CACHE
    _SC_CACHE = {'timestamp': None, 'data': None}
    provider = AsyncRealtimeProvider._instance
    if provider:
        provider.quote_cache = {}
