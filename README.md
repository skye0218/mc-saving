# Mc. Saving（McSaving）

> 取数交给 MCP，算术交给代码，表达交给 Agent。
> 让每一单都点到麦当劳的最低价。

**Mc. Saving**是参加「麦当劳程序员创意开发大赛」的开源 Skill：基于麦当劳官方 **MCP** 能力，帮你把"怎么点最便宜"算得清清楚楚。它拉取实时菜单与四路券池，用确定性优化器算出合规最低价组合，再用 `calculate-price` 核价，最后可以一键下单。

本项目由 WorkBuddy 辅助开发。

---

## 它能做什么

- **点名模式**："我要巨无霸+薯条+可乐，怎么点最便宜？" → 在包含你点名单品的前提下，套用最优券组合。
- **预算模式**："30 块在麦当劳能吃什么？" → 在预算内筛出最值（省得最多）的搭配。
- **省钱解释**：讲清省了多少、用了哪张券、为什么这么搭。
- **闭环核价**：下单前用麦当劳 MCP 的 `calculate-price` 复核，确保"说的价 = 收银台的价"。

## 为什么不用大模型直接算

价格计算是典型的组合爆炸：菜单几十项、券十几张、每张券规则不同（单品改价 / 折扣 / 满减 / 组合价 / 赠品），还要算"为凑满减加购划不划算"。大模型做多步算术和约束推理错误率很高，而价格错一位数就是事故。所以本项目把算术彻底从模型里拿出来，做成纯标准库、零依赖、**可测试、可复现、可断言**的确定性优化器。

## 安装与使用

### 1. 获取麦当劳 MCP Token（免费）
打开 https://open.mcd.cn/mcp ，用手机号验证登录 → 右上角「控制台」→「激活」→ 复制 Token。

### 2. 接入 WorkBuddy（推荐）
左侧【专家·技能·连接器】→【连接器】→【自定义连接器】→【配置 MCP】，粘贴：
```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": { "Authorization": "Bearer 你的MCP_Token" }
    }
  }
}
```
启用 `mcd-mcp` 后即可在对话框直接说需求。

### 3. 离线运行优化器（无需 Token）
```bash
cd optimizer
python optimizer.py --selftest          # 10 项自测
python optimizer.py --meals meals.json --coupons coupons.json --wishlist "big_mac,mid_fries,mid_coke"
python optimizer.py --meals meals.json --coupons coupons.json --budget 30
```
> 真实使用时，`meals.json` 来自 MCP `query-meals`（需 `storeCode`），`coupons.json` 来自 `auto-bind-coupons` / `available-coupons` / `query-my-coupons` / `query-store-coupons` 四路合并（前三路无需 `storeCode`）。

### 4. 真实 MCP 端到端验证（已实测）
`optimizer/mcp_client.py` 是最小化的麦当劳 MCP 客户端（纯标准库，读环境变量 `MCD_MCP_TOKEN`），`optimizer/live_proof.py` 用它**真实连接 `mcd-mcp`**：

- 拉取了真实卡包券（`query-my-coupons`）与可领券（`available-coupons`）——例如实测返回「11.9元麦辣鸡腿堡」「19.9元王牌炸鸡任选2」「免费脆薯饼」；
- 把真实券语义（单品改价 / 组合价 / 赠品）1:1 映射进优化器，跑出真实省钱方案；
- 过程中还发现并修复了一处 `free_gift` 赠品分支的 bug（已在 `optimizer.py` 修正，自测回归覆盖）。

完整输出见 **[`LIVE_DEMO.md`](./LIVE_DEMO.md)**（为该次真实调用的快照，券含"今日到期"等时效信息，仅供参考）。

## 目标用户

- 想"吃得饱又吃得省"的普通消费者
- 选择困难、不想研究菜单比价的人
- 减脂/控卡期需要按营养约束点餐的人

## 项目结构

```
mc-saving/
├── SKILL.md                    # WorkBuddy Skill 定义
├── README.md                   # 本文件
├── CONTEST_DECLARATION.md      # 参赛声明（官方原文，不可改）
├── MCP_INTEGRATION.md          # MCP 接入与工具说明（含实测响应格式）
├── mcp-config.example.json     # 脱敏 MCP 配置（仅占位符）
├── workbuddy.md                # WorkBuddy 专项奖励所需开发上下文
├── LIVE_DEMO.md                # 真实 MCP 取数演示快照（实测证据）
└── optimizer/
    ├── optimizer.py            # 确定性价格优化器（核心）
    ├── sample_data.py          # 离线样例菜单与券
    ├── selftest.py             # 10 项自测
    ├── mcp_client.py           # 最小化麦当劳 MCP 客户端（纯标准库）
    └── live_proof.py           # 真实取数 → 优化器 端到端演示
```

## 声明

本项目为大赛参赛作品，由参赛者独立开发，**非麦当劳官方产品**。餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准。详见 `CONTEST_DECLARATION.md`。
