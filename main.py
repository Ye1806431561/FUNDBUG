"""
FUNDBUG 基金净值估算系统 - 主入口文件
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn

from config import API_HOST, API_PORT, UPDATE_INTERVAL_SECONDS
from src.db.models import init_db
from src.api.routes import router
from src.engine import nav_estimator
from src.data import holdings, fund_list
from src.data.realtime import AsyncRealtimeProvider
from src.db import crud

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 定时任务调度器
scheduler = BackgroundScheduler()

def is_trading_time():
    """判断当前是否为交易时间（周一至周五 09:30-15:00）。"""
    now = datetime.now()
    if now.weekday() >= 5:  # 周六日
        return False
    
    current_time = now.strftime("%H:%M")
    return "09:30" <= current_time <= "15:05" # 稍微宽限 5 分钟

def scheduled_intraday_estimation():
    """盘中执行估算。"""
    if not is_trading_time():
        return
    logger.info("Starting scheduled intraday estimation...")
    nav_estimator.estimate_all_watchlist()

def scheduled_holdings_update():
    """每日早晨更新所有关注基金的持仓。"""
    logger.info("Starting scheduled holdings update...")
    watchlist = crud.get_watchlist()
    for item in watchlist:
        holdings.save_fund_holdings(item["fund_code"])

def scheduled_nav_daily_update():
    """每日收盘后更新实际净值并计算误差。"""
    logger.info("Starting scheduled daily NAV update...")
    # 这里需要获取当天的实际净值，通常来自 akshare
    # 逻辑待完善，目前先作为占位任务
    pass

def scheduled_nav_cleanup():
    """每日清理旧数据。"""
    logger.info("Starting scheduled data cleanup...")
    crud.cleanup_old_estimates()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 初始化数据库并启动调度器
    logger.info("Application starting up...")
    init_db()
    
    # 启动实时数据提供者 (后台异步任务)
    realtime_provider = AsyncRealtimeProvider.get_instance()
    realtime_provider.start()
    
    # 1. 注册持仓更新任务 (每日 08:30)
    scheduler.add_job(scheduled_holdings_update, CronTrigger(hour=8, minute=30))
    
    # 2. 注册盘中估算任务 (周一至周五 09:30-15:00, 每3秒执行一次)
    # 配合 AsyncRealtimeProvider 的 1 秒级数据更新
    scheduler.add_job(
        scheduled_intraday_estimation,
        CronTrigger(day_of_week='mon-fri', hour='9-15', second='*/3'),
    )
    
    # 3. 注册每日净值回填任务 (每日 18:00)
    scheduler.add_job(scheduled_nav_daily_update, CronTrigger(hour=18, minute=0))
    
    # 4. 注册清理任务 (每日 00:00)
    scheduler.add_job(scheduled_nav_cleanup, CronTrigger(hour=0, minute=0))
    
    scheduler.start()
    logger.info("Scheduler started.")
    
    yield
    
    # Shutdown: 关闭调度器和数据提供者
    logger.info("Application shutting down...")
    scheduler.shutdown()
    realtime_provider.stop()

app = FastAPI(title="FUNDBUG API", lifespan=lifespan)

# 挂载 API 路由
app.include_router(router)

# 挂载前端静态文件
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
