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
-

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
<!-- CRITICAL: Update after every 2 view/browser operations -->
<!-- Multimodal content must be captured as text immediately -->
-

---
<!-- 
  REMINDER: The 2-Action Rule
  After every 2 view/browser/search operations, you MUST update this file.
  This prevents visual information from being lost when context resets.
-->
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
