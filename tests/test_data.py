import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.data.fund_list import get_fund_info, validate_fund_code, save_fund_info

@pytest.fixture
def mock_ak_basic_info():
    df = pd.DataFrame({
        'item': ['基金名称', '基金类型'],
        'value': ['测试基金', '混合型']
    })
    return df

@pytest.fixture
def mock_ak_nav_info():
    df = pd.DataFrame({
        '净值日期': ['2023-01-01', '2023-01-02'],
        '单位净值': [1.0, 1.1],
        '日增长率': [0.0, 10.0]
    })
    return df

def test_get_fund_info_success(mock_ak_basic_info, mock_ak_nav_info):
    with patch('akshare.fund_individual_basic_info_xq', return_value=mock_ak_basic_info), \
         patch('akshare.fund_open_fund_info_em', return_value=mock_ak_nav_info):
        
        info = get_fund_info('000001')
        assert info is not None
        assert info['fund_name'] == '测试基金'
        assert info['fund_type'] == '混合型'
        assert info['latest_nav'] == 1.1
        assert info['nav_date'] == '2023-01-02'

def test_get_fund_info_basic_fail():
    with patch('akshare.fund_individual_basic_info_xq', side_effect=Exception("Network error")):
        info = get_fund_info('000001')
        assert info is None

def test_validate_fund_code_format():
    assert validate_fund_code('123') is False
    assert validate_fund_code('abcdef') is False
    # Valid format, but we mock failure for internal check if we want, 
    # but here we rely on mock of get_fund_info within validate_fund_code
    
def test_validate_fund_code_success(mock_ak_basic_info, mock_ak_nav_info):
    with patch('src.data.fund_list.get_fund_info') as mock_get:
        mock_get.return_value = {'fund_name': 'Test'}
        assert validate_fund_code('000001') is True

def test_validate_fund_code_not_found():
    with patch('src.data.fund_list.get_fund_info') as mock_get:
        mock_get.return_value = None
        assert validate_fund_code('000001') is False

def test_save_fund_info_success():
    mock_info = {
        'fund_code': '000001',
        'fund_name': 'Test',
        'fund_type': 'Mixed',
        'latest_nav': 1.0,
        'nav_date': '2023-01-01'
    }
    with patch('src.data.fund_list.get_fund_info', return_value=mock_info), \
         patch('src.data.fund_list.insert_fund', return_value=True) as mock_insert:
        
        result = save_fund_info('000001')
        assert result is True
        mock_insert.assert_called_once()

def test_save_fund_info_fail():
    with patch('src.data.fund_list.get_fund_info', return_value=None):
        result = save_fund_info('000001')
        assert result is False

def test_get_fund_info_retry_success(mock_ak_basic_info, mock_ak_nav_info):
    # Fail twice, then succeed
    side_effects = [Exception("Fail 1"), Exception("Fail 2"), mock_ak_basic_info]
    
    # We need to patch where the function is imported or used. 
    # Since _fetch_fund_info_impl calls ak.fund_individual_basic_info_xq, we patch akshare.fund_individual_basic_info_xq
    with patch('akshare.fund_individual_basic_info_xq', side_effect=side_effects) as mock_ak:
        with patch('akshare.fund_open_fund_info_em', return_value=mock_ak_nav_info):
            # We need to ensure we call the decorated function, which is _fetch_fund_info_impl called by get_fund_info
            # But get_fund_info calls _fetch_fund_info_impl.
            # _fetch_fund_info_impl is decorated.
            # So calling get_fund_info('000001') should trigger retries.
            
            # Note: The retry delay is 1.0s. To speed up tests, we can patch time.sleep
            with patch('time.sleep'):
                info = get_fund_info('000001')
                
            assert info is not None
            assert info['fund_name'] == '测试基金'
            assert mock_ak.call_count == 3
