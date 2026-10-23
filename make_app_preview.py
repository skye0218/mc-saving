#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Mc. Saving H5/小程序 的真实界面预览图（SVG）。
用真实优化器算出结果后，把界面用矢量还原，便于 README 与分享展示。
"""
import os, sys
sys.path.insert(0, "optimizer")
from optimizer import cheapest_for_wishlist, Item, Coupon
import sample_data as SD

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 真实计算 ----
menu = {it["code"]: Item(it["code"], it["name"], it["price"], it.get("tags", []))
        for it in SD.SAMPLE_MEALS["meals"]}
coupons = [Coupon(c["id"], c["kind"], target=c.get("target"), fixed=c.get("fixed"),
                 discount=c.get("discount"), min_spend=c.get("min_spend"),
                 threshold=c.get("threshold"), reduce=c.get("reduce"),
                 bundle_items=c.get("bundle_items"), min_count=c.get("min_count", 2),
                 bundle_price=c.get("bundle_price"), gift=c.get("gift"),
                 stackable=bool(c.get("stackable", False)), desc=c.get("desc", ""))
          for c in SD.SAMPLE_COUPONS["coupons"]]

wish = ["big_mac", "mid_fries", "mid_coke"]
plan = cheapest_for_wishlist(wish, menu, coupons)[0]
base = sum(menu[c].price * q for c, q in plan.cart.items())
saved = round(base - plan.total, 2)
cname = {c.coupon_id: c.desc for c in coupons}

# ---- 绘制 ----
W, H = 390, 780
parts = []
parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="-apple-system,PingFang SC,Microsoft YaHei,Arial">')

# 手机外框
parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="36" fill="#fff" stroke="#e4ddcf" stroke-width="2"/>')
# 状态栏
parts.append(f'<rect x="0" y="0" width="{W}" height="34" rx="36" fill="#da291c"/>')
parts.append(f'<text x="20" y="23" fill="#fff" font-size="13" font-weight="700">9:41</text>')
parts.append(f'<text x="{W-20}" y="23" fill="#fff" font-size="12" text-anchor="end">Mc. Saving</text>')

# Header
parts.append(f'<rect x="0" y="34" width="{W}" height="96" fill="#da291c"/>')
parts.append(f'<text x="22" y="82" fill="#fff" font-size="26" font-weight="800">🍔 Mc. Saving</text>')
parts.append(f'<text x="22" y="108" fill="#ffe" font-size="12">接麦当劳官方 MCP · 算出点到最低价的组合</text>')

# Tabs
parts.append(f'<rect x="16" y="142" width="178" height="40" rx="12" fill="#ffc72c"/>')
parts.append(f'<text x="105" y="167" fill="#2b2b2b" font-size="15" font-weight="700" text-anchor="middle">点名最省</text>')
parts.append(f'<rect x="196" y="142" width="178" height="40" rx="12" fill="#fff" stroke="#eee"/>')
parts.append(f'<text x="285" y="167" fill="#8a8a8a" font-size="15" font-weight="700" text-anchor="middle">预算内最值</text>')

# 点名面板标题
parts.append(f'<text x="22" y="208" fill="#8a8a8a" font-size="12">勾选你想吃的，一键算「用哪几张券最便宜」。</text>')

# 菜单卡片（2 列）
sel = set(wish)
codes = [m["code"] for m in SD.SAMPLE_MEALS["meals"]]
card_w, card_h, gx, gy = 168, 70, 14, 220
for i, it in enumerate(SD.SAMPLE_MEALS["meals"]):
    col, row = i % 2, i // 2
    x = 16 + col * (card_w + gx)
    y = gy + row * (card_h + gx)
    is_sel = it["code"] in sel
    fill = "#fff3f1" if is_sel else "#fff"
    stroke = "#da291c" if is_sel else "#f0e4d2"
    parts.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    parts.append(f'<text x="{x+12}" y="{y+24}" fill="#2b2b2b" font-size="14" font-weight="700">{it["name"]}</text>')
    parts.append(f'<text x="{x+12}" y="{y+46}" fill="#da291c" font-size="15" font-weight="800">¥{it["price"]:.2f}</text>')
    if is_sel:
        parts.append(f'<circle cx="{x+card_w-18}" cy="{y+18}" r="10" fill="#da291c"/>')
        parts.append(f'<text x="{x+card_w-18}" y="{y+22}" fill="#fff" font-size="11" font-weight="800" text-anchor="middle">✓</text>')

# 结果卡片（基于真实计算）
ry = gy + 5 * (card_h + gx) + 6
parts.append(f'<rect x="16" y="{ry}" width="358" height="216" rx="16" fill="#fff" stroke="#f0e4d2" stroke-width="2"/>')
# 总价黄框
parts.append(f'<rect x="16" y="{ry}" width="358" height="74" rx="16" fill="#ffc72c"/>')
parts.append(f'<text x="32" y="{ry+24}" fill="#6b5300" font-size="12">最优应付</text>')
parts.append(f'<text x="32" y="{ry+58}" fill="#b51f14" font-size="30" font-weight="900">¥{plan.total:.2f}</text>')
parts.append(f'<text x="356" y="{ry+46}" fill="#b51f14" font-size="13" font-weight="700" text-anchor="end">直购 ¥{base:.2f} · 立省 ¥{saved:.2f}</text>')
# 明细行
lines_y = ry + 96
for c, q in plan.cart.items():
    parts.append(f'<text x="32" y="{lines_y}" fill="#2b2b2b" font-size="14">{menu[c].name} ×{q}</text>')
    parts.append(f'<text x="356" y="{lines_y}" fill="#2b2b2b" font-size="14" text-anchor="end">¥{menu[c].price:.2f}</text>')
    lines_y += 24
for g in plan.gifts:
    parts.append(f'<text x="32" y="{lines_y}" fill="#2e9e5b" font-size="14" font-weight="700">🎁 {menu[g].name} ×1（免费）</text>')
    lines_y += 24
used = "、".join(cname[u] for u in plan.used_coupons)
parts.append(f'<text x="32" y="{lines_y+8}" fill="#8a8a8a" font-size="12">已用券：<tspan fill="#da291c" font-weight="700">{used}</tspan></text>')

parts.append('</svg>')

out = os.path.join(HERE, "app_preview.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print("已生成:", out, "字节:", len("\n".join(parts)))
print(f"真实结果: 应付 ¥{plan.total:.2f} / 直购 ¥{base:.2f} / 省 ¥{saved:.2f}")
