#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 mc-saving 仓库内容同步到 GitHub（通过 Contents API，绕开被代理拦截的 git 智能 HTTP）。
- 新文件：POST 创建
- 已存在文件：GET 取 sha 后 PUT 更新
- 自动排除 .git / 本地 token 文件 / 临时文件
用法：MCD_GH_PAT=xxx python3 sync_github.py
"""
import os, sys, json, base64, urllib.request, urllib.error

REPO = "skye0218/mc-saving"
ROOT = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {".git", ".mcd_token.local", ".gh_pat.local", ".gitignore.orig"}

def _read_local_token():
    p = os.path.join(ROOT, ".gh_pat.local")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

TOKEN = os.environ.get("MCD_GH_PAT", "") or _read_local_token()

def api(method, path, body=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}

def main():
    if not TOKEN:
        print("缺少 MCD_GH_PAT 环境变量（GitHub PAT，需 repo 权限）"); sys.exit(1)
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if ".git" in dirnames: dirnames.remove(".git")
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel in EXCLUDE or rel.startswith(".git"): continue
            files.append(rel)
    files.sort()
    ok = 0
    for rel in files:
        full = os.path.join(ROOT, rel)
        with open(full, "rb") as f:
            content = base64.b64encode(f.read()).decode("ascii")
        status, resp = api("GET", rel)
        sha = resp.get("sha") if status == 200 else None
        msg = ("chore: 更新 " if sha else "add: ") + rel
        if sha:
            st, r = api("PUT", rel, {"message": msg, "content": content, "sha": sha, "branch": "main"})
        else:
            st, r = api("PUT", rel, {"message": msg, "content": content, "branch": "main"})
            # 某些情况下未初始化的路径用 PUT 也可创建；若失败再用 POST
            if st not in (200, 201):
                st, r = api("POST", rel, {"message": msg, "content": content, "branch": "main"})
        if st in (200, 201):
            ok += 1
            print(f"  [{'更新' if sha else '新建'}] {rel}")
        else:
            print(f"  [失败 {st}] {rel} -> {r.get('message')}")
    print(f"\n同步完成：成功 {ok}/{len(files)} 个文件。")
    print(f"仓库地址：https://github.com/{REPO}")

if __name__ == "__main__":
    main()
