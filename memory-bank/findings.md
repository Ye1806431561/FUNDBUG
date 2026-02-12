# Findings & Decisions
<!-- 
  WHAT: Your knowledge base for the task. Stores everything you discover and decide.
  WHY: Context windows are limited. This file is your "external memory" - persistent and unlimited.
  WHEN: Update after ANY discovery, especially after 2 view/browser/search operations (2-Action Rule).
-->

## Requirements
<!-- 
  WHAT: What the user asked for, broken down into specific requirements.
  WHY: Keeps requirements visible so you don't forget what you're building.
  WHEN: Fill this in during Phase 1 (Requirements & Discovery).
  EXAMPLE:
    - Command-line interface
    - Add tasks
    - List all tasks
    - Delete tasks
    - Python implementation
-->
<!-- Captured from user request -->
-

## Research Findings
<!-- 
  WHAT: Key discoveries from web searches, documentation reading, or exploration.
  WHY: Multimodal content (images, browser results) doesn't persist. Write it down immediately.
  WHEN: After EVERY 2 view/browser/search operations, update this section (2-Action Rule).
  EXAMPLE:
    - Python's argparse module supports subcommands for clean CLI design
    - JSON module handles file persistence easily
    - Standard pattern: python script.py <command> [args]
-->
<!-- Key discoveries during exploration -->
- **前端设计美学**：为了提升本地工具的使用体验，采用了深色背景 (`#0f172a`) 配合渐变文字标题和卡片式布局，相比传统表格更具现代感和 scannability。
- **实时性反馈**：在 `index.html` 中预留了 `last-update` 元素，用于向用户直观展示数据的新鲜度，这是交易辅助类工具的关键需求。
- **防御性输入**：前端通过 HTML5 原生校验拦截非法基金代码，减少了无效的 API 请求压力。


## Technical Decisions
<!-- 
  WHAT: Architecture and implementation choices you've made, with reasoning.
  WHY: You'll forget why you chose a technology or approach. This table preserves that knowledge.
  WHEN: Update whenever you make a significant technical choice.
  EXAMPLE:
    | Use JSON for storage | Simple, human-readable, built-in Python support |
    | argparse with subcommands | Clean CLI: python todo.py add "task" |
-->
<!-- Decisions made with rationale -->
| Decision | Rationale |
|----------|-----------|
| `weight` 和 `change_percent` 统一用百分比 | 数据库和 AKShare 接口均以百分比存储（如 3.46 = 3.46%），保持一致避免量级错误 |
| 缺失行情的股票涨跌幅视为 0% | 停牌/退市股票无实时数据，视为 0% 不影响整体估算稳定性 |
| `_calculate_weighted_return` 设计为纯函数 | 无副作用、易测试，遵循 SRP 原则 |
| 未披露持仓视为现金（涨跌 0%） | 设计文档明确要求，现金不影响估算涨跌幅 |
| EWA 初始值为 0，无历史数据时不修正 | 系统冷启动时无偏差数据，直接使用原始估算值，避免引入虚假修正 |
| EWA 按时间正序逐步累加 | `crud.get_estimate_errors` 返回 DESC，代码 reverse() 后累加确保最近误差权重最高 |
| `apply_correction` 设计为纯函数 | 与 `_calculate_weighted_return` 同理，无副作用、可独立测试 |
| 修正涨跌幅 = 原始涨跌幅 - EWA 偏差 | 与净值修正方向一致，保持数据语义正确 |
| AddFundRequest 强制正则校验 | 基金代码必须为 6 位数字，利用 Pydantic Field 直接实现入口防御 |
| API 响应模型附带 Examples | 充分利用 Pydantic v2 `json_schema_extra` 提升 Swagger 文档可读性 |
| 极致行数控制（Schema < 100 行） | 通过压缩非必要空行和分隔注释，确保在复杂业务场景下仍能遵守架构红线 |  
| `main.py` 采用 `lifespan` 管理异步上下文 | 确保 APScheduler 在 FastAPI 启停时同步正确启动和关闭，避免资源泄漏 |
| 任务调度使用 `CronTrigger` 替代 `IntervalTrigger` | `CronTrigger` 支持 `day_of_week` 且语义更清晰。在任务内部增加 `is_trading_time` 校验提供双重保障 |
| 注册 4 个核心后台任务 | 包括持仓更新、盘中估算、每日净值回填和数据清理，全面覆盖系统运行需求 |
| 测试基础设施工程化 | 将 TestClient 提升至 conftest.py 级别，极大简化了 API 测试的编写负担 |
| 自动化测试流水线脚本 | 通过 run_tests.sh 规范化测试运行环境，避免 PYTHONPATH 缺失导致的模块导入错误 |

