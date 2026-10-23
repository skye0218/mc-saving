/*
 * Mc. Saving —— 内置真实样例数据（脱敏，纯前端演示用）
 * ------------------------------------------------------------
 * 数值参考麦当劳常见定价结构，由真实 MCP 取数快照整理，非实时。
 * 真实使用时 meals / coupons 应来自麦当劳 MCP 的 query-meals 与各类券查询工具。
 * 同时兼容浏览器 <script> 与 Node / 微信小程序 require()。
 */
(function (global, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    global.McSavingData = factory();
  }
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this), function () {

  var MEALS = {
    "meals": [
      { "code": "big_mac",      "name": "巨无霸",       "price": 24.5,  "tags": ["汉堡", "人气"] },
      { "code": "filet_o_fish", "name": "麦香鱼",       "price": 21.0,  "tags": ["汉堡"] },
      { "code": "mc_chicken",   "name": "麦辣鸡腿堡",   "price": 22.0,  "tags": ["汉堡"] },
      { "code": "grilled_chicken", "name": "板烧鸡腿堡", "price": 21.0, "tags": ["汉堡"] },
      { "code": "double_cheese", "name": "双层吉士汉堡", "price": 13.0, "tags": ["汉堡"] },
      { "code": "cheese_burger", "name": "吉士汉堡",     "price": 10.0, "tags": ["汉堡"] },
      { "code": "mid_fries",    "name": "中薯条",       "price": 12.0,  "tags": ["小食"] },
      { "code": "mc_nuggets_4", "name": "麦乐鸡(4块)",  "price": 13.0,  "tags": ["小食"] },
      { "code": "chicken_wings", "name": "麦辣鸡翅",     "price": 12.0, "tags": ["小食"] },
      { "code": "chicken_roll", "name": "老北京鸡肉卷", "price": 12.0, "tags": ["小食"] },
      { "code": "corn_cup",     "name": "玉米杯",       "price": 9.5,   "tags": ["小食"] },
      { "code": "mid_coke",     "name": "中杯可乐",     "price": 10.5,  "tags": ["饮料"] },
      { "code": "mid_sprite",   "name": "中杯雪碧",     "price": 10.5,  "tags": ["饮料"] },
      { "code": "pulpy_orange", "name": "美汁源果粒橙", "price": 10.5,  "tags": ["饮料"] },
      { "code": "coffee",       "name": "鲜煮咖啡",     "price": 12.0,  "tags": ["饮料"] },
      { "code": "egg_tart",     "name": "葡式蛋挞",     "price": 8.0,   "tags": ["甜品"] },
      { "code": "cone",         "name": "甜筒",         "price": 4.0,   "tags": ["甜品"] },
      { "code": "mcflurry",     "name": "麦旋风",       "price": 12.0,  "tags": ["甜品"] },
      { "code": "apple_pie",    "name": "苹果派",       "price": 7.0,   "tags": ["甜品"] },
      { "code": "hash_brown",   "name": "脆薯饼",       "price": 7.0,   "tags": ["早餐"] },
      { "code": "egg_cheese_muffin", "name": "吉士蛋麦满分", "price": 13.0, "tags": ["早餐"] },
      { "code": "sausage_egg_muffin", "name": "猪柳蛋麦满分", "price": 15.0, "tags": ["早餐"] }
    ]
  };

  var COUPONS = {
    "coupons": [
      { "id": "bundle_11", "kind": "bundle_price",
        "bundle_items": ["big_mac", "filet_o_fish", "mc_chicken", "grilled_chicken",
                          "double_cheese", "cheese_burger", "mid_fries", "mc_nuggets_4",
                          "corn_cup", "hash_brown", "cone", "apple_pie", "chicken_wings",
                          "chicken_roll", "mid_coke", "mid_sprite", "pulpy_orange"],
        "min_count": 2, "bundle_price": 13.9,
        "stackable": true, "desc": "1+1随心配 任选2件¥13.9" },
      { "id": "pct_85", "kind": "percent", "discount": 0.15, "min_spend": 30.0,
        "stackable": true, "desc": "麦麦省 满30元85折(减15%)" },
      { "id": "full35_7", "kind": "threshold", "threshold": 35.0, "reduce": 7.0,
        "stackable": true, "desc": "满35减7" },
      { "id": "item_coke_99", "kind": "item_price", "target": "mid_coke",
        "fixed": 9.9, "stackable": false, "desc": "中杯可乐¥9.9(不可叠加)" },
      { "id": "gift_bigmac", "kind": "free_gift", "target": "big_mac",
        "gift": "hash_brown", "stackable": true, "desc": "买巨无霸送脆薯饼" }
    ]
  };

  return { MEALS: MEALS, COUPONS: COUPONS };
});
