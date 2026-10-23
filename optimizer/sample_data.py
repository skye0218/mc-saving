#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线样例数据：不依赖真实 MCP Token 即可跑通优化器与自测。
数值参考麦当劳常见定价结构（非实时，仅供演示与复现）。
真实使用时，meals / coupons 应来自麦当劳 MCP 的 query-meals 与各类券查询工具。
与 H5 / 小程序 内置样例（shared、app、miniprogram/utils 下的 sample_data）保持一致。
"""

SAMPLE_MEALS = {
    "meals": [
        {"code": "big_mac",      "name": "巨无霸",       "price": 24.50, "tags": ["汉堡", "人气"]},
        {"code": "filet_o_fish", "name": "麦香鱼",       "price": 21.00, "tags": ["汉堡"]},
        {"code": "mc_chicken",   "name": "麦辣鸡腿堡",   "price": 22.00, "tags": ["汉堡"]},
        {"code": "grilled_chicken", "name": "板烧鸡腿堡", "price": 21.00, "tags": ["汉堡"]},
        {"code": "double_cheese", "name": "双层吉士汉堡", "price": 13.00, "tags": ["汉堡"]},
        {"code": "cheese_burger", "name": "吉士汉堡",     "price": 10.00, "tags": ["汉堡"]},
        {"code": "mid_fries",    "name": "中薯条",       "price": 12.00, "tags": ["小食"]},
        {"code": "mc_nuggets_4", "name": "麦乐鸡(4块)",  "price": 13.00, "tags": ["小食"]},
        {"code": "chicken_wings", "name": "麦辣鸡翅",     "price": 12.00, "tags": ["小食"]},
        {"code": "chicken_roll", "name": "老北京鸡肉卷", "price": 12.00, "tags": ["小食"]},
        {"code": "corn_cup",     "name": "玉米杯",       "price": 9.50,  "tags": ["小食"]},
        {"code": "mid_coke",     "name": "中杯可乐",     "price": 10.50, "tags": ["饮料"]},
        {"code": "mid_sprite",   "name": "中杯雪碧",     "price": 10.50, "tags": ["饮料"]},
        {"code": "pulpy_orange", "name": "美汁源果粒橙", "price": 10.50, "tags": ["饮料"]},
        {"code": "coffee",       "name": "鲜煮咖啡",     "price": 12.00, "tags": ["饮料"]},
        {"code": "egg_tart",     "name": "葡式蛋挞",     "price": 8.00,  "tags": ["甜品"]},
        {"code": "cone",         "name": "甜筒",         "price": 4.00,  "tags": ["甜品"]},
        {"code": "mcflurry",     "name": "麦旋风",       "price": 12.00, "tags": ["甜品"]},
        {"code": "apple_pie",    "name": "苹果派",       "price": 7.00,  "tags": ["甜品"]},
        {"code": "hash_brown",   "name": "脆薯饼",       "price": 7.00,  "tags": ["早餐"]},
        {"code": "egg_cheese_muffin", "name": "吉士蛋麦满分", "price": 13.00, "tags": ["早餐"]},
        {"code": "sausage_egg_muffin", "name": "猪柳蛋麦满分", "price": 15.00, "tags": ["早餐"]},
    ]
}

# 优惠券建模（stackable 字段严格遵守活动/平台真实规则）
SAMPLE_COUPONS = {
    "coupons": [
        # 1+1 随心配：从指定池里任选 2 件，组合价 13.9
        {"id": "bundle_11", "kind": "bundle_price",
         "bundle_items": ["big_mac", "filet_o_fish", "mc_chicken", "grilled_chicken",
                         "double_cheese", "cheese_burger", "mid_fries", "mc_nuggets_4",
                         "corn_cup", "hash_brown", "cone", "apple_pie", "chicken_wings",
                         "chicken_roll", "mid_coke", "mid_sprite", "pulpy_orange"],
         "min_count": 2, "bundle_price": 13.90,
         "stackable": True, "desc": "1+1随心配 任选2件¥13.9"},
        # 麦麦省 折扣券：订单满 30 元享 85 折（减 15%）
        {"id": "pct_85", "kind": "percent", "discount": 0.15, "min_spend": 30.0,
         "stackable": True, "desc": "麦麦省 满30元85折(减15%)"},
        # 满 35 减 7
        {"id": "full35_7", "kind": "threshold", "threshold": 35.0, "reduce": 7.0,
         "stackable": True, "desc": "满35减7"},
        # 单品改价：中杯可乐 9.9
        {"id": "item_coke_99", "kind": "item_price", "target": "mid_coke",
         "fixed": 9.90, "stackable": False, "desc": "中杯可乐¥9.9(不可叠加)"},
        # 赠品：买巨无霸送脆薯饼
        {"id": "gift_bigmac", "kind": "free_gift", "target": "big_mac",
         "gift": "hash_brown", "stackable": True, "desc": "买巨无霸送脆薯饼"},
    ]
}
