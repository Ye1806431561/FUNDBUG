
import pytest
import asyncio
import pandas as pd
from unittest.mock import MagicMock, patch
from src.data.realtime import AsyncRealtimeProvider

@pytest.fixture
def provider():
    # Reset singleton for each test
    AsyncRealtimeProvider._instance = None
    AsyncRealtimeProvider._init_done = False
    p = AsyncRealtimeProvider.get_instance()
    yield p
    p.stop()

def test_singleton_pattern():
    p1 = AsyncRealtimeProvider.get_instance()
    p2 = AsyncRealtimeProvider.get_instance()
    assert p1 is p2

def test_initial_state(provider):
    assert provider.is_running is False
    assert provider.quote_cache == {}
    assert provider._background_task is None

def test_start_stop(provider):
    # This involves async loop management, tricky in sync test without async runner
    # We mock _fetch_worker to just return (be efficient)
    
    async def mock_worker():
        pass
        
    with patch.object(provider, '_fetch_worker', side_effect=mock_worker):
        # We need a loop to run create_task
        # But provider.start() calls asyncio.get_running_loop()
        # So we must run this inside asyncio.run
        
        async def run_test():
            # Mock get_running_loop if needed or just let it use the current one
            # create_task requires a running loop
            provider.start() 
            assert provider.is_running is True
            # provider.start() uses loop.create_task. 
            # In asyncio.run, there is a loop.
            assert provider._background_task is not None
            
            provider.stop()
            assert provider.is_running is False
            
        asyncio.run(run_test())

def test_fetch_data_safe_success(provider):
    # Mock ak.stock_zh_a_spot_em
    mock_df = pd.DataFrame({
        "代码": ["000001", "000002"],
        "名称": ["平安银行", "万科A"],
        "最新价": [10.5, 9.8],
        "涨跌幅": [1.2, -0.5]
    })
    
    with patch("akshare.stock_zh_a_spot_em", return_value=mock_df):
        # _fetch_data_safe is synchronous/blocking (run in executor)
        # So we can call it directly
        df = provider._fetch_data_safe()
        assert df is not None
        assert len(df) == 2
        assert "代码" in df.columns

def test_fetch_data_safe_failure(provider):
    with patch("akshare.stock_zh_a_spot_em", side_effect=Exception("API Error")):
        df = provider._fetch_data_safe()
        assert df is None

def test_update_cache(provider):
    mock_df = pd.DataFrame({
        "代码": ["000001"],
        "名称": ["平安银行"],
        "最新价": [10.5],
        "涨跌幅": [1.2]
    })
    
    provider._update_cache(mock_df)
    
    cached = provider.get_cached_quote("000001")
    assert cached is not None
    assert cached["current_price"] == 10.5
    assert cached["change_percent"] == 1.2
    assert "updated_at" in cached

def test_fetch_worker_flow(provider):
    mock_df = pd.DataFrame({
        "代码": ["000001"],
        "最新价": [10.0],
        "涨跌幅": [1.0]
    })
    
    async def run_test():
        # Capture original sleep to use in test control flow
        original_sleep = asyncio.sleep
        
        async def fast_sleep(*args, **kwargs):
            # Non-blocking sleep for the worker
            pass

        # Patch akshare so _fetch_data_safe runs normally in thread but gets mock data
        with patch("akshare.stock_zh_a_spot_em", return_value=mock_df), \
             patch('asyncio.sleep', side_effect=fast_sleep):
            
            provider.is_running = True
            task = asyncio.create_task(provider._fetch_worker())
            
            # Give enough time for the thread pool to execute
            # Since we can't easily wait for thread, we poll the cache
            for _ in range(10):
                if provider.quote_cache.get("000001") is not None:
                    break
                await original_sleep(0.01) # Real sleep to let threads work
            
            assert provider.quote_cache.get("000001") is not None
            
            provider.is_running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(run_test())

def test_circuit_breaker(provider):
    async def run_test():
        original_sleep = asyncio.sleep
        async def fast_sleep(*args, **kwargs):
            pass

        # Patch akshare to raise exception
        with patch("akshare.stock_zh_a_spot_em", side_effect=Exception("API Fail")), \
             patch('asyncio.sleep', side_effect=fast_sleep):
            
            provider.is_running = True
            task = asyncio.create_task(provider._fetch_worker())
            
            # Poll for failures
            for _ in range(10):
                if provider.consecutive_failures > 0:
                    break
                await original_sleep(0.01)
            
            assert provider.consecutive_failures > 0
            
            provider.is_running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    asyncio.run(run_test())
