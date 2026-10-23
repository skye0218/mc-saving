#!/usr/bin/env python3
"""
最小化的麦当劳 MCP 客户端（Streamable-HTTP / JSON-RPC）。
仅依赖 Python 标准库，用于：
  1) 在本地/CI 用真实 MCP 验证 Skill 可用（取数闭环）
  2) 作为 Skill 的"取数参考实现"（WorkBuddy 内由平台 MCP 客户端托管，这里仅用于离线/自测）

安全约定：
  - Token 只从环境变量 MCD_MCP_TOKEN 读取，绝不写死、绝不提交。
  - 真实 Token 放 .mcd_token.local（已在 .gitignore 排除），运行时 export 即可。
"""
import json
import os
import re
import urllib.request

MCP_URL = os.environ.get("MCD_MCP_URL", "https://mcp.mcd.cn")
TOKEN = os.environ.get("MCD_MCP_TOKEN", "")


def _post(payload: dict) -> dict:
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {TOKEN}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    # 服务端返回纯 JSON（偶尔可能是 SSE 文本），统一兜底解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # SSE: 取最后一个 data: 行
        for line in reversed(raw.splitlines()):
            line = line.strip()
            if line.startswith("data:"):
                return json.loads(line[len("data:"):].strip())
        raise


def initialize() -> dict:
    return _post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "mc-saving", "version": "0.1.0"},
        },
    })


def _extract_json(text: str) -> dict:
    """麦当劳 MCP 的 tools/call 返回是『字段说明 + ## Original Response 里的真 JSON』，
    需要把最后的真 JSON 抠出来；同时兼容纯 JSON / ```json 块。"""
    # 1) 整段直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) ## Original Response 之后的 JSON
    m = re.search(r"##\s*Original Response\s*\n+(.*)", text, re.S)
    if m:
        chunk = m.group(1)
        s = chunk.find("{"); e = chunk.rfind("}")
        if s >= 0 and e > s:
            try:
                return json.loads(chunk[s:e + 1])
            except Exception:
                pass
    # 3) 任意 ```json 块
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 4) 兜底：文本末尾的裸 JSON（说明文字 + 直接追加的 {...}）
    s = text.rfind("{"); e = text.rfind("}")
    if s >= 0 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:
            pass
    return {"raw": text}


def call_tool(name: str, arguments: dict) -> dict:
    """调用 MCP 工具，返回解析后的业务对象（data / success 字段）。"""
    resp = _post({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    if "error" in resp:
        raise RuntimeError(f"MCP error calling {name}: {resp['error']}")
    content = resp.get("result", {}).get("content", [])
    for c in content:
        if c.get("type") == "text":
            return _extract_json(c["text"])
    return {}


if __name__ == "__main__":
    if not TOKEN:
        print("MCD_MCP_TOKEN 未设置，退出。")
        raise SystemExit(1)
    init = initialize()
    print("initialize:", init.get("result", {}).get("serverInfo"))
    # 示例：拉取在售餐品（到店自提）
    meals = call_tool("query-meals", {"orderType": 1})
    print("query-meals 返回键:", list(meals.keys()) if isinstance(meals, dict) else type(meals))
