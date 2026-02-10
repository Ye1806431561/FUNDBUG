# 基金净值估算系统 - 实施计划

> [!IMPORTANT]
> **此文档为 AI 开发者的分步指令，每一步都必须小而具体，并包含验证测试。**
> **严禁包含代码！只写清晰、具体的指令。**

---

## 📋 设计决策（已确认）

| 项目 | 决策 |
|------|------|
| **数据范围** | 用户指定的基金列表（需实现基金管理功能） |
| **更新频率** | 每分钟一次 |
| **数据保留** | 估算记录保留 7 天 |
| **未披露持仓** | 假设为现金（涨跌 0%） |
| **误差修正** | 指数加权平均（EWA） |
| **前端界面** | 简单 Web 页面 |
| **部署环境** | 本地 Mac |

---

## 阶段 0: 环境准备

### 步骤 0.1: 创建项目目录结构

**指令：**
1. 在项目根目录下创建以下目录结构：
   - `src/data/`
   - `src/engine/`
   - `src/api/`
   - `src/db/`
   - `src/utils/`
   - `frontend/` （前端目录）
   - `data/` （SQLite 数据库文件目录）
2. 在每个 `src/` 子目录下创建空的 `__init__.py` 文件
3. 在项目根目录创建 `config.py` 配置文件
4. 在项目根目录创建 `main.py` 入口文件

**验证测试：**
- [ ] 运行 `ls -R src/` 确认目录结构存在
- [ ] 运行 `find src -name "__init__.py" | wc -l` 确认有 5 个 `__init__.py` 文件
- [ ] 确认 `config.py`、`main.py`、`frontend/`、`data/` 存在

---

### 步骤 0.2: 创建 requirements.txt

**指令：**
1. 在项目根目录创建 `requirements.txt` 文件
2. 添加以下依赖：
   - fastapi>=0.109.0
   - uvicorn>=0.27.0
   - akshare>=1.12.0
   - pandas>=2.2.0
   - numpy>=1.26.0
   - apscheduler>=3.10.0
   - jinja2>=3.1.0 （前端模板）
   - python-multipart>=0.0.6 （表单处理）
   - pytest>=8.0.0 （测试）

**验证测试：**
- [ ] 运行 `cat requirements.txt` 确认内容正确
- [ ] 运行 `pip install -r requirements.txt` 确认所有依赖可安装

---

### 步骤 0.3: 创建 Python 虚拟环境

**指令：**
1. 在项目根目录运行 `python3 -m venv .venv`
2. 激活虚拟环境：`source .venv/bin/activate`
3. 安装依赖：`pip install -r requirements.txt`

**验证测试：**
- [ ] 运行 `which python` 确认路径包含 `.venv`
- [ ] 运行 `python -c "import fastapi; print(fastapi.__version__)"` 确认 FastAPI 已安装
- [ ] 运行 `python -c "import akshare; print(akshare.__version__)"` 确认 AKShare 已安装

---

## 阶段 1: 数据库层 (src/db/)

### 步骤 1.1: 创建配置文件 (config.py)

**指令：**
1. 在 `config.py` 中定义以下配置项：
   - `DATABASE_PATH`: SQLite 数据库文件路径（默认：`./data/fundbug.db`）
   - `API_HOST`: API 服务主机（默认：`127.0.0.1`）
   - `API_PORT`: API 服务端口（默认：`8000`）
   - `TRADING_START`: 开盘时间（`09:30`）
   - `TRADING_END`: 收盘时间（`15:00`）
   - `UPDATE_INTERVAL_SECONDS`: 更新间隔（`60` 秒，即每分钟）
   - `DATA_RETENTION_DAYS`: 数据保留天数（`7` 天）
   - `EWA_ALPHA`: 指数加权平均衰减系数（`0.3`，近期权重更高）
2. 使用常量定义，禁止硬编码

**验证测试：**
- [ ] 运行 `python -c "from config import DATABASE_PATH, UPDATE_INTERVAL_SECONDS; print(DATABASE_PATH, UPDATE_INTERVAL_SECONDS)"` 确认可导入
- [ ] 确认文件行数不超过 50 行

