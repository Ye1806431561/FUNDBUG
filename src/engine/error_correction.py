"""
误差修正模块 - 基于指数加权平均 (EWA) 的 NAV 估算误差修正

EWA 公式: EWA_t = α × error_t + (1-α) × EWA_{t-1}
α = 0.3（近期误差权重更高）
"""

import logging
from typing import Dict

from config import EWA_ALPHA
from src.db import crud

logger = logging.getLogger(__name__)


def calculate_ewa_bias(
    fund_code: str, alpha: float = None, limit: int = 10
) -> float:
    """
    计算基金的 EWA 误差偏差（百分比）。

    从数据库获取历史误差记录，按时间正序逐步累加 EWA。
    正值=估算偏高，负值=估算偏低，无数据返回 0.0。
    """
    if alpha is None:
        alpha = EWA_ALPHA

    errors = crud.get_estimate_errors(fund_code, limit=limit)
    if not errors:
        logger.info(f"No historical errors for fund {fund_code}, bias=0.0")
        return 0.0

    # get_estimate_errors 返回 DESC 排列，反转为正序
    errors.reverse()

    ewa = 0.0
    for record in errors:
        error_rate = record.get("error_rate", 0.0)
        if error_rate is None:
            continue
        ewa = alpha * float(error_rate) + (1 - alpha) * ewa

    logger.info(f"Fund {fund_code}: EWA bias={ewa:.4f}% ({len(errors)} records, α={alpha})")
    return round(ewa, 6)


def apply_correction(estimated_nav: float, ewa_bias: float) -> float:
    """
    应用 EWA 偏差修正估算净值。

    bias > 0（历史偏高）→ 向下修正；bias < 0 → 向上修正。
    返回修正后净值（4 位小数）。
    """
    corrected = estimated_nav * (1 - ewa_bias / 100.0)
    return round(corrected, 4)


def correct_fund_estimate(
    fund_code: str, estimated_nav: float, estimated_return: float,
) -> Dict:
    """
    完整误差修正流程：计算 EWA → 修正净值 → 修正涨跌幅。

    返回 dict: corrected_nav, corrected_return, ewa_bias, is_corrected
    """
    ewa_bias = calculate_ewa_bias(fund_code)

    if abs(ewa_bias) < 1e-8:
        return {
            "corrected_nav": estimated_nav,
            "corrected_return": estimated_return,
            "ewa_bias": 0.0,
            "is_corrected": False,
        }

    corrected_nav = apply_correction(estimated_nav, ewa_bias)
    corrected_return = round(estimated_return - ewa_bias, 4)

    logger.info(f"Fund {fund_code}: NAV {estimated_nav} → {corrected_nav} (bias={ewa_bias:.4f}%)")

    return {
        "corrected_nav": corrected_nav,
        "corrected_return": corrected_return,
        "ewa_bias": round(ewa_bias, 4),
        "is_corrected": True,
    }


def update_actual_and_errors(
    fund_code: str, actual_nav: float, nav_date: str
) -> bool:
    """
    收盘后回填实际净值，数据库层自动计算 error_rate。

    由定时任务在每日收盘后调用。
    """
    success = crud.update_actual_nav(fund_code, nav_date, actual_nav)
    if success:
        logger.info(f"Fund {fund_code}: Updated actual NAV={actual_nav} for {nav_date}")
    else:
        logger.warning(f"Fund {fund_code}: No estimates found for {nav_date}")
    return success
