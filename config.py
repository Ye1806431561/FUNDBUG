"""
FUNDBUG 基金净值估算系统 - 配置文件

所有配置项集中管理，禁止在其他模块中硬编码配置值。
"""
import os

# ============ 数据库配置 ============
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "data", "fundbug.db")

# ============ API 服务配置 ============
API_HOST = "127.0.0.1"
API_PORT = 8000

# ============ 交易时间配置 ============
TRADING_START = "09:30"
TRADING_END = "15:00"

# ============ 定时任务配置 ============
UPDATE_INTERVAL_SECONDS = 60  # 每分钟更新一次估算

# ============ 数据保留配置 ============
DATA_RETENTION_DAYS = 7  # 估算记录保留 7 天

# ============ 误差修正配置 ============
EWA_ALPHA = 0.3  # 指数加权平均衰减系数（近期权重更高）