---

### 步骤 1.2: 创建数据库模型 (src/db/models.py)

**指令：**
1. 定义数据库初始化函数，创建 SQLite 连接
2. 根据 `architecture.md` 中的表结构，创建以下 5 张表：
   - `funds`: 基金基础信息表
   - `holdings`: 基金持仓表
   - `nav_history`: 历史净值表
   - `nav_estimates`: 估算记录表
   - `user_watchlist`: **用户关注的基金列表**（新增）
3. `user_watchlist` 表结构：
   - `id`: INTEGER PRIMARY KEY
   - `fund_code`: TEXT NOT NULL UNIQUE
   - `fund_name`: TEXT
   - `added_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
4. 包含表创建的 SQL 语句（使用 `CREATE TABLE IF NOT EXISTS`）
5. 导出数据库初始化函数

**验证测试：**
- [ ] 运行初始化函数后，确认 `fundbug.db` 文件被创建
- [ ] 运行 `sqlite3 data/fundbug.db ".tables"` 确认 5 张表存在
- [ ] 运行 `sqlite3 data/fundbug.db ".schema user_watchlist"` 确认表结构正确
- [ ] 确认文件行数不超过 150 行

---

### 步骤 1.3: 创建 CRUD 操作 (src/db/crud.py)

**指令：**
1. 创建通用数据库连接获取函数
2. 为每张表创建以下操作函数：
   - **funds 表**：`insert_fund()`, `get_fund()`, `get_all_funds()`, `update_fund_nav()`
   - **holdings 表**：`insert_holdings()`, `get_holdings_by_fund()`, `get_latest_holdings()`
   - **nav_history 表**：`insert_nav()`, `get_nav_history()`, `get_latest_nav()`
   - **nav_estimates 表**：`insert_estimate()`, `update_actual_nav()`, `get_estimate_errors()`, `cleanup_old_estimates(days=7)`
   - **user_watchlist 表**：`add_to_watchlist()`, `remove_from_watchlist()`, `get_watchlist()`, `is_in_watchlist()`
3. `cleanup_old_estimates()` 函数需删除超过 7 天的估算记录
4. 所有函数必须包含异常处理
5. 使用参数化查询，防止 SQL 注入

**验证测试：**
- [ ] 编写测试：添加基金到关注列表，然后查询确认存在
- [ ] 编写测试：删除基金从关注列表，确认已移除
- [ ] 编写测试：cleanup_old_estimates 正确删除旧数据
- [ ] 运行 `pytest tests/test_db.py -v` 确认所有测试通过
- [ ] 确认文件行数不超过 200 行

---

## 阶段 2: 数据采集层 (src/data/)

### 步骤 2.1: 创建基金列表获取模块 (src/data/fund_list.py)

**指令：**
1. 创建函数调用 AKShare 的 `ak.fund_open_fund_info_em()` 或类似接口获取公募基金列表
2. 创建函数：根据基金代码查询基金名称和类型
3. 创建函数：验证基金代码是否有效
4. 创建函数将获取的基金信息保存到数据库（调用 crud.py）
5. 添加错误处理和重试机制

**验证测试：**
- [ ] 使用已知基金代码（如 `000001`）验证函数返回正确的基金名称
- [ ] 验证无效基金代码返回错误或空结果
- [ ] 确认文件行数不超过 200 行

---

### 步骤 2.2: 创建持仓数据获取模块 (src/data/holdings.py)

**指令：**
1. 创建函数调用 AKShare 获取指定基金的季报持仓数据
2. 使用 `ak.fund_portfolio_hold_em()` 或类似接口
3. 解析返回数据，提取：股票代码、股票名称、持仓占比、报告期
4. 创建函数将持仓数据保存到数据库
5. 处理数据不存在的情况（部分基金可能无持仓数据）
6. **计算已披露持仓的总占比，未披露部分视为现金**

**验证测试：**
- [ ] 使用已知基金代码运行函数，确认返回数据
- [ ] 验证返回 DataFrame 包含 `stock_code`, `weight`, `report_date` 列
- [ ] 验证 weight 总和计算正确（用于现金比例推算）
- [ ] 确认文件行数不超过 200 行

---

### 步骤 2.3: 创建实时行情获取模块 (src/data/realtime.py)

**指令：**
1. 创建函数调用 AKShare 获取股票实时行情
2. 使用 `ak.stock_zh_a_spot_em()` 或类似接口
3. 支持批量获取多只股票的实时价格
4. 返回包含 stock_code、current_price、change_percent 的 DataFrame
5. 添加接口调用频率限制（每分钟更新一次，符合设计决策）
6. 添加缓存机制，避免同一分钟内重复请求

**验证测试：**
- [ ] 在交易时间（9:30-15:00）运行函数，确认返回实时数据
- [ ] 验证返回价格为正数
- [ ] 验证涨跌幅在合理范围内（-11% 到 +11%）
- [ ] 确认文件行数不超过 200 行

---

## 阶段 3: 计算引擎层 (src/engine/)

### 步骤 3.1: 创建 NAV 估算核心算法 (src/engine/nav_estimator.py)

**指令：**
1. 创建函数实现 NAV 估算核心算法：
   - 输入：基金代码
   - 步骤：
     1. 从数据库获取该基金最新持仓数据
     2. 从实时行情模块获取持仓股票的当前价格
     3. 计算持仓股票的加权涨跌幅
     4. **未披露持仓视为现金，涨跌幅为 0%**
     5. 基于前一日净值计算预估净值
   - 输出：预估净值、预估涨跌幅、现金比例
2. 创建函数：批量估算用户关注列表中的所有基金
3. 添加估算结果保存到数据库

**验证测试：**
- [ ] 使用测试数据（固定持仓和价格）验证计算逻辑正确
- [ ] 验证现金比例 = 100% - 已披露持仓总占比
- [ ] 验证预估涨跌幅在合理范围内
- [ ] 确认文件行数不超过 200 行

---

### 步骤 3.2: 创建误差修正模块 (src/engine/error_correction.py)

**指令：**
1. 创建函数分析历史估算误差：
   - 从数据库获取历史估算记录和实际净值
   - 计算误差 = (估算净值 - 实际净值) / 实际净值 * 100%
2. 创建函数应用**指数加权平均（EWA）**误差修正：
   - 使用 `config.EWA_ALPHA` 作为衰减系数
   - EWA 公式：`EWA_t = α * error_t + (1-α) * EWA_{t-1}`
   - 近期误差权重更高
3. 创建函数：修正后估算值 = 原始估算值 - EWA误差
4. 创建函数在收盘后更新实际净值并计算误差

**验证测试：**
- [ ] 使用模拟的历史数据验证 EWA 计算正确
- [ ] 验证 α=0.3 时，最近一次误差占 30% 权重
- [ ] 验证修正后的估算值与未修正值不同
- [ ] 确认文件行数不超过 150 行

---

## 阶段 4: API 服务层 (src/api/)

### 步骤 4.1: 创建 Pydantic 模型 (src/api/schemas.py)

**指令：**
1. 为每个 API 响应创建 Pydantic 模型：
   - `FundInfo`: 基金基础信息
   - `FundHolding`: 持仓信息
   - `NAVEstimate`: 净值估算结果（含预估净值、涨跌幅、现金比例、更新时间）
   - `NAVHistory`: 历史净值
   - `WatchlistItem`: 关注列表项
   - `AddFundRequest`: 添加基金请求（fund_code）
2. 添加字段验证规则
3. 添加示例数据（用于 API 文档）

**验证测试：**
- [ ] 运行 `python -c "from src.api.schemas import NAVEstimate; print(NAVEstimate.model_json_schema())"` 确认模型有效
- [ ] 确认文件行数不超过 100 行

---

### 步骤 4.2: 创建 API 路由 (src/api/routes.py)

**指令：**
1. 创建 FastAPI 路由器
2. 实现以下 API 端点：
   - `GET /api/watchlist`: 获取用户关注的基金列表
   - `POST /api/watchlist`: 添加基金到关注列表
   - `DELETE /api/watchlist/{fund_code}`: 从关注列表移除基金
   - `GET /api/funds/{fund_code}`: 获取单个基金详情
   - `GET /api/funds/{fund_code}/holdings`: 获取基金持仓
   - `GET /api/funds/{fund_code}/estimate`: 获取实时净值估算
   - `GET /api/funds/{fund_code}/history`: 获取历史净值
   - `GET /api/estimates`: 获取所有关注基金的实时估算
3. 添加错误处理（404、500 等）
4. 添加请求参数验证

**验证测试：**
- [ ] 启动服务后访问 `/docs` 确认 Swagger 文档生成
- [ ] 使用 `curl` 测试添加/删除关注基金
- [ ] 使用 `curl` 测试获取估算结果
- [ ] 测试不存在的基金代码返回 404
- [ ] 确认文件行数不超过 150 行

---

## 阶段 5: 主程序与定时任务

### 步骤 5.1: 创建主入口文件 (main.py)

**指令：**
1. 初始化数据库
2. 创建 FastAPI 应用实例
3. 配置静态文件服务（`frontend/` 目录）
4. 注册 API 路由
5. 配置 APScheduler 定时任务：
   - 每日 8:30 更新关注基金的持仓数据
   - **盘中每 60 秒（1分钟）更新实时估算**（9:30-15:00）
   - 每日 18:00 获取实际净值并计算误差
   - **每日 0:00 清理超过 7 天的估算记录**
6. 启动 uvicorn 服务

**验证测试：**
- [ ] 运行 `python main.py` 确认服务启动无报错
- [ ] 访问 `http://127.0.0.1:8000/docs` 确认 API 文档可访问
- [ ] 确认定时任务已注册（查看启动日志）
- [ ] 确认文件行数不超过 100 行

