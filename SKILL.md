---
name: Mc. Saving
description: 基于麦当劳 MCP 的"省钱/优惠精算助手"。当用户想在麦当劳点到最便宜的组合、问"XX 怎么点最划算""XX 预算能吃什么""帮我算最低价"时使用。它调用麦当劳 MCP 拉取实时菜单与四路券池，再用确定性优化器算出合规最低价，最后用 calculate-price 核价。绝不靠大模型口算价格。
---

# Mc. Saving（McSaving）

一个把"麦当劳怎么点最便宜"讲清楚的工具。核心信念：**取数交给 MCP，算术交给代码，表达交给 Agent。**

价格计算是组合爆炸问题（几十个单品 × 十几张券 × 不同叠加规则），大模型口算必错。本 Skill 把算术交给 `optimizer/optimizer.py`（纯标准库、零依赖、可离线自测），只让 Agent 负责理解需求、取数、讲解与下单。

## 使用前提

- 已在 WorkBuddy【连接器】中接入麦当劳 MCP（`mcd-mcp`），并配置 `Authorization: Bearer ${MCD_MCP_TOKEN}`。
- MCP Token 在 https://open.mcd.cn/mcp 用手机号登录后"控制台→激活"获取（免费）。
- 每个 Token 限 600 次/分钟，注意控制调用频率，避免 429。

## ⚠️ MCP 工具响应格式（必读，否则会解析失败）

麦当劳 MCP 的工具返回**不是统一 JSON**，而是面向 LLM 的混合格式：

- 有的工具返回**纯 JSON**（如 `now-time-info`、`query-nearby-stores` 出错时、`query-meals` 出错时）；
- 有的工具返回**Markdown 文本**（如 `available-coupons` 直接列出「优惠券标题 / 状态」，`query-my-coupons` 按 `## 标题 / - **优惠**: ¥X` 罗列）；
- 成功的结构化数据常包在「字段说明 + `## Original Response` 里的真 JSON」里。

**因此 Agent 不要直接 `json.loads` 整个响应**，而要先读文本、抽取结构化字段，再喂给优化器。参考实现见 `optimizer/mcp_client.py`（`_extract_json` 已处理三种情况）。

## ⚠️ storeCode 必填

`query-meals`、`query-meal-detail`、`query-store-coupons`、`calculate-price`、`create-order` **都必须带 `storeCode`（门店编码，纯数字）+ `beType`（1-到店取餐 / 2-麦乐送到家 / 5-得来速 / 6-企业团餐）**；到店/得来速还需 `beCode`（与 storeCode 配对，从 `query-nearby-stores` 返回里取）。`storeCode` 来自：

- APP 内用户已选的门店（WorkBuddy 在 APP WebView 中运行时有上下文）；
- 或调用 `query-nearby-stores`（`beType` + `searchType`/`city`+`keyword`）拿门店列表取 `storeCode`。

而 `available-coupons`、`query-my-coupons`、`auto-bind-coupons`、`now-time-info`、`list-nutrition-foods`、`campaign-calendar` **不需要 storeCode**，可立即调用——这正是优化器券池的主要来源。

## 工作流程

1. **定位门店并拿到 `storeCode`**：在 APP 上下文直接用用户当前门店；否则 `query-nearby-stores` 取门店列表拿 `storeCode` + `beCode`。
2. **拉菜单**：带 `storeCode`/`beType` 调用 `query-meals` 获取当前门店可售餐品（分类、code、价格、标签），抽取为 `meals.json`。
3. **集齐四路券**（少一路就少省钱）：
   - `auto-bind-coupons`：一键领取麦麦省所有可领券；
   - `available-coupons`：麦麦省可领券列表；
   - `query-my-coupons`：账户已有券；
   - `query-store-coupons`：当前门店专属券。
   合并去重后存为 `coupons.json`。
4. **识别意图**：
   - 点名单品（"我要巨无霸+薯条+可乐"）→ wishlist 模式；
   - 预算约束（"30 块能吃什么""减脂期 800 大卡以内"）→ budget 模式（可用 `list-nutrition-foods` 拉营养数据做热量约束）。
5. **算价（关键！不要自己算）**：把 `meals.json` + `coupons.json` 交给 `optimizer/optimizer.py`：
   ```
   python optimizer/optimizer.py --meals meals.json --coupons coupons.json --wishlist "big_mac,mid_fries,mid_coke"
   python optimizer/optimizer.py --meals meals.json --coupons coupons.json --budget 30
   ```
   优化器会输出券后最低价方案。
6. **核价（闭环）**：用 `calculate-price` 对选定方案做最终核价，确保"Agent 说的价 = 收银台的价"。若不一致，以 `calculate-price` 为准并重新解释。
7. **讲解与下单**：把方案讲成人话（省了多少、用了哪张券、为什么这么搭）；用户确认后可用 `create-order` 下单。

## 约束与红线

- **绝不**用大模型直接做多步价格算术或叠加判断——一律交给 `optimizer.py`。
- 叠加策略保守：标 `stackable:false` 的券与任何其他券互斥；宁可少报优惠，也不给"到店付不出来"的假低价。
- 真实下单前必须 `calculate-price` 核价。
- 不要提交真实 Token；配置只用 `${MCD_MCP_TOKEN}` 占位符。
- 餐品/价格/供应以麦当劳官方实时结果为准。

## 离线验证

没有 Token 也能跑通与复现：
```
cd optimizer && python optimizer.py --selftest
```
内置样例菜单与券，含 10 项断言，验证组合价、满减、折扣、赠品、预算模式与确定性。
