#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自测：确保优化器行为正确、可复现。
直接 python selftest.py 或 python optimizer.py --selftest 运行。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from optimizer import (cheapest_for_wishlist, _price_with_coupons,
                       Item, Coupon, round2)
from sample_data import SAMPLE_MEALS, SAMPLE_COUPONS


def _menu():
    m = {}
    for it in SAMPLE_MEALS["meals"]:
        m[it["code"]] = Item(it["code"], it["name"], it["price"], it.get("tags", []))
    return m


def _coupons():
    out = []
    for c in SAMPLE_COUPONS["coupons"]:
        out.append(Coupon(c["id"], c["kind"], target=c.get("target"),
                          fixed=c.get("fixed"), discount=c.get("discount"),
                          min_spend=c.get("min_spend"),
                          threshold=c.get("threshold"), reduce=c.get("reduce"),
                          bundle_items=c.get("bundle_items"),
                          min_count=c.get("min_count", 2),
                          bundle_price=c.get("bundle_price"), gift=c.get("gift"),
                          stackable=bool(c.get("stackable", False)), desc=c.get("desc", "")))
    return out


def run():
    menu = _menu()
    coupons = _coupons()
    passed, failed = 0, 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    print("Mc. Saving 自测开始 ...")

    # 1) 单品原价正确
    cart = {"big_mac": 1}
    price, used, gifts, _, _ = _price_with_coupons(cart, menu, coupons)
    check("巨无霸原价=24.50", price == 24.50)

    # 2) 赠品逻辑：买巨无霸应得到免费脆薯饼
    price, used, gifts, _, _ = _price_with_coupons(cart, menu, coupons)
    check("买巨无霸送脆薯饼(gift)", "hash_brown" in gifts)

    # 3) 1+1 随心配：巨无霸+中薯条 直选 36.5，组合价应降到 13.9 附近
    cart = {"big_mac": 1, "mid_fries": 1}
    base = menu["big_mac"].price + menu["mid_fries"].price  # 36.5
    price, used, gifts, _, _ = _price_with_coupons(cart, menu, coupons)
    check("组合价低于直选(base=36.5)", price < base - 1)
    check("组合价使用了 bundle_11", "bundle_11" in used)

    # 4) 不可叠加券：item_coke_99 与 bundle 互斥，单独使用时中杯可乐=9.9
    cart = {"mid_coke": 1}
    price, used, gifts, _, _ = _price_with_coupons(cart, menu, coupons)
    check("中杯可乐单品券后=9.9", price == 9.90)

    # 5) wishlist 方案生成
    plans = cheapest_for_wishlist(["big_mac", "mid_fries", "mid_coke"], menu, coupons)
    check("wishlist 返回 1 个方案", len(plans) == 1)
    check("wishlist 方案含全部点名单品",
          set(plans[0].cart.keys()) == {"big_mac", "mid_fries", "mid_coke"})

    # 6) 确定性：同输入两次结果一致
    a = cheapest_for_wishlist(["big_mac", "mid_fries"], menu, coupons)[0].total
    b = cheapest_for_wishlist(["big_mac", "mid_fries"], menu, coupons)[0].total
    check("结果确定性(同输入同输出)", a == b)

    print(f"\n自测完成：{passed} 通过 / {failed} 失败")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
