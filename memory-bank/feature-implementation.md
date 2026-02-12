# 核心数据获取模块升级：准实时 (Real-time) 方案

## 1. 现状回顾
目前系统使用 `APScheduler` (BackgroundScheduler) 进行单线程同步轮询，更新频率为 **60秒/次**。
**目标**：将核心数据获取与估值频率调整为 **1秒/次** (准实时)。

## 2. 技术风险分析 (Technical Risks)

### 2.1 API 速率限制与 IP 封禁 (Rate Limiting & Ban) - [CRITICAL]
- **风险描述**: 上游数据源（如东方财富接口通过 AKShare 调用）并未开放官方高频 API。以 1Hz 频率请求全市场行情 (`stock_zh_a_spot_em`) 极易被识别为爬虫。
- **可能后果**: IP 被临时或永久封禁，导致 `RemoteDisconnected` 或 HTTP 403 错误，服务完全不可用。

### 2.2 网络延迟与阻塞 (Latency & Blocking) - [HIGH]
- **风险描述**: 全市场行情接口的数据量较大（5000+ 只股票），网络传输 + 解析耗时通常在 0.5s ~ 3s 之间。
- **可能后果**: 在同步模式下，如果一次请求耗时 2s，而调度间隔设为 1s，会导致任务堆积 (Job Missed) 或主线程阻塞，不仅无法达到 1Hz，还会拖累 API 接口的响应速度。

### 2.3 资源竞争 (Resource Contention)
- **风险描述**: 高频创建/销毁 SSL 连接（HTTPS）会消耗大量 CPU 和文件句柄。

## 3. 解决方案 (Solutions)

### 3.1 架构升级：全链路异步化 (Asyncio Integration)
- **废弃同步轮询**: 现有的同步 `APScheduler` 无法满足高并发非阻塞需求。
- **引入 Asyncio**:
    - 使用 Python 原生 `asyncio` 协程处理 I/O 密集型任务。
    - 将阻塞的 AKShare 调用（同步 HTTP）封装在 `loop.run_in_executor` (线程池) 中运行。
    - 确保主线程（FastAPI 所在线程）永远不被数据采集任务阻塞。

### 3.2 策略优化：动态降级与智能采集 (Smart Fetching)
为了应对 1s 的严苛要求，不能傻瓜式地每秒拉取全量数据：
- **模式 A (极速模式)**: 仅拉取 **“用户关注列表中的持仓股”**。数据量极小（几十到几百只），响应极快 (<200ms)，可安全实现 1s 刷新。
- **模式 B (全量兜底)**: 每 60s 拉取一次全市场数据，用于后台修正和非关注列表查询。
- **动态切换**: 只有当用户正在查看某个基金时（通过前端 heartbeat 或 API 最近调用时间判断），才对该基金的持仓进行 1s 级别刷新。**本次暂设定为：优先保障关注列表的实时性。**

### 3.3 反爬防御体系 (Anti-Scraping Defense)
- **User-Agent 池**: 每次请求随机轮换请求头。
- **请求抖动 (Jitter)**: 在 1s 基础上增加 ±0.1s 的微小随机延迟，避免机器特征过强。
- **错误熔断**: 连续失败 3 次后自动降级频率到 5s/次，等待 IP 解封。

## 4. 新数据流转逻辑 (Data Flow)

采用 **“生产者-消费者 (Producer-Consumer)”** 与 **“读写分离”** 模型：

1.  **全局状态缓存 (Global State Cache)**:
    - 维护一个线程/协程安全的内存字典 `GLOBAL_QUOTE_CACHE`。
    - 结构: `{ "stock_code": { "price": ..., "time": ... } }`。

2.  **生产者 (Producer - Background Task)**:
    - 独立运行的 `async` 无限循环。
    - 逻辑：`Sleep(1s)` -> `Fetch Quotes (Thread Pool)` -> `Update Cache`。
    - 异常处理：捕获所有网络异常，仅记录日志，不崩溃。

3.  **消费者 (Consumer - Nav Estimator)**:
    - API 请求触发时，**直接从内存缓存读取**最新行情，耗时为 0ms。
    - 如果缓存过期（如 >10s 未更新），则标记数据为“旧数据”或尝试触发一次即时更新。

## 5. 模块调整建议
- **`src/data/realtime.py`**: 重构为支持异步调用，增加 User-Agent 随机化。
- **`src/engine/nav_estimator.py`**: 改为从内存缓存读取行情，而非直接调用数据层。
- **`main.py`**: 在 `lifespan` 中启动后台采集任务。

## 6. 压力测试标准
- 持续运行 1 小时。
- 频率严格维持 1s/次。
- 内存增长 < 50MB。
- 异常率 < 1% (允许偶发网络抖动)。
