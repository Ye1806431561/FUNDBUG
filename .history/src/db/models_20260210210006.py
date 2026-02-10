"""
数据库模型定义 — 5 张表 + 初始化函数

表结构严格遵循 architecture.md，禁止在此文件外定义表。
"""
import os
import sqlite3

from config import DATABASE_PATH


# ──────────────────────── SQL 表定义 ────────────────────────

_CREATE_FUNDS = """
CREATE TABLE IF NOT EXISTS funds (
    fund_code   TEXT PRIMARY KEY,
    fund_name   TEXT NOT NULL,
    fund_type   TEXT,
    latest_nav  REAL,
    nav_date    DATE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_HOLDINGS = """
CREATE TABLE IF NOT EXISTS holdings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code   TEXT NOT NULL,
    stock_code  TEXT NOT NULL,
    stock_name  TEXT,
    weight      REAL NOT NULL,
    report_date DATE NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fund_code) REFERENCES funds(fund_code),
    UNIQUE(fund_code, stock_code, report_date)
);
"""

_CREATE_NAV_HISTORY = """
CREATE TABLE IF NOT EXISTS nav_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code    TEXT NOT NULL,
    nav_date     DATE NOT NULL,
    nav          REAL NOT NULL,
    acc_nav      REAL,
    daily_return REAL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fund_code) REFERENCES funds(fund_code),
    UNIQUE(fund_code, nav_date)
);
"""

_CREATE_NAV_ESTIMATES = """
CREATE TABLE IF NOT EXISTS nav_estimates (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code        TEXT NOT NULL,
    estimate_time    TIMESTAMP NOT NULL,
    estimated_nav    REAL NOT NULL,
    estimated_return REAL,
    actual_nav       REAL,
    error_rate       REAL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fund_code) REFERENCES funds(fund_code)
);
"""

_CREATE_USER_WATCHLIST = """
CREATE TABLE IF NOT EXISTS user_watchlist (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL UNIQUE,
    fund_name TEXT,
    added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_ALL_TABLES = [
    _CREATE_FUNDS,
    _CREATE_HOLDINGS,
    _CREATE_NAV_HISTORY,
    _CREATE_NAV_ESTIMATES,
    _CREATE_USER_WATCHLIST,
]


# ──────────────────────── 公共接口 ────────────────────────

def get_connection(db_path: str = DATABASE_PATH) -> sqlite3.Connection:
    """获取 SQLite 连接（启用外键约束）。"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row          # 以字典风格访问列
    return conn


def init_db(db_path: str = DATABASE_PATH) -> None:
    """初始化数据库：创建目录 + 建表（幂等）。"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = get_connection(db_path)
    try:
        for sql in _ALL_TABLES:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()