---

### 步骤 5.2: 创建测试目录

**指令：**
1. 在项目根目录创建 `tests/` 目录
2. 创建 `tests/__init__.py`
3. 创建 `tests/conftest.py` 配置测试夹具：
   - 测试用数据库（使用内存 SQLite）
   - 测试用 FastAPI 客户端
4. 为每个模块创建对应测试文件：
   - `tests/test_db.py`
   - `tests/test_data.py`
   - `tests/test_engine.py`
   - `tests/test_api.py`

**验证测试：**
- [ ] 运行 `pytest tests/ -v` 确认测试框架可用
- [ ] 运行 `pytest tests/ --collect-only` 确认测试用例被发现

---

## 阶段 6: 前端界面 (frontend/)

### 步骤 6.1: 创建 HTML 主页面 (frontend/index.html)

**指令：**
1. 创建简洁的单页面 HTML 文件
2. 页面布局包含：
   - 顶部：标题 "基金净值估算系统"
   - 添加基金：输入框 + 添加按钮
   - 基金列表：表格显示关注的基金（代码、名称、最新净值、预估涨跌幅、更新时间、删除按钮）
   - 底部：上次更新时间、自动刷新状态
3. 使用内联 CSS 或单独的 `style.css` 文件
4. 设计风格：简洁、清晰、适合本地使用