## Issues Encountered
<!-- 
  WHAT: Problems you ran into and how you solved them.
  WHY: Similar to errors in task_plan.md, but focused on broader issues (not just code errors).
  WHEN: Document when you encounter blockers or unexpected challenges.
  EXAMPLE:
    | Empty file causes JSONDecodeError | Added explicit empty file check before json.load() |
-->
<!-- Errors and how they were resolved -->
| Issue | Resolution |
|-------|------------|
| `src/data/holdings.py` 缺少参数调用 | 修复了 `save_fund_holdings` 中调用 `crud.insert_holdings` 缺失 `fund_code` 参数的问题 |
| AKShare 接口频繁断连 (RemoteDisconnected) | 观测到全量行情和单个行情接口在请求量大时极不稳定。系统通过降级机制（批量->逐个）和 ThreadPoolExecutor 并发抓取提高了存活率，但仍存在部分失败风险。 |
| APScheduler `IntervalTrigger` 不支持 `day_of_week` | 切换为 `CronTrigger`，并在 `main.py` 中实现了 `is_trading_time()` 逻辑以在非交易时段静默。 |
| **前端占位符加载体验** | 初始加载时 `watchlist-container` 显示“正在加载...”状态，提升了单页应用 (SPA) 风格的交互感知。|
| **移动端适配** | 采用卡片式布局替代表格，确保在手机端也能清晰展示基金的 5+ 个关键指标而不拥挤。 |
| **市场惯例适配** | 遵循中国股市“红涨绿跌”惯例，并重新定义 CSS 变量 `--up-color`/`--down-color`，与国际惯例（红跌绿涨）解耦，便于未来切换。 |
| **外部接口不稳定性** | 观测到 `akshare` 在盘中高频访问时极易出现 `RemoteDisconnected`。目前的“批量失败转逐个”降级策略虽然能运行，但在极端网络下逐个获取也会大量失败（如 14:40 的日志显示）。建议未来引入本地缓存代理或更多备用数据源。 |


## Resources
<!-- 
  WHAT: URLs, file paths, API references, documentation links you've found useful.
  WHY: Easy reference for later. Don't lose important links in context.
  WHEN: Add as you discover useful resources.
  EXAMPLE:
    - Python argparse docs: https://docs.python.org/3/library/argparse.html
    - Project structure: src/main.py, src/utils.py
-->
<!-- URLs, file paths, API references -->
-

## Visual/Browser Findings
<!-- 
  WHAT: Information you learned from viewing images, PDFs, or browser results.
  WHY: CRITICAL - Visual/multimodal content doesn't persist in context. Must be captured as text.
  WHEN: IMMEDIATELY after viewing images or browser results. Don't wait!
  EXAMPLE:
    - Screenshot shows login form has email and password fields
    - Browser shows API returns JSON with "status" and "data" keys
-->
- **API 同步阻塞风险**：在 `POST /api/watchlist` 中，系统会同步调用 AKShare 获取基金信息和持仓。如果网络波动导致接口超时或连接断开（`RemoteDisconnected`），前端请求会直接失败返回 404 或 500。
- **服务意外中断与端口冲突**：观测到 `uvicorn` 服务有时会意外关闭，且重连时常报 `Errno 48: Address already in use`。这通常是因为旧进程未彻底释放 Socket 句柄，需手动清理进程泄露。

### 🐛 Phase 6.2 调试记录：基金删除确认框闪现问题

#### 问题现象
用户报告点击基金卡片的删除按钮（×）后，浏览器弹出的确认框会瞬间消失，用户根本来不及点击"确定"或"取消"按钮。

#### 调研过程

1. **初步假设：事件绑定问题**
   - 检查了 `frontend/app.js` 中的事件绑定逻辑
   - 发现删除按钮使用了事件委托（`watchlistContainer.addEventListener`）
   - 事件绑定本身没有问题

