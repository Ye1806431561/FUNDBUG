"""
verify_step_3_1.py - 步骤 3.1 手动验证脚本

使用模拟数据验证 NAV 估算核心算法的计算正确性。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch
import pandas as pd

from src.engine.nav_estimator import _calculate_weighted_return, estimate_fund_nav


def main():
    print("=" * 60)
    print("  步骤 3.1 验证: NAV 估算核心算法")
    print("=" * 60)

    # ── 验证 1: 加权涨跌幅计算 ──
    print("\n--- 验证 1: 加权涨跌幅计算 ---")
    holdings = [
        {"stock_code": "000001", "weight": 10.0},
        {"stock_code": "600519", "weight": 20.0},
        {"stock_code": "300750", "weight": 30.0},
    ]
    quotes = pd.DataFrame({
        "stock_code": ["000001", "600519", "300750"],
        "change_percent": [2.0, -1.0, 3.0],
    })

    weighted_return, cash_ratio = _calculate_weighted_return(holdings, quotes)
    expected_return = (10.0 * 2.0 + 20.0 * (-1.0) + 30.0 * 3.0) / 100.0  # 0.90
    expected_cash = 100.0 - 60.0  # 40.0

    print(f"  持仓总占比: 60.0%")
    print(f"  现金比例: {cash_ratio:.2f}% (预期: {expected_cash:.2f}%)")
    print(f"  加权涨跌幅: {weighted_return:.4f}% (预期: {expected_return:.4f}%)")

    assert abs(weighted_return - expected_return) < 0.001, "❌ 加权涨跌幅计算错误"
    assert abs(cash_ratio - expected_cash) < 0.001, "❌ 现金比例计算错误"
    print("  ✅ 加权涨跌幅计算正确")

    # ── 验证 2: 完整估算流程 (Mock) ──
    print("\n--- 验证 2: 完整估算流程 ---")
    mock_fund = {
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "latest_nav": 2.0000,
    }

    with patch("src.engine.nav_estimator.crud") as mock_crud, \
         patch("src.engine.nav_estimator.get_realtime_quotes") as mock_quotes:
        mock_crud.get_latest_holdings.return_value = holdings
        mock_crud.get_fund.return_value = mock_fund
        mock_crud.insert_estimate.return_value = True
        mock_quotes.return_value = quotes

        result = estimate_fund_nav("000001")

    assert result is not None, "❌ 估算返回 None"
    print(f"  基金代码: {result['fund_code']}")
    print(f"  基金名称: {result['fund_name']}")
    print(f"  前一日净值: {result['latest_nav']}")
    print(f"  预估净值: {result['estimated_nav']}")
    print(f"  预估涨跌幅: {result['estimated_return']}%")
    print(f"  现金比例: {result['cash_ratio']}%")
    print(f"  持仓数量: {result['holdings_count']}")
    print(f"  估算时间: {result['estimate_time']}")

    # 验证: 2.0 * (1 + 0.90/100) = 2.018
    expected_nav = round(2.0 * (1 + 0.90 / 100.0), 4)
    assert abs(result["estimated_nav"] - expected_nav) < 0.001, \
        f"❌ 预估净值错误: {result['estimated_nav']} != {expected_nav}"
    print(f"  ✅ 预估净值正确: {result['estimated_nav']} == {expected_nav}")

    # ── 验证 3: 无持仓场景 ──
    print("\n--- 验证 3: 无持仓场景 ---")
    with patch("src.engine.nav_estimator.crud") as mock_crud, \
         patch("src.engine.nav_estimator.get_realtime_quotes"):
        mock_crud.get_latest_holdings.return_value = []
        result = estimate_fund_nav("999999")

    assert result is None, "❌ 无持仓应返回 None"
    print("  ✅ 无持仓返回 None (符合预期)")

    # ── 验证 4: 行数检查 ──
    print("\n--- 验证 4: 文件行数检查 ---")
    filepath = os.path.join("src", "engine", "nav_estimator.py")
    with open(filepath) as f:
        line_count = sum(1 for _ in f)
    print(f"  src/engine/nav_estimator.py: {line_count} 行")
    assert line_count <= 200, f"❌ 超过 200 行限制"
    print(f"  ✅ 行数合规 ({line_count} ≤ 200)")

    print("\n" + "=" * 60)
    print("  ✅ 步骤 3.1 全部验证通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
