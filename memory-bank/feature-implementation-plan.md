# 实施计划 Checklist：准实时数据获取升级 (1s/次)

目标：将核心数据刷新频率从 60s 提升至 1s，并确保系统稳定性。

---

## Phase 1: 准备工作 (Preparation)

- [ ] **1.1 环境配置**
    - [ ] 确认 Python 版本支持 `asyncio` (已满足 3.11+)。
    - [ ] 决定是否引入 `httpx` (异步 HTTP 客户端) 或继续使用 `requests` + `run_in_executor`。
    - [ ] *决策*: 鉴于深度依赖 `akshare` (其内部使用 `requests`)，采用 **线程池 (ThreadPoolExecutor)** 方案最稳妥，无需重写底层请求逻辑。

- [ ] **1.2 依赖梳理**
    - [ ] 检查 `APScheduler` 版本是否支持 `AsyncIOScheduler` (已满足 3.10+)。
    - [ ] 确认是否需要安装 `fake-useragent` (用于反爬) -> 决定手动维护 User-Agent 列表以减少依赖。

---

## Phase 2: 核心代码重构 (Core Refactoring)

### 2.1 重构数据层 (`src/data/realtime.py`)
- [ ] **创建 `AsyncRealtimeProvider` 类**
    - [ ] 实现单例模式，维护 `_quote_cache` (字典) 和 `_last_update_time`。
    - [ ] 实现 `start_background_loop()`: 启动 `asyncio` 任务。
    - [ ] 实现 `_fetch_worker()`: 
        - [ ] 死循环 `while True`。
        - [ ] 调用 `loop.run_in_executor` 执行 `ak.stock_zh_a_spot_em`。
        - [ ] 增加随机 User-Agent。
        - [ ] 增加异常捕获 (Log only, no crash)。
        - [ ] 每次循环末尾 `await asyncio.sleep(1)`.

### 2.2 重构计算引擎 (`src/engine/nav_estimator.py`)
- [ ] **适配异步读取**
    - [ ] 修改 `estimate_fund_nav`: 不再直接调用 `get_realtime_quotes` (网络请求)，而是调用 `AsyncRealtimeProvider.get_cached_quote` (内存读取)。
    - [ ] 确保在缓存未就绪时有兜底逻辑 (如返回 None 或阻塞等待一次)。

### 2.3 重构主入口 (`main.py`)
- [ ] **切换调度器**
    - [ ] 将 `BackgroundScheduler` (同步) 替换为 `AsyncIOScheduler` (异步) 或仅使用 `lifespan` 管理后台任务。
    - [ ] *方案*: 保持 `APScheduler` 用于低频任务 (持仓更新、清理)，新增 `asyncio.create_task` 用于 1s 级别的高频行情拉取。

---

## Phase 3: 稳定性增强 (Robustness)

- [ ] **3.1 反爬策略集成**
    - [ ] 实现 User-Agent 随机池。
    - [ ] 实现请求间隔抖动 (Jitter: 0.8s ~ 1.2s)。
    - [ ] 实现连续失败自动降级 (Circuit Breaker): 失败 > 5次 -> 休眠 30s。

- [ ] **3.2 内存管理**
    - [ ] 确保 `_quote_cache` 不会无限增长 (仅存储最新快照，由于是覆盖写入，天然无泄漏)。

---

## Phase 4: 测试验证 (Verification & Stress Testing)

- [ ] **4.1 单元测试 (`tests/test_async_realtime.py`)**
    - [ ] Mock `run_in_executor` 模拟网络延迟。
    - [ ] 验证 `get_cached_quote` 是否立即返回。
    - [ ] 验证背景任务是否自动从故障中恢复。

- [ ] **4.2 压力测试脚本 (`stress_test_1Hz.py`)**
    - [ ] **目标**: 模拟 1 小时运行，验证内存和频率。
    - [ ] **步骤**:
        1. 启动 `AsyncRealtimeProvider`。
        2. 记录每次 update 的时间戳，计算 Δt。
        3. 统计成功/失败次数。
        4. 检测内存占用 (`psutil`)。
    - [ ] **通过标准**:
        - 平均间隔: 1.0s ± 0.2s
        - 内存泄漏: < 10MB/hour
        - 异常崩溃: 0 次

- [ ] **4.3 集成测试**
    - [ ] 启动 `main.py`，观察日志输出。
    - [ ] 前端页面刷新，确认估值随行情变动而跳动。

