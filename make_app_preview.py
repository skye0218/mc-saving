#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Mc. Saving H5/小程序 的真实界面预览图（SVG）。
用真实优化器算出结果后，把完整界面用矢量还原，便于 README 与分享展示。
覆盖：状态栏 / Header / 模式 Tab / 分类 sheet / 菜单卡片 / CTA / 可用优惠券 / 最优方案 + 计算说明。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "optimizer"))
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

# ---- 分类（与 H5 一致：取 tags[0]） ----
cats_order = []
for it in SD.SAMPLE_MEALS["meals"]:
    c = (it.get("tags") or ["其他"])[0]
    if c not in cats_order:
        cats_order.append(c)
N_MEALS = len(SD.SAMPLE_MEALS["meals"])

# 预览里展示的 6 张卡片（跨品类，含 3 个已选）
show_codes = ["big_mac", "mid_fries", "mid_coke", "cone", "hash_brown", "mc_chicken"]
sel = set(wish)

def short_for(uid):
    m = {"bundle_11": "1+1随心配", "pct_85": "麦麦省85折", "full35_7": "满35减7",
         "item_coke_99": "可乐¥9.9", "gift_bigmac": "送脆薯饼"}
    return m.get(uid, cname.get(uid, uid))

# ---- 绘制 ----
W = 390
H = 1620
parts = []

def rect(x, y, w, h, fill="#fff", stroke=None, sw=1, rx=14):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    parts.append(s + "/>")

def text(x, y, s, size=14, fill="#2b2b2b", weight="400", anchor="start"):
    # 转义 XML 特殊字符
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    parts.append(f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
                 f'font-weight="{weight}" text-anchor="{anchor}">{s}</text>')

parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="-apple-system,PingFang SC,Microsoft YaHei,Arial">')

# 手机外框
rect(0, 0, W, H, fill="#fff", stroke="#e4ddcf", sw=2, rx=36)
# 状态栏
rect(0, 0, W, 34, fill="#da291c", rx=36)
text(20, 23, "9:41", size=13, fill="#fff", weight="700")
text(W - 20, 23, "Mc. Saving", size=12, fill="#fff", anchor="end")
# Header
rect(0, 34, W, 96, fill="#da291c")
text(22, 82, "🍔 Mc. Saving", size=26, fill="#fff", weight="800")
text(22, 108, "接麦当劳官方 MCP · 算出点到最低价的组合", size=12, fill="#ffe")
# Tabs
rect(16, 142, 178, 40, fill="#ffc72c", rx=12)
text(105, 167, "点名最省", size=15, fill="#2b2b2b", weight="700", anchor="middle")
rect(196, 142, 178, 40, fill="#fff", stroke="#eee", rx=12)
text(285, 167, "预算内最值", size=15, fill="#8a8a8a", weight="700", anchor="middle")
# Hint
text(22, 206, "勾选你想吃的，一键算「用哪几张券最便宜」。", size=12, fill="#8a8a8a")
# 全选/清空
rect(16, 220, 80, 30, fill="#fff", stroke="#f0e4d2", sw=1, rx=20)
text(56, 240, "全选", size=13, fill="#da291c", weight="700", anchor="middle")
rect(104, 220, 80, 30, fill="#fff", stroke="#f0e4d2", sw=1, rx=20)
text(144, 240, "清空", size=13, fill="#da291c", weight="700", anchor="middle")

# 分类 sheet 标签条（全部 + 各品类）
chips = ["全部"] + cats_order
cx = 16
cy = 262
for i, c in enumerate(chips):
    cw = len(c) * 13 + 18
    active = (i == 0)
    rect(cx, cy, cw, 28, fill="#da291c" if active else "#fff",
         stroke=None if active else "#f0e4d2", sw=1, rx=18)
    text(cx + cw / 2, cy + 19, c, size=12,
         fill="#fff" if active else "#8a8a8a", weight="700", anchor="middle")
    cx += cw + 6

# 菜单卡片（6 张，跨品类）
card_w, card_h, gx, gy = 168, 70, 14, 304
pos = [(16, 304), (198, 304), (16, 388), (198, 388), (16, 472), (198, 472)]
name_map = {it["code"]: it for it in SD.SAMPLE_MEALS["meals"]}
for code, (x, y) in zip(show_codes, pos):
    it = name_map[code]
    is_sel = code in sel
    rect(x, y, card_w, card_h, fill="#fff3f1" if is_sel else "#fff",
         stroke="#da291c" if is_sel else "#f0e4d2", sw=2)
    text(x + 12, y + 24, it["name"], size=14, fill="#2b2b2b", weight="700")
    text(x + 12, y + 46, f"¥{it['price']:.2f}", size=15, fill="#da291c", weight="800")
    # 品类小标
    tag = (it.get("tags") or [""])[0]
    text(x + 12, y + 64, tag, size=10, fill="#8a8a8a")
    if is_sel:
        rect(x + card_w - 28, y + 8, 20, 20, fill="#da291c", rx=10)
        text(x + card_w - 18, y + 22, "✓", size=11, fill="#fff", weight="800", anchor="middle")
