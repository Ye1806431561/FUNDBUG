"""
tests/test_engine.py - NAV 估算引擎单元测试

使用 unittest.mock 模拟所有外部依赖（crud + realtime），
验证计算逻辑正确性。
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.engine.nav_estimator import (
    _calculate_weighted_return,
    estimate_fund_nav,
    estimate_all_watchlist,
)


# ── 测试数据 ──────────────────────────────────────────────

MOCK_HOLDINGS = [
    {"stock_code": "000001", "stock_name": "平安银行", "weight": 10.0, "report_date": "2024-12-31"},
    {"stock_code": "600519", "stock_name": "贵州茅台", "weight": 20.0, "report_date": "2024-12-31"},
    {"stock_code": "300750", "stock_name": "宁德时代", "weight": 30.0, "report_date": "2024-12-31"},
]
# 总持仓占比 = 60%，现金比例 = 40%

MOCK_QUOTES_DF = pd.DataFrame({
    "stock_code": ["000001", "600519", "300750"],
    "name": ["平安银行", "贵州茅台", "宁德时代"],
    "current_price": [11.0, 1800.0, 250.0],
    "change_percent": [2.0, -1.0, 3.0],
})

MOCK_FUND_INFO = {
    "fund_code": "000001",
    "fund_name": "测试基金A",
    "fund_type": "混合型",
    "latest_nav": 2.0000,
    "nav_date": "2024-01-19",
}


# ── 加权涨跌幅计算测试 ──────────────────────────────────

class TestCalculateWeightedReturn:

    def test_normal_calculation(self):
        """固定持仓+固定涨跌幅 → 验证加权计算正确"""
        weighted_return, cash_ratio = _calculate_weighted_return(
            MOCK_HOLDINGS, MOCK_QUOTES_DF
        )
        # weight=10 * change=2.0 / 100 = 0.20
        # weight=20 * change=-1.0 / 100 = -0.20
        # weight=30 * change=3.0 / 100 = 0.90
        # total = 0.20 + (-0.20) + 0.90 = 0.90
        assert abs(weighted_return - 0.90) < 0.001
        assert abs(cash_ratio - 40.0) < 0.001

    def test_cash_ratio_calculation(self):
        """持仓总占比 60% → 现金比例 = 40%"""
        _, cash_ratio = _calculate_weighted_return(MOCK_HOLDINGS, MOCK_QUOTES_DF)
        assert abs(cash_ratio - 40.0) < 0.001

    def test_empty_holdings(self):
        """无持仓 → 涨跌幅 0%，现金 100%"""
        weighted_return, cash_ratio = _calculate_weighted_return([], MOCK_QUOTES_DF)
        assert weighted_return == 0.0
        assert cash_ratio == 100.0

    def test_missing_quote(self):
        """持仓中有股票无行情 → 该股票涨跌幅视为 0%"""
        partial_quotes = pd.DataFrame({
            "stock_code": ["000001"],
            "name": ["平安银行"],
            "current_price": [11.0],
            "change_percent": [2.0],
        })
        weighted_return, cash_ratio = _calculate_weighted_return(
            MOCK_HOLDINGS, partial_quotes
        )
        # 只有 000001 有行情: 10 * 2.0 / 100 = 0.20
        # 其余两只股票涨跌幅视为 0
        assert abs(weighted_return - 0.20) < 0.001
        assert abs(cash_ratio - 40.0) < 0.001

    def test_empty_quotes(self):
        """行情为空 → 所有股票涨跌幅视为 0%"""
        empty_df = pd.DataFrame(
            columns=["stock_code", "name", "current_price", "change_percent"]
        )
        weighted_return, cash_ratio = _calculate_weighted_return(
            MOCK_HOLDINGS, empty_df
        )
        assert weighted_return == 0.0
        assert abs(cash_ratio - 40.0) < 0.001


# ── 单基金估算测试 ────────────────────────────────────────

class TestEstimateFundNav:

    @patch("src.engine.nav_estimator.get_realtime_quotes")
    @patch("src.engine.nav_estimator.crud")
    def test_success(self, mock_crud, mock_quotes):
        """正常估算流程：持仓+净值+行情均有效"""
        mock_crud.get_latest_holdings.return_value = MOCK_HOLDINGS
        mock_crud.get_fund.return_value = MOCK_FUND_INFO
        mock_crud.insert_estimate.return_value = True
        mock_quotes.return_value = MOCK_QUOTES_DF

        result = estimate_fund_nav("000001")

        assert result is not None
        assert result["fund_code"] == "000001"
        assert result["fund_name"] == "测试基金A"
        assert result["holdings_count"] == 3
        assert abs(result["cash_ratio"] - 40.0) < 0.001
        # estimated_return = 0.90 (加权涨跌幅)
        assert abs(result["estimated_return"] - 0.90) < 0.01
        # estimated_nav = 2.0 * (1 + 0.90/100) = 2.0 * 1.009 = 2.018
        assert abs(result["estimated_nav"] - 2.018) < 0.001

        # 验证保存到数据库
        mock_crud.insert_estimate.assert_called_once()

    @patch("src.engine.nav_estimator.get_realtime_quotes")
    @patch("src.engine.nav_estimator.crud")
    def test_no_holdings(self, mock_crud, mock_quotes):
        """无持仓数据 → 返回 None"""
        mock_crud.get_latest_holdings.return_value = []
        result = estimate_fund_nav("999999")
        assert result is None

    @patch("src.engine.nav_estimator.get_realtime_quotes")
    @patch("src.engine.nav_estimator.crud")
    def test_no_latest_nav(self, mock_crud, mock_quotes):
        """无前一日净值 → 返回 None"""
        mock_crud.get_latest_holdings.return_value = MOCK_HOLDINGS
        mock_crud.get_fund.return_value = {"fund_code": "000001", "latest_nav": None}
        result = estimate_fund_nav("000001")
        assert result is None


# ── 批量估算测试 ──────────────────────────────────────────

class TestEstimateAllWatchlist:

    @patch("src.engine.nav_estimator.estimate_fund_nav")
    @patch("src.engine.nav_estimator.crud")
    def test_batch_estimate(self, mock_crud, mock_estimate):
        """批量估算关注列表"""
        mock_crud.get_watchlist.return_value = [
            {"fund_code": "000001", "fund_name": "基金A"},
            {"fund_code": "000002", "fund_name": "基金B"},
        ]
        mock_estimate.side_effect = [
            {"fund_code": "000001", "estimated_nav": 2.018},
            {"fund_code": "000002", "estimated_nav": 1.500},
        ]

        results = estimate_all_watchlist()
        assert len(results) == 2
        assert mock_estimate.call_count == 2

    @patch("src.engine.nav_estimator.crud")
    def test_empty_watchlist(self, mock_crud):
        """空关注列表 → 返回空列表"""
        mock_crud.get_watchlist.return_value = []
        results = estimate_all_watchlist()
        assert results == []
