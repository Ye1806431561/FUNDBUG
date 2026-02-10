
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data.realtime import get_realtime_quotes, clear_cache, _get_all_a_share_quotes

# Sample data returned by AKShare
SAMPLE_DATA = pd.DataFrame({
    "代码": ["000001", "600519", "000002"],
    "名称": ["平安银行", "贵州茅台", "万科A"],
    "最新价": [10.50, 1800.00, 9.80],
    "涨跌幅": [1.5, -0.5, 0.0]
})

@pytest.fixture(autouse=True)
def clean_cache_before_test():
    clear_cache()
    yield
    clear_cache()

@patch('src.data.realtime.ak.stock_zh_a_spot_em')
def test_get_realtime_quotes_success(mock_ak):
    mock_ak.return_value = SAMPLE_DATA.copy()
    
    # Test valid codes
    codes = ["000001", "600519"]
    df = get_realtime_quotes(codes)
    
    assert len(df) == 2
    assert "000001" in df["stock_code"].values
    assert "600519" in df["stock_code"].values
    assert "000002" not in df["stock_code"].values
    
    # Check columns
    expected_cols = ["stock_code", "name", "current_price", "change_percent"]
    for col in expected_cols:
        assert col in df.columns
        
    # Check values
    row = df[df["stock_code"] == "000001"].iloc[0]
    assert row["name"] == "平安银行"
    assert row["current_price"] == 10.50
    assert row["change_percent"] == 1.5

@patch('src.data.realtime.ak.stock_zh_a_spot_em')
def test_get_realtime_quotes_caching(mock_ak):
    mock_ak.return_value = SAMPLE_DATA.copy()
    
    # First call
    get_realtime_quotes(["000001"])
    assert mock_ak.call_count == 1
    
    # Second call (should hit cache)
    get_realtime_quotes(["600519"])
    assert mock_ak.call_count == 1
    
    # Clear cache and call again
    clear_cache()
    get_realtime_quotes(["000002"])
    assert mock_ak.call_count == 2

@patch('src.data.realtime.ak.stock_zh_a_spot_em')
def test_get_realtime_quotes_invalid_code(mock_ak):
    mock_ak.return_value = SAMPLE_DATA.copy()
    
    # Test code that doesn't exist in market
    df = get_realtime_quotes(["999999"])
    assert df.empty
    assert list(df.columns) == ["stock_code", "name", "current_price", "change_percent"]

@patch('src.data.realtime.ak.stock_bid_ask_em')
@patch('src.data.realtime._get_all_a_share_quotes')
def test_get_realtime_quotes_fallback(mock_get_all, mock_bid_ask):
    # Mock batch fetch failure
    mock_get_all.side_effect = Exception("Batch Fetch Failed")
    
    # Mock individual fetch success
    # ak.stock_bid_ask_em returns DataFrame with item/value columns
    def side_effect(symbol):
        if symbol == "000001":
            return pd.DataFrame({
                "item": ["最新", "涨幅"],
                "value": [10.50, 1.5]
            })
        elif symbol == "600519":
             return pd.DataFrame({
                "item": ["最新", "涨幅"],
                "value": [1800.00, -0.5]
            })
        return pd.DataFrame(columns=["item", "value"])

    mock_bid_ask.side_effect = side_effect
    
    # Call get_realtime_quotes
    codes = ["000001", "600519"]
    df = get_realtime_quotes(codes)
    
    # Verify fallback was used
    assert mock_get_all.called
    assert mock_bid_ask.call_count == 2
    
    # Verify results
    assert len(df) == 2
    row1 = df[df['stock_code'] == "000001"].iloc[0]
    assert row1['current_price'] == 10.50
    assert row1['change_percent'] == 1.5


