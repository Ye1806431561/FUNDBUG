# FUNDBUG 开发进度记录

> 此文档记录开发过程，供后续开发者参考。

---

## 2026-02-10 - 步骤 0.1: 创建项目目录结构 & Git 初始化 ✅

### 完成内容

1. **创建项目结构**：
    ```
    FUNDBUG/
    ├── src/                    # 源代码目录
    │   ├── __init__.py
    │   ├── data/               # 数据采集层
    │   ├── engine/             # 计算引擎层
    │   ├── api/                # API 服务层
    │   ├── db/                 # 数据库层
    │   └── utils/              # 公共工具
    ├── frontend/               # 前端目录
    ├── data/                   # SQLite 数据库目录
    ├── config.py               # 配置文件
    └── main.py                 # 主入口文件
    ```

2. **Git 初始化**：
    - 创建/确认 `.gitignore`
    - 执行 `git init`
    - 执行 `git add .`
    - 执行 `git commit -m "Initial commit..."`
    - **远程仓库**：`https://github.com/Ye1806431561/FUNDBUG.git`（已推送）

### 关键决策

1. **config.py 已预填充配置** - 包含 DATABASE_PATH, API_HOST/PORT, UPDATE_INTERVAL_SECONDS(60), DATA_RETENTION_DAYS(7), EWA_ALPHA(0.3)
2. **每个模块都有 `__init__.py`** - 确保 Python 包结构正确
3. **data/ 目录独立于 src/data/** - 前者存放 SQLite 文件，后者存放数据采集代码

### 验证结果

```bash
$ find src -name "__init__.py" | wc -l
6  ✅

$ ls config.py main.py frontend/ data/
config.py  main.py  data/  frontend/  ✅

$ git status
On branch master (or main)
nothing to commit, working tree clean ✅
```

---

## 2026-02-10 - 步骤 0.2: 创建 requirements.txt ✅

### 完成内容

1. **创建 `requirements.txt`**（9 个依赖项，按功能分组）：

    | 功能分类 | 依赖包 | 版本要求 |
    |----------|--------|----------|
    | API 服务 | fastapi, uvicorn | >=0.109.0, >=0.27.0 |
    | 数据采集 | akshare | >=1.12.0 |
    | 数据计算 | pandas, numpy | >=2.2.0, >=1.26.0 |
    | 定时任务 | apscheduler | >=3.10.0 |
    | 前端模板 | jinja2 | >=3.1.0 |
    | 表单处理 | python-multipart | >=0.0.6 |
    | 测试 | pytest | >=8.0.0 |

2. **提交并推送到 GitHub**：
    - Commit: `876a317` - `feat: 步骤 0.2 - 创建 requirements.txt`

### 关键决策

1. **使用 `>=` 而非 `==` 版本约束** — 允许向上兼容，避免依赖锁死，适合开发阶段
2. **依赖按功能分组并加中文注释** — 便于后续开发者快速理解每个包的用途
3. **jinja2 和 python-multipart 独立列出** — 虽然是 FastAPI 的可选依赖，但本项目确实需要（前端模板渲染 + 表单处理），显式声明更清晰

### 验证结果

```bash
$ cat requirements.txt
# 内容正确，9 个依赖项全部列出 ✅
```

### 注意事项（供后续开发者）

- `akshare` 安装时会拉取较多子依赖（约 50+ 个包），首次安装耗时较长属正常
- 建议在虚拟环境中安装，避免污染全局 Python 环境（步骤 0.3）
- 如遇 akshare 版本兼容问题，可参考 [AKShare 文档](https://akshare.akfamily.xyz/)

---

## 2026-02-10 - 步骤 0.3: 创建 Python 虚拟环境 ✅

### 完成内容

1. **创建虚拟环境**：
    - 运行 `python3 -m venv .venv`
    - 虚拟环境目录：`/Users/pingu/Documents/FUNDBUG/.venv/`

2. **安装全部依赖**：
    - 运行 `.venv/bin/pip install -r requirements.txt`
    - 共安装 47 个包（含子依赖）

3. **已安装依赖版本**：

    | 依赖包 | 安装版本 | 要求版本 |
    |--------|----------|----------|
    | fastapi | 0.128.6 | ≥0.109.0 |
    | uvicorn | 0.40.0 | ≥0.27.0 |
    | akshare | 1.18.23 | ≥1.12.0 |
    | pandas | 3.0.0 | ≥2.2.0 |
    | numpy | 2.4.2 | ≥1.26.0 |
    | apscheduler | 3.11.2 | ≥3.10.0 |
    | jinja2 | 3.1.6 | ≥3.1.0 |
    | python-multipart | 0.0.22 | ≥0.0.6 |
    | pytest | 9.0.2 | ≥8.0.0 |

### 关键决策

1. **使用 `.venv/bin/python` 直接调用** — 无需手动 `source activate`，避免 shell 环境差异
2. **`.venv/` 已在 `.gitignore` 中** — 不会被提交到 Git 仓库
3. **Python 版本为 3.13** — pip 提示有新版本可用（24.3.1 → 26.0.1），暂未升级，不影响功能

### 验证结果

```bash
$ .venv/bin/python -c "import sys; print(sys.executable)"
/Users/pingu/Documents/FUNDBUG/.venv/bin/python  ✅

$ .venv/bin/python -c "import fastapi; print(fastapi.__version__)"
0.128.6  ✅

$ .venv/bin/python -c "import akshare; print(akshare.__version__)"
1.18.23  ✅
```

### 注意事项（供后续开发者）

- 运行项目代码时，使用 `.venv/bin/python` 或先执行 `source .venv/bin/activate`
- 如需添加新依赖，先更新 `requirements.txt`，再运行 `.venv/bin/pip install -r requirements.txt`
- akshare 子依赖包含 `curl_cffi`、`lxml`、`beautifulsoup4` 等，首次安装约 47 个包属正常

---

## 阶段 0 完成总结

| 步骤 | 内容 | 状态 |
|------|------|------|
| 0.1 | 创建项目目录结构 & Git 初始化 | ✅ |
| 0.2 | 创建 requirements.txt | ✅ |
| 0.3 | 创建 Python 虚拟环境 | ✅ |

> **阶段 0（环境准备）已全部完成，可以开始阶段 1（数据库层）。**

---

## 2026-02-10 - 步骤 1.1: 完善 config.py 配置文件 ✅

### 完成内容

1. **验证 config.py 配置完整性**：
    - 由步骤 0.1 时已创建 `config.py` 并预填充全部 8 个配置项
    - 本步骤确认所有配置项符合步骤 1.1 要求，无需额外修改

2. **配置项清单**：

    | 配置项 | 值 | 用途 |
    |--------|-----|------|
    | `DATABASE_PATH` | `./data/fundbug.db` | SQLite 数据库文件路径（使用 `os.path.join` 动态拼接） |
    | `API_HOST` | `127.0.0.1` | API 服务主机 |
    | `API_PORT` | `8000` | API 服务端口 |
    | `TRADING_START` | `09:30` | 开盘时间 |
    | `TRADING_END` | `15:00` | 收盘时间 |
    | `UPDATE_INTERVAL_SECONDS` | `60` | 估算更新间隔（秒） |
    | `DATA_RETENTION_DAYS` | `7` | 估算记录保留天数 |
    | `EWA_ALPHA` | `0.3` | 指数加权平均衰减系数 |

### 关键决策

1. **config.py 无需修改** — 步骤 0.1 时已按 `implementation-plan.md` 的要求完整实现，本步骤仅做验证确认
2. **DATABASE_PATH 使用 `os.path.join` 动态拼接** — 避免路径分隔符在不同 OS 上的差异，比硬编码字符串更健壮
3. **所有配置均为模块级常量** — 遵循 Python 惯例，大写命名，可通过 `from config import X` 直接引用

### 验证结果

```bash
$ .venv/bin/python -c "from config import DATABASE_PATH, UPDATE_INTERVAL_SECONDS; ..."
DATABASE_PATH=/Users/pingu/Documents/FUNDBUG/data/fundbug.db  ✅
UPDATE_INTERVAL_SECONDS=60  ✅
# 全部 8 个配置项均可成功导入

$ wc -l config.py
26  ✅ (上限 50 行)
```

### 注意事项（供后续开发者）

- `config.py` 是全局唯一的配置来源，所有模块必须从此处导入配置，**禁止硬编码**
- 如需新增配置项（如日志级别、缓存时间等），直接在此文件追加即可
- `DATABASE_PATH` 使用 `__file__` 相对路径拼接，确保无论从哪个目录运行都能正确定位数据库

---

## 2026-02-10 - 步骤 1.2: 创建数据库模型 (src/db/models.py) ✅

### 完成内容

1. **创建 `src/db/models.py`**（106 行）：
    - 定义 `init_db()` 函数：创建数据目录 + 建表（幂等）
    - 定义 `get_connection()` 函数：获取 SQLite 连接（启用外键约束 + Row factory）
    - 创建 5 张表，严格遵循 `architecture.md` 表结构

2. **5 张表清单**：

    | 表名 | 主键 | 关键约束 |
    |------|------|----------|
    | `funds` | `fund_code` (TEXT PK) | 无外键 |
    | `holdings` | `id` (AUTOINCREMENT) | FK→funds, UNIQUE(fund_code, stock_code, report_date) |
    | `nav_history` | `id` (AUTOINCREMENT) | FK→funds, UNIQUE(fund_code, nav_date) |
    | `nav_estimates` | `id` (AUTOINCREMENT) | FK→funds |
    | `user_watchlist` | `id` (AUTOINCREMENT) | fund_code UNIQUE |

### 关键决策

1. **启用 `PRAGMA foreign_keys = ON`** — SQLite 默认不强制外键约束，必须显式开启
2. **使用 `sqlite3.Row` 作为 row_factory** — 使查询结果可以按列名访问（`row['fund_code']`），方便后续 CRUD 操作
3. **`init_db()` 接受可选 `db_path` 参数** — 默认从 `config.DATABASE_PATH` 读取，测试时可传入 `:memory:` 使用内存数据库
4. **SQL 语句使用模块级常量** — 以 `_CREATE_XXX` 命名，收集到 `_ALL_TABLES` 列表中统一执行，便于维护
5. **`os.makedirs(exist_ok=True)` 自动创建目录** — 避免首次运行时因 `data/` 目录不存在而失败

### 验证结果

```bash
$ .venv/bin/python -c "from src.db.models import init_db; init_db(); ..."
✅ fundbug.db 创建成功

$ sqlite3 data/fundbug.db ".tables"
funds  holdings  nav_estimates  nav_history  user_watchlist  ✅ (5 张表)

$ sqlite3 data/fundbug.db ".schema user_watchlist"
CREATE TABLE user_watchlist (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL UNIQUE,
    fund_name TEXT,
    added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);  ✅

$ wc -l src/db/models.py
106  ✅ (上限 150 行)
```

### 注意事项（供后续开发者）

- `get_connection()` 是后续 `crud.py` 获取数据库连接的唯一入口，禁止在其他模块中直接调用 `sqlite3.connect()`
- `init_db()` 是幂等操作，重复调用不会清除已有数据
- 所有表的 `created_at` 字段默认使用 `CURRENT_TIMESTAMP`（UTC 时间）
- 测试时建议使用 `init_db(":memory:")` 创建内存数据库，避免污染正式 DB

---

## 2026-02-10 - 步骤 1.3: 创建 CRUD 操作 (src/db/crud.py) ✅

### 完成内容

1. **实现 `src/db/crud.py`**：
    - 完整实现了 5 张表的增删改查操作
    - **Funds**: `insert_fund`, `get_fund`, `get_all_funds`, `update_fund_nav`
    - **Holdings**: `insert_holdings` (批量), `get_holdings_by_fund`, `get_latest_holdings`
    - **NAV History**: `insert_nav`, `get_nav_history`, `get_latest_nav`
    - **NAV Estimates**: `insert_estimate`, `update_actual_nav`, `get_estimate_errors`, `cleanup_old_estimates`
    - **Watchlist**: `add_to_watchlist`, `remove_from_watchlist`, `get_watchlist`, `is_in_watchlist`

2. **创建测试基础设施**：
    - `tests/conftest.py`: 定义 `test_db_path` fixture 和自动 patch `get_connection`
    - `tests/test_db.py`: 覆盖所有 CRUD 函数的单元测试

### 关键决策

1. **依赖注入测试 (Mocking)** — 为了在不污染 `config.DATABASE_PATH` 所指真实数据库的情况下测试，使用了 `unittest.mock.patch` 拦截 `src.db.crud.get_connection`，将其重定向到临时文件数据库。这是确保测试安全性的关键架构模式。
2. **资源管理 (Resource Management)** — 所有数据库操作均包裹在 `try...finally` 块中，确保连接（Connection）在操作后必定关闭，防止连接泄漏。
3. **批量写入优化** — `insert_holdings` 使用 `executemany` 进行批量插入，显著提升写入性能。
4. **幂等性设计 (Idempotency)** — 插入操作广泛使用 `ON CONFLICT DO UPDATE` 或 `DO NOTHING`，允许重复调用而不会报错或产生重复数据。

### 验证结果

```bash
$ PYTHONPATH=. .venv/bin/pytest tests/test_db.py -v
tests/test_db.py::test_fund_operations PASSED                            [ 20%]
tests/test_db.py::test_holdings_operations PASSED                        [ 40%]
tests/test_db.py::test_nav_history_operations PASSED                     [ 60%]
tests/test_db.py::test_nav_estimates_cleanup PASSED                      [ 80%]
tests/test_db.py::test_watchlist_operations PASSED                       [100%]
```

---

## 阶段 1 进度

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1.1 | 完善 config.py 配置文件 | ✅ |
| 1.2 | 创建数据库模型 (src/db/models.py) | ✅ |
| 1.3 | 创建 CRUD 操作 (src/db/crud.py) | ✅ |

---


## 2026-02-10 - 步骤 2.1: 创建基金列表获取模块 (src/data/fund_list.py) ✅

### 完成内容

1.  **创建 `src/data/fund_list.py`**：
    -   实现 `get_fund_info(fund_code)`:
        -   使用 `ak.fund_individual_basic_info_xq` 获取基金名称和类型（如“混合型-偏股”）。
        -   使用 `ak.fund_open_fund_info_em` 获取最新单位净值和净值日期。
    -   实现 `validate_fund_code(fund_code)`: 校验 6 位数字格式并调用 `get_fund_info` 确认存在。
    -   实现 `save_fund_info(fund_code)`: 获取信息并调用 `crud.insert_fund` 保存至数据库。
    -   **实现重试机制**：使用 `@retry_on_failure` 装饰器处理网络波动。

2.  **创建 `src/utils/helpers.py`**：
    -   实现 `@retry_on_failure` 装饰器，为网络请求提供重试机制（默认重试 3 次，间隔 1 秒）。
    -   将其应用于 `get_fund_info` 的内部实现 `_fetch_fund_info_impl`，增强稳定性。

3.  **创建测试 `tests/test_data.py`**：
    -   覆盖正常获取、网络异常重试、无效代码校验等场景。
    -   验证重试机制正确工作（模拟前 2 次失败，第 3 次成功）。

### 关键决策

1.  **分步获取信息** — AKShare 没有单一接口同时返回“基金类型”和“最新净值”，因此组合使用了两个接口。
2.  **重试装饰器** — 将重试逻辑抽离到 `src/utils/helpers.py`，保持业务代码整洁，方便后续复用于其他数据获取模块。
3.  **异常处理策略** — `get_fund_info` 内部捕获最终异常并返回 `None`，调用方（如 `save_fund_info`）据此判断失败，避免程序崩溃。

### 验证结果

```bash
$ PYTHONPATH=. .venv/bin/pytest tests/test_data.py -v
tests/test_data.py::test_get_fund_info_retry_success PASSED              [ 12%]
tests/test_data.py::test_get_fund_info_success PASSED                    [ 25%]
# ... 全部 8 个测试通过 ✅

$ python verify_step_2_1.py
--- 验证 1: 已知基金代码 (000001) ---
✅ 获取成功: {'fund_code': '000001', 'fund_name': '华夏成长混合', ...}
✅ 基金名称正确

--- 验证 2: 无效基金代码 (999999) ---
✅ 返回 None (符合预期)

$ wc -l src/data/fund_list.py
89 src/data/fund_list.py  ✅ (上限 200 行)
```

---

## 2026-02-10 - 步骤 2.2: 创建持仓数据获取模块 (src/data/holdings.py) ✅

### 完成内容

1. **创建 `src/data/holdings.py`**：
    - 实现 `get_fund_holdings(fund_code)`：
        - 调用 `ak.fund_portfolio_hold_em` 获取持仓数据。
        - 自动解析“季度”字段（如 `2024年1季度...`）为标准 `YYYY-MM-DD` 格式。
        - 仅筛选并返回**最新报告期**的数据。
    - 实现 `save_fund_holdings(fund_code)`：
        - 获取数据并调用 `crud.insert_holdings` 存入数据库。
        - 计算并打印“已披露持仓占比”和“未披露/现金占比”。

2. **创建测试 `tests/test_holdings.py`**：
    - 使用 `unittest.mock` 模拟 AKShare 返回数据，测试解析逻辑、成功获取、空数据处理、异常处理等场景。
    - 验证 `_parse_report_date` 函数对不同季度格式的解析能力。

### 关键决策

1. **只取最新季度数据** — AKShare 接口可能返回历史所有季度的数据，本系统只关注最新的持仓结构用于估算，因此在获取后立即通过日期筛选只保留最新一期。
2. **日期自动提取** — 从中文字符串（如“2024年1季度股票投资明细”）中正则提取年份和季度，并映射为具体的季度末日期（03-31, 06-30等），确保存储到数据库的是标准 DATE 类型。
3. **未披露部分算作现金** — 在验证脚本中明确输出了“未披露/现金”比例，这是后续 NAV 估算的关键假设（未披露部分涨跌幅设为 0%）。

### 验证结果

```bash
$ PYTHONPATH=. .venv/bin/pytest tests/test_holdings.py -v
tests/test_holdings.py::test_parse_report_date PASSED                    [ 14%]
tests/test_holdings.py::test_get_fund_holdings_success PASSED            [ 28%]
# ... 全部 7 个测试通过 ✅

$ PYTHONPATH=. python verify_step_2_2.py
--- Verifying Step 2.2 for Fund 000001 ---
Fetching and saving holdings...
Fund 000001 (2024-12-31): Found 175 stocks.
Total disclosed weight: 64.07% (Undisclosed/Cash: 35.93%)
✅ save_fund_holdings returned True
✅ Found 175 holdings in DB
```

---

## 下一步

- [x] 阶段 1 步骤 1.1: 完善 config.py 配置文件 ✅
- [x] 阶段 1 步骤 1.2: 创建数据库模型 (src/db/models.py) ✅
- [x] 阶段 1 步骤 1.3: 创建 CRUD 操作 (src/db/crud.py) ✅
- [x] 阶段 2 步骤 2.1: 创建基金列表获取模块 (src/data/fund_list.py) ✅
- [x] 阶段 2 步骤 2.2: 创建持仓数据获取模块 (src/data/holdings.py) ✅
- [x] 阶段 2 步骤 2.3: 创建实时行情获取模块 (src/data/realtime.py) ✅

---

## 2026-02-10 - 步骤 2.3: 创建实时行情获取模块 (src/data/realtime.py) ✅

### 完成内容

1. **创建 `src/data/realtime.py`**：
    - 实现 `get_realtime_quotes(stock_codes)` 函数，输入股票代码列表，返回包含 `stock_code`, `name`, `current_price`, `change_percent` 的 DataFrame。
    - **批量获取优先**：默认使用 `ak.stock_zh_a_spot_em()` 一次性获取全市场实时行情（速度快，适合大规模数据）。
    - **降级机制 (Fallback)**：当批量接口失败（如网络波动或接口不稳定）时，自动切换到 `_get_quotes_by_symbols`，使用 `ak.stock_bid_ask_em` 逐个获取。
    - **并发加速**：降级模式下使用 `concurrent.futures.ThreadPoolExecutor` 并发请求（最大 10 线程），显著提升逐个获取的速度。
    - **缓存机制**：使用模块级全局变量 `_SC_CACHE` 缓存全市场行情 60 秒，避免在一分钟内重复请求外部接口。

2. **创建测试 `tests/test_realtime.py`**：
    - 测试正常批量获取流程。
    - 测试缓存是否生效（Mock 验证调用次数）。
    - 测试无效股票代码处理。
    - **测试降级机制**：Mock 批量接口失败，验证是否自动切换到逐个获取并返回正确数据。

3. **验证脚本 `verify_step_2_3.py`**：
    - 验证真实网络环境下的 API 连通性。
    - 验证数据字段 integrity（价格 > 0，涨跌幅合理）。
    - 验证降级逻辑（在批量接口不稳定时自动恢复）。

### 关键决策

1. **双重获取策略** — `ak.stock_zh_a_spot_em` 接口虽然高效但近期不稳定（频繁出现 `RemoteDisconnected`），因此引入 `ak.stock_bid_ask_em` 作为兜底方案。这种“乐观批量，悲观并发”的策略极大地提高了系统的鲁棒性。
2. **线程池并发** — 单线程逐个获取 100 只股票可能需要数十秒，使用 ThreadPoolExecutor 将耗时压缩到可接受范围（~2-5秒）。
3. **缓存粒度** — 缓存设为 60 秒，与项目要求的“每分钟更新一次”频率一致，既保证实时性又避免触发反爬限制。

### 验证结果

```bash
$ PYTHONPATH=. .venv/bin/pytest tests/test_realtime.py -v
tests/test_realtime.py::test_get_realtime_quotes_success PASSED          [ 25%]
tests/test_realtime.py::test_get_realtime_quotes_caching PASSED          [ 50%]
tests/test_realtime.py::test_get_realtime_quotes_invalid_code PASSED     [ 75%]
tests/test_realtime.py::test_get_realtime_quotes_fallback PASSED         [100%]
# 全部测试通过 ✅

$ python verify_step_2_3.py
--- Verifying Step 2.3: Realtime Quotes ---
Fetching quotes for: ['000001', '600519', '300750']
Error fetching batch real-time quotes: ...
Attempt 1/3 failed ...
...
Fallback: Fetching 3 stocks individually...
✅ Successfully fetched 3 quotes.
✅ Price for 000001 (11.06) is valid
✅ Change percent for 000001 (-0.09%) is reasonable
```

---

## 阶段 2 完成总结

| 步骤 | 内容 | 状态 |
|------|------|------|
| 2.1 | 基金列表获取 (fund_list.py) | ✅ |
| 2.2 | 持仓数据获取 (holdings.py) | ✅ |
| 2.3 | 实时行情获取 (realtime.py) | ✅ |

> **阶段 2（数据采集层）已全部完成，可以开始阶段 3（计算引擎层）。**

