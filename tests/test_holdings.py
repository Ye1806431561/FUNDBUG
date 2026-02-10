
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.data.holdings import get_fund_holdings, save_fund_holdings, _parse_report_date

# Sample data for mocking AKShare response
def get_mock_holdings_df():
    data = {
        '序号': [1, 2],
        '股票代码': ['000001', '600519'],
        '股票名称': ['平安银行', '贵州茅台'],
        '占净值比例': [5.5, 10.2],
        '持股数': [1000, 200],
        '持仓市值': [10000, 300000],
        '季度': ['2024年1季度股票投资明细', '2024年1季度股票投资明细']
    }
    return pd.DataFrame(data)

def test_parse_report_date():
    assert _parse_report_date('2024年1季度股票投资明细') == '2024-03-31'
    assert _parse_report_date('2023年4季度股票投资明细') == '2023-12-31'
    assert _parse_report_date('invalid') is None

@patch('src.data.holdings._fetch_holdings_impl')
def test_get_fund_holdings_success(mock_fetch):
    mock_fetch.return_value = get_mock_holdings_df()
    
    holdings = get_fund_holdings('000001')
    
    assert holdings is not None
    assert len(holdings) == 2
    assert holdings[0]['fund_code'] == '000001'
    assert holdings[0]['stock_code'] == '000001'
    assert holdings[0]['report_date'] == '2024-03-31'
    assert holdings[1]['weight'] == 10.2

@patch('src.data.holdings._fetch_holdings_impl')
def test_get_fund_holdings_empty(mock_fetch):
    mock_fetch.return_value = pd.DataFrame()
    assert get_fund_holdings('000001') is None

@patch('src.data.holdings._fetch_holdings_impl')
def test_get_fund_holdings_error(mock_fetch):
    mock_fetch.side_effect = Exception("Network error")
    assert get_fund_holdings('000001') is None

@patch('src.data.holdings.get_fund_holdings')
@patch('src.db.crud.insert_holdings')
def test_save_fund_holdings_success(mock_insert, mock_get):
    mock_get.return_value = [
        {'fund_code': '000001', 'stock_code': 'S1', 'stock_name': 'N1', 'weight': 50.0, 'report_date': '2024-03-31'},
        {'fund_code': '000001', 'stock_code': 'S2', 'stock_name': 'N2', 'weight': 30.0, 'report_date': '2024-03-31'}
    ]
    
    result = save_fund_holdings('000001')
    
    assert result is True
    mock_insert.assert_called_once()
    # Check total weight calculation (printed to stdout, but we verify logic flow here)

@patch('src.data.holdings.get_fund_holdings')
def test_save_fund_holdings_no_data(mock_get):
    mock_get.return_value = None
    result = save_fund_holdings('000001')
    assert result is False

@patch('src.data.holdings.get_fund_holdings')
@patch('src.db.crud.insert_holdings')
def test_save_fund_holdings_db_error(mock_insert, mock_get):
    mock_get.return_value = [{'weight': 10, 'report_date': '2024-03-31'}]
    mock_insert.side_effect = Exception("DB Error")
    
    result = save_fund_holdings('000001')
    assert result is False
