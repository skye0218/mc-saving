# MCP 接入说明（MCP_INTEGRATION.md）

## 使用的麦当劳 MCP Server

- **服务地址**：`https://mcp.mcd.cn`
- **传输协议**：Streamable HTTP
- **鉴权方式**：请求头 `Authorization: Bearer ${MCD_MCP_TOKEN}`（Token 在 https://open.mcd.cn/mcp 获取）
- **开放平台**：https://open.mcd.cn/mcp
- **官方指南仓库**：https://github.com/M-China/mcd-mcp-server

脱敏配置示例见 `mcp-config.example.json`（仅使用 `${MCD_MCP_TOKEN}` 环境变量占位符，不含任何真实凭证）。

## 响应格式（实测结论，重要）

麦当劳 MCP Server（`mcd-mcp` v1.0.0，共 **35 个工具**）的 `tools/call` 返回是**面向 LLM 的混合格式**，不是统一 JSON：

- **纯 JSON**：如 `now-time-info`、`query-nearby-stores`（出错时）、`query-meals`（参数缺失时）会返回 `{"success":false,"code":...,"message":...}`；
- **Markdown 列表**：如 `available-coupons` 直接输出「- 优惠券标题：XXX \ 状态：已领取/可领取」；`query-my-coupons` 按 `## 标题 / - **优惠**: ¥X (用券价格) / - **标签**: ...` 罗列；
- **说明 + 真 JSON**：成功的结构化数据常包在「字段说明」之后、`## Original Response` 之下的 JSON 块里（如 `query-meals` 成功时）。

因此调用方**不能**直接 `json.loads` 整个响应，而要读文本、按工具分别抽取结构化字段。`optimizer/mcp_client.py` 的 `_extract_json` 已处理上述三种情况，可作为参考实现。

## 实际调用的工具（Tool）

> 必填参数实测结论：`query-meals`/`query-meal-detail`/`query-store-coupons`/`calculate-price`/`create-order` 必须带 `storeCode` + `beType`（`query-meal-detail` 还需 `code`；到店/得来速需 `beCode`）。`available-coupons`/`query-my-coupons`/`auto-bind-coupons`/`now-time-info`/`list-nutrition-foods`/`campaign-calendar` 不需要 `storeCode`。

| 工具 | 用途 | 必填参数 | 在流程中的角色 |
|------|------|----------|----------------|
| `query-nearby-stores` | 查询附近可用门店 | `beType`,`searchType`(+ `city`/`keyword`) | 定位门店、取 `storeCode`/`beCode` |
| `query-meals` | 查询当前门店可售餐品（分类、code、价格、标签） | `storeCode`,`orderType`,`beType` | **价格主数据源** |
| `query-meal-detail` | 查询套餐组成与可替换项 | `storeCode`,`orderType`,`beType`,`code` | 查看套餐内容 |
| `auto-bind-coupons` | 一键领取麦麦省所有可领券 | 无 | 集券（第 1 路） |
| `available-coupons` | 麦麦省可领券列表 | 无 | 集券（第 2 路） |
| `query-my-coupons` | 账户已有券 | 无 | 集券（第 3 路） |
| `query-store-coupons` | 当前门店专属券 | `orderType`,`beType`,`storeCode`(+`beCode`) | 集券（第 4 路） |
| `calculate-price` | 按选购商品+券计算应付总价 | `storeCode`,`orderType`,`beType`,`items` | **下单前核价（权威）** |
| `create-order` | 创建订单并返回支付链接 | `storeCode`,`orderType`,`beType`,`items` | 确认后下单 |
| `now-time-info` | 获取当前时间 | 无 | 辅助判断时段/活动（如"今日到期"券） |
| `list-nutrition-foods` | 餐品营养数据（能量/蛋白/脂肪/碳水/钠等） | 无 | 预算模式下的热量约束 |

> 集券必须走**四路合并**（麦麦省可领 + 账户已有 + 门店专属 + 一键领取后新增），少查一路就会少省钱。其中前三路无需 `storeCode`，可最先调用；门店专属券需先确定 `storeCode`。

## 调用流程

```
用户需求
   │
   ├─ query-nearby-stores        → 确定门店
   ├─ query-meals                → meals.json（价格主数据）
   ├─ auto-bind-coupons          ┐
   ├─ available-coupons          ├─ 合并去重 → coupons.json
   ├─ query-my-coupons           ┤
   └─ query-store-coupons        ┘
   │
   ├─ optimizer.py（本地确定性计算）  → 券后最低价方案 Top-N
   │       （取数交给 MCP，算术交给代码）
   │
   ├─ calculate-price            → 最终核价（以官方返回为准）
   │
   └─ create-order（用户确认后） → 支付链接
```

## 业务价值

1. **可验证的"最低价"**：价格算术从大模型移到确定性代码，同一输入永远同一输出，带 10 项自测，可离线复现与审查。
2. **不漏券**：四路券池合并，避免人为漏看优惠。
3. **防虚报**：叠加策略保守（不可叠加券互斥、折扣先于满减），且下单前用 `calculate-price` 二次核价，绝不输出"到店付不出来"的假低价。
4. **可扩展**：预算模式已支持热量约束（结合 `list-nutrition-foods`），可继续扩展外送场景、团餐、麦麦商城积分兑换等。
