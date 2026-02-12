"""
Pydantic v2 请求/响应模型 — API 数据校验与文档生成
所有字段严格对齐数据库表结构和引擎返回值，禁止自造字段。
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AddFundRequest(BaseModel):
    """添加基金到关注列表的请求体。"""
    fund_code: str = Field(
        ..., pattern=r"^\d{6}$", description="6 位基金代码",
        json_schema_extra={"examples": ["000001"]},
    )


class FundInfo(BaseModel):
    """基金基础信息（对齐 funds 表）。"""
    fund_code: str = Field(..., description="基金代码")
    fund_name: str = Field(..., description="基金名称")
    fund_type: Optional[str] = Field(None, description="基金类型")
    latest_nav: Optional[float] = Field(None, description="最新单位净值")
    nav_date: Optional[str] = Field(None, description="净值日期")
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"fund_code": "000001", "fund_name": "华夏成长混合",
                       "fund_type": "混合型-偏股", "latest_nav": 1.234,
                       "nav_date": "2026-02-11"}],
    })


class FundHolding(BaseModel):
    """基金持仓信息（对齐 holdings 表）。"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    weight: float = Field(..., description="持仓占比 (%)")
    report_date: str = Field(..., description="报告期 (YYYY-MM-DD)")
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"stock_code": "600519", "stock_name": "贵州茅台",
                       "weight": 8.56, "report_date": "2025-12-31"}],
    })


class NAVEstimate(BaseModel):
    """净值估算结果（对齐 estimate_fund_nav + correct_fund_estimate 返回值）。"""
    fund_code: str
    fund_name: str = ""
    estimated_nav: float = Field(..., description="预估净值")
    estimated_return: float = Field(..., description="预估涨跌幅 (%)")
    cash_ratio: float = Field(0.0, description="现金比例 (%)")
    holdings_count: int = Field(0, description="持仓股票数量")
    latest_nav: float = Field(0.0, description="前一日净值")
    estimate_time: str = Field("", description="估算时间")
    corrected_nav: Optional[float] = Field(None, description="修正后净值")
    corrected_return: Optional[float] = Field(None, description="修正后涨跌幅 (%)")
    ewa_bias: Optional[float] = Field(None, description="EWA 偏差 (%)")
    is_corrected: bool = Field(False, description="是否已应用误差修正")
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"fund_code": "000001", "fund_name": "华夏成长混合",
                       "estimated_nav": 1.238, "estimated_return": 0.32,
                       "cash_ratio": 35.93, "holdings_count": 175,
                       "latest_nav": 1.234, "estimate_time": "2026-02-12 10:30:00",
                       "corrected_nav": 1.237, "corrected_return": 0.28,
                       "ewa_bias": 0.04, "is_corrected": True}],
    })


class NAVHistory(BaseModel):
    """历史净值记录（对齐 nav_history 表）。"""
    fund_code: str
    nav_date: str = Field(..., description="净值日期")
    nav: float = Field(..., description="单位净值")
    acc_nav: Optional[float] = Field(None, description="累计净值")
    daily_return: Optional[float] = Field(None, description="日涨跌幅 (%)")
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"fund_code": "000001", "nav_date": "2026-02-11",
                       "nav": 1.234, "acc_nav": 3.456, "daily_return": -0.16}],
    })


class WatchlistItem(BaseModel):
    """用户关注列表项（对齐 user_watchlist 表）。"""
    fund_code: str
    fund_name: Optional[str] = None
    added_at: Optional[str] = Field(None, description="加入时间")
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"fund_code": "000001", "fund_name": "华夏成长混合",
                       "added_at": "2026-02-12 08:00:00"}],
    })
