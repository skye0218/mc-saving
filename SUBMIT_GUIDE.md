# 提交指南（SUBMIT_GUIDE.md）

本文件不计入参赛必交文件，仅供你按官方要求完成报名与提交。

## 时间红线（北京时间）
- **报名 + 排名截止：2026-10-25 23:59**（今天 10-23，只剩约 2.5 天！）
- 定榜：2026-10-26 00:00
- 兑奖 / 收货信息提交：**2026-11-14**

> ✅ **已用真实 MCP Token 实测通过**：`optimizer/mcp_client.py` + `live_proof.py` 已真实连接 `mcd-mcp`（35 个工具），拉到真实券（如「11.9元麦辣鸡腿堡」「19.9元王牌炸鸡任选2」「免费脆薯饼」）并跑通优化器，详见 `LIVE_DEMO.md`。优化器自测 10/10。可放心提交。

## 第 1 步：拿麦当劳 MCP Token（免费，约 2 分钟）
1. 打开 https://open.mcd.cn/mcp
2. 右上角「登录」→ 手机号验证登录
3. 登录后右上角变「控制台」→ 点开 →「激活」→ 同意协议 → 一键复制 Token
4. 在 WorkBuddy【连接器】→【自定义连接器】→【配置 MCP】粘贴（Token 替换为你的真实 Token，仅本地用，切勿提交进仓库）

> ⚠️ 你之前发的 `m.mcd.cn/githubRelate` 是"开发者认证领券"活动，和本比赛无关；本比赛用的 Token 在 `open.mcd.cn/mcp`。

## 第 2 步：建公开 GitHub 仓库
- 仓库名建议：`mc-saving`（或你喜欢的名字）
- **必须是 Public（公开）仓库**
- 仓库创建时间须在 **2025-12-25 ～ 2026-10-25** 之间（现在建完全符合）

## 第 3 步：把本项目推上去
把本目录（`mc-saving/`）下的全部文件推到你的公开仓库根目录：
- `SKILL.md` / `README.md` / `CONTEST_DECLARATION.md` / `MCP_INTEGRATION.md` / `mcp-config.example.json` / `workbuddy.md`
- `optimizer/` 整个目录
> 确保 `CONTEST_DECLARATION.md` 内容一字未改；`mcp-config.example.json` 只有 `${MCD_MCP_TOKEN}` 占位符，没有任何真实 Token；本地 `.mcd_token.local` 已被 `.gitignore` 排除，不会进仓库。

**可直接复制的 Git 命令**（在 `mc-saving/` 目录内执行，把 `你的用户名` 换成你的 GitHub 用户名）：
```bash
git init
git add .
git commit -m "Mc. Saving: 基于麦当劳 MCP 的省钱精算助手"
git branch -M main
git remote add origin https://github.com/你的用户名/mc-saving.git
git push -u origin main
```
> 注意：本机尚未安装 `gh`，上命令用标准 Git。若你希望我代为推送，请提供「有 repo 权限的 GitHub PAT」（用完即删，绝不进仓库），或在本机 `gh auth login` 后告知我。

## 第 4 步：在活动仓库发 Issue 报名
到官方活动仓库的 Issues 标签页提交：
https://github.com/M-China/mcd-developer-innovation-challenge/issues

**Issue 标题**（自定义，例）：
```
Mc. Saving - 基于麦当劳 MCP 的省钱精算助手
```

**Issue 正文**（严格照抄，先别加空行；字段名与值同行；URL 用纯文本不用 Markdown 链接）：
```
【参赛申请】
项目名称：Mc. Saving
项目地址：https://github.com/你的用户名/mc-saving
项目简介：基于麦当劳官方 MCP 的省钱/优惠精算助手：拉取实时菜单与四路券池，用确定性优化器算出合规最低价组合，下单前再用 calculate-price 核价。取数交给 MCP，算术交给代码。
```

> 🚫 官方校验三大坑（已踩过很多人）：
> 1. Issue 标题与正文之间**不要加空行**（正文直接以【参赛申请】开头）；
> 2. 【项目名称】/【项目地址】/【项目简介】与后面的内容**不要换行**（同一行）；
> 3. 项目地址**不要用 Markdown 链接**（`[文字](url)` 会被判失败），用纯文本 URL。

提交后系统会在 Issue 下回复成功 / 失败原因；失败按提示改完重提即可。

## 第 5 步：冲榜与领奖
- 报名成功后，麦当劳定时抓取公开 Star 数；**Star>0 且进前 100** 即获奖（汉堡回车键玩具 + 程序员节实体徽章）。
- 用了 WorkBuddy 且交了 `workbuddy.md` 并进前 100 → 再得 3000 积分。
- 获奖后麦当劳会用 GitHub 注册邮箱 / Issue 留言联系你，于 **2026-11-14 前**填问卷提交收货信息（中国大陆地址）或手机号。

## 自查清单
- [ ] 已拿 open.mcd.cn/mcp 的 Token 并接好 WorkBuddy 连接器
- [ ] 公开仓库已建（Public）
- [ ] 6 个必交文件 + optimizer/ 已推送
- [ ] CONTEST_DECLARATION.md 未改内容
- [ ] mcp-config.example.json 无真实 Token
- [ ] Issue 按上述严格格式提交（无空行 / 同行的字段 / 纯文本 URL）
- [ ] 截止前（10-25 23:59）完成，并适当拉 Star
