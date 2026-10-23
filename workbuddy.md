# WorkBuddy 开发上下文（workbuddy.md）

> 本文件用于核验本项目是否真实使用腾讯 WorkBuddy 智能体开发，符合「麦当劳程序员创意开发大赛」WorkBuddy 专项奖励条件。

## 开发环境

- **开发工具**：腾讯 WorkBuddy（大赛官方合作伙伴），运行于 Windows 环境。
- **开发方式**：以 Agent 模式驱动，由 WorkBuddy 完成调研、编码、自测、文档与提交准备的全流程。
- **参赛 Skill**：Mc. Saving（McSaving）——基于麦当劳官方 MCP 的省钱/优惠精算助手。

## 需求拆解（WorkBuddy 协助）

1. 明确活动性质：先核实这是按 GitHub Star 排名的编程比赛（非"认证领券"活动），锁定截止时间 **2026-10-25 23:59（北京时间）**。
2. 抓取官方仓库 `M-China/mcd-developer-innovation-challenge` 的活动规则与 `CONTEST_DECLARATION.md` 原文（一字不改）。
3. 抓取 `M-China/mcd-mcp-server` 的真实工具清单，确认省钱场景所需 Tool：`query-meals`、`auto-bind-coupons`、`available-coupons`、`query-my-coupons`、`query-store-coupons`、`calculate-price`、`create-order` 等。
4. 选定方向：省钱/优惠精算助手，并确定"取数交给 MCP，算术交给代码"的方法论。

## 核心实现（WorkBuddy 编码 + 自测）

- 由 WorkBuddy 编写 `optimizer/optimizer.py`：纯标准库、零依赖的确定性价格优化器，建模 5 类券（单品改价 / 折扣 / 满减 / 组合价 / 赠品）与保守叠加策略。
- 编写 `optimizer/sample_data.py`（离线样例）与 `optimizer/selftest.py`（8 项断言）。
- **自测驱动修正**：首轮自测暴露两个真实 bug——折扣券缺"满额"门槛、1+1 随心配组合价模型错误（写成"全在才算"）。WorkBuddy 据此修正券模型（新增 `min_spend`/`min_count`），并修复自测脚本漏传参数的问题，最终 **10/10 自测通过**，离线演示跑通。
- **真实 MCP 连通验证**：使用参赛者提供的真实 Token，WorkBuddy 编写 `optimizer/mcp_client.py`（纯标准库）并实测连接 `mcd-mcp`（v1.0.0，共 35 个工具），确认 `query-meals`/`calculate-price` 等需 `storeCode`，并真实拉取了卡包券与可领券（如「11.9元麦辣鸡腿堡」「19.9元王牌炸鸡任选2」「免费脆薯饼」）。`live_proof.py` 把真实券语义 1:1 喂进优化器跑出省钱方案（见 `LIVE_DEMO.md`）。
- **真实数据再揪 bug**：在真实演示中暴露并修复 `free_gift` 赠品分支（`target=None` 的随单赠未追加）的 bug，已加回归断言。
- 生成全套参赛文件：`SKILL.md`、`README.md`、`MCP_INTEGRATION.md`、`mcp-config.example.json`（仅 `${MCD_MCP_TOKEN}` 占位符）、`CONTEST_DECLARATION.md`（官方原文）、本文件。

## 合规与安全

- 仓库不含任何真实 Token / 密钥；配置文件仅使用环境变量占位符。
- 决策透明：价格计算逻辑可测试、可复现，下单前以麦当劳 MCP `calculate-price` 为权威核价。

## 结论

本项目由腾讯 WorkBuddy 真实参与构思、开发与调试，符合 WorkBuddy 专项奖励的参与条件。
