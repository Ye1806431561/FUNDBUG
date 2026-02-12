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
    # Patch the 'ak' module imported in src.data.fund_list
    with patch('src.data.fund_list.ak') as mock_ak:
        # Mock all potential calls to raise Exception
        mock_ak.fund_individual_basic_info_xq.side_effect = Exception("XQ Error")
        mock_ak.fund_open_fund_info_em.side_effect = Exception("EM Error")
        mock_ak.fund_name_em.side_effect = Exception("Fallback Error")
        
        info = get_fund_info('000001')
        assert info is None

def test_get_fund_info_retry_success(mock_ak_basic_info, mock_ak_nav_info):
    # Fail twice, then succeed
    side_effects = [Exception("Fail 1"), Exception("Fail 2"), mock_ak_basic_info]
    
    with patch('src.data.fund_list.ak') as mock_ak:
        # Setup the sequence of failures then success for the primary source
        mock_ak.fund_individual_basic_info_xq.side_effect = side_effects
        
        # Ensure fallbacks also fail so that the main function raises ValueError, triggering the retry decorator
        mock_ak.fund_open_fund_info_em.return_value = mock_ak_nav_info # EM works for NAV
        # But if XQ fails, we look for name in fallback
        mock_ak.fund_name_em.side_effect = Exception("Fallback Name Error")
        
        # When XQ fails (first 2 times), and Fallback fails, _fetch_fund_info_impl raises ValueError.
        # This triggers retry.
        
        # On 3rd time, XQ succeeds (returns df), so we don't need fallback.
        
        # Patch sleep to speed up
        with patch('time.sleep'):
            info = get_fund_info('000001')

        assert info is not None
        assert info['fund_name'] == '测试基金'
        # Verification of call count is tricky with side_effect list on a property
        # providing it succeeds eventually, we are good.