**验证测试：**
- [ ] 在浏览器中打开 `frontend/index.html` 确认页面结构正确
- [ ] 确认页面在 Mac Safari/Chrome 中显示正常

---

### 步骤 6.2: 创建前端 JavaScript (frontend/app.js)

**指令：**
1. 使用原生 JavaScript（无框架）
2. 实现以下功能：
   - 页面加载时从 API 获取关注列表并渲染
   - 添加基金：调用 POST `/api/watchlist`
   - 删除基金：调用 DELETE `/api/watchlist/{fund_code}`
   - 刷新估算：调用 GET `/api/estimates` 获取所有估算
   - **每 60 秒自动刷新估算数据**
   - 显示加载状态和错误提示
3. 涨跌幅颜色：正数显示红色，负数显示绿色
4. 添加输入验证（基金代码格式：6位数字）

**验证测试：**
- [ ] 输入有效基金代码，点击添加，确认基金出现在列表
- [ ] 点击删除按钮，确认基金从列表移除
- [ ] 等待 60 秒，确认数据自动刷新
- [ ] 输入无效代码，确认显示错误提示

---

### 步骤 6.3: 创建前端样式 (frontend/style.css)

**指令：**
1. 创建响应式样式
2. 主要样式包含：
   - 页面最大宽度 800px，居中显示
   - 表格样式：边框、斑马条纹
   - 按钮样式：添加按钮（蓝色）、删除按钮（红色）
   - 涨跌幅颜色：`.positive { color: red; }` `.negative { color: green; }`
   - 输入框样式
   - 错误提示样式（红色背景）
