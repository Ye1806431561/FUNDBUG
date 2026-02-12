"""
API 路由定义 - 基于 FastAPI 的 REST 接口实现。
连接数据库 CRUD、数据采集和计算引擎。
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from src.db import crud
from src.api.schemas import (
    AddFundRequest, FundInfo, FundHolding, 
    NAVEstimate, NAVHistory, WatchlistItem
)
from src.engine import nav_estimator, error_correction
from src.data import fund_list, holdings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist():
    """获取用户关注的基金列表。"""
    return crud.get_watchlist()

@router.post("/watchlist", response_model=bool)
async def add_to_watchlist(request: AddFundRequest):
    """
    添加基金到关注列表。
    若数据库中无该基金，同步抓取基础信息和持仓数据。
    """
    fund_code = request.fund_code
    
    # 检查基金是否已在库中
    fund = crud.get_fund(fund_code)
    if not fund:
        # 同步抓取基金基础信息
        success = fund_list.save_fund_info(fund_code)
        if not success:
            raise HTTPException(status_code=404, detail=f"Invalid fund code: {fund_code}")
        # 同步抓取持仓数据
        holdings.save_fund_holdings(fund_code)
        fund = crud.get_fund(fund_code)

    # 添加到关注列表
    return crud.add_to_watchlist(fund_code, fund.get("fund_name"))

@router.delete("/watchlist/{fund_code}", response_model=bool)
async def remove_from_watchlist(fund_code: str):
    """从关注列表移除基金。"""
    success = crud.remove_from_watchlist(fund_code)
    if not success:
        raise HTTPException(status_code=404, detail="Fund not found in watchlist")
    return success

@router.get("/funds/{fund_code}", response_model=FundInfo)
async def get_fund_info(fund_code: str):
    """获取基金详情。"""
    fund = crud.get_fund(fund_code)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund info not found")
    return fund

@router.get("/funds/{fund_code}/holdings", response_model=List[FundHolding])
async def get_fund_holdings(fund_code: str):
    """获取基金持仓。"""
    data = crud.get_latest_holdings(fund_code)
    if not data:
        # 尝试现场抓取一次
        if holdings.save_fund_holdings(fund_code):
            data = crud.get_latest_holdings(fund_code)
    return data

@router.get("/funds/{fund_code}/history", response_model=List[NAVHistory])
async def get_fund_history(fund_code: str, limit: int = 30):
    """获取历史净值记录。"""
    return crud.get_nav_history(fund_code, limit=limit)

@router.get("/funds/{fund_code}/estimate", response_model=NAVEstimate)
async def get_single_estimate(fund_code: str):
    """计算并获取单只基金的实时净值估算。"""
    # 1. 执行原始估算
    res = nav_estimator.estimate_fund_nav(fund_code)
    if not res:
        raise HTTPException(status_code=404, detail="Unable to estimate (no holdings or NAV)")
    
    # 2. 执行误差修正
    correction = error_correction.correct_fund_estimate(
        fund_code, res["estimated_nav"], res["estimated_return"]
    )
    
    # 3. 合并结果
    res.update(correction)
    return res

@router.get("/estimates", response_model=List[NAVEstimate])
async def get_all_estimates():
    """获取关注列表中所有基金的批量估算结果。"""
    raw_results = nav_estimator.estimate_all_watchlist()
    final_results = []
    
    for res in raw_results:
        fund_code = res["fund_code"]
        correction = error_correction.correct_fund_estimate(
            fund_code, res["estimated_nav"], res["estimated_return"]
        )
        res.update(correction)
        final_results.append(res)
        
    return final_results
