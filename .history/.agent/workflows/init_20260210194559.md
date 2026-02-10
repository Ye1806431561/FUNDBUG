---
description: Initialize or review the FUNDBUG project status
---

# Project Initialization Workflow

Run this workflow to get oriented with the project and prepare for development.

---

## ⚠️ ALWAYS - 写代码前必读规则

> [!CAUTION]
> **以下规则必须始终遵守，AI 在生成任何代码前必须强制阅读：**

### 🚨 强制阅读文档
1. **写任何代码前必须完整阅读** `memory-bank/@architecture.md`（包含完整数据库结构与模块设计）
2. **写任何代码前必须完整阅读** `Fund_Design_Document.md`（系统设计文档）
3. **写任何代码前必须完整阅读** `tech-stack.md`（技术栈选型）

### 🚨 代码结构规则 - 禁止单体巨文件

> [!WARNING]
> **禁止 Monolith（单体巨文件）！必须采用模块化多文件结构！**

| ❌ 禁止 | ✅ 必须 |
|---------|---------|
| 单个 `main.py` 超过 200 行 | 拆分为多个模块文件 |
| 所有功能写在一个文件 | 按功能分层：`data/`, `engine/`, `api/`, `db/` |
| 复制粘贴重复代码 | 抽取公共函数到 `utils/` |
| 数据库操作散落各处 | 统一放在 `db/` 模块 |

### 🚨 模块化结构要求

```
src/
├── data/           # 数据采集层 (AKShare)
│   ├── __init__.py
│   ├── fund_list.py      # 基金列表获取
│   ├── holdings.py       # 持仓数据获取
│   └── realtime.py       # 实时行情获取
├── engine/         # 计算引擎层
│   ├── __init__.py
│   ├── nav_estimator.py  # NAV 估算核心算法
│   └── error_correction.py # 误差修正
├── api/            # API 服务层 (FastAPI)
│   ├── __init__.py
│   ├── routes.py         # 路由定义
│   └── schemas.py        # 请求/响应模型
├── db/             # 数据库层 (SQLite)
│   ├── __init__.py
│   ├── models.py         # 数据模型
│   └── crud.py           # 增删改查操作
└── utils/          # 公共工具
    ├── __init__.py
    └── helpers.py
```

#### 文件行数限制
- **单文件最大行数：200 行**
- 超过 200 行必须拆分
- 每个函数最大行数：50 行

---

## 1. Review Project Documents

Read the core design documents:
- `Fund_Design_Document.md` - System architecture and requirements
- `tech-stack.md` - Technology choices and rationale
- `memory-bank/@architecture.md` - Database schema and module design

## 2. Check Project Structure

// turbo
```bash
ls -la
```

## 3. Set Up Python Environment (if not exists)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Project Quick Reference

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Core development |
| Database | SQLite | Data persistence |
| API | FastAPI | REST endpoints |
| Data Source | AKShare | Real-time A-share quotes |
| Scheduler | APScheduler | Scheduled tasks |
| Compute | Pandas + NumPy | Financial calculations |

## 5. Key Development Commands

// turbo
```bash
# Run the app
python main.py

# Run with hot reload (development)
uvicorn main:app --reload
```
