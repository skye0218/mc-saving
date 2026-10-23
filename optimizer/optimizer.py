#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mc. Saving —— 确定性价格优化器
================================

设计原则（也是本项目的核心方法论）：
    取数交给 MCP，算术交给代码，表达交给 Agent。

麦当劳点餐的"算最便宜"是典型的组合爆炸问题：
    - 菜单几十项，用户手里的券 + 能领的券动辄十几张；
    - 每张券规则不同：单品改价 / 折扣 / 满减 / 组合价 / 赠品；
    - 还要考虑"为了让满减生效而加购到底划不划算"。

人类懒得算，大模型也真的算不准（多步算术 + 约束推理错误率高），
而价格错一位数就是事故。所以本项目把算术彻底从模型里拿出来，
做成一个纯标准库、零依赖的确定性优化器：
    - 同一份输入，永远得到同一个输出 —— 可测试、可复现、可断言；
    - 下单前再调用麦当劳 MCP 的 calculate-price 做最终核价，形成闭环：
      Agent 说的价 = 收银台的价。

本文件不依赖任何第三方库，也不依赖真实 MCP Token，可离线运行与自测。

优惠券类型建模（覆盖麦当劳所有优惠玩法）：
    item_price  : 单品改价（如 9.9 元专区），target 为单品 code，fixed 为改后单价
    percent     : 折扣（如 8 折），discount 为折扣比例（0~1），可设 min_spend 满额门槛
    threshold   : 满减（如 满 35 减 7），threshold 为门槛、reduce 为减免额
    bundle_price: 组合价（如 1+1 随心配），从 bundle_items 池中任选 min_count 件按 bundle_price 计价
    free_gift   : 赠品（如 买 A 送 B），base 为需购买单品、gift 为赠送单品

叠加策略（保守但安全）：
    stackable=False 的券与任何其他券互斥，只能单独使用；
    stackable=True  的券之间可叠加。
    percent 在 threshold 之前计算（满减基于折后金额），整体偏向"少报优惠"，
    宁可少报，也绝不给用户一个"到店付不出来"的假低价；
    最终以麦当劳 MCP calculate-price 的返回为权威。
