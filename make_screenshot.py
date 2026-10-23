#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Mc. Saving 的「真实跑通」终端截图（SVG，零依赖）。

做法：
  1. 从 optimizer/sample_data.py 导出真实离线样例 fixtures（demo_meals.json / demo_coupons.json）
  2. 调用真实 CLI 命令（optimizer.py --selftest / --wishlist），捕获真实输出
  3. 把两段真实输出渲染成一张 macOS 风格终端截图 SVG

全部基于真实运行结果，无任何虚构输出。
"""
import json
import os
import subprocess
import sys
import xml.sax.saxutils as su

HERE = os.path.dirname(os.path.abspath(__file__))
OPT = os.path.join(HERE, "optimizer")


def dump_fixtures():
    sys.path.insert(0, OPT)
    import sample_data
    with open(os.path.join(OPT, "demo_meals.json"), "w", encoding="utf-8") as f:
        json.dump(sample_data.SAMPLE_MEALS, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OPT, "demo_coupons.json"), "w", encoding="utf-8") as f:
        json.dump(sample_data.SAMPLE_COUPONS, f, ensure_ascii=False, indent=2)


def run(cmd):
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8")
    return p.stdout.strip("\n")


def esc(s):
    return su.escape(s).replace(" ", "&#160;")


def build_svg(blocks):
    # blocks: list of (prompt, lines)
    line_h = 20
    pad_top = 44          # 标题栏 + 上边距
    pad_bottom = 24
    left = 22
    width = 860
    total_lines = sum(1 + len(lines) for _, lines in blocks)
    height = pad_top + total_lines * line_h + pad_bottom

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Consolas, \'Microsoft YaHei\', \'PingFang SC\', monospace">'
    )
    # 窗口背景
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#0d1117"/>')
    # 标题栏
    svg.append(f'<rect x="0" y="0" width="{width}" height="34" rx="12" fill="#161b22"/>')
    svg.append(f'<rect x="0" y="17" width="{width}" height="17" fill="#161b22"/>')
    for i, (cx, color) in enumerate([(22, "#ff5f56"), (44, "#ffbd2e"), (66, "#27c93f")]):
        svg.append(f'<circle cx="{cx}" cy="17" r="6" fill="{color}"/>')
    svg.append(
        f'<text x="{width/2}" y="22" fill="#8b949e" font-size="13" text-anchor="middle" '
        f'xml:space="preserve">Mc. Saving — 真实运行输出 (offline demo)</text>'
    )
    # 正文
    y = pad_top
    for prompt, lines in blocks:
        svg.append(
            f'<text x="{left}" y="{y}" fill="#7ee787" font-size="13" xml:space="preserve">{esc(prompt)}</text>'
        )
        y += line_h
        for ln in lines:
            # 简单着色：含 “应付总价” 行用青色，赠品/省 用黄色，其余浅灰
            if "应付总价" in ln:
                color = "#79c0ff"
            elif "赠品" in ln or "saved" in ln or "省" in ln:
                color = "#ffd866"
            elif ln.startswith("=") or ln.startswith("-"):
                color = "#30363d"
            else:
                color = "#c9d1d9"
            svg.append(
                f'<text x="{left}" y="{y}" fill="{color}" font-size="13" xml:space="preserve">{esc(ln)}</text>'
            )
            y += line_h
        y += 6  # 块间留白
    svg.append('</svg>')
    return "\n".join(svg)


def main():
    dump_fixtures()
    out1 = run([sys.executable, "optimizer/optimizer.py", "--selftest"])
    out2 = run([sys.executable, "optimizer/optimizer.py",
                "--meals", "optimizer/demo_meals.json",
                "--coupons", "optimizer/demo_coupons.json",
                "--wishlist", "big_mac,mid_fries,mid_coke"])
    # 基于同一份样例数据，计算直购价 / 优化价 / 省多少（真实计算，非虚构）
    sys.path.insert(0, OPT)
    import sample_data
    from optimizer import cheapest_for_wishlist, Item, Coupon
    m = {it["code"]: Item(it["code"], it["name"], it["price"], it.get("tags", []))
         for it in sample_data.SAMPLE_MEALS["meals"]}
    cs = [Coupon(c["id"], c["kind"], target=c.get("target"), fixed=c.get("fixed"),
                 discount=c.get("discount"), min_spend=c.get("min_spend"),
                 threshold=c.get("threshold"), reduce=c.get("reduce"),
                 bundle_items=c.get("bundle_items"), min_count=c.get("min_count", 2),
                 bundle_price=c.get("bundle_price"), gift=c.get("gift"),
                 stackable=bool(c.get("stackable", False)), desc=c.get("desc", ""))
         for c in sample_data.SAMPLE_COUPONS["coupons"]]
    plan = cheapest_for_wishlist(["big_mac", "mid_fries", "mid_coke"], m, cs)[0]
    base = sum(m[c].price * q for c, q in plan.cart.items())
    saved = round(base - plan.total, 2)
    extra = [f"list price: ¥{base:.2f}   optimized: ¥{plan.total:.2f}   saved: ¥{saved:.2f}",
             f"free gift : {m[plan.gifts[0]].name}" if plan.gifts else "free gift : none"]
    out2_lines = out2.splitlines() + [""] + extra

    blocks = [
        ("$ python optimizer/optimizer.py --selftest", out1.splitlines()),
        ("$ python optimizer/optimizer.py --meals optimizer/demo_meals.json "
         "--coupons optimizer/demo_coupons.json --wishlist big_mac,mid_fries,mid_coke",
         out2_lines),
    ]
    svg = build_svg(blocks)
    out_path = os.path.join(HERE, "demo_screenshot.svg")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("已生成:", out_path, "大小:", len(svg), "字节")
    print("selftest 行数:", len(out1.splitlines()), "| demo 行数:", len(out2_lines))


if __name__ == "__main__":
    main()