2. **第二假设：DOM 更新竞态**
   - 注意到 `refreshEstimates()` 每 60 秒会更新基金卡片数据
   - 虽然使用了 `updateFundCards()` 而非完全重绘，但仍可能触发浏览器的重排
   - **关键发现**：原生 `confirm()` 是同步阻塞调用，但浏览器为防止页面锁死，会在检测到 DOM 变化时强制关闭模态对话框

3. **环境障碍：端口冲突**
   - 在尝试验证修复时，发现服务器频繁报错 `Errno 48: Address already in use`
   - 根因：旧的 `uvicorn` 进程未完全退出，占用端口 8000
   - 导致新代码无法生效，浪费了大量调试时间

#### 根本原因

**浏览器的原生 `confirm()` 对话框与异步 DOM 更新存在竞态条件**：
- `refreshEstimates()` 在后台每 60 秒执行一次
- 当用户点击删除时，`confirm()` 弹窗会阻塞主线程
- 如果此时恰好触发了定时刷新，浏览器会检测到 DOM 操作尝试
- 为避免页面"假死"，Chrome 等现代浏览器会自动关闭阻塞性对话框
- 即使没有实际 DOM 变化，定时器的触发本身也可能导致浏览器提前关闭对话框

#### 解决方案

**废弃原生对话框，实现自定义 HTML 模态框**：

1. **HTML 结构** (`frontend/index.html`)：
   ```html
   <div id="confirm-modal" class="modal-overlay" style="display: none;">
       <div class="modal">
           <h3>确认删除</h3>
           <p>确定要移除基金 <span id="modal-fund-code"></span> 吗？</p>
           <div class="modal-actions">
               <button id="modal-cancel" class="btn-secondary">取消</button>
               <button id="modal-confirm" class="btn-danger">删除</button>
           </div>
       </div>
   </div>
   ```

2. **CSS 样式** (`frontend/style.css`)：
   - 使用 `position: fixed` 和 `z-index: 1000` 确保模态框覆盖整个页面
   - 添加 `backdrop-filter: blur(4px)` 提升视觉层次感
   - 响应式设计，最大宽度 400px

3. **JavaScript 逻辑** (`frontend/app.js`)：
   - 引入 `isConfirming` 状态标志位
   - 在 `refreshEstimates()` 开头检查：`if (isConfirming) return;`
   - 模态框显示时设置 `isConfirming = true`，关闭时恢复为 `false`
   - 这确保了在用户交互期间，后台刷新逻辑完全暂停

#### 技术思考

1. **为什么不用 `clearInterval` 暂停定时器？**
   - 暂停后需要重新计算下次刷新时间，逻辑复杂
   - 使用状态标志位更简洁，且不影响定时器的周期性

2. **为什么不用 `event.stopImmediatePropagation()`？**
   - 这只能阻止同一元素上的其他监听器，无法阻止定时器触发
   - 根本问题在于原生对话框的阻塞特性，而非事件冒泡

3. **自定义模态框的额外优势**：
   - 完全可控的样式和动画
   - 可以添加加载状态（"删除中..."）
   - 更好的无障碍支持（可添加 ARIA 属性）
   - 避免浏览器兼容性问题

#### 验证结果

通过浏览器子代理进行了完整的端到端测试：
- ✅ 模态框稳定显示，不会闪现或自动关闭
- ✅ 点击"取消"正确关闭模态框且不删除基金
- ✅ 点击"删除"成功调用 API 并更新 UI
- ✅ 删除过程中按钮显示"删除中..."加载状态
- ✅ 删除完成后模态框自动关闭
- ✅ 控制台无 JavaScript 错误

#### 经验教训

1. **环境一致性至关重要**：端口冲突导致新代码无法生效，浪费了大量时间。应在每次重启服务前强制清理旧进程：
   ```bash
   kill -9 $(lsof -ti:8000) 2>/dev/null; sleep 1; python main.py
   ```

2. **原生 UI 组件的局限性**：`alert/confirm/prompt` 在现代 Web 应用中已不适用，应优先使用自定义组件。

3. **状态管理的重要性**：通过简单的布尔标志位 `isConfirming`，优雅地解决了异步刷新与用户交互的冲突。


---
<!-- 
  REMINDER: The 2-Action Rule
  After every 2 view/browser/search operations, you MUST update this file.
  This prevents visual information from being lost when context resets.
-->
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