"""

from __future__ import annotations

import json
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def round2(x: float) -> float:
    """避免浮点误差导致 47.00 变成 46.9999999。"""
    return round(x + 1e-9, 2)


@dataclass
class Item:
    code: str
    name: str
    price: float
    tags: List[str] = field(default_factory=list)


@dataclass
class Coupon:
    coupon_id: str
    kind: str  # item_price | percent | threshold | bundle_price | free_gift
    target: Optional[str] = None       # item_price / free_gift 的目标单品 code
    fixed: Optional[float] = None      # item_price: 改后单价
    discount: Optional[float] = None   # percent: 折扣比例 0~1
    min_spend: Optional[float] = None  # percent: 满额门槛（可选）
    threshold: Optional[float] = None  # threshold: 满减门槛
    reduce: Optional[float] = None     # threshold: 减免额
    bundle_items: Optional[List[str]] = None  # bundle_price: 可选单品池
    min_count: int = 2                 # bundle_price: 需从池中选取的件数
    bundle_price: Optional[float] = None      # bundle_price: 组合价
    gift: Optional[str] = None         # free_gift: 赠送单品 code
    stackable: bool = False
    desc: str = ""


@dataclass
class Plan:
    cart: Dict[str, int]        # code -> 数量
    total: float                # 应付总价（含券后）
    used_coupons: List[str]     # 使用的优惠券 id
    gifts: List[str] = field(default_factory=list)  # 赠送单品 code
    steps: List[dict] = field(default_factory=list)  # 逐步结算明细（解释"怎么算出来的"）
    tried: int = 0                                   # 枚举过的券组合数
    saved: float = 0.0                                # 省下的金额（原价 - 应付）
    note: str = ""


# ---------------------------------------------------------------------------
# 核心：对一份"固定购物篮"计算最便宜合规价格
# ---------------------------------------------------------------------------

def _applicable(c: Coupon, cart: Dict[str, int], base_total: float) -> bool:
    """判断优惠券对当前购物篮是否可用。"""
    if c.kind == "item_price":
        return c.target in cart and cart.get(c.target, 0) > 0
    if c.kind == "threshold":
        return base_total >= (c.threshold or 0)
    if c.kind == "bundle_price":
        pool = [i for i in (c.bundle_items or []) if cart.get(i, 0) > 0]
        return len(pool) >= c.min_count
    if c.kind == "free_gift":
        return c.target is None or (c.target in cart and cart.get(c.target, 0) > 0)
    if c.kind == "percent":
        if c.min_spend and base_total < c.min_spend:
            return False
        return True  # 订单级折扣，满额后始终可用
    return False


def _price_with_coupons(cart: Dict[str, int], menu: Dict[str, Item],
                        coupons: List[Coupon]) -> (float, List[str], List[str]):
    """
    对固定购物篮，在所有合规券组合里求最低价。
    返回 (最低价, 使用的券id列表, 赠送单品列表)。
    """
    base_total = sum(menu[code].price * qty for code, qty in cart.items())

    # 候选券组合：
    #   1) 空集
    #   2) 每个不可叠加券单独使用
    #   3) 所有"可叠加券"的子集（可叠加券通常很少，枚举安全）
    stackable = [c for c in coupons if c.stackable and _applicable(c, cart, base_total)]
    non_stack = [c for c in coupons if (not c.stackable) and _applicable(c, cart, base_total)]

    candidate_sets: List[List[Coupon]] = [[]]
    candidate_sets += [[c] for c in non_stack]
    if len(stackable) <= 12:
        for r in range(1, len(stackable) + 1):
            for combo in itertools.combinations(stackable, r):
                candidate_sets.append(list(combo))
    else:
        candidate_sets.append(stackable)  # 退化为"全部叠加券一起用"

    best_price = base_total
    best_gift_count = 0
    best_used: List[str] = []
    best_gifts: List[str] = []
    best_steps: List[dict] = []
    for cs in candidate_sets:
        price, gifts, steps = _apply(cart, menu, cs, base_total)
        price = round2(price)
        # 价格更优则更新；价格相同则优先"白拿赠品"的方案（gifts 更多）
        if (price < best_price - 1e-9) or (
                abs(price - best_price) <= 1e-9 and len(gifts) > best_gift_count):
            best_price = price
            best_gift_count = len(gifts)
            best_used = [c.coupon_id for c in cs]
            best_gifts = gifts
            best_steps = steps
    return (best_price, best_used, best_gifts, best_steps, len(candidate_sets))


def _apply(cart: Dict[str, int], menu: Dict[str, Item], cs: List[Coupon],
           base_total: float) -> (float, List[str], List[dict]):
    """按顺序应用一组券：单品改价 -> 组合价 -> 折扣 -> 满减，并返回逐步明细。"""
    adjusted_unit: Dict[str, float] = {code: menu[code].price for code in cart}
    steps: List[dict] = []
    running = base_total
    # 1) 单品改价：每个单品取可适用的最低改价
    for c in cs:
        if c.kind == "item_price" and c.target in adjusted_unit:
            old_u = adjusted_unit[c.target]
            new_u = min(old_u, c.fixed)
            if new_u < old_u - 1e-9:
                qty = cart.get(c.target, 0)
                before = running
                adjusted_unit[c.target] = new_u
                running = sum(adjusted_unit[code] * q for code, q in cart.items())
                steps.append({"label": "单品改价",
                              "detail": f"{menu[c.target].name} 单价 ¥{old_u:.2f} → ¥{new_u:.2f}（×{qty}）",
                              "before": round2(before), "after": round2(running),
                              "saved": round2((old_u - new_u) * qty)})
    # 用最新单价重算基准小计（无单品改价时等价于 base_total）
    running = sum(adjusted_unit[code] * q for code, q in cart.items())
    # 2) 组合价：从池中选取 min_count 件最便宜的参与组合（贪心）
    bundle_coupons = [c for c in cs if c.kind == "bundle_price"]
    consumed: Dict[str, int] = {}
    gifts: List[str] = []
    for c in bundle_coupons:
        pool = [i for i in (c.bundle_items or []) if (cart.get(i, 0) - consumed.get(i, 0)) > 0]
        if len(pool) < c.min_count:
            continue
        pool.sort(key=lambda i: adjusted_unit[i])
        chosen = pool[:c.min_count]
        original = sum(adjusted_unit[i] for i in chosen)
        delta = round2((c.bundle_price or 0) - original)
        before = running
        running += delta
        names = " + ".join(f"{menu[i].name} ¥{adjusted_unit[i]:.2f}" for i in chosen)
        steps.append({"label": c.desc,
                      "detail": f"从券池任选最便宜的 {c.min_count} 件：{names} 改按组合价 ¥{(c.bundle_price or 0):.2f} 结算",
                      "before": round2(before), "after": round2(running),
                      "saved": round2(-delta)})
        for i in chosen:
            consumed[i] = consumed.get(i, 0) + 1
    # 3) 折扣（先于满减，基于折后金额，更保守）
    for c in cs:
        if c.kind == "percent":
            before = running
            running *= (1 - (c.discount or 0))
            steps.append({"label": c.desc,
                          "detail": f"小计 ¥{before:.2f} ×{1 - (c.discount or 0):.2f}（减 {(c.discount or 0) * 100:.0f}%）",
                          "before": round2(before), "after": round2(running),
                          "saved": round2(before - running)})
    # 4) 满减
    for c in cs:
        if c.kind == "threshold" and running >= (c.threshold or 0):
            before = running
            running -= (c.reduce or 0)
            steps.append({"label": c.desc,
                          "detail": f"小计 ¥{before:.2f} ≥ 门槛 ¥{(c.threshold or 0):.2f}，立减 ¥{(c.reduce or 0):.2f}",
                          "before": round2(before), "after": round2(running),
                          "saved": round2(before - running)})
    # 5) 赠品（不影响应付，仅作为额外所得记录）
    for c in cs:
        if c.kind == "free_gift" and (c.target is None or c.target in cart):
            if c.gift:
                gifts.append(c.gift)
                steps.append({"label": "赠品",
                              "detail": f"买 {menu[c.target].name if c.target else '任意单品'} 送 {menu[c.gift].name}（免费，不计入应付）",
                              "before": round2(running), "after": round2(running),
                              "saved": 0, "gift": True})
    return max(round2(running), 0.0), gifts, steps


# ---------------------------------------------------------------------------
# 对外 API
# ---------------------------------------------------------------------------

def cheapest_for_wishlist(wishlist: List[str], menu: Dict[str, Item],
                          coupons: List[Coupon], top_n: int = 3) -> List[Plan]:
    """用户点名了想吃的单品（wishlist 为 code 列表），求最便宜点法。"""
    cart = {code: 1 for code in wishlist if code in menu}
    if not cart:
        return []
    total, used, gifts, steps, tried = _price_with_coupons(cart, menu, coupons)
    plan = Plan(cart=cart, total=total, used_coupons=used, gifts=gifts, steps=steps,
                tried=tried, note="已含你点名的全部单品，并在此基础上套用最优券组合")
    return [plan]


def budget_combos(menu: Dict[str, Item], coupons: List[Coupon],
                 budget: float, top_n: int = 5) -> List[Plan]:
    """
    预算内最值：在 ¥budget 以内，尽量把这笔钱花得值。
    枚举 1~4 件组合（菜单规模下完全可行），取券后价 <= budget 的方案，
    排序优先级：① 券后总价尽量贴近预算（不浪费、吃得丰盛）；② 同档下省得越多越靠前；③ 件数更多优先。
    """
    codes = list(menu.keys())
    max_items = 4 if len(codes) >= 4 else len(codes)
    candidates: List[Dict[str, int]] = []
    for d in range(1, max_items + 1):
        for grp in itertools.combinations(codes, d):
            candidates.append({c: 1 for c in grp})

    plans: List[Plan] = []
    for cart in candidates:
        total, used, gifts, steps, tried = _price_with_coupons(cart, menu, coupons)
        if total <= budget + 1e-9:
            original = sum(menu[code].price * qty for code, qty in cart.items())
            saved = round2(original - total)
            plans.append(Plan(cart=cart, total=total, used_coupons=used,
                             gifts=gifts, steps=steps, tried=tried,
                             saved=saved,
                             note=f"原价¥{original:.2f}，省¥{saved:.2f}"))
    # 券后总价优先（贴近预算） → 省得越多 → 件数越多
    plans.sort(key=lambda p: (round(p.total * 1000), round(p.saved * 1000), len(p.cart)),
               reverse=True)
    return plans[:top_n]


def _saved(plan: Plan, menu: Dict[str, Item]) -> float:
    original = sum(menu[code].price * qty for code, qty in plan.cart.items())
    return round2(original - plan.total)


def cart_readable(plan: Plan, menu: Dict[str, Item]) -> str:
    """把方案渲染成人类可读文本。"""
    lines = []
    for code, qty in plan.cart.items():
        name = menu.get(code, Item(code, code, 0)).name
        lines.append(f"  - {name} x{qty} (¥{menu[code].price:.2f}/份)")
    if plan.gifts:
        for g in plan.gifts:
            gn = menu.get(g, Item(g, g, 0)).name
            lines.append(f"  - 【赠品】{gn} x1 (免费)")
    lines.append(f"  应付总价：¥{plan.total:.2f}")
    if plan.used_coupons:
        lines.append(f"  已用券：{', '.join(plan.used_coupons)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _menu_from_json(data) -> Dict[str, Item]:
    menu = {}
    for it in data.get("meals", data.get("items", [])):
        menu[it["code"]] = Item(
            code=it["code"], name=it.get("name", it["code"]),
            price=float(it["price"]), tags=it.get("tags", []))
    return menu


def _coupons_from_json(data) -> List[Coupon]:
    out = []
    for c in data.get("coupons", []):
        out.append(Coupon(
            coupon_id=c["id"], kind=c["kind"],
            target=c.get("target"), fixed=c.get("fixed"),
            discount=c.get("discount"), min_spend=c.get("min_spend"),
            threshold=c.get("threshold"), reduce=c.get("reduce"),
            bundle_items=c.get("bundle_items"), min_count=c.get("min_count", 2),
            bundle_price=c.get("bundle_price"), gift=c.get("gift"),
            stackable=bool(c.get("stackable", False)), desc=c.get("desc", "")))
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Mc. Saving 价格优化器")
    ap.add_argument("--meals", help="MCP query-meals 输出的 JSON 路径")
    ap.add_argument("--coupons", help="MCP 券池输出的 JSON 路径")
    ap.add_argument("--wishlist", help="点名单品 code，逗号分隔")
    ap.add_argument("--budget", type=float, help="预算上限（元）")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--selftest", action="store_true", help="运行自测")
    args = ap.parse_args()

    if args.selftest:
        import selftest
        selftest.run()
        return

    if not args.meals:
        print("请提供 --meals（菜单 JSON）。可用 --selftest 查看离线演示。")
        return

    menu = _menu_from_json(_load_json(args.meals))
    coupons = _coupons_from_json(_load_json(args.coupons)) if args.coupons else []

    if args.wishlist:
        wish = [x.strip() for x in args.wishlist.split(",") if x.strip()]
        plans = cheapest_for_wishlist(wish, menu, coupons, args.top)
    elif args.budget:
        plans = budget_combos(menu, coupons, args.budget, args.top)
    else:
        print("请指定 --wishlist 或 --budget。")
        return

    for i, p in enumerate(plans, 1):
        print(f"\n方案 {i}（应付 ¥{p.total:.2f}）")
        print(cart_readable(p, menu))
        if p.note:
            print(f"  说明：{p.note}")


if __name__ == "__main__":
    main()