text(16, 568, f"… 等共 {N_MEALS} 款，点上方分类可切换 sheet（单页内筛选，不跳转）", size=11, fill="#8a8a8a")

# CTA
rect(16, 582, 358, 46, fill="#da291c", rx=14)
text(195, 611, "算最省组合", size=16, fill="#fff", weight="800", anchor="middle")

# 可用优惠券
text(16, 654, "🎟️ 可用优惠券（内置真实样例）", size=15, fill="#2b2b2b", weight="800")
cy2 = 666
for c in coupons:
    rect(16, cy2, 358, 40, fill="#fff8f6", stroke="#da291c", sw=1, rx=12)
    badge = {"item_price": "单品价", "percent": "折扣", "threshold": "满减",
             "bundle_price": "组合价", "free_gift": "赠品"}.get(c.kind, c.kind)
    rect(26, cy2 + 11, 52, 18, fill="#da291c", rx=6)
    text(52, cy2 + 24, badge, size=11, fill="#fff", weight="800", anchor="middle")
    text(88, cy2 + 25, c.desc, size=12.5, fill="#2b2b2b")
    stk = "可叠加" if c.stackable else "不可叠加"
    text(362, cy2 + 25, stk, size=11, fill="#2e9e5b" if c.stackable else "#b06",
         anchor="end")
    cy2 += 48

# 最优方案卡片
ry = 910
rect(16, ry, 358, 358, fill="#fff", stroke="#f0e4d2", sw=2)
# 总价黄框
rect(16, ry, 358, 74, fill="#ffc72c", rx=16)
text(32, ry + 24, "最优应付", size=12, fill="#6b5300")
text(32, ry + 58, f"¥{plan.total:.2f}", size=30, fill="#b51f14", weight="900")
text(356, ry + 46, f"直购 ¥{base:.2f} · 立省 ¥{saved:.2f}", size=13,
     fill="#b51f14", weight="700", anchor="end")
# 明细行
ly = ry + 100
for c, q in plan.cart.items():
    text(32, ly, f"{menu[c].name} ×{q}", size=14, fill="#2b2b2b")
    text(356, ly, f"¥{menu[c].price:.2f}", size=14, fill="#2b2b2b", anchor="end")
    ly += 24
for g in plan.gifts:
    text(32, ly, f"🎁 {menu[g].name} ×1（免费）", size=14, fill="#2e9e5b", weight="700")
    ly += 24
used = "、".join(short_for(u) for u in plan.used_coupons)
text(32, ly + 6, f"已用券：{used}", size=12, fill="#8a8a8a")
ly += 32

# 计算说明
text(32, ly, "🧮 计算说明（一步步怎么算的）", size=14, fill="#b51f14", weight="800")
ly += 26
for s in plan.steps:
    if s.get("gift"):
        text(32, ly, f"🎁 {s['label']}（免费，不计入应付）", size=12.5, fill="#2e9e5b", weight="700")
    else:
        text(32, ly, f"{s['label']}：¥{s['before']:.2f}→¥{s['after']:.2f}　省¥{s['saved']:.2f}",
             size=12.5, fill="#2b2b2b")
    ly += 24
text(32, ly, f"算法枚举 {plan.tried} 种券组合，按『单品改价→组合价→折扣→满减』结算；",
     size=11.5, fill="#8a8a8a")
text(32, ly + 18, "取应付最低且赠品最多的方案。", size=11.5, fill="#8a8a8a")

# 下单卡片
oy = ly + 50
text(16, oy, "🛒 带着最优方案去下单", size=15, fill="#2b2b2b", weight="800")
oy += 28
for c, q in plan.cart.items():
    text(32, oy + 18, f"{menu[c].name} ×{q}", size=13.5, fill="#2b2b2b")
    text(356, oy + 18, f"¥{menu[c].price:.2f}", size=13.5, fill="#2b2b2b", anchor="end")
    oy += 26
for g in plan.gifts:
    text(32, oy + 18, f"🎁 {menu[g].name} ×1（免费）", size=13.5, fill="#2e9e5b", weight="700")
    oy += 26
text(32, oy + 18, f"应付 ¥{plan.total:.2f} · 省 ¥{saved:.2f} · 已用券：{used}", size=12, fill="#8a8a8a")
oy += 34
rect(16, oy, 358, 46, fill="#da291c", rx=14)
text(195, oy + 29, "去麦当劳官方小程序下单确认", size=15, fill="#fff", weight="800", anchor="middle")
oy += 64
text(16, oy, "跳转后按此清单点单，并使用上方算好的券。", size=11, fill="#8a8a8a")

parts.append("</svg>")

out = os.path.join(HERE, "app_preview.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))
print("已生成:", out, "尺寸:", W, "x", H, "字节:", len("\n".join(parts)))
print(f"真实结果: 应付 ¥{plan.total:.2f} / 直购 ¥{base:.2f} / 省 ¥{saved:.2f} / 枚举 {plan.tried} 种")