3. 适配 Mac 本地浏览器

**验证测试：**
- [ ] 确认表格显示美观
- [ ] 确认涨跌颜色正确（红涨绿跌）
- [ ] 确认按钮样式区分明显

---

## 阶段 7: 集成测试与验收

### 步骤 7.1: 端到端功能验证

**指令：**
1. 启动服务：`python main.py`
2. 打开浏览器访问 `http://127.0.0.1:8000`
3. 添加一只测试基金（如 `000001` 华夏成长）
4. 验证基金信息显示正确
5. 等待 1 分钟，确认估算数据更新

**验证测试：**
- [ ] 基金已添加到关注列表
- [ ] 显示正确的基金名称
- [ ] 显示预估净值和涨跌幅
- [ ] 数据每分钟自动刷新

---

### 步骤 7.2: 数据清理验证

**指令：**
1. 手动插入一条 8 天前的估算记录到数据库
2. 触发清理任务或等待 0:00 自动执行
3. 验证该记录已被删除

**验证测试：**
- [ ] 运行 `sqlite3 data/fundbug.db "SELECT COUNT(*) FROM nav_estimates"` 确认旧记录被清理

---

### 步骤 7.3: 代码质量检查

**指令：**
1. 检查所有 Python 文件行数不超过 200 行
2. 检查没有重复的代码块
3. 检查所有配置都在 `config.py` 中定义
4. 检查所有数据库操作都在 `src/db/` 中

**验证测试：**
- [ ] 运行 `wc -l src/**/*.py` 确认每个文件行数
- [ ] 运行 `grep -r "sqlite3.connect" src/ | grep -v db/` 确认无散落的数据库连接

---

## 检查清单总览

| 阶段 | 步骤 | 状态 |
|------|------|------|
| 0. 环境准备 | 0.1 创建目录结构 | [ ] |
| 0. 环境准备 | 0.2 创建 requirements.txt | [ ] |
| 0. 环境准备 | 0.3 创建虚拟环境 | [ ] |
| 1. 数据库层 | 1.1 创建 config.py | [ ] |
| 1. 数据库层 | 1.2 创建 models.py | [ ] |
| 1. 数据库层 | 1.3 创建 crud.py | [ ] |
| 2. 数据采集层 | 2.1 创建 fund_list.py | [ ] |
| 2. 数据采集层 | 2.2 创建 holdings.py | [ ] |
| 2. 数据采集层 | 2.3 创建 realtime.py | [ ] |
| 3. 计算引擎层 | 3.1 创建 nav_estimator.py | [ ] |
| 3. 计算引擎层 | 3.2 创建 error_correction.py | [ ] |
| 4. API 服务层 | 4.1 创建 schemas.py | [ ] |
| 4. API 服务层 | 4.2 创建 routes.py | [ ] |
| 5. 主程序 | 5.1 创建 main.py | [ ] |
| 5. 主程序 | 5.2 创建测试目录 | [ ] |
| 6. 前端界面 | 6.1 创建 index.html | [ ] |
| 6. 前端界面 | 6.2 创建 app.js | [ ] |
| 6. 前端界面 | 6.3 创建 style.css | [ ] |
| 7. 集成测试 | 7.1 端到端验证 | [ ] |
| 7. 集成测试 | 7.2 数据清理验证 | [ ] |
| 7. 集成测试 | 7.3 代码质量检查 | [ ] |
