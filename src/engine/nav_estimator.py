"""
NAV 估算核心算法模块

根据基金持仓数据和股票实时行情，计算基金预估净值。
核心公式：预估净值 = 前一日净值 × (1 + 加权涨跌幅/100)
未披露持仓视为现金（涨跌幅 0%）。
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from src.db import crud
from src.data.realtime import get_realtime_quotes

logger = logging.getLogger(__name__)


def _calculate_weighted_return(
    holdings: List[Dict], quotes_df
) -> Tuple[float, float]:
    """
    计算持仓加权涨跌幅和现金比例。

    Args:
        holdings: 持仓列表，每项含 stock_code, weight (百分比，如 3.46)
        quotes_df: 实时行情 DataFrame，含 stock_code, change_percent (百分比)

    Returns:
        (weighted_return_pct, cash_ratio_pct)
        - weighted_return_pct: 加权涨跌幅（百分比），已考虑现金
        - cash_ratio_pct: 现金比例（百分比）
    """
    if not holdings:
        return 0.0, 100.0

    # 构建行情查找字典: stock_code -> change_percent
    quote_map = {}
    if quotes_df is not None and not quotes_df.empty:
        for _, row in quotes_df.iterrows():
            quote_map[str(row["stock_code"])] = float(row["change_percent"])

    total_weight = 0.0
    weighted_return = 0.0

    for h in holdings:
        stock_code = str(h["stock_code"])
        weight = float(h["weight"])  # 百分比，如 3.46
        total_weight += weight

        change_pct = quote_map.get(stock_code, 0.0)
        # weight=3.46 表示占净值 3.46%，change_pct=1.5 表示涨 1.5%
        # 贡献 = 3.46 * 1.5 / 100 = 0.0519 个百分点
        weighted_return += weight * change_pct / 100.0

    cash_ratio = 100.0 - total_weight
    # 现金部分涨跌幅为 0%，不影响 weighted_return

    return weighted_return, cash_ratio


def estimate_fund_nav(fund_code: str) -> Optional[Dict]:
    """
    估算单只基金的实时净值。

    步骤：
    1. 获取最新持仓数据
    2. 获取基金前一日净值
    3. 获取持仓股票的实时行情
    4. 计算加权涨跌幅（未披露持仓视为现金）
    5. 估算净值并保存到数据库

    Returns:
        估算结果字典，或 None（数据不足时）
    """
    # 1. 获取持仓
    holdings = crud.get_latest_holdings(fund_code)
    if not holdings:
        logger.warning(f"No holdings found for fund {fund_code}")
        return None

    # 2. 获取基金信息（含前一日净值）
    fund_info = crud.get_fund(fund_code)
    if not fund_info or not fund_info.get("latest_nav"):
        logger.warning(f"No latest NAV found for fund {fund_code}")
        return None

    latest_nav = float(fund_info["latest_nav"])
    fund_name = fund_info.get("fund_name", "")

    # 3. 提取持仓股票代码，获取实时行情
    stock_codes = [str(h["stock_code"]) for h in holdings]
    quotes_df = get_realtime_quotes(stock_codes)

    # 4. 计算加权涨跌幅
    weighted_return, cash_ratio = _calculate_weighted_return(holdings, quotes_df)

    # 5. 计算预估净值
    estimated_nav = round(latest_nav * (1 + weighted_return / 100.0), 4)
    estimated_return = round(weighted_return, 4)

    # 6. 保存估算结果到数据库
    crud.insert_estimate(fund_code, estimated_nav, estimated_return)

    result = {
        "fund_code": fund_code,
        "fund_name": fund_name,
        "estimated_nav": estimated_nav,
        "estimated_return": estimated_return,
        "cash_ratio": round(cash_ratio, 2),
        "holdings_count": len(holdings),
        "latest_nav": latest_nav,
        "estimate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    logger.info(
        f"Fund {fund_code}: NAV={estimated_nav} "
        f"return={estimated_return}% cash={cash_ratio:.1f}%"
    )
    return result


def estimate_all_watchlist() -> List[Dict]:
    """
    批量估算用户关注列表中所有基金的净值。

    Returns:
        成功估算的结果列表
    """
    watchlist = crud.get_watchlist()
    if not watchlist:
        logger.info("Watchlist is empty, nothing to estimate")
        return []

    results = []
    for item in watchlist:
        fund_code = item["fund_code"]
        try:
            result = estimate_fund_nav(fund_code)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Error estimating fund {fund_code}: {e}")

    logger.info(f"Estimated {len(results)}/{len(watchlist)} funds")
    return results
